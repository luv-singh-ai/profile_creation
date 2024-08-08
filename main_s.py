import os
import json
import re
import tempfile
import base64
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove # type: ignore
from telegram.ext import ( # type: ignore
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, filters, ConversationHandler, CallbackContext
)
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationInfo, field_validator

from datetime import date, datetime
from typing import Literal
from utils.profile import generate_otp, verify_otp, profile_creation
from utils.openai_utils_s import chat_completion, audio_chat, get_duration_pydub
from utils.MESSAGES import MESSAGES
# from utils.openai_utils_s import bhashini_text_chat, bhashini_audio_chat
from utils.redis_utils import set_redis, get_redis_value

load_dotenv("ops/.env")

token = os.getenv('TELEGRAM_BOT_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Define conversation states
LANGUAGE, MOBILE, OTP, NAME, DOB, GENDER, MARITAL_STATUS, FINAL = range(8)

# Pydantic model for user data validation
class User(BaseModel):
    firstName: str = Field(..., min_length=1)
    lastName: str = Field(..., min_length=1)
    mobile: str
    gender: Literal["M", "F", "O"]
    maritalStatus: Literal["Single", "Married", "Divorced", "Widowed", "Others"]
    dob: str

    @field_validator('mobile')
    def validate_mobile(cls, v: str, info: ValidationInfo) -> str:
        if not re.match(r'^\d{10}$', v):
            raise ValueError('Mobile number must be 10 digits')
        return v

    @field_validator('dob')
    def validate_dob(cls, v: str) -> str:
        try:
            # Parse the input string to a date object
            dob_date = datetime.strptime(v, "%Y-%m-%d").date()
            
            # Compare with today's date
            if dob_date >= date.today():
                raise ValueError('Date of birth cannot be in the future')
            
            # If all checks pass, return the original string
            return v
        except ValueError as e:
            # This will catch both parsing errors and our custom future date error
            raise ValueError(f"Invalid date of birth: {str(e)}")

# # Rate limiting constants
# MAX_OTP_REQUESTS = 5
# OTP_WINDOW_SECONDS = 3600  # 1 hour
# Rate limiting tracker
# otp_request_tracker = {}

# Define keyboard layouts
LANGUAGE_KEYBOARD = [['English', 'हिंदी', 'मराठी']]
GENDER_KEYBOARD = [['Male', 'Female', 'Other']]
MARITAL_STATUS_KEYBOARD = [['Single', 'Married', 'Divorced', 'Widowed', 'Others']]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(MESSAGES['en']['welcome'])
    try:
        context.user_data.clear()
    except AttributeError:
        context.user_data = {}
    return await language_handler(update, context)

async def language_handler(update: Update, context: CallbackContext) -> int:
    reply_markup = ReplyKeyboardMarkup(LANGUAGE_KEYBOARD, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(MESSAGES['en']['choose_language'], reply_markup=reply_markup)
    return LANGUAGE

async def language_callback(update: Update, context: CallbackContext) -> int:
    lang_map = {'English': 'en', 'हिंदी': 'hi', 'मराठी': 'mr'}
    lang = lang_map.get(update.message.text, 'en')
    context.user_data['lang'] = lang
    await update.message.reply_text(MESSAGES[lang]['provide_mobile'])
    return MOBILE

async def mobile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get('lang', 'en')
    match = re.search(r'(\+91[-\s]?|0)?(\d{10})\b', update.message.text)
    if not match:
        await update.message.reply_text(MESSAGES[lang]['invalid_mobile'])
        return MOBILE
    
    num = match.group(2)
    context.user_data['mobile'] = num
    if generate_otp(num):
        await update.message.reply_text(MESSAGES[lang]['otp_sent'])
        context.user_data['otp_attempts'] = 0
        return OTP
    else:
        await update.message.reply_text(MESSAGES[lang]['otp_failed'])
        return ConversationHandler.END

async def otp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get('lang', 'en')
    otp = update.message.text
    context.user_data['otp_attempts'] = context.user_data.get('otp_attempts', 0) + 1
    num = context.user_data['mobile']
    if verify_otp(otp, num):
        await update.message.reply_text(MESSAGES[lang]['otp_verified'])
        return NAME
    else:
        if context.user_data['otp_attempts'] >= 5:
            num = context.user_data['mobile']
            if generate_otp(num):
                await update.message.reply_text(MESSAGES[lang]['otp_max_attempts'])
                context.user_data['otp_attempts'] = 0
            else:
                await update.message.reply_text(MESSAGES[lang]['otp_gen_failed'])
                return ConversationHandler.END
        else:
            await update.message.reply_text(MESSAGES[lang]['otp_invalid'].format(5 - context.user_data['otp_attempts']))
        return OTP

async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get('lang', 'en')
    # chat_id = update.effective_chat.id
    
    if update.message.text:
        response = await text_chat_handler(update, context, update.message.text, 1)
    elif update.message.voice:
        voice = await context.bot.get_file(update.message.voice.file_id)
        response = await voice_chat_handler(update, context, voice)
    else:
        await update.message.reply_text(MESSAGES[lang]['input_error'])
        return NAME
        
    try:
        print(f"Response from chat completion: {response}")
        parsed_data = json.loads(response)
        # parsed_data = response
        print("type of parsed_data is:", type(parsed_data))
        # Check if parsed_data is a dictionary
        if not isinstance(parsed_data, dict):
            raise ValueError("Parsed data is not a dictionary")
        
        if parsed_data.get('firstName') == 'None' or parsed_data.get('lastName') == 'None':
            await update.message.reply_text(MESSAGES[lang]['invalid_name'])
            return NAME
        
        try: 
            context.user_data.update(parsed_data)
            print(f"Updated user data: {context.user_data}")
        except Exception as e:
            print(e)
            for key, value in parsed_data.items():
                context.user_data[key] = value
            print(f"Updated user data: {context.user_data}")
        
        await update.message.reply_text(MESSAGES[lang]['ask_dob'])
        return DOB
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {str(e)}")
        await update.message.reply_text(MESSAGES[lang]['parse_error'])
        return NAME
    except ValueError as e:
        print(f"Value error: {str(e)}")
        await update.message.reply_text(MESSAGES[lang]['parse_error'])
        return NAME

async def dob_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get('lang', 'en')
    # chat_id = update.effective_chat.id
    
    if update.message.text:
        response = await text_chat_handler(update, context, update.message.text, 2)
    elif update.message.voice:
        voice = await context.bot.get_file(update.message.voice.file_id)
        response = await voice_chat_handler(update, context, voice)
    else:
        await update.message.reply_text(MESSAGES[lang]['input_error'])
        return DOB
        
    try:
        print(f"Response from chat completion: {response}")
        parsed_data = json.loads(response)
        if parsed_data.get('dob') == 'None':
            await update.message.reply_text(MESSAGES[lang]['invalid_dob'])
            return DOB
        
        try: 
            context.user_data.update(parsed_data)
            print(f"Updated user data: {context.user_data}")
        except Exception as e:
            print(e)
            for key, value in parsed_data.items():
                context.user_data[key] = value
            print(f"Updated user data: {context.user_data}")
        
        await update.message.reply_text(
            MESSAGES[lang]['select_gender'],
            reply_markup=ReplyKeyboardMarkup(GENDER_KEYBOARD, one_time_keyboard=True, resize_keyboard=True)
        )
        return GENDER
    except AttributeError:
        await update.message.reply_text(MESSAGES[lang]['invalid_dob'])
        return DOB

async def text_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, track):
    chat_id = update.effective_chat.id
    lang = context.user_data.get('lang', 'en')
    # if lang == 'en':
    response_json = chat_completion(chat_id, text, track)
    
    # try:
    #     response_en = json.dumps(response_json)
    #     print("output is ", type(response_en))
    # # await context.bot.send_message(chat_id=chat_id, text=response_en)
    # except Exception as e:
    #     print(f"Error occurred while processing text chat: {str(e)}")
    #     # await context.bot.send_message(chat_id=chat_id, text=MESSAGES[lang]['process_error'])
    #     return None
    #     # await context.bot.send_message(chat_id=chat_id, text=(MESSAGES['en']['msg']))
    # return response_en
    return response_json

async def voice_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, voice) -> None:
    lang = context.user_data.get('lang', 'en')
    chat_id = update.effective_chat.id

    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_audio_file:
            await voice.download_to_drive(custom_path=temp_audio_file.name)
            
            with open(temp_audio_file.name, "rb") as file:
                response_audio, response_text = audio_chat(chat_id, audio_file=file)
            
            # Process the response text through chat_completion
            response_json = chat_completion(chat_id, response_text)
            response = json.dumps(response_json)
        
        duration = get_duration_pydub(temp_audio_file.name)
        await context.bot.send_audio(
            chat_id=chat_id,
            audio=open(temp_audio_file.name, "rb"),
            duration=duration,
            filename="response.wav" if lang == 'en' else "response.mp3",
            performer="Yojana Didi",
        )
    
    except Exception as e:
        print(f"Error occurred while processing voice chat: {str(e)}")
        await context.bot.send_message(chat_id=chat_id, text=MESSAGES[lang]['process_error'])
        return None
        # with tempfile.NamedTemporaryFile(suffix='.wav' if lang == 'en' else '.mp3', delete=True) as temp_audio_file:
        #     await voice.download_to_drive(custom_path=temp_audio_file.name)
        #     with open(temp_audio_file.name, "rb") as file:
        #         audio_data = file.read()
        #         audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        #         if lang == 'en':
        #             response_audio, response = audio_chat(chat_id, audio_file=file)
        #             # response_audio.with_streaming_response.method(temp_audio_file.name)
        #             # response_audio.with_streaming_response.method()
        #         else:
        #             response_audio, response = audio_chat(chat_id, audio_file=file)
        #             # response_audio, response = bhashini_audio_chat(chat_id, audio_file=audio_base64, lang=lang)
        #             with open(temp_audio_file.name, "wb") as file_:
        #                 file_.write(response_audio.content)
    
    return response

