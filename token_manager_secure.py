# token_manager_secure.py
import os
import json
import time
import requests
from datetime import datetime

class MercadoLivreTokenManager:
    def __init__(self):
        self.tokens_file = 'tokens_secure.json'
        self.client_id = None
        self.client_secret = None
        self.load_config()
    
    def load_config(self):
        """Carrega configuração do arquivo seguro"""
        try:
            if os.path.exists(self.tokens_file):
                with open(self.tokens_file, 'r', encoding='utf-8') as f:
                    tokens_data = json.load(f)
                
                # Busca configuração do Mercado Livre
                ml_config = tokens_data.get('mercadolivre', {})
                if not ml_config:
                    # Tenta estrutura antiga
                    for key, value in tokens_data.items():
                        if isinstance(value, dict) and value.get('tipo') == 'mercadolivre':
                            ml_config = value
                            break
                
                if ml_config:
                    self.client_id = ml_config.get('client_id')
                    self.client_secret = ml_config.get('client_secret')
                    
        except Exception as e:
            print(f"❌ Erro ao carregar configuração: {str(e)}")
    
    def save_tokens(self, token_data):
        """Salva tokens de forma segura no arquivo"""
        try:
            tokens = {}
            
            # Carrega tokens existentes se o arquivo já existe
            if os.path.exists(self.tokens_file):
                with open(self.tokens_file, 'r', encoding='utf-8') as f:
                    tokens = json.load(f)
            
            # Atualiza apenas a seção do Mercado Livre
            tokens['mercadolivre'] = {
                'tipo': 'mercadolivre',
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'expires_in': token_data.get('expires_in', 21600),
                'created_at': datetime.now().isoformat(),
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'ultimo_uso': datetime.now().isoformat()
            }
            
            # Garante que o diretório existe
            os.makedirs(os.path.dirname(self.tokens_file) or '.', exist_ok=True)
            
            # Salva o arquivo
            with open(self.tokens_file, 'w', encoding='utf-8') as f:
                json.dump(tokens, f, indent=2, ensure_ascii=False)
            
            print("✅ Tokens salvos com segurança")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar tokens: {str(e)}")
            return False
    
    def load_tokens(self):
        """Carrega tokens do arquivo seguro"""
        try:
            if not os.path.exists(self.tokens_file):
                return None
            
            with open(self.tokens_file, 'r', encoding='utf-8') as f:
                tokens_data = json.load(f)
            
            # Busca tokens do Mercado Livre
            ml_tokens = tokens_data.get('mercadolivre', {})
            if not ml_tokens:
                # Tenta estrutura antiga
                for key, value in tokens_data.items():
                    if isinstance(value, dict) and value.get('tipo') == 'mercadolivre':
                        ml_tokens = value
                        break
            
            return ml_tokens if ml_tokens else None
            
        except Exception as e:
            print(f"❌ Erro ao carregar tokens: {str(e)}")
            return None
    
    def get_valid_token(self):
        """Obtém token válido (renova se necessário)"""
        try:
            token_data = self.load_tokens()
            if not token_data:
                print("❌ Nenhum token configurado para Mercado Livre")
                return None
            
            access_token = token_data.get('access_token')
            refresh_token = token_data.get('refresh_token')
            created_at = token_data.get('created_at')
            expires_in = token_data.get('expires_in', 21600)  # Default 6 horas
            
            if not access_token or not refresh_token:
                print("❌ Tokens incompletos")
                return None
            
            # Verifica se o token expirou
            if created_at:
                created_time = datetime.fromisoformat(created_at)
                expires_time = created_time.timestamp() + expires_in
                current_time = datetime.now().timestamp()
                
                # Renova se faltar menos de 5 minutos para expirar
                if current_time >= (expires_time - 300):
                    print("🔁 Token expirado ou próximo de expirar, renovando...")
                    return self.refresh_token(refresh_token)
            
            print("✅ Token válido")
            return access_token
            
        except Exception as e:
            print(f"❌ Erro ao obter token válido: {str(e)}")
            return None
    
    def refresh_token(self, refresh_token):
        """Renova o token usando refresh_token"""
        try:
            if not self.client_id or not self.client_secret:
                print("❌ Client ID ou Client Secret não configurados")
                return None
            
            response = requests.post(
                'https://api.mercadolibre.com/oauth/token',
                data={
                    'grant_type': 'refresh_token',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'refresh_token': refresh_token
                },
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.save_tokens(token_data)
                print("✅ Token renovado com sucesso")
                return token_data['access_token']
            else:
                print(f"❌ Erro ao renovar token: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erro na renovação: {str(e)}")
            return None
    
    def set_config(self, client_id, client_secret):
        """Define client_id e client_secret"""
        self.client_id = client_id
        self.client_secret = client_secret
        
        # Salva a configuração
        token_data = self.load_tokens() or {}
        token_data.update({
            'client_id': client_id,
            'client_secret': client_secret
        })
        self.save_tokens(token_data)
    
    def is_authenticated(self):
        """Verifica se está autenticado"""
        return self.get_valid_token() is not None
    
    def remove_tokens(self):
        """Remove tokens do Mercado Livre"""
        try:
            if os.path.exists(self.tokens_file):
                with open(self.tokens_file, 'r', encoding='utf-8') as f:
                    tokens_data = json.load(f)
                
                # Remove apenas a seção do Mercado Livre
                if 'mercadolivre' in tokens_data:
                    del tokens_data['mercadolivre']
                    
                    with open(self.tokens_file, 'w', encoding='utf-8') as f:
                        json.dump(tokens_data, f, indent=2, ensure_ascii=False)
                
                print("✅ Tokens removidos com segurança")
                return True
                
        except Exception as e:
            print(f"❌ Erro ao remover tokens: {str(e)}")
            return False

# Instância global
ml_token_manager = MercadoLivreTokenManager()

def get_valid_ml_token():
    """Função auxiliar para obter token válido"""
    return ml_token_manager.get_valid_token()