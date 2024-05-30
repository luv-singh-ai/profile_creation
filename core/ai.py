from openai import OpenAI
import numpy as np
import cv2
import pytesseract
# from utils.digit_utils import (
#     get_auth_token, 
#     file_complaint, 
#     search_complaint
# )
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
import cv2
import pytesseract

load_dotenv(
    dotenv_path="ops/.env",
)

openai_api_key = os.getenv("OPENAI_API_KEY")

# USERNAME = os.getenv("USERNAME")
# PASSWORD = os.getenv("PASSWORD")

assistant_id = get_redis_value("assistant_id")

print(f"assistant id is {assistant_id}")

client = OpenAI(
    api_key=openai_api_key,
)

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
    if thread_id:
        thread = client.beta.threads.retrieve(thread_id)
        thread_id = thread.id
    else:
        thread = create_thread(client)
        thread_id = thread.id
    return thread_id

def gather_user_details(input_message, history, assistant_id):
    """
    Converse with the user and gather details using 
    openAI assistant API
    """
    thread_id = history.get("thread_id")
    status = history.get("status")
    print(thread_id, input_message, assistant_id)
    run_id, status = upload_message(client, thread_id, input_message, assistant_id)
    print("run.status is", status)
    run_id, status = get_run_status(client, thread_id, run_id)
    print(f"input message is {input_message}")
    print(f"run status is {status}")
    if status == "completed":
        assistant_message = get_assistant_message(client, thread_id)
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
            assistant_message = "something went wrong please check the openAI API"
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
#     # The JSON string containing the function arguments
#     '''
#     parameters = 
#     {
#     "Religion(CT0000OU)": "Hinduism(CT0000OT)",
#     "Caste Category(CT00003I)": "OBC(LT000004)",
#     "Ration card type(CT00001D)": "Above Poverty Line(CT00002C)",
#     "Land Ownership(CT0001AJ)": "Yes - for agriculture(CT0001AH)",
#     "Occupational Status(CT0000PF)": "Working(CT00019G)",
#     "Nature of Job(CT000015)": "Farmer(CT0000BU)"
#     }
#     '''

#     response = client.chat.completions.create(
#                         model="gpt-4",
#                         response_format={ "type": "json_object" },
#                         messages=[
#                             {"role": "system", "content": 
#                                 '''
#                                 "You are a helpful assistant designed to convert the provided JSON data into the desired format,you would perform the following steps:
#                                 Create a New Dictionary: For each key-value pair in the original JSON, create a new dictionary where:
#                                 The key "concept" corresponds to the concept code extracted from the original key.
#                                 The key "value" corresponds to the value code extracted from the original value.
#                                 eg if input is {"Religion(CT0000OU)": "Hinduism(CT0000OT)","Caste Category(CT00003I)": "OBC(LT000004)"}, then output will be 
#                                 {"concept": "CT0000OU", "value": "CT0000OT"},{"concept": "CT00003I", "value": "LT000004"}
#                                 '''},
#                             {"role": "user", "content": parameters}
#                             ]
#                         )
#     print(response.choices[0].message.content)

#     # Extracting the concept codes and their values
#     output = [{"concept": key.split('(')[1].split(')')[0], "value": value.split('(')[1].split(')')[0]} for key, value in params.items()]

#     if isinstance(output, list):
#         # Print the output list of dictionaries
#         print(json.dumps(output, indent=2))
#         return output
#     else:
#         return False

def process_parameters(parameters):
    # print(parameters)
    output = extract_codes(parameters)
    print(output)
    
    if isinstance(output, list):
        # Print the output list of dictionaries
        print(json.dumps(output, indent=2))
        return output
    else:
        return False

def extract_codes(data):
    """ Extract concept and value codes from a dictionary with improved efficiency and readability """
    output = [{
        "concept": decode_if_bytes(parse_code(key)),
        "value": decode_if_bytes(parse_code(value)) if isinstance(value, str) else value
    } for key, value in data.items()]
    return output

def parse_code(text):
    """ Utility function to parse codes from text contained within parentheses """
    if '(' in text and ')' in text:
        return text.split('(')[1].split(')')[0]
    return text

def decode_if_bytes(item):
    """ Utility function to decode bytes to string if needed """
    return item.decode('utf-8') if isinstance(item, bytes) else item

# def extract_codes(data):
#     output = []
#     for key, value in data.items():
#         concept = key.split('(')[1].split(')')[0]  # Extract concept code from key
#         if isinstance(value, str) and '(' in value and ')' in value:
#             value_code = value.split('(')[1].split(')')[0]  # Extract value code from value if it is string and contains parentheses
#         else:
#             value_code = value  # Use value as is if it doesn't contain parentheses or is not a string
#         if isinstance(value_code, bytes):
#             value_code = value_code.decode('utf-8')
#         if isinstance(concept, bytes):
#             concept = concept.decode('utf-8')
#         output.append({"concept": concept, "value": value_code})
#     return output

