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
        """Carrega configuração do arquivo seguro - COM FALLBACK PARA DADOS ANTIGOS"""
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
                    
            # 🔄 FALLBACK: Se não encontrou configuração, usa dados antigos
            if not self.client_id or not self.client_secret:
                print("⚠️  Usando Client ID/Secret do sistema antigo como fallback")
                self.client_id = "922777025648012"
                self.client_secret = "CRm4VwwTgPuPICJAPAymadxPQzIdR7e7"
                    
        except Exception as e:
            print(f"❌ Erro ao carregar configuração: {str(e)}")
            # Fallback para dados antigos
            self.client_id = "922777025648012"
            self.client_secret = "CRm4VwwTgPuPICJAPAymadxPQzIdR7e7"
    
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
                print("❌ Arquivo de tokens seguro não encontrado")
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
            
            if ml_tokens:
                print("✅ Tokens carregados do arquivo seguro")
                return ml_tokens
            else:
                print("❌ Nenhum token do Mercado Livre encontrado")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao carregar tokens: {str(e)}")
            return None

    def testar_token_api(self, token):
        """Testa se o token funciona na API do Mercado Livre"""
        try:
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(
                'https://api.mercadolibre.com/users/me',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Token OK - Usuário: {user_data.get('nickname')}")
                return True
            else:
                print(f"❌ Token inválido - Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao testar token: {str(e)}")
            return False
    
    def get_valid_token(self):
        """Obtém token válido (renova se necessário) - VERSÃO CORRIGIDA"""
        try:
            token_data = self.load_tokens()
            if not token_data:
                print("❌ Nenhum token configurado para Mercado Livre")
                return None
            
            access_token = token_data.get('access_token')
            refresh_token = token_data.get('refresh_token')
            
            if not access_token or not refresh_token:
                print("❌ Tokens incompletos")
                return None
            
            # 🔥 CORREÇÃO CRÍTICA: Testar o token na API antes de usar
            token_funciona = self.testar_token_api(access_token)
            
            if not token_funciona:
                print("🔁 Token não funciona na API, tentando renovar...")
                new_token = self.refresh_token(refresh_token)
                if new_token:
                    return new_token
                else:
                    print("❌ Não foi possível renovar o token")
                    return None
            
            # Se chegou aqui, o token funciona
            print("✅ Token válido e funcionando na API")
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
            
            print(f"🔄 Renovando token com Client ID: {self.client_id[:10]}...")
            
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
                if self.save_tokens(token_data):
                    print("✅ Token renovado com sucesso")
                    return token_data['access_token']
                else:
                    print("❌ Token renovado mas erro ao salvar")
                    return token_data['access_token']  # Retorna mesmo assim
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

    def get_token_info(self):
        """Retorna informações sobre o token atual (para debug)"""
        token_data = self.load_tokens()
        if not token_data:
            return None
        
        return {
            'client_id': self.client_id,
            'has_access_token': bool(token_data.get('access_token')),
            'has_refresh_token': bool(token_data.get('refresh_token')),
            'created_at': token_data.get('created_at'),
            'migrado_em': token_data.get('migrado_em', 'Não')
        }

# Instância global
ml_token_manager = MercadoLivreTokenManager()

def get_valid_ml_token():
    """Função auxiliar para obter token válido"""
    return ml_token_manager.get_valid_token()