import json
import os

def test_token_file():
    print("=== TESTE DO ARQUIVO TOKEN ===")
    print(f"Arquivo existe: {os.path.exists('tokens_secure.json')}")
    
    if os.path.exists('tokens_secure.json'):
        with open('tokens_secure.json', 'r') as f:
            content = f.read()
            print(f"Conteúdo: {content}")
            
            try:
                data = json.loads(content)
                print(f"Estrutura válida: {data}")
                print(f"Token anymarket: {'SIM' if data.get('anymarket', {}).get('token') else 'NÃO'}")
            except Exception as e:
                print(f"Erro JSON: {e}")

if __name__ == "__main__":
    test_token_file()