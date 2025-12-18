import json
import os

print("=== DEBUG INTELIPOST TOKEN ===")

# 1. Verifica se arquivo existe
tokens_file = 'tokens_secure.json'
print(f"1. Arquivo existe: {os.path.exists(tokens_file)}")

if os.path.exists(tokens_file):
    # 2. Lê o conteúdo
    with open(tokens_file, 'r', encoding='utf-8') as f:
        try:
            tokens = json.load(f)
            print(f"2. JSON válido: SIM")
            print(f"3. Chaves no arquivo: {list(tokens.keys())}")
            
            # 3. Procura token intelipost
            if 'intelipost' in tokens:
                print(f"4. 'intelipost' encontrado: SIM")
                intelipost_data = tokens['intelipost']
                print(f"5. Dados do intelipost: {intelipost_data.keys()}")
                
                api_key = intelipost_data.get('api_key')
                if api_key:
                    print(f"6. API Key encontrada: SIM")
                    print(f"7. API Key (primeiros 20 chars): {api_key[:20]}...")
                    print(f"8. Tamanho da API Key: {len(api_key)} caracteres")
                else:
                    print(f"6. API Key encontrada: NÃO")
                    print(f"7. Conteúdo de 'intelipost': {intelipost_data}")
            else:
                print(f"4. 'intelipost' encontrado: NÃO")
                
        except json.JSONDecodeError as e:
            print(f"2. JSON válido: NÃO - Erro: {e}")
else:
    print(f"1. Arquivo NÃO encontrado: {tokens_file}")