def process_full_details(parameters, tool_id, thread_id, run_id):
    """
    save the responses of full details
    """
    PID = 0
    PID = get_redis_value("PID") # IF PID FAILS, RESORT TO DEFAULT OR ANOTHER METHOD
    print(PID)
    details = process_parameters(parameters)
    print(details)
    try:
        ans = mini_screening(PID, details)
        print(ans)
    except Exception as e:
        print(e)

    if ans == "Success": # if ans is True
        tool_output_array = [
            {
                "tool_call_id": tool_id,
                "output": "Success"
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
            assistant_message = "something went wrong please check the openAI API"
        # print(f"assistant message is {assistant_message}")

        history = {
            "thread_id": thread_id,
            "run_id": run_id,
            "status": status,
        }
        return assistant_message, history
    else:
        error = "Profile creation failed. Please try again later."
        print(error)
        history = {
            "thread_id": thread_id,
            "run_id": run_id,
            "status": "failed",
        }
        return error, history

def process_function_calls(tools_to_call, thread_id, run_id):
    """
    Method to manage all function calls using openAI
    """
    for tool in tools_to_call:
        func_name = tool.function.name
        print(f"function name is {func_name}")
        parameters = compose_function_call_params(
            func_name, tool.function.arguments
        )
        if func_name == "get_user_details":
            assistant_message, history = process_profile(
                parameters, tool.id, thread_id, run_id
            )
        elif func_name == "get_full_details":
            assistant_message, history = process_full_details(
                parameters, tool.id, thread_id, run_id
            )
        else:
            assistant_message = "This functionality is not supported yet. Please try again later."
            history = {
                "thread_id": thread_id,
                "run_id": run_id,
                "status": "requires_action",
            }
    return assistant_message, history

def compose_function_call_params(func_name, arguments): # this function can be removed
    """
    Compose function call parameters based on the args
    provided by openAI function calling API
    """
    print(f"function name is {func_name}")
    parameters = json.loads(arguments)
    return parameters


# def get_miniscreening_questions():
#     url = "http://testapi.haqdarshak.com/api/get_miniscreening_questions_api"

#     payload = json.dumps({
#     "state": "Maharashtra",
#     "lang": "en"
#     })
#     headers = {
#     'Content-Type': 'application/json'
#     }

#     response = requests.request("POST", url, headers=headers, data=payload)

#     print(response.text)
#     return response.json()

def chat(chat_id, input_message, client=client, assistant_id=assistant_id):
    """
    Main chat logic using OpenAI assistant API and function calling API
    """
    # setting default assistant_message
    assistant_message = "Something went wrong. Please try again later."    
    history = get_metadata(chat_id)
    print(history)
    thread_id = history.get("thread_id")
    run_id = history.get("run_id")
    status = history.get("status")
    thread_id = get_or_create_thread_id(client, thread_id)
    history["thread_id"] = thread_id
    print(f"thread id is {thread_id}")
    if status == "failed":
        run = client.beta.threads.runs.cancel(
                thread_id=thread_id,
                run_id=run_id
        )
        status = None
    if status == "completed" or status == None: # s1
        assistant_message, history = gather_user_details( 
            input_message, history, assistant_id
        )      
        thread_id, run_id, status = set_metadata(chat_id, history)
        history = {
            "thread_id": thread_id,
            "run_id": run_id,
            "status": status,
        }
    if status == "requires_action":
        tools_to_call, run_id, status = get_tools_to_call( # s2
            client, thread_id, run_id
        )
        assistant_message, history = process_function_calls( #s3
            tools_to_call, thread_id, run_id
        )
        thread_id, run_id, status = set_metadata(chat_id, history)

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


def parse_photo_text(photo_text):
    """
    Method to parse text from a photo
    """
    prompt = '''
    You are a helpful assistant that reads extracted text data from an image. the image data is read using opencv and pytesseract, so they are slightly jumbled together. 
    Your task is to read the given text and identitfy entites like first name, last name, mobile number, gender, marital status, and date of birth (dob). If some details are not possible, ask the user to input it as text.  
    Whatever entites you're able to identify, try to organize this information into a structured JSON string with the following format:
    {
    "firstName": <value>,
    "lastName": <value>,
    "mobile": <value>,
    "gender": <value>,
    "maritalStatus": <value>,
    "dob": <value>,
    }
    '''
    response = ""
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt.replace('\n', ' ')},
            {"role": "user", "content": photo_text}
        ]
    )

    try:
        print(f"completion is {completion}\n\n")
        # print("completion is", completion, "\n\n")
        response = completion.choices[0].message.content
        print(f"response_text is {response}")
        print(type(response))
        #response = json.loads(response)
    except Exception as e:
        print(e)
        response = "Cannot read image. Input all details as text"
    return response

def process_image(chat_id, image_data):
    """
    Process the uploaded image and extract text using OCR.

    Parameters:
    - chat_id (int): The ID of the chat.
    - image_data (str): Binary data of the uploaded image.

    Returns:
    - text (str): The extracted text from the image.
    """
    # Process the uploaded image as needed
    # Decode the image from binary data
    image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply thresholding to preprocess the image
    threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    # Set the path to the Tesseract executable
    pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'

    # Perform text extraction using pytesseract
    text = pytesseract.image_to_string(threshold)
    print(f"text from inside the func is {text}")

    return text

