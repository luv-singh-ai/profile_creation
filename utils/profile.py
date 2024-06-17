import requests
import json
import re
from datetime import date
from pydantic import BaseModel, Field, validator
from typing import Literal

from utils.redis_utils import (
    get_redis_value,
    set_redis,
)
# Define a Pydantic model for user data
class User(BaseModel):
    firstName: str = Field(..., min_length=1)
    lastName: str = Field(..., min_length=1)
    mobile: str 
    gender: str # Literal["male", "female", "other"] = Field(...)
    maritalStatus: str # Literal["single", "married", "divorced", "widowed"] = Field(...)
    dob: date = Field(...)
    # state: int
    # district: int 
    @validator('dob', pre=True)
    def parse_dob(cls, value):
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                raise ValueError(f"Invalid date format for dob: {value}")
        return value

def generate_token():

    url = "https://testapi.haqdarshak.com/api/generate_token"

    payload = json.dumps({
    "api_key": "346ca1a3fb416f084b8e737970f57751",
    "secret_key": "358567b4d67e639bbb02bb02e6df58605eed447a",
    "state_code": "MH", # change state code as per state_code
    "agent_id": "451"
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    token_res = json.loads(response.text)
    token = token_res.get("token")
    return token

def generate_otp(text):
    # extract 10 digit mobile number from text and send OTP
    match = re.search(r'(\+91[-\s]?|0)?(\d{10})\b', text) # re.sub(pattern, text)
    
    if not match:
        return None # when there is no mobile number in text
    
    num =  match.group(2)
    # print(type(num))
    
    url = "https://testapi.haqdarshak.com/api/send_otp"
    token = generate_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    payload = json.dumps({
        "mobile": num
    })
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()  # Raise an error for bad status codes
        print(response.text)
        set_redis("number", str(num)) # Redis can only store strings
        return True
    except requests.RequestException as e:
        print(f"Error: {e}")
        return None

def verify_otp(text):
    # extract 6 digit OTP
    # text = json.dumps(text) if text is JSON file 
    match = re.search(r'\b\d{6}\b', text)
    
    if not match:
        return None # when there is no OTP in text
    
    otp = match.group()  # Extracted OTP
    print(otp)
    
    url = "https://testapi.haqdarshak.com/api/verify_otp"
    token = generate_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    num = get_redis_value("number").decode('utf-8') # Use decode('utf-8') to convert the byte string back to a regular string.
    
    print("Number is", num)
    payload = json.dumps({
            "mobile": num,
            "otp": otp
    })
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()  # Raise an error for bad status codes
        print(response.text)
        return True
    except requests.RequestException as e:
        print(f"Error: {e}")
        return False

def profile_creation(parameters: dict) -> int:
    url = "https://testapi.haqdarshak.com/api/create_citizen"
    '''parameters = {"firstName": value, "lastName": value, "mobile": value, "gender": value, 
    "maritalStatus": value, "dob": value, "state": value, "district": value, "livingType": value, 
    "ulb": value, "ward": value, "pincode": value}
    '''
    location_details = {"state": 27, "district": 468, "livingType": "urban", "ulb": 251323, "ward": 65537, "pincode": "422603"}
    parameters.update(location_details)
    print(parameters)
    
    try:
        payload = json.dumps(parameters)
    except Exception as e:
        print(e)
        # payload = json.dumps({
        #     "firstName": "Shriram",
        #     "lastName": "Kanawade",
        #     "mobile": "7020922248",
        #     "gender": "M",
        #     "maritalStatus": "Married",
        #     "dob": "1992-04-11",
        #     "state": 27,
        #     "district": 468,
        #     "livingType": "urban",
        #     "ulb": 251323,
        #     "ward": 65537,
        #     "pincode": "422603"
        # })
    # crating new auth token 
    token = generate_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text) # it's in string format - {"code": 200, "message": "Success", "data": {"personId": 505099}}
    # type(response) is <class 'requests.models.Response'>
    try:
        answer = json.loads(response.text)
    except Exception as e:
        print(e)
        print(response.status_code)
        return 0 # 0 for false profile creation
    try:
        if answer.get("code") == 200 and answer.get("message") == "Success":
            print("Done!")
            PID = answer.get("data")["personId"]
            return PID # returns the person id of profile just created
    except Exception as e:
        print(e)
        print(response.status_code)
        return 0 # 0 for false profile creation

def mini_screening(PID, details):
    url = "https://testapi.haqdarshak.com/api/save_mini_scr_question"
    # PID = get_redis_value(PID)
    print(type(PID))
    print(type(details))
    # json_payload = json.dumps(details)
    payload = json.dumps({
    "personId": int(PID),
    "answers": details
    })
    token = generate_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        print(response.text)
        return "Success"
    except Exception as e:
        print(e)
        print(response.status_code)
        return 0 # 0 for false profile creation
 
# if __name__ == '__main__':
#     message = ""
#     message = profile_creation({}, "")
#     print(message)

def get_location_details(data, lang, state_code = 27, district_code = 468 , sub_district_code = 45, village_code = 10, ulb_code = 251323, ward_code = 65537, pincode = 422603):
    # sub_district_code = 45, village_code = 10 are random values
    # url = "https://testapi.haqdarshak.com/api/get_location_details"
    # payload = json.dumps(data)
    
    # USE PINCODE TO CAPTURE ADDRESS
  
    token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJvcmdhbml6YXRpb25faWQiOjE5LCJzdGF0ZSI6Ik1haGFyYXNodHJhIiwidXNlcl9pZCI6Mjg5NjAsImlkIjoyODk2MCwiZXhwIjoxNzE0MTQ1NjI5fQ.59HQnIt5iYaE9IVj8_zFd7ev7Kpp-pPHn1d0lJ5ZJio'
    # lang = 'en'
    headers = {
        'Authorization': 'Bearer ' + token,
        'content-type': 'application/json',
        'User-Agent': '*/*'
        }
    response = requests.get('https://testapi.haqdarshak.com/elastic/lgd?req_type=get_states&lang='+lang, headers=headers) # english - 'en' and Hindi - 'Hi', marathi - 'mr'
    states = response.json()['data']
    
    headers = {
        'Authorization': 'Bearer ' + token,
        'content-type': 'application/json',
        'User-Agent': '*/*'
        }
    response = requests.get('https://testapi.haqdarshak.com/elastic/lgd?req_type=get_districts_by_state&state_code='+state_code+'&lang='+lang, headers=headers)
    districts = response.json()['data']
    
    headers = {
        'Authorization': 'Bearer ' + token,
        'content-type': 'application/json',
        'User-Agent': '*/*'
        }
    response = requests.get('https://testapi.haqdarshak.com/elastic/lgd?req_type=get_blocks_by_district&district_code='+district_code+'&lang='+lang, headers=headers)
    blocks = response.json()['data']
    
    headers = {
        'Authorization': 'Bearer ' + token,
        'content-type': 'application/json',
        'User-Agent': '*/*'
        }
    response = requests.get('https://testapi.haqdarshak.com/elastic/lgd?req_type=get_sub_districts_by_district&district_code='+district_code+'&lang='+lang, headers=headers)
    subDistricts = response.json()['data']
    
    # headers = {
    #     'Authorization': 'Bearer ' + token,
    #     'content-type': 'application/json',
    #     'User-Agent': '*/*'
    #     }
    # response = requests.get('https://testapi.haqdarshak.com/elastic/lgd?req_type=get_villages_by_block_sub_district&sub_district_code='+sub_district_code+'&block_code='+block_code+'&lang='+lang, headers=headers)
    villages = response.json()['data']
    
    headers = {
        'Authorization': 'Bearer ' + token,
        'content-type': 'application/json',
        'User-Agent': '*/*'
        }
    response = requests.get('https://testapi.haqdarshak.com/elastic/lgd?req_type=get_pincode_by_village&village_code='+village_code+'&lang='+lang, headers=headers)
    pincodes = response.json()['data']
    
    headers = {
        'Authorization': 'Bearer ' + token,
        'content-type': 'application/json',
        'User-Agent': '*/*'
        }
    response = requests.get('https://testapi.haqdarshak.com/elastic/lgd?req_type=get_ulb_by_district&district_code='+district_code+'&lang='+lang, headers=headers)
    ulbs = response.json()['data']
    
    headers = {
        'Authorization': 'Bearer ' + token,
        'content-type': 'application/json',
        'User-Agent': '*/*'
        }
    response = requests.get('https://testapi.haqdarshak.com/elastic/lgd?req_type=get_wards_by_ulb&localbody_code='+ulb_code+'&lang='+lang, headers=headers)
    wards = response.json()['data']
    
    headers = {
        'Authorization': 'Bearer ' + token,
        'content-type': 'application/json',
        'User-Agent': '*/*'
        }
    response = requests.get('https://testapi.haqdarshak.com/elastic/lgd?req_type=get_pincode_by_ulb&localbody_code='+ulb_code+'&lang='+lang, headers=headers)
    pincodes = response.json()['data']