import requests
from datetime import datetime, timezone, timedelta

# ======= CONFIGURAÇÕES =======
token = "259086916L259063550E1850844837445C175753283744500O259063550.I"
order_id = 256423596
url = f"https://api.anymarket.com.br/v2/orders/{order_id}"

# ======= DATA ATUAL FORMATADA =======
fuso_br = timezone(timedelta(hours=-3))
data_formatada = datetime.now(fuso_br).strftime("%Y-%m-%dT%H:%M:%S%z")
data_formatada = data_formatada[:-2] + ":" + data_formatada[-2:]  # deixa -03:00 bonitinho

# ======= CORPO DA REQUISIÇÃO =======
payload = {
    "status": "INVOICED",
    "invoice": {
        "accessKey": "4125 1010 6566 4900 0119 5500 1000 1313 0916 2273 9710",
        "series": "1",
        "number": "131309",
        "date": data_formatada,
        "cfop": "5102",
        "companyStateTaxId": "0",
        "linkNfe": "",
        "invoiceLink": "",
        "extraDescription": ""
    },
    "metadata": {
        "number-of-packages": "1",
        "cdZipCode": ""
    }
}

# ======= HEADERS =======
headers = {
    "Content-Type": "application/json",
    "gumgaToken": token
}

# ======= REQUISIÇÃO PUT =======
response = requests.put(url, json=payload, headers=headers)

# ======= RESULTADO =======
print("Status code:", response.status_code)
print("Resposta da API:")
print(response.text)
