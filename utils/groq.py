'''
using groq
'''
import os
from dotenv import load_dotenv
import requests
import json

load_dotenv(
    dotenv_path="ops/.env",
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

from llama_index.llms.groq import Groq

def groq_chat(input_message): # chat_id, 
    llm = Groq(model="mixtral-8x7b-32768", api_key=GROQ_API_KEY)
    response = llm.complete("Explain the importance of low latency LLMs")
    print(response)
    
    # for streaming responses 
    response = llm.stream_complete("Explain the importance of low latency LLMs")
    for r in response:
        print(r.delta, end="")
    
    
# from llama_index.core.llms import ChatMessage

# messages = [
#     ChatMessage(
#         role="system", content="You are a pirate with a colorful personality"
#     ),
#     ChatMessage(role="user", content="What is your name"),
# ]
# resp = llm.chat(messages)
    
if __name__=="__main__":
    # chat_id = 1234567890
    # input_message = "hi"
    # assistant_message, history = chat(chat_id, input_message)
    # assistant_message, history = bhashini_text_chat(chat_id, input_message, "en")
    # assistant_message, history = bhashini_audio_chat(chat_id, input_message, "en")
    # assistant_message, history = audio_chat(chat_id, input_message)
    input_message = "hi"
    groq_chat(input_message)