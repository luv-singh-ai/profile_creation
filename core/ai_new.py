from openai import OpenAI
import numpy as np

from utils.profile import (
    generate_otp, 
    verify_otp
    )
from utils.openai_utils import (
    create_run,
    create_thread,
    upload_message,
    get_run_status,
    get_assistant_message,
    create_assistant,
    transcribe_audio,
    generate_audio,
    get_tools_to_call
)
from utils.redis_utils import (
    get_redis_value,
    set_redis,
    delete_redis
)

from utils.bhashini_utils import (
    bhashini_translate,
    bhashini_asr,
    bhashini_tts
)

from utils.profile import (
    profile_creation,
    mini_screening
)

import os
import json
import time
from dotenv import load_dotenv

load_dotenv(
    dotenv_path="ops/.env",
)

openai_api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key=openai_api_key,
)

try:
    # assistant_id = get_redis_value("assistant_id")
    assistant_id = os.getenv("ASSISTANT_ID")
    print(f"assistant id is {assistant_id}")
    assistant = client.beta.assistants.retrieve(assistant_id=assistant_id)
except Exception as e:
    print(e)
    assistant = create_assistant(client, assistant_id)
    assistant_id = assistant.id


def get_metadata(chat_id):
    """
    Get thread_id, run_id and status from redis
    """
    history = get_redis_value(chat_id)
    if history == None:
        history = {
            "thread_id": None,
            "run_id": None,
            "status": None,
        }
    else:
        history = json.loads(history)
    return history

def set_metadata(chat_id, history):
    """
    Set thread_id, run_id and status in redis
    """
    set_redis(chat_id, json.dumps(history))
    thread_id = history.get("thread_id")
    run_id = history.get("run_id")
    status = history.get("status")
    return thread_id, run_id, status

def get_or_create_thread_id(client, thread_id):
    """
    Get thread_id if exists else create a new thread
    using openAI assistant API
    """
    # Replace retriving thread as concurrent requests are getting merged into a single thread
    
    try:
        thread = create_thread(client) # switched blocks here
        thread_id = thread.id
    except:
        thread = client.beta.threads.retrieve(thread_id)
        thread_id = thread.id
    return thread_id

def gather_user_details(input_message, history, assistant_id):
    """
    Converse with the user and gather details using 
    openAI assistant API
    """
    thread_id = history.get("thread_id")
    print("Thread ID is", thread_id)
    status = history.get("status")
    print(thread_id, input_message, assistant_id)
    run_id, status = upload_message(client, thread_id, input_message, assistant_id)
    
    print("run.status is", status)
    run_id, status = get_run_status(client, thread_id, run_id)
    print(f"input message is {input_message}")
    print(f"run status is {status}")
    if status == "completed":
        assistant_message = get_assistant_message(client, thread_id)
        set_redis('conversation_complete', "True")
    else:
        assistant_message = "something went wrong please check the openAI API"
        # call the function

    print(f"assistant message is {assistant_message}")

    history = {
        "thread_id": thread_id,
        "run_id": run_id,
        "status": status,
    }
    return assistant_message, history


def process_profile(parameters, tool_id, thread_id, run_id):
    """
    Creates the citizen profile and get the person_id when the action required is profile_creation
    """
    try:
        # otp_verified = get_redis_value("otp_verified")
        otp_verified = get_redis_value('otp_verified')
        print("OTP verified data is :", otp_verified)
        # otp_check = False
        if otp_verified != "True":
            error = "OTP not verified. Please verify OTP before creating profile."
            history = {
                "thread_id": thread_id,
                "run_id": run_id,
                "status": "failed",
            }
            return error, history
        else:
            if history['status'] == 'completed':
                set_redis('conversation_complete', "True")
    except Exception as e:
        print(e)
    
    try:
        add_1 = get_redis_value("keyboard_details")
        keyboard_details_1 = json.loads(add_1)
        parameters.update(keyboard_details_1)
        print(parameters)
    except Exception as e:
        print(e)
    
    id = profile_creation(parameters) # id is int
    set_redis("PID", id)
    if id != 0:
        person_id = str(id)
        tool_output_array = [
            {
                "tool_call_id": tool_id,
                "output": person_id
            }
        ]
        run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=tool_output_array
        )
        run_id, status = get_run_status(client, thread_id, run.id)

        if status == "completed":
            assistant_message = get_assistant_message(client, thread_id)
        else:
            assistant_message = "process profile not completed"
        print(f"assistant message is {assistant_message}")

        history = {
            "thread_id": thread_id,
            "run_id": run_id,
            "status": status,
        }
        return assistant_message, history
    else:
        error = "Profile creation failed. Please try again later."
        history = {
            "thread_id": thread_id,
            "run_id": run_id,
            "status": "failed",
        }
        return error, history

