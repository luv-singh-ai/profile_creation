import requests
import json
def generate_token() -> int:

    url = "https://testapi.haqdarshak.com/api/generate_token"

    payload = json.dumps({
    "api_key": "346ca1a3fb416f084b8e737970f57751",
    "secret_key": "358567b4d67e639bbb02bb02e6df58605eed447a",
    "state_code": "MH",
    "agent_id": "451"
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    token_res = json.loads(response.text)
    token = token_res.get("token")
    return token

if __name__ == '__main__':
    token = generate_token()
    print(token)