import os
import base64
import tempfile
import time
from typing import Union

import asyncio
import logging
import dotenv

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler
)

from core.ai import (
    chat, 
    audio_chat, 
    bhashini_text_chat, 
    bhashini_audio_chat,
    parse_photo_text
    # process_image
)

from utils.redis_utils import (
    set_redis,
    get_redis_value,
    delete_redis
)
# import pytesseract
# from PIL import Image
from utils.openai_utils import (
    get_duration_pydub, 
    get_random_wait_messages
)

dotenv.load_dotenv("ops/.env")

token = os.getenv('TELEGRAM_BOT_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# class BotInitializer:
#     _instance = None
#     run_once = False
    
#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super(BotInitializer, cls).__new__(cls)
#             cls.run_once = True
#         return cls._instance

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # BotInitializer()  # To initialize only once

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Hello I am Yojana Didi , please share your details with me."
        # func to take consent from user to be added later
    )
    try:
        context.user_data.clear()
        keys_to_delete = ['otp_verified','thread_id', 'chat_id', 'PID','number'] # 'assistant_id'
        # Delete the specified keys
        for key in keys_to_delete:
            delete_redis(key)
    except:
        print("some keys could not be found")
    await relay_handler(update, context)

async def relay_handler(update: Update, context: CallbackContext):
    await language_handler(update, context)
    
async def language_handler(update: Update, context: CallbackContext):
    # Handle user's language selection
    keyboard = [
        [InlineKeyboardButton("English", callback_data='1')],
        [InlineKeyboardButton("हिंदी", callback_data='2')],
        [InlineKeyboardButton("मराठी", callback_data='3')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Choose a Language:", 
        reply_markup=reply_markup
    )

async def preferred_language_callback(update: Update, context: CallbackContext):
    
    callback_query = update.callback_query
    languages = {"1": "en", "2": "hi", "3": "mr"}
    try:
        preferred_language = callback_query.data
        lang = languages.get(preferred_language)
        context.user_data['lang'] = lang
    except (AttributeError, ValueError):
        lang = 'en'
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="Error getting language! Setting default to English."
        )
    
    text_message = ""
    if lang == "en":
        text_message = "You have chosen English. \nPlease share your details. What is your 10 digit mobile number?"
    elif lang == "hi":
        text_message = "आपने हिंदी चुनी है. \n कृपया मुझे अपने बारे में बताएं। आपका 10 अंकों वाला मोबाइल नंबर क्या है?"
    elif lang == "mr":
        text_message = "तुम्ही मराठीची निवड केली आहे. \n कृपया तुमचे तपशील शेअर करा। तुमचा 10 अंकी मोबाईल नंबर काय आहे?"
        
    # set_redis('lang', lang)
    
    await context.bot.send_message(
    chat_id=update.effective_chat.id, 
    text=text_message
)

async def response_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await query_handler(update, context)

# def check_change_language_query(text):
#     return text.lower() in ["change language", "set language", "language"]

async def query_handler(update: Update, context: CallbackContext):

    lang = context.user_data.get('lang')
    if not lang:
        await language_handler(update, context)
        return

    if update.message.text:
        text = update.message.text # add mobile number here in text 
        print(f"text is {text}")
        # if check_change_language_query(text):
        #     await language_handler(update, context)
        #     return
        await chat_handler(update, context, text)
    elif update.message.voice:
        voice = await context.bot.get_file(update.message.voice.file_id)
        await talk_handler(update, context, voice)
    # elif update.message.photo:
    #     photo = await context.bot.get_file(update.message.photo[-1].file_id) # update.message.photo[0].file_id
    #     await photo_handler(update, context, photo)

# async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, photo):
    
#     assistant_message = ""
#     chat_id = update.effective_chat.id
#     lang = context.user_data.get('lang')
    
#     with tempfile.NamedTemporaryFile(suffix='.jpg', delete=True) as temp_image_file:
#         await photo.download_to_drive(custom_path=temp_image_file.name)
#         chat_id = update.effective_chat.id

#         wait_message = get_random_wait_messages(
#                 not_always=True,
#                 lang=lang
#         )
#         if wait_message:
#             await context.bot.send_message(chat_id=chat_id, text=wait_message)