# def process_parameters(parameters):
#     print(parameters)
#     output = extract_codes(parameters)
#     print(output)
    
#     if isinstance(output, list):
#         # Print the output list of dictionaries
#         print(json.dumps(output, indent=2))
#         return output
#     else:
#         return False


def process_OTP(parameters, tool_id, thread_id, run_id):
    """
    Sends the OTP 
    """
    number = parameters.get("num") 
    # check number is string or integer if error
    print("number is", number)
        
    if generate_otp(number):
        # set_redis("current_mobile", number) 
        tool_output_array = [
            {
                "tool_call_id": tool_id,
                "output": number # True
            }
        ]
        run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=tool_output_array
        )
        run_id, status = get_run_status(client, thread_id, run.id)

        if status == "completed":
            assistant_message = get_assistant_message(client, thread_id)
        else:
            assistant_message = "couldn't get the assistant message. Please try again later."
        # print(f"assistant message is {assistant_message}")

        history = {
            "thread_id": thread_id,
            "run_id": run_id,
            "status": status,
        }
        return assistant_message, history
    else:
        error = "Failed to gererate OTP for this Number. Please try again later."
        print(error)
        history = {
            "thread_id": thread_id,
            "run_id": run_id,
            "status": "failed",
        }
        return error, history
    
def process_vOTP(parameters, tool_id, thread_id, run_id):
    """
    Verify the OTP 
    """
    otp = parameters.get("OTP") 
    print("Submitted OTP is", otp)
    print("type of parameters is: ", type(parameters))

    # stored_number = get_redis_value("current_mobile")
    
    if verify_otp(otp):
        
        set_redis("otp_verified", "True")
        
        tool_output_array = [
            {
                "tool_call_id": tool_id,
                "output": "success" # -> indicates that the OTP was successfully verified.
            }
        ]
        run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=tool_output_array
        )
        run_id, status = get_run_status(client, thread_id, run.id)

        if status == "completed":
            assistant_message = get_assistant_message(client, thread_id)
        else:
            assistant_message = "couldn't get the assistant message. Please try again later."
        # print(f"assistant message is {assistant_message}")

        history = {
            "thread_id": thread_id,
            "run_id": run_id,
            "status": status,
        }
        # history['otp_value'] = True
        return assistant_message, history
    else:
        error = "Failed to verify OTP for this Number. Please try again later." # Do not proceed further without verifying the OTP
        print(error)
        history = {
            "thread_id": thread_id,
            "run_id": run_id,
            "status": "failed",
        }
        # history['otp_value'] = False
        return error, history

def process_function_calls(tools_to_call, thread_id, run_id):
    for tool in tools_to_call:
        func_name = tool.function.name
        parameters = json.loads(tool.function.arguments)
        
        if func_name == "get_user_details":
            assistant_message, history = process_user_details(parameters, tool.id, thread_id, run_id)
        elif func_name == "get_OTP":
            assistant_message, history = process_OTP(parameters, tool.id, thread_id, run_id)
        elif func_name == "verify_OTP":
            assistant_message, history = process_vOTP(parameters, tool.id, thread_id, run_id)
        else:
            assistant_message = "This functionality is not supported yet. Please try again later."
            history = {
                "thread_id": thread_id,
                "run_id": run_id,
                "status": "requires_action",
            }
    return assistant_message, history

