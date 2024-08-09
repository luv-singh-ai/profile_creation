from openai import OpenAI
from dotenv import load_dotenv
from utils.bhashini_utils import bhashini_translate
from utils.redis_utils import set_redis
import random
from pydub import AudioSegment # type: ignore
import time
import os
import json

from utils.bhashini_utils import (
    bhashini_translate,
    bhashini_asr,
    bhashini_tts
)

# import anthropic
# claude_api_key = os.getenv("ANTHROPIC_API_KEY")
load_dotenv(
    dotenv_path="ops/.env",
)

openai_api_key = os.getenv("OPENAI_API_KEY")
model_name = os.getenv("MODEL_NAME")

client = OpenAI(
    api_key=openai_api_key,
)

# Mixtral performs best at generating JSON, followed by Gemma, then Llama

from groq import Groq
groq_api_key = os.getenv("GROQ_API_KEY")
groq_model = os.getenv("GROQ_CHAT_MODEL")
client_1 = Groq(api_key=groq_api_key)

def chat_completion(chat_id, text, track):
    
    if track == 1:
        with open("prompts/prompt_s.txt", "r") as file:
            prompt = file.read().replace('\n', ' ')
    else:
        with open("prompts/prompt_s1.txt", "r") as file:
            prompt = file.read().replace('\n', ' ')
    
    chat_completion = client_1.chat.completions.create(
        messages=[
            # Set an optional system message. This sets the behavior of the
            # assistant and can be used to provide specific instructions for
            # how it should behave throughout the conversation.
            {
                "role": "system",
                "content": prompt
            },
            # Set a user message for the assistant to respond to.
            {
                "role": "user",
                "content": text,
            }
        ],

        # The language model which will generate the completion.
        model=groq_model,
        temperature=0.1,
        max_tokens=100,
        top_p=1,
        # A stop sequence is a predefined or user-specified text string that
        # signals an AI to stop generating content, ensuring its responses
        # remain focused and concise. Examples include punctuation marks and
        # markers like "[end]".
        stop=None,
        # If set, partial message deltas will be sent.
        stream=False,
        response_format={"type": "json_object"},
    )

    ans = chat_completion.choices[0].message.content
    print("type is :", type(ans))
    print(ans)
    return ans


# def chat_completion(chat_id, text, track):
#     client = anthropic.Anthropic(api_key = claude_api_key)
    
#     if track == 1:
#         with open("prompts/prompt_s.txt", "r") as file:
#             prompt = file.read().replace('\n', ' ')
#     else:
#         with open("prompts/prompt_s1.txt", "r") as file:
#             prompt = file.read().replace('\n', ' ')
    
#     model_name = "claude-3-5-sonnet-20240620"
#     message = client.messages.create(
#             model=model_name,
#             max_tokens=100,
#             temperature=0.1,
#             system=prompt,
#             messages=[
#                 {
#                     "role": "user",
#                     "content": [
#                         {
#                             "type": "text",
#                             "text": text
#                         }
#                     ]
#                 }
#             ],
#             # response_format={"type": "json_object"}  # Specify JSON output
#         )
#     ans =  message.content[0].text # message.content
    
#     try:
#         # Attempt to parse the response as JSON
#         json_response = json.loads(ans)
#         print("Response type:", type(json_response))
#         print(json.dumps(json_response, indent=2))
#         return json_response
#     except json.JSONDecodeError:
#         print("Error: Response is not valid JSON")
#         return {"error": "Invalid JSON response"}

# def chat_completion(chat_id, text, track):
#     '''
#     SAMPLE JSON SCHEMA
#     {
#         "firstName": <value>,
#         "lastName": <value>
#     }
#     '''
#     if track == 1:
#         with open("prompts/prompt_s.txt", "r") as file:
#             prompt = file.read().replace('\n', ' ')
#     else:
#         with open("prompts/prompt_s1.txt", "r") as file:
#             prompt = file.read().replace('\n', ' ')
    
#     completion = client.chat.completions.create(
#         model=model_name,
#         messages=[
#             {"role": "system", "content": prompt},
#             {"role": "user", "content": text},
#         ],
#         response_format={"type": "json_object"},
#         # temperature=0.1,
#         # stream=True 
#     )
#     # for chunk in completion:
#     #     return chunk.choices[0].delta
#     ans = completion.choices[0].message.content
#     print("type is :", type(ans))
#     print(ans)
#     return ans

def audio_chat(chat_id, track, lang, audio_file):
    """
    Audio chat logic using OpenAI tts and stt
    """
    input_message = transcribe_audio(audio_file, client) # client_1 for groq whisper v3 model
    print(f"input_message is: ", input_message)
    translated_message = bhashini_translate(input_message, lang, "en")
    response_json =  chat_completion(chat_id, translated_message, track)
    print(f"response_json is: ", response_json)
    response = json.dumps(response_json)
    print(f"response is: ", response)
    response_audio = generate_audio(response, client)
    return response_audio, response_json

# def bhashini_text_chat(chat_id, text, lang): 
#     """
#     bhashini text chat logic
#     """
#     input_message = bhashini_translate(text, lang, "en")
#     response_json= chat_completion(chat_id, input_message)
#     response_en = json.loads(response_json)
#     response = bhashini_translate(response_en, "en", lang)
#     return response, response_en

# def bhashini_audio_chat(chat_id, audio_file, lang):
#     """
#     bhashini voice chat logic
#     """
#     input_message = bhashini_asr(audio_file, lang, "en")
#     response_json = chat_completion(chat_id, input_message)
#     response = json.loads(response_json)
#     response = bhashini_translate(response, "en", lang)
#     audio_content = bhashini_tts(response, lang)
#     return audio_content, response

def transcribe_audio(audio_file, client):
    transcription = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file, 
        response_format="text"
    )
    msg = transcription # transcription.text
    print(msg)
    return msg

'''
def transcribe_audio(audio_file, client_1):
    transcription = client.audio.transcriptions.create(
        
        file=audio_file, # (filename, file.read())
        model="whisper-large-v3",
        #   prompt="Specify context or spelling",  # Optional
        #   response_format="json",  # Optional
        #   language="en",  # Optional
        #   temperature=0.0  # Optional
        )
    msg = transcription.text
    print(msg)
    return msg
'''

def generate_audio(text, client):
    response = client.audio.speech.create(
                model="tts-1",
                voice="nova", # original = alloy
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
