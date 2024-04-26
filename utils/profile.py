import requests
import json

from datetime import date
from pydantic import BaseModel, Field, validator
from typing import Literal
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
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJvcmdhbml6YXRpb25faWQiOjE5LCJzdGF0ZSI6Ik1haGFyYXNodHJhIiwidXNlcl9pZCI6Mjg5NjAsImlkIjoyODk2MCwiZXhwIjoxNzE0MTQ1NjI5fQ.59HQnIt5iYaE9IVj8_zFd7ev7Kpp-pPHn1d0lJ5ZJio'
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
            return answer.get("data")["personId"] # returns the person id of profile just created
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
  
    token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJvcmdhbml6YXRpb25faWQiOjE5LCJzdGF0ZSI6Ik1haGFyYXNodHJhIiwidXNlcl9pZCI6Mjg5NjAsImlkIjoyODk2MCwiZXhwIjoxNzE0MTQ1NjI5fQ.59HQnIt5iYaE9IVj8_zFd7ev7Kpp-pPHn1d0lJ5ZJio'
    # lang = 'en'
    headers = {
        'Authorization': 'Bearer ' + token,
        'content-type': 'application/json',
        'User-Agent': '*/*'
        }
    response = requests.get('https://testapi.haqdarshak.com/elastic/lgd?req_type=get_states&lang='+lang, headers=headers)
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
    
    headers = {
        'Authorization': 'Bearer ' + token,
        'content-type': 'application/json',
        'User-Agent': '*/*'
        }
    response = requests.get('https://testapi.haqdarshak.com/elastic/lgd?req_type=get_villages_by_block_sub_district&sub_district_code='+sub_district_code+'&block_code='+block_code+'&lang='+lang, headers=headers)
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