#         with open(temp_image_file.name, "rb") as file: # Open the image file in binary mode
#             photo_data = file.read()
#             text = process_image(chat_id, photo_data) # file
#             print(f"text is {text}")
#             text_1 = parse_photo_text(text)
#             assistant_message, history = chat(chat_id, text_1)
#             print(f"assistant_message is {assistant_message}")
#             print(type(assistant_message))
#             # response_photo, assistant_message, history = parse_photo_text(
#             #     chat_id, photo_file=open(temp_image_file.name, "rb")
#             # )
#             # response_photo.stream_to_file(temp_image_file.name)
#             #duration = get_duration_pydub(temp_image_file.name)
#             # await context.bot.send_photo(
#             #     chat_id=chat_id, 
#             #     #photo=open(temp_image_file.name, "rb"), 
#             #     filename="response.jpg",
#             #     performer="Yojana Didi",
#             # )
#             await context.bot.send_message(
#                 chat_id=chat_id, text=assistant_message # try adding [0] if it doesn't work
#             )
#             file.close()

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    response = ""
    chat_id = update.effective_chat.id
    lang = context.user_data.get('lang')
    wait_message = get_random_wait_messages(
        not_always=True,
        lang=lang
    )
    if wait_message:
        await context.bot.send_message(chat_id=chat_id, text=wait_message)
    if lang == 'en':
        response_en, history = chat(chat_id, text)
    else:
        response, response_en, history = bhashini_text_chat(chat_id,text, lang)
    if response:
        await context.bot.send_message(chat_id=chat_id, text=response)
    # set_redis(history, history)
    await context.bot.send_message(chat_id=chat_id, text=response_en)

async def talk_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, voice):    
    lang = context.user_data.get('lang')
    # getting audio file
    audio_file = voice
    # audio_file = await context.bot.get_file(update.message.voice.file_id)

    if lang == 'en':
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_audio_file:
            await audio_file.download_to_drive(custom_path=temp_audio_file.name)
            chat_id = update.effective_chat.id

            wait_message = get_random_wait_messages(
                not_always=True,
                lang=lang
        )
            if wait_message:
                await context.bot.send_message(chat_id=chat_id, text=wait_message)

            with open(temp_audio_file.name, "rb") as file:
                audio_data = file.read()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')

                response_audio, assistant_message, history = audio_chat(
                    chat_id, audio_file=open(temp_audio_file.name, "rb")
                )
                response_audio.stream_to_file(temp_audio_file.name)
                # fix this error "raise JSONDecodeError("Expecting value", s, err.value) from None" here
                # duration = get_duration_pydub(temp_audio_file.name)
                await context.bot.send_audio(
                    chat_id=chat_id, 
                    audio=open(temp_audio_file.name, "rb"), 
                    #duration=duration, 
                    filename="response.wav",
                    performer="Yojana Didi",
                )
                await context.bot.send_message(
                    chat_id=chat_id, text=assistant_message
                )
                file.close()
    else:
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=True) as temp_audio_file: # suffix='.wav'
            await audio_file.download_to_drive(custom_path=temp_audio_file.name)
            chat_id = update.effective_chat.id

            wait_message = get_random_wait_messages(
                    not_always=True,
                    lang=lang
            )
            if wait_message:
                await context.bot.send_message(chat_id=chat_id, text=wait_message)

            with open(temp_audio_file.name, "rb") as file:
                audio_data = file.read()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                response_audio, response, history = bhashini_audio_chat(
                    chat_id, 
                    audio_file=audio_base64, 
                    lang=lang
                )
                file_ = open(temp_audio_file.name, "wb")
                file_.write(response_audio.content)
                file_.close()
                with open(temp_audio_file.name, "rb") as file:
                    duration = get_duration_pydub(temp_audio_file.name)
                    await context.bot.send_audio(
                        chat_id=chat_id, 
                        audio=open(temp_audio_file.name, "rb"), 
                        duration=duration, 
                        filename="response.mp3",
                        performer="Yojana Didi",
                    )
                await context.bot.send_message(
                    chat_id=chat_id, text=response
                )
                file_.close()

# NEW CODE
# from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
# from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from utils.openai_utils import get_full_details
# Define states for our conversation handler
(RELIGION, CASTE, RATION_CARD, LAND_OWNERSHIP, OCCUPATIONAL_STATUS, MONTHLY_INCOME) = range(6)

# Define a dictionary to store user responses
user_responses = {}