# def process_user_details(parameters, tool_id, thread_id, run_id):
#     chat_id = thread_id  # Assuming thread_id is unique per user
#     user_details = json.loads(get_redis_value(f'user_details_{chat_id}') or '{}')
#     user_details.update(parameters)
#     set_redis(f'user_details_{chat_id}', json.dumps(user_details))
    
#     tool_output_array = [
#         {
#             "tool_call_id": tool_id,
#             "output": json.dumps(user_details)
#         }
#     ]
    
#     run = client.beta.threads.runs.submit_tool_outputs(
#         thread_id=thread_id,
#         run_id=run_id,
#         tool_outputs=tool_output_array
#     )
    
#     run_id, status = get_run_status(client, thread_id, run.id)
    
#     if status == "completed":
#         assistant_message = get_assistant_message(client, thread_id)
#     else:
#         assistant_message = "Could not process user details. Please try again."
    
#     history = {
#         "thread_id": thread_id,
#         "run_id": run_id,
#         "status": status,
#     }
    
#     return assistant_message, history

def compose_function_call_params(func_name, arguments): # this function can be removed
    """
    Compose function call parameters based on the args
    provided by openAI function calling API
    """
    print(f"function name is {func_name}")
    parameters = json.loads(arguments)
    return parameters


def chat(chat_id, input_message, client=client, assistant_id=assistant_id):
    """
    Main chat logic using OpenAI assistant API and function calling API
    """
    assistant_message = ""  
    history = get_metadata(chat_id)
    print(history)
    
    try: 
        thread_id = history.get("thread_id")
        if thread_id is None:
            thread_id = get_or_create_thread_id(client, thread_id)
            history["thread_id"] = thread_id
            print(f"thread id is {thread_id}")
        run_id = history.get("run_id")
        status = history.get("status")
    except Exception as e:
        print(e)

    if status == None: #
        assistant_message, history = gather_user_details( 
            input_message, history, assistant_id
        )      
        thread_id, run_id, status = set_metadata(chat_id, history)
        history = {
            "thread_id": thread_id,
            "run_id": run_id,
            "status": status,
        }
        # we can add set_redis(conversation_complete = True) here
        print("history is \n", history)
    
    if status == "requires_action":
        tools_to_call, run_id, status = get_tools_to_call( # s2
            client, thread_id, run_id
        )
        assistant_message, history = process_function_calls( #s3
            tools_to_call, thread_id, run_id
        )
        thread_id, run_id, status = set_metadata(chat_id, history)

        # user_details = json.loads(get_redis_value(f'user_details_{chat_id}') or '{}')
        # if 'firstName' in user_details and 'lastName' in user_details and 'dob' in user_details:
        #     set_redis('conversation_complete', "True")
    if status == "failed":
        run = client.beta.threads.runs.cancel(
                thread_id=thread_id,
                run_id=run_id
        )
        status = None

    return assistant_message, history

def audio_chat(chat_id, audio_file):
    """
    Audio chat logic using OpenAI tts and stt
    """
    input_message = transcribe_audio(audio_file, client)
    assistant_message, history =  chat(chat_id, input_message)
    response_audio = generate_audio(assistant_message, client)
    return response_audio, assistant_message, history

def bhashini_text_chat(chat_id, text, lang): 
    """
    bhashini text chat logic
    """
    input_message = bhashini_translate(text, lang, "en")
    response_en, history = chat(chat_id, input_message)
    response = bhashini_translate(response_en, "en", lang)
    return response, response_en, history

def bhashini_audio_chat(chat_id, audio_file, lang):
    """
    bhashini voice chat logic
    """
    input_message = bhashini_asr(audio_file, lang, "en")
    response, history = chat(chat_id, input_message)
    response = bhashini_translate(response, "en", lang)
    audio_content = bhashini_tts(response, lang)
    return audio_content, response, history