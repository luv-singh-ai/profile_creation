import requests
import json
import re

# from utils.profile import generate_token

'''  
def OTP_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: #  context: CallbackContext)
    # Handle user's OTP verification
    if update.message.voice:
        # input_message = transcribe_audio(audio_file, client)
        pass
    
    text = update.message.text
    print(f"text is {text}")
    # Send a copy of the received message
    # await message.send_copy(chat_id=message.chat.id)
    num = generate_otp(text)
    if num is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="No mobile number detected."
        )
        await language_handler(update, context)
        return  # Early return to avoid unnecessary processing
    set_redis("number", num)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Please enter the 6 digit OTP received on your mobile number."
    )
    # async def OTP_handler_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Handle user's OTP verification
    
    # otp_message = await context.bot.get_updates()  # Hypothetical function to get the latest message
    otp_message = update.message.text
    print(f"otp message is {otp_message}")
    # num = get_redis_value("number")

    if verify_otp(num, otp_message):
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="OTP verified successfully. You have given your consent to share your details. Please share your name and other details."
        )
        await response_handler(update, context)
        # return
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="OTP verification failed. Please type your mobile number again."
        )
        await language_handler(update, context)
        return 
'''    
# def get_auth_token(data):
#     url = 'https://staging.digit.org/user/oauth/token'
#     headers = {
#         'Authorization': 'Basic ZWdvdi11c2VyLWNsaWVudDo=',
#         'Content-Type': 'application/x-www-form-urlencoded'
#     }
#     data.update({
#         'grant_type': 'password',
#         'scope': 'read',
#         'tenantId': 'pg',
#         'userType': 'citizen'
#     })
#     response = requests.post(url, headers=headers, data=data, verify=False)
    
#     # Check if the request was successful (status code 200)
#     if response.status_code == 200:
#         # Process the response
#         return response.json()['access_token']
#     else:
#         return None

# def search_complaint(data):
#     headers = {'Content-Type': 'application/json'}
#     mobile_number = data["username"]
#     url = f"https://staging.digit.org/pgr-services/v2/request/_search?tenantId=pg.cityb&mobileNumber={mobile_number}&_=1704443852959"

#     data = {
#         "RequestInfo":{
#             "apiId":"Rainmaker",
#             "authToken":data["auth_token"],
#             "userInfo":{
#                 "id":2079,
#                 "uuid":"7e2b023a-2f7f-444c-a48e-78d75911387a",
#                 "userName":data["username"],
#                 "name":data["name"],
#                 "mobileNumber":data["mobile_number"],
#                 "emailId":"",
#                 "locale":None,
#                 "type":"CITIZEN",
#                 "roles":[
#                     {
#                         "name":"Citizen",
#                         "code":"CITIZEN",
#                         "tenantId":"pg"
#                     }
#                 ],
#                 "active":True,
#                 "tenantId":"pg",
#                 "permanentCity":"pg.cityb"
#             },
#             "msgId":"1704443852959|en_IN",
#             "plainAccessRequest":{}
#         }
#     }

#     response = requests.post(url, headers=headers, data=json.dumps(data), verify=False)

#     if response.status_code == 200:
#         response_data = response.json()
#         print(response_data)
#         return response_data
#     else:
#         return None

# def validate_city(data):
#     headers = {'Content-Type': 'application/json'}
#     source_city = data.get("city", "")
#     print(data)
#     data = {
#         "RequestInfo": {
#             "apiId": "Rainmaker",
#             "authToken": data.get("auth_token", ""),
#             "userInfo": {
#                 "id": 2079,
#                 "uuid": "7e2b023a-2f7f-444c-a48e-78d75911387a",
#                 "userName": "7878787878",
#                 "name": data.get("name", ""),
#                 "mobileNumber": data.get("mobile_number", ""),
#                 "emailId": "",
#                 "locale": None,
#                 "type": "CITIZEN",
#                 "roles": [
#                     {
#                         "name": "Citizen",
#                         "code": "CITIZEN",
#                         "tenantId": "pg"
#                     }
#                 ],
#                 "active": True,
#                 "tenantId": "pg",
#                 "permanentCity": "pg.citya"
#             },
#             "msgId": "1706156400076|en_IN",
#             "plainAccessRequest": {}
#         },
#         "MdmsCriteria": {
#             "tenantId": "pg",
#             "moduleDetails": [
#                 {
#                     "moduleName": "tenant",
#                     "masterDetails": [
#                         {
#                             "name": "tenants"
#                         }
#                     ]
#                 }
#             ]
#         }
#     }

#     url = "https://staging.digit.org/egov-mdms-service/v1/_search"

#     response = requests.post(
#         url, 
#         headers=headers, 
#         data=json.dumps(data), 
#         verify=False
#     )

#     if response.status_code == 200:
#         response_data = response.json()
#         cities = {}
#         for city in response_data["MdmsRes"]["tenant"]["tenants"]:
#             city_name = city["name"].lower().replace(" ", "")
#             cities[city_name] = city["code"]
#         source_city = source_city.lower().replace(" ", "")
#         code = cities.get(source_city.lower(), None)
#     else:
#         code = None
#     if code:
#         return {
#                 "city_code": code
#             }
#     else:
#         cities_str = "\n".join(
#             [city["name"] for city in response_data["MdmsRes"]["tenant"]["tenants"]]
#         )
#         return {
#             "error": f"Service is unavailable in this city. Choose another city from this list\n  {cities_str}"
#         }
    
# def file_complaint(data):
#     city_code = validate_city(data)
#     if "error" in city_code:
#         return city_code
#     data["city_code"] = city_code.get("city_code")
#     locality_code = validate_locality(data)
#     if "error" in locality_code:
#         return locality_code
#     data["locality_code"] = locality_code.get("locality_code")
#     print(f"locality code is {locality_code}")
#     headers = {'Content-Type': 'application/json'}
#     data = {
#     "service": {
#         "tenantId": "pg.cityb",
#         "serviceCode": data.get("service_code"),
#         "description": "",
#         "additionalDetail": {},
#         "source": "web",
#         "address": {
#             "city": data.get("city", ""),
#             "district": data.get("district", ""),
#             "region": data.get("region", ""),
#             "state": data.get("state", ""),
#             "locality": {
#                 "code": data.get("locality_code", ""),
#                 "name": data.get("locality", "")
#             },
#             "geoLocation": {}
#         }
#     },
#     "workflow": {
#         "action": "APPLY"
#     },
#     "RequestInfo": {
#         "apiId": "Rainmaker",
#         "authToken": data["auth_token"],
#         "userInfo": {
#             "id": 2079,
#             "uuid": "7e2b023a-2f7f-444c-a48e-78d75911387a",
#             "userName": data["username"],
#             "name": data["name"],
#             "mobileNumber": data["username"],
#             "emailId": "",
#             "locale": None,
#             "type": "CITIZEN",
#             "roles": [
#                 {
#                     "name": "Citizen",
#                     "code": "CITIZEN",
#                     "tenantId": "pg"
#                 }
#             ],
#             "active": True,
#             "tenantId": "pg",
#             "permanentCity": "pg.citya"
#         },
#         "msgId": "1703653602370|en_IN",
#         "plainAccessRequest": {}
#     }
# }
#     url = "https://staging.digit.org/pgr-services/v2/request/_create"

#     response = requests.post(url, headers=headers, data=json.dumps(data), verify=False)

#     if response.status_code == 200:
#         response_data = response.json()
#         return response_data
#     else:
#         return {
#             "error": "Something went wrong please try again later"
#         }
    

    