async def start_full_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_responses[user_id] = {}
    
    keyboard = [
        [InlineKeyboardButton(religion.split('(')[0], callback_data=religion)]
        for religion in get_full_details['properties']['Religion(CT0000OU)']['enum']
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please select your religion:", reply_markup=reply_markup)
    return RELIGION

async def religion_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_responses[user_id]['Religion(CT0000OU)'] = query.data

    keyboard = [
        [InlineKeyboardButton(caste.split('(')[0], callback_data=caste)]
        for caste in get_full_details['properties']['Caste Category(CT00003I)']['enum']
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Please select your caste category:", reply_markup=reply_markup)
    return CASTE

async def caste_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    selected_caste = query.data
    user_responses[user_id]['Caste Category(CT00003I)'] = query.data

    keyboard = [
        [InlineKeyboardButton(ration.split('(')[0], callback_data=ration)]
        for ration in get_full_details['properties']['Ration card type(CT00001D)']['enum']
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Please select your ration card type:", reply_markup=reply_markup)
    return RATION_CARD

async def ration_card_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    selected_ration = query.data
    user_responses[user_id]['Ration card type(CT00001D)'] = query.data

    keyboard = [
        [InlineKeyboardButton(land.split('(')[0], callback_data=land)]
        for land in get_full_details['properties']['Land Ownership(CT0001AJ)']['enum']
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Please select your land ownership status:", reply_markup=reply_markup)
    return LAND_OWNERSHIP

async def land_ownership_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    selected_land = query.data
    user_responses[user_id]['Land Ownership(CT0001AJ)'] = query.data

    keyboard = [
        [InlineKeyboardButton(status.split('(')[0], callback_data=status)]
        for status in get_full_details['properties']['Occupational Status(CT0000PF)']['enum']
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Please select your occupational status:", reply_markup=reply_markup)
    return OCCUPATIONAL_STATUS

async def occupational_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_responses[user_id]['Occupational Status(CT0000PF)'] = query.data

    await query.edit_message_text("Please enter your monthly income:")
    return MONTHLY_INCOME

async def monthly_income(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_responses[user_id]['Personal Monthly Income(CT000013)'] = float(update.message.text)

    # Process the collected data
    await process_full_details(update, context, user_responses[user_id])
    del user_responses[user_id]  # Clean up
    return ConversationHandler.END

async def process_full_details(update: Update, context: ContextTypes.DEFAULT_TYPE, details: dict):
    chat_id = update.effective_chat.id
    # Call the existing process_full_details function from ai.py
    # You'll need to modify this function to accept the details directly
    assistant_message, history = await process_full_details(chat_id, details, context.bot_data['thread_id'], context.bot_data['run_id'])
    await update.message.reply_text(assistant_message)

# Add this to your main() function


if __name__ == '__main__':
    application = ApplicationBuilder().token(
        token
    ).read_timeout(30).write_timeout(30).build()
    start_handler = CommandHandler('start', start)
    language_handler_ = CommandHandler('set_language', language_handler)
    chosen_language = CallbackQueryHandler(preferred_language_callback, pattern='[1-3]')
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('full_details', start_full_details)],
        states={
            RELIGION: [CallbackQueryHandler(religion_callback)],
            CASTE: [CallbackQueryHandler(caste_callback)],
            RATION_CARD: [CallbackQueryHandler(ration_card_callback)],
            LAND_OWNERSHIP: [CallbackQueryHandler(land_ownership_callback)],
            OCCUPATIONAL_STATUS: [CallbackQueryHandler(occupational_status_callback)],
            MONTHLY_INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, monthly_income)],
        },
        fallbacks=[],
)
    # otp_handler = MessageHandler((filters.TEXT & (~filters.COMMAND)) | (filters.VOICE & (~filters.COMMAND)), OTP_handler)
    # otpv_handler = MessageHandler((filters.TEXT & (~filters.COMMAND)) | (filters.VOICE & (~filters.COMMAND)), OTP_handler_1)
    application.add_handler(start_handler)
    application.add_handler(language_handler_)
    application.add_handler(chosen_language)
    application.add_handler(conv_handler)
    # application.add_handler(otp_handler)
    application.add_handler(
        MessageHandler(
            (filters.TEXT & (~filters.COMMAND)) | (filters.VOICE & (~filters.COMMAND)), 
            response_handler
        )
    )
    application.run_polling()

