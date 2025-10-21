# Função de teste para verificar a nova API
from api_anymarket import AnyMarketAPI, obter_token_anymarket_seguro


def testar_nova_api(product_id="347730803"):
    """Testa a conexão com a nova API"""
    try:
        token = obter_token_anymarket_seguro()
        print(f"🔑 Token obtido: {token[:20]}...")
        
        api = AnyMarketAPI(token)
        
        # Testa com um produto conhecido
        resultado = api.buscar_fotos_produto(product_id)
        print("=== TESTE NOVA API ===")
        print(f"Sucesso: {resultado['sucesso']}")
        print(f"Status: {resultado['status_code']}")
        print(f"Fotos encontradas: {resultado.get('quantidade_fotos', 0)}")
        
        if resultado['sucesso'] and resultado.get('dados'):
            for i, foto in enumerate(resultado['dados'][:3]):  # Mostra apenas 3 primeiras
                print(f"Foto {i+1}: ID={foto['id']}, Principal={foto['main']}, URL={foto['url'][:50]}...")
        elif resultado.get('erro'):
            print(f"❌ Erro: {resultado['erro']}")
        
        return resultado
        
    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")
        return None