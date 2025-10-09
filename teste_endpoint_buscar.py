import requests

product_id = "347749246"  # ou outro que você queira testar
token = "259086916L259063550E1850844837445C175753283744500O259063550.I"

url = f"https://app.anymarket.com.br/rest/api/products/{product_id}/photos"

headers = {
    "Content-Type": "application/json",
    "gumgaToken": token
}

response = requests.get(url, headers=headers)

print("Status Code:", response.status_code)

try:
    imagens = response.json()
    for img in imagens:
        print(f"ID: {img['id']} | MAIN: {img['main']} | INDEX: {img['index']} | Status IMG: {img['status']}")
        print(f"URL original: {img['original']}")
        print("------")
except Exception as e:
    print("Erro ao decodificar JSON:", e)
    print(response.text)
