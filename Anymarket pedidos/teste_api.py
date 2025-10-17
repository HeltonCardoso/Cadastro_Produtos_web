import requests
import json
from datetime import datetime

# Configurações da API
BASE_URL = "https://api.anymarket.com.br/v2"
ENDPOINT = "/orders"

# Seu token de autenticação
GUMGA_TOKEN = "MjU5MDYzNTUwLg==.BS2OnGYhSD2nuXU5KRe59Iht02xoxdpAjpAuFORzs9EUbCHj9z16jYdLqCLwndvvaRd+jr+GlgmUMUEjIFYKdg=="

def listar_pedidos():
    """
    Função para buscar e listar pedidos da API do AnyMarket
    """
    headers = {
        "Content-Type": "application/json",
        "gumgaToken": GUMGA_TOKEN
    }
    
    # Parâmetros da requisição
    params = {
        "limit": 20,
        "offset": 0,
        "sort": "createdAt",
        "order": "DESC"
    }
    
    try:
        # Fazendo a requisição GET
        response = requests.get(
            f"{BASE_URL}{ENDPOINT}",
            headers=headers,
            params=params
        )
        
        # Verificando se a requisição foi bem sucedida
        if response.status_code == 200:
            dados = response.json()
            pedidos = dados.get("content", [])
            
            if not pedidos:
                print("Nenhum pedido encontrado.")
                return
            
            # Informações de paginação
            page_info = dados.get("page", {})
            print(f"Total de pedidos: {page_info.get('totalElements', len(pedidos))}")
            print(f"Página {page_info.get('number', 0) + 1} de {page_info.get('totalPages', 1)}")
            print("=" * 100)
            
            # Listando os pedidos
            for i, pedido in enumerate(pedidos, 1):
                print(f"\n--- Pedido {i} ---")
                print(f"ID: {pedido.get('id', 'N/A')}")
                print(f"Marketplace: {pedido.get('marketPlace', 'N/A')}")
                print(f"Status: {pedido.get('status', 'N/A')}")
                print(f"Número Marketplace: {pedido.get('marketPlaceNumber', 'N/A')}")
                
                # Formatando a data
                data_criacao = pedido.get('createdAt')
                if data_criacao:
                    try:
                        data_formatada = datetime.fromisoformat(data_criacao.replace('Z', '+00:00'))
                        print(f"Data de criação: {data_formatada.strftime('%d/%m/%Y %H:%M')}")
                    except:
                        print(f"Data de criação: {data_criacao}")
                
                # Informações do comprador
                buyer = pedido.get('buyer', {})
                if buyer:
                    print(f"Comprador: {buyer.get('name', 'N/A')}")
                    print(f"Email: {buyer.get('email', 'N/A')}")
                    print(f"Documento: {buyer.get('document', 'N/A')}")
                
                # Valores
                gross = pedido.get('gross', 0)
                total = pedido.get('total', 0)
                freight = pedido.get('freight', 0)
                discount = pedido.get('discount', 0)
                
                print(f"Valor bruto: R$ {gross:.2f}")
                print(f"Frete: R$ {freight:.2f}")
                print(f"Desconto: R$ {discount:.2f}")
                print(f"Valor total: R$ {total:.2f}")
                
                # Itens do pedido
                itens = pedido.get('items', [])
                if itens:
                    print(f"Itens ({len(itens)}):")
                    for item in itens:
                        sku_info = item.get('sku', {})
                        product_info = item.get('product', {})
                        print(f"  - {product_info.get('title', 'N/A')}")
                        print(f"    SKU: {sku_info.get('title', 'N/A')}")
                        print(f"    Quantidade: {item.get('amount', 0)}")
                        print(f"    Valor unitário: R$ {item.get('unit', 0):.2f}")
                        print(f"    Valor total: R$ {item.get('total', 0):.2f}")
                
                # Informações de entrega
                shipping = pedido.get('shipping', {})
                if shipping:
                    print(f"Endereço: {shipping.get('receiverName', 'N/A')}")
                    print(f"          {shipping.get('address', '')}, {shipping.get('number', '')}")
                    print(f"          {shipping.get('neighborhood', '')} - {shipping.get('city', '')}/{shipping.get('state', '')}")
                    print(f"          CEP: {shipping.get('zipCode', '')}")
                
                print("-" * 50)
                
            # Links de paginação
            links = dados.get('links', [])
            if links:
                print("\nLinks de paginação:")
                for link in links:
                    print(f"  {link.get('rel', '')}: {link.get('href', '')}")
                
        else:
            print(f"Erro na requisição: {response.status_code}")
            print(f"Detalhes: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão: {e}")
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON: {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")

def listar_pedidos_resumido():
    """
    Versão resumida para exibição em tabela simples
    """
    headers = {
        "Content-Type": "application/json",
        "gumgaToken": GUMGA_TOKEN
    }
    
    params = {
        "limit": 15,
        "offset": 0,
        "sort": "createdAt",
        "order": "DESC"
    }
    
    try:
        response = requests.get(f"{BASE_URL}{ENDPOINT}", headers=headers, params=params)
        
        if response.status_code == 200:
            dados = response.json()
            pedidos = dados.get("content", [])
            
            if not pedidos:
                print("Nenhum pedido encontrado.")
                return
            
            page_info = dados.get("page", {})
            print(f"\nTotal de pedidos: {page_info.get('totalElements', 'N/A')}")
            print("=" * 130)
            print(f"{'#':<3} {'ID':<8} {'Marketplace':<15} {'Status':<12} {'Número':<12} {'Data':<12} {'Comprador':<20} {'Total':<10}")
            print("=" * 130)
            
            for i, pedido in enumerate(pedidos, 1):
                # Formatando data
                data_criacao = pedido.get('createdAt', '')
                if data_criacao:
                    try:
                        data_formatada = datetime.fromisoformat(data_criacao.replace('Z', '+00:00'))
                        data_str = data_formatada.strftime('%d/%m/%Y')
                    except:
                        data_str = data_criacao[:10]
                else:
                    data_str = 'N/A'
                
                buyer_name = pedido.get('buyer', {}).get('name', 'N/A')
                if len(buyer_name) > 18:
                    buyer_name = buyer_name[:15] + "..."
                
                print(f"{i:<3} {pedido.get('id', 'N/A'):<8} "
                      f"{pedido.get('marketPlace', 'N/A'):<15} "
                      f"{pedido.get('status', 'N/A'):<12} "
                      f"{pedido.get('marketPlaceNumber', 'N/A'):<12} "
                      f"{data_str:<12} "
                      f"{buyer_name:<20} "
                      f"R$ {pedido.get('total', 0):<8.2f}")
            
            print("=" * 130)
            
        else:
            print(f"Erro: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Erro: {e}")

def buscar_pedidos_por_status(status="PENDING"):
    """
    Buscar pedidos por status específico
    """
    headers = {
        "Content-Type": "application/json",
        "gumgaToken": GUMGA_TOKEN
    }
    
    params = {
        "limit": 50,
        "offset": 0,
        "status": status,
        "sort": "createdAt",
        "order": "DESC"
    }
    
    try:
        response = requests.get(f"{BASE_URL}{ENDPOINT}", headers=headers, params=params)
        
        if response.status_code == 200:
            dados = response.json()
            pedidos = dados.get("content", [])
            
            print(f"\nPedidos com status: {status}")
            print(f"Encontrados: {len(pedidos)} pedidos")
            print("=" * 80)
            
            for i, pedido in enumerate(pedidos, 1):
                data_criacao = pedido.get('createdAt', '')
                if data_criacao:
                    try:
                        data_formatada = datetime.fromisoformat(data_criacao.replace('Z', '+00:00'))
                        data_str = data_formatada.strftime('%d/%m/%Y %H:%M')
                    except:
                        data_str = data_criacao
                else:
                    data_str = 'N/A'
                
                print(f"{i}. ID: {pedido.get('id')} | "
                      f"Marketplace: {pedido.get('marketPlace')} | "
                      f"Data: {data_str} | "
                      f"Total: R$ {pedido.get('total', 0):.2f}")
                
        else:
            print(f"Erro: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Erro: {e}")

# Menu principal
if __name__ == "__main__":
    print("Sistema de Listagem de Pedidos - AnyMarket")
    print("1. Listar pedidos detalhados")
    print("2. Listar pedidos resumidos")
    print("3. Buscar pedidos pendentes")
    print("4. Buscar pedidos faturados")
    
    opcao = input("\nEscolha uma opção (1-4): ").strip()
    
    if opcao == "1":
        listar_pedidos()
    elif opcao == "2":
        listar_pedidos_resumido()
    elif opcao == "3":
        buscar_pedidos_por_status("PENDING")
    elif opcao == "4":
        buscar_pedidos_por_status("INVOICED")
    else:
        print("Opção inválida!")