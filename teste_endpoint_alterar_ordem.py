import requests

product_id = "347749246"
token = "259086916L259063550E1850844837445C175753283744500O259063550.I"

url = f"https://app.anymarket.com.br/rest/api/products/{product_id}/images"  # <- /images


headers = {
    "Content-Type": "application/json",
    "gumgaToken": token
}

data = {
    "index": 0,
    "main": True,
    "url": "https://mpozenato.fbitsstatic.net/img/p/sofa-4-lugares-290cm-organico-quito-z08-boucle-verde-mpozenato-140141/304785-1.jpg",
    "variation": None
}

response = requests.post(url, headers=headers, json=data)

print("Status:", response.status_code)
print("Resposta:", response.text)
