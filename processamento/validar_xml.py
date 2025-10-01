import requests

# Configurações
BASE_URL = "https://sellercenter-api.theiconic.com.au/api/v2"
TOKEN = "SEU_TOKEN_AQUI"  # substitui pelo token que a Iconic te forneceu

# Cabeçalhos para autenticação
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json"
}

def listar_produtos(page=1, per_page=50):
    """
    Consulta produtos da API do The Iconic SellerCenter.
    :param page: Página de resultados
    :param per_page: Quantidade de produtos por página
    """
    url = f"{BASE_URL}/products"
    params = {
        "page": page,
        "per_page": per_page
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Erro:", response.status_code, response.text)
        return None


if __name__ == "__main__":
    produtos = listar_produtos(page=1, per_page=10)

    if produtos:
        print("Produtos encontrados:")
        for p in produtos.get("data", []):  # depende da estrutura JSON que a Iconic retorna
            print(f"- SKU: {p.get('sku')} | Nome: {p.get('name')}")
