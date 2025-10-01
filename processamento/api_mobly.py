import requests
import hashlib
import hmac
import base64
import urllib.parse
from datetime import datetime, timezone

# Configurações
API_URL = "https://sellercenter-api.theiconic.com.au/"
USER_ID = "SEU_EMAIL_AQUI"
API_KEY = "7ea65b9233f8dcb948df78021a69b965ce74930c"

def gerar_signature(params, api_key):
    # Ordena os parâmetros em ordem alfabética
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    query_string = urllib.parse.urlencode(sorted_params)

    # Calcula HMAC-SHA256
    signature = hmac.new(
        api_key.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256
    ).digest()

    # Base64 encode
    return base64.b64encode(signature).decode()

def get_products():
    # Monta parâmetros
    params = {
        "Action": "GetProducts",
        "Format": "JSON",
        "UserID": USER_ID,
        "Version": "1.0",
        "Timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    }

    # Gera assinatura
    params["Signature"] = gerar_signature(params, API_KEY)

    # Faz requisição
    response = requests.get(API_URL, params=params)

    print("Status:", response.status_code)
    print("URL final:", response.url)
    print("Resposta:", response.text[:500])

    if response.status_code == 200:
        return response.json() if params["Format"] == "JSON" else response.text
    return None

if __name__ == "__main__":
    dados = get_products()
    if dados:
        print("Consulta OK 🚀")
