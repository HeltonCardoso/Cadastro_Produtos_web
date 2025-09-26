import requests

BASE_URL = "https://sellercenter-api.theiconic.com.au/api/v2"
TOKEN = "7ea65b9233f8dcb948df78021a69b965ce74930c"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json"
}

response = requests.get(f"{BASE_URL}/products", headers=headers)

print("Status:", response.status_code)
print("Resposta:", response.text)
