import os
import base64
import tempfile
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler,
    filters, CallbackContext, CallbackQueryHandler, ConversationHandler
)
from core.ai import chat, audio_chat, bhashini_text_chat, bhashini_audio_chat
from utils.redis_utils import set_redis, get_redis_value, delete_redis
from utils.openai_utils import get_duration_pydub, get_random_wait_messages
import dotenv

dotenv.load_dotenv("ops/.env")

token = os.getenv('TELEGRAM_BOT_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Define conversation states
LANGUAGE, CHAT, GENDER, MARITAL_STATUS = range(4)

# Define keyboard layouts
gender_keyboard = [['Male', 'Female', 'Other']]
marital_status_keyboard = [['Married', 'Divorced', 'Single', 'Widowed', 'Others']]
keyboard_details = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Hello, I am Yojana Didi. Please share your details with me."
    )
    try:
        context.user_data.clear()
        keys_to_delete = ['otp_verified', 'thread_id', 'chat_id', 'PID', 'number','conversation_complete', 'keyboard_details']
        for key in keys_to_delete:
            delete_redis(key)
    except Exception as e:
        logging.error(f"Error clearing data: {e}")
    
    return await language_handler(update, context)

async def language_handler(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("English", callback_data='en')],
        [InlineKeyboardButton("हिंदी", callback_data='hi')],
        [InlineKeyboardButton("मराठी", callback_data='mr')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Choose a Language:", 
        reply_markup=reply_markup
    )
    return LANGUAGE

async def language_callback(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    lang = query.data
    context.user_data['lang'] = lang
    
    messages = {
        "en": "You have chosen English. What is your 10 digit mobile number?",
        "hi": "आपने हिंदी चुनी है। आपका 10 अंकों का मोबाइल नंबर क्या है?",
        "mr": "तुम्ही मराठीची निवड केली आहे। तुमचा 10 अंकी मोबाईल नंबर काय आहे?"
    }
    await query.edit_message_text(text=messages.get(lang, messages["en"]))
    return CHAT

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    
    if update.message.text:
        assistant_message, history = await text_chat_handler(update, context, update.message.text)
    elif update.message.voice:
        voice = await context.bot.get_file(update.message.voice.file_id)
        assistant_message, history = await voice_chat_handler(update, context, voice)
    else:
        await update.message.reply_text("Sorry, I can only process text or voice messages.")
        return CHAT

    # Check if the conversation is complete
    item = get_redis_value('conversation_complete')
    conversation_complete =  item.decode('utf-8') if isinstance(item, bytes) else item
    print("conversation_complete data is :", conversation_complete)
    
    if conversation_complete == "True":
        # Reset the conversation_complete flag
        # set_redis('conversation_complete', "False")
        
        lang = context.user_data.get('lang', 'en')
        messages = {
            "en": "Please select your gender:",
            "hi": "कृपया अपना लिंग चुनें:",
            "mr": "कृपया तुमचे लिंग निवडा:"
        }
        gender_keyboard = [['Male', 'Female', 'Other']]
        await update.message.reply_text(
            messages.get(lang, messages["en"]),
            reply_markup=ReplyKeyboardMarkup(gender_keyboard, one_time_keyboard=True)
        )
        return GENDER
    else:
        return CHAT

async def text_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    chat_id = update.effective_chat.id
    lang = context.user_data.get('lang', 'en')
    wait_message = get_random_wait_messages(not_always=True, lang=lang)
    if wait_message:
        await context.bot.send_message(chat_id=chat_id, text=wait_message)
    
    if lang == 'en':
        response_en, history = chat(chat_id, text)
        await context.bot.send_message(chat_id=chat_id, text=response_en)
    else:
        response, response_en, history = bhashini_text_chat(chat_id, text, lang)
        if response:
            await context.bot.send_message(chat_id=chat_id, text=response)
        await context.bot.send_message(chat_id=chat_id, text=response_en)
    
    return response_en, history

async def voice_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, voice) -> None:
    lang = context.user_data.get('lang', 'en')
    chat_id = update.effective_chat.id

    with tempfile.NamedTemporaryFile(suffix='.wav' if lang == 'en' else '.mp3', delete=True) as temp_audio_file:
        await voice.download_to_drive(custom_path=temp_audio_file.name)
        
        wait_message = get_random_wait_messages(not_always=True, lang=lang)
        if wait_message:
            await context.bot.send_message(chat_id=chat_id, text=wait_message)

        with open(temp_audio_file.name, "rb") as file:
            audio_data = file.read()
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            if lang == 'en':
                response_audio, assistant_message, history = audio_chat(chat_id, audio_file=file)
                response_audio.stream_to_file(temp_audio_file.name)
            else:
                response_audio, response, history = bhashini_audio_chat(chat_id, audio_file=audio_base64, lang=lang)
                with open(temp_audio_file.name, "wb") as file_:
                    file_.write(response_audio.content)

            duration = get_duration_pydub(temp_audio_file.name)
            await context.bot.send_audio(
                chat_id=chat_id, 
                audio=open(temp_audio_file.name, "rb"), 
                duration=duration, 
                filename="response.wav" if lang == 'en' else "response.mp3",
                performer="Yojana Didi",
            )
            await context.bot.send_message(
                chat_id=chat_id, 
                text=assistant_message if lang == 'en' else response
            )

async def gender_handler(update: Update, context: CallbackContext) -> int:
    gender_dict = {"Male": "M", "Female": "F", "Other": "O"}
    keyboard_details['gender'] = gender_dict.get(update.message.text)
    
    lang = context.user_data.get('lang', 'en')
    messages = {
        "en": "Thank you. Now, please select your marital status:",
        "hi": "धन्यवाद। अब, कृपया अपनी वैवाहिक स्थिति चुनें:",
        "mr": "धन्यवाद. आता, कृपया तुमची वैवाहिक स्थिती निवडा:"
    }
    await update.message.reply_text(
        messages.get(lang, messages["en"]),
        reply_markup=ReplyKeyboardMarkup(marital_status_keyboard, one_time_keyboard=True)
    )
    return MARITAL_STATUS

async def marital_status_handler(update: Update, context: CallbackContext) -> int:
    keyboard_details['marital_status'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    messages = {
        "en": f"Thank you for providing your information!\n\n",
        "hi": f"जानकारी प्रदान करने के लिए धन्यवाद!\n\n",
        "mr": f"माहिती प्रदान केल्याबद्दल धन्यवाद!\n\n"
    }
    await update.message.reply_text(
        messages.get(lang, messages["en"]),
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Store keyboard_details in Redis
    set_redis("keyboard_details", json.dumps(keyboard_details))
    
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "Operation cancelled. To start again, use the /start command.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token(token).read_timeout(30).write_timeout(30).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LANGUAGE: [CallbackQueryHandler(language_callback)],
            CHAT: [MessageHandler(filters.TEXT | filters.VOICE, chat_handler)],
            GENDER: [MessageHandler(filters.Regex('^(Male|Female|Other)$'), gender_handler)],
            MARITAL_STATUS: [MessageHandler(filters.Regex('^(Married|Divorced|Single|Widowed|Others)$'), marital_status_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=False
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