async def gender_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get('lang', 'en')
    gender_dict = {"Male": "M", "Female":"F", "Other": "O"}
    context.user_data['gender'] = gender_dict.get(update.message.text)
    await update.message.reply_text(
        MESSAGES[lang]['select_marital'],
        reply_markup=ReplyKeyboardMarkup(MARITAL_STATUS_KEYBOARD, one_time_keyboard=True, resize_keyboard=True) 
    )
    return MARITAL_STATUS

async def marital_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['maritalStatus'] = update.message.text
    return await final_handler(update, context)

async def final_handler(update: Update, context: CallbackContext) -> int:
    lang = context.user_data.get('lang', 'en')
    try:
        if isinstance(context.user_data.get('dob'), date):
            context.user_data['dob'] = context.user_data['dob'].strftime("%Y_%m_%d")
        user_data = User(**context.user_data)
        # print("type of user_data is (should be dict)", type(user_data.model_dump()))
        person_id = profile_creation(user_data.model_dump())
        
        if person_id:
            profile_summary = MESSAGES[lang]['profile_created'].format(**user_data.model_dump(), person_id=person_id)
            await update.message.reply_text(profile_summary, reply_markup=ReplyKeyboardRemove())
        else:
            await update.message.reply_text(MESSAGES[lang]['profile_failed'], reply_markup=ReplyKeyboardRemove())
    
    except ValueError as e:
        await update.message.reply_text(MESSAGES[lang]['invalid_data'].format(str(e)), reply_markup=ReplyKeyboardRemove())
    
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    lang = context.user_data.get('lang', 'en')
    await update.message.reply_text(MESSAGES[lang]['cancelled'], reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token(token).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LANGUAGE: [MessageHandler(filters.Regex('^(English|हिंदी|मराठी)$'), language_callback)],
            MOBILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, mobile_handler)],
            OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, otp_handler)],
            NAME: [MessageHandler((filters.TEXT | filters.VOICE) & ~filters.COMMAND, name_handler)],
            DOB: [MessageHandler((filters.TEXT | filters.VOICE) & ~filters.COMMAND, dob_handler)],
            GENDER: [MessageHandler(filters.Regex('^(Male|Female|Other)$'), gender_handler)],
            MARITAL_STATUS: [MessageHandler(filters.Regex('^(Single|Married|Divorced|Widowed)$'), marital_status_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()