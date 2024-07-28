from openai import OpenAI
from dotenv import load_dotenv
from utils.bhashini_utils import bhashini_translate
from utils.redis_utils import set_redis
import random
from pydub import AudioSegment
import time
import os

from utils.bhashini_utils import (
    bhashini_translate,
    bhashini_asr,
    bhashini_tts
)

load_dotenv(
    dotenv_path="ops/.env",
)

openai_api_key = os.getenv("OPENAI_API_KEY")
model_name = os.getenv("MODEL_NAME")

client = OpenAI(
    api_key=openai_api_key,
)

def chat_completion(chat_id, text):
    '''
    FINAL JSON SCHEMA
    {
        "firstName": <value>,
        "lastName": <value>,
        "dob": <value>,
    }
    '''
    with open("prompts/prompt_s.txt", "r") as file: # original prompt_v2 version
        prompt = file.read().replace('\n', ' ')
    
    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ], 
        temperature=0.1,
        # stream=True
        # { "type": "json_object" } - to produce only json
    )
    # for chunk in completion:
    #     return chunk.choices[0].delta
    ans = completion.choices[0].message.content
    print("type is :", type(ans))
    return ans

def audio_chat(chat_id, audio_file):
    """
    Audio chat logic using OpenAI tts and stt
    """
    input_message = transcribe_audio(audio_file, client)
    response, history =  chat_completion(chat_id, input_message)
    response_audio = generate_audio(response, client)
    return response_audio, response, history

def bhashini_text_chat(chat_id, text, lang): 
    """
    bhashini text chat logic
    """
    input_message = bhashini_translate(text, lang, "en")
    response_en= chat_completion(chat_id, input_message)
    response = bhashini_translate(response_en, "en", lang)
    return response, response_en

def bhashini_audio_chat(chat_id, audio_file, lang):
    """
    bhashini voice chat logic
    """
    input_message = bhashini_asr(audio_file, lang, "en")
    response, history = chat_completion(chat_id, input_message)
    response = bhashini_translate(response, "en", lang)
    audio_content = bhashini_tts(response, lang)
    return audio_content, response, history

def transcribe_audio(audio_file, client):
    transcript = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file
    )
    return transcript.text

def generate_audio(text, client):
    response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
    return response

def get_duration_pydub(file_path):
    try:
        audio_file = AudioSegment.from_file(file_path)
        duration = audio_file.duration_seconds
        return duration
    except Exception as e:
        print(f"Error occurred while getting duration: {e}")
        return None
