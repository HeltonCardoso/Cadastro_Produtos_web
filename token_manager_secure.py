# token_manager_secure.py
import os
import json
import time
import requests
from datetime import datetime

# ======================================================
# NOVA IMPORT: Usando token manager do banco de dados
# ======================================================
from utils.token_manager_db import salvar_token, obter_token, remover_token

class MercadoLivreTokenManager:
    def __init__(self):
        self.current_account_id = None
        self.accounts = {}
        self.client_id = None
        self.client_secret = None
        self.load_accounts()
    
    def load_accounts(self):
        """Carrega contas do BANCO DE DADOS (persistente)"""
        try:
            # 1. Tenta carregar do BANCO DE DADOS primeiro (PERSISTENTE!)
            data = obter_token('mercadolivre')
            
            if data:
                self.accounts = data.get('accounts', {})
                self.current_account_id = data.get('current_account_id')
                self.client_id = data.get('client_id')
                self.client_secret = data.get('client_secret')
                print(f"✅ {len(self.accounts)} conta(s) carregada(s) do BANCO DE DADOS")
                
                # Define conta atual (primeira que tiver token)
                if not self.current_account_id and self.accounts:
                    for account_id, account in self.accounts.items():
                        if account.get('access_token'):
                            self.current_account_id = account_id
                            break
                    if not self.current_account_id:
                        self.current_account_id = list(self.accounts.keys())[0]
                
                print(f"📊 Total de contas: {len(self.accounts)}")
                print(f"📌 Conta atual: {self.current_account_id}")
                return
            
            # 2. Fallback: Tenta migrar do arquivo antigo (migração única)
            print("🔄 Banco de dados vazio. Verificando arquivo antigo...")
            self.migrar_do_arquivo_antigo()
            
        except Exception as e:
            print(f"❌ Erro ao carregar contas do banco: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def migrar_do_arquivo_antigo(self):
        """Migra contas do arquivo tokens_secure.json para o banco de dados"""
        tokens_file = 'tokens_secure.json'
        
        if not os.path.exists(tokens_file):
            print("ℹ️  Nenhum arquivo antigo encontrado. Iniciando com contas vazias.")
            return
        
        try:
            with open(tokens_file, 'r', encoding='utf-8') as f:
                tokens_data = json.load(f)
            
            print("📂 Migrando dados do arquivo antigo...")
            
            # Se já tem a nova estrutura multi-contas
            if 'mercadolivre_accounts' in tokens_data:
                self.accounts = tokens_data['mercadolivre_accounts']
                print(f"✅ {len(self.accounts)} conta(s) migradas da nova estrutura")
            
            # Se tem estrutura antiga (sua conta atual)
            elif 'mercadolivre' in tokens_data:
                print("🔄 Convertendo estrutura antiga para multi-contas...")
                self.converter_conta_atual(tokens_data['mercadolivre'])
            
            # Se tem client_id/secret no config
            elif 'config' in tokens_data:
                self.client_id = tokens_data['config'].get('client_id')
                self.client_secret = tokens_data['config'].get('client_secret')
            
            # Define conta atual
            if not self.current_account_id and self.accounts:
                for account_id, account in self.accounts.items():
                    if account.get('access_token'):
                        self.current_account_id = account_id
                        break
                if not self.current_account_id and self.accounts:
                    self.current_account_id = list(self.accounts.keys())[0]
            
            # Salva no banco de dados
            self.save_to_database()
            print(f"✅ Dados migrados para o banco de dados com sucesso!")
            
            # Backup do arquivo antigo
            backup_file = f"{tokens_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(tokens_file, backup_file)
            print(f"📁 Arquivo antigo renomeado para: {backup_file}")
            
        except Exception as e:
            print(f"❌ Erro na migração: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def save_to_database(self):
        """Salva as contas no BANCO DE DADOS"""
        data = {
            'accounts': self.accounts,
            'current_account_id': self.current_account_id,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'updated_at': datetime.now().isoformat()
        }
        return salvar_token('mercadolivre', data)
    
    def converter_conta_atual(self, ml_data):
        """Converte sua conta atual para a nova estrutura"""
        try:
            # Cria ID baseado no user_id ou timestamp
            if ml_data.get('user_id'):
                account_id = f"conta_{ml_data['user_id']}"
            else:
                account_id = "conta_principal"
            
            self.accounts[account_id] = {
                'account_name': 'Conta Principal',
                'app_id': ml_data.get('client_id', ''),
                'secret_key': ml_data.get('client_secret', ''),
                'access_token': ml_data.get('access_token'),
                'refresh_token': ml_data.get('refresh_token'),
                'expires_in': ml_data.get('expires_in', 21600),
                'created_at': ml_data.get('created_at', datetime.now().isoformat()),
                'user_id': ml_data.get('user_id'),
                'nickname': ml_data.get('nickname'),
                'is_active': True,
                'is_default': True,
                'migrado_em': datetime.now().isoformat()
            }
            
            self.current_account_id = account_id
            self.save_to_database()
            print(f"✅ Sua conta atual foi convertida para: {account_id}")
            print(f"   Access Token: {ml_data.get('access_token', '')[:20]}...")
            print(f"   Refresh Token: {ml_data.get('refresh_token', '')[:20]}...")
            
        except Exception as e:
            print(f"❌ Erro na conversão: {str(e)}")
    
    # =========================================
    # MÉTODOS COMPATIBILIDADE (ANTIGOS)
    # =========================================
    
    def is_authenticated(self):
        """Compatibilidade: verifica se a conta atual está autenticada"""
        try:
            if not self.current_account_id:
                return False
            
            account = self.accounts.get(self.current_account_id)
            if not account:
                return False
            
            return bool(account.get('access_token'))
            
        except Exception as e:
            print(f"❌ Erro em is_authenticated: {str(e)}")
            return False
    
    def set_config(self, client_id, client_secret):
        """Compatibilidade: define configuração para conta atual"""
        try:
            if not self.current_account_id:
                # Cria uma conta padrão se não existir
                self.current_account_id = 'conta_principal'
                self.accounts[self.current_account_id] = {
                    'account_name': 'Conta Principal',
                    'is_active': True,
                    'is_default': True,
                    'created_at': datetime.now().isoformat()
                }
            
            account = self.accounts[self.current_account_id]
            account['app_id'] = client_id
            account['secret_key'] = client_secret
            
            # Salva no banco de dados
            self.save_to_database()
            print(f"✅ Configuração salva para conta: {self.current_account_id}")
            return True
            
        except Exception as e:
            print(f"❌ Erro em set_config: {str(e)}")
            return False
    
    def remove_tokens(self):
        """Compatibilidade: remove tokens da conta atual"""
        try:
            if not self.current_account_id:
                return False
            
            account = self.accounts.get(self.current_account_id)
            if not account:
                return False
            
            # Remove tokens mas mantém a conta
            account['access_token'] = None
            account['refresh_token'] = None
            account['nickname'] = None
            account['user_id'] = None
            
            self.save_to_database()
            print(f"✅ Tokens removidos da conta: {self.current_account_id}")
            return True
            
        except Exception as e:
            print(f"❌ Erro em remove_tokens: {str(e)}")
            return False
    
    def save_tokens(self, token_data):
        """Compatibilidade: salva tokens (método antigo)"""
        try:
            if not self.current_account_id:
                self.current_account_id = 'conta_principal'
                self.accounts[self.current_account_id] = {
                    'account_name': 'Conta Principal',
                    'created_at': datetime.now().isoformat()
                }
            
            account = self.accounts[self.current_account_id]
            account['access_token'] = token_data.get('access_token')
            account['refresh_token'] = token_data.get('refresh_token')
            account['expires_in'] = token_data.get('expires_in', 21600)
            account['updated_at'] = datetime.now().isoformat()
            
            # Tenta obter dados do usuário
            self.atualizar_dados_usuario(self.current_account_id)
            
            self.save_to_database()
            print(f"✅ Tokens salvos para conta: {self.current_account_id}")
            return True
            
        except Exception as e:
            print(f"❌ Erro em save_tokens: {str(e)}")
            return False
    
    def load_tokens(self):
        """Compatibilidade: carrega tokens (método antigo)"""
        try:
            if not self.current_account_id:
                return None
            
            account = self.accounts.get(self.current_account_id)
            if not account:
                return None
            
            return {
                'access_token': account.get('access_token'),
                'refresh_token': account.get('refresh_token'),
                'expires_in': account.get('expires_in', 21600),
                'created_at': account.get('created_at')
            }
            
        except Exception as e:
            print(f"❌ Erro em load_tokens: {str(e)}")
            return None
    
    # =========================================
    # MÉTODO PARA ADICIONAR NOVA CONTA
    # =========================================
    
    def add_account_with_app_credentials(self, account_name, app_id, secret_key):
        """Adiciona nova conta e OBTÉM TOKENS AUTOMATICAMENTE"""
        try:
            print(f"➕ Adicionando nova conta: {account_name}")
            
            # Gera ID único
            account_id = f"conta_{int(time.time())}"
            
            # Cria conta inicial (sem tokens ainda)
            self.accounts[account_id] = {
                'account_name': account_name,
                'app_id': app_id,
                'secret_key': secret_key,
                'access_token': None,
                'refresh_token': None,
                'created_at': datetime.now().isoformat(),
                'is_active': True,
                'is_default': False,
                'status': 'pending_tokens'
            }
            
            self.save_to_database()
            print(f"✅ Conta '{account_name}' criada. Agora obtendo tokens...")
            
            # Tenta obter tokens automaticamente
            tokens_obtidos = self.obter_tokens_automaticamente(account_id)
            
            if tokens_obtidos:
                return account_id, True, "Conta adicionada e autenticada com sucesso!"
            else:
                return account_id, False, "Conta criada, mas não foi possível obter tokens automaticamente. Você pode adicioná-los manualmente."
            
        except Exception as e:
            print(f"❌ Erro ao adicionar conta: {str(e)}")
            return None, False, f"Erro: {str(e)}"
    
    def obter_tokens_automaticamente(self, account_id):
        """Tenta obter tokens usando Test OAuth do Mercado Livre"""
        try:
            if account_id not in self.accounts:
                return False
            
            account = self.accounts[account_id]
            app_id = account.get('app_id')
            secret_key = account.get('secret_key')
            
            if not app_id or not secret_key:
                print("❌ App ID ou Secret Key não configurados")
                return False
            
            print(f"🔐 Obtendo tokens para App ID: {app_id[:10]}...")
            
            # Método 1: Tenta usar Test OAuth (sem callback)
            try:
                return self.obter_tokens_test_oauth(account_id)
            except Exception as e:
                print(f"⚠️  Método Test OAuth falhou: {e}")
            
            print("❌ Nenhum método funcionou para obter tokens automaticamente")
            return False
            
        except Exception as e:
            print(f"❌ Erro ao obter tokens: {str(e)}")
            return False
    
    def obter_tokens_test_oauth(self, account_id):
        """Usa endpoint de Test OAuth do Mercado Livre"""
        try:
            account = self.accounts[account_id]
            app_id = account['app_id']
            secret_key = account['secret_key']
            
            # URL do Test OAuth
            url = "https://api.mercadolibre.com/oauth/token"
            
            # Parâmetros para Test OAuth
            data = {
                'grant_type': 'client_credentials',
                'client_id': app_id,
                'client_secret': secret_key
            }
            
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            print(f"🌐 Tentando Test OAuth para {account['account_name']}...")
            response = requests.post(url, data=data, headers=headers, timeout=30)
            
            print(f"📡 Resposta: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Atualiza conta com tokens
                account['access_token'] = token_data.get('access_token')
                account['refresh_token'] = token_data.get('refresh_token')
                account['expires_in'] = token_data.get('expires_in', 21600)
                account['token_type'] = token_data.get('token_type', 'Bearer')
                account['scope'] = token_data.get('scope', '')
                account['updated_at'] = datetime.now().isoformat()
                
                # Obtém dados do usuário
                self.atualizar_dados_usuario(account_id)
                
                self.save_to_database()
                print(f"🎉 Tokens obtidos AUTOMATICAMENTE para: {account['account_name']}")
                
                return True
            else:
                print(f"❌ Test OAuth falhou: {response.status_code} - {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Erro no Test OAuth: {str(e)}")
            return False
    
    def atualizar_dados_usuario(self, account_id):
        """Obtém nickname e user_id para a conta"""
        try:
            account = self.accounts[account_id]
            token = account.get('access_token')
            
            if not token:
                return False
            
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(
                'https://api.mercadolibre.com/users/me',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                account['user_id'] = user_data.get('id')
                account['nickname'] = user_data.get('nickname')
                account['last_api_check'] = datetime.now().isoformat()
                print(f"👤 Usuário identificado: {account['nickname']} (ID: {account['user_id']})")
                self.save_to_database()
                return True
            
            return False
            
        except Exception as e:
            print(f"⚠️  Erro ao obter dados do usuário: {e}")
            return False
    
    # =========================================
    # MÉTODOS PARA ADICIONAR TOKENS MANUALMENTE
    # =========================================
    
    def add_tokens_manually(self, account_id, access_token, refresh_token):
        """Adiciona tokens manualmente a uma conta existente"""
        try:
            if account_id not in self.accounts:
                return False, "Conta não encontrada"
            
            account = self.accounts[account_id]
            
            account['access_token'] = access_token
            account['refresh_token'] = refresh_token
            account['updated_at'] = datetime.now().isoformat()
            account['status'] = 'manual_tokens'
            
            # Obtém dados do usuário
            self.atualizar_dados_usuario(account_id)
            
            self.save_to_database()
            print(f"✅ Tokens adicionados manualmente à conta: {account['account_name']}")
            return True, "Tokens adicionados com sucesso!"
            
        except Exception as e:
            print(f"❌ Erro ao adicionar tokens: {str(e)}")
            return False, f"Erro: {str(e)}"
    
    # =========================================
    # MÉTODOS DE USO
    # =========================================
    
    def get_valid_token(self, account_id=None):
        """Obtém token válido para uso"""
        try:
            if not account_id:
                account_id = self.current_account_id
            
            if not account_id or account_id not in self.accounts:
                print("❌ Conta não encontrada")
                return None
            
            account = self.accounts[account_id]
            access_token = account.get('access_token')
            
            if not access_token:
                print(f"❌ Conta '{account.get('account_name')}' não tem token")
                return None
            
            # Testa se o token funciona
            if self.testar_token_api(access_token):
                return access_token
            
            # Tenta renovar
            refresh_token = account.get('refresh_token')
            if refresh_token:
                new_token = self.refresh_token(account_id, refresh_token)
                if new_token:
                    return new_token
            
            return None
            
        except Exception as e:
            print(f"❌ Erro ao obter token: {str(e)}")
            return None
    
    def refresh_token(self, account_id, refresh_token):
        """Renova token"""
        try:
            if account_id not in self.accounts:
                return None
            
            account = self.accounts[account_id]
            app_id = account.get('app_id')
            secret_key = account.get('secret_key')
            
            if not app_id or not secret_key:
                print("❌ App ID ou Secret Key não configurado")
                return None
            
            response = requests.post(
                'https://api.mercadolibre.com/oauth/token',
                data={
                    'grant_type': 'refresh_token',
                    'client_id': app_id,
                    'client_secret': secret_key,
                    'refresh_token': refresh_token
                },
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                account['access_token'] = token_data.get('access_token')
                account['refresh_token'] = token_data.get('refresh_token', refresh_token)
                account['expires_in'] = token_data.get('expires_in', 21600)
                account['updated_at'] = datetime.now().isoformat()
                
                self.save_to_database()
                print(f"✅ Token renovado para: {account.get('account_name')}")
                return token_data['access_token']
            else:
                print(f"❌ Erro ao renovar: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro na renovação: {str(e)}")
            return None
    
    def testar_token_api(self, token):
        """Testa se o token funciona"""
        try:
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(
                'https://api.mercadolibre.com/users/me',
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    # =========================================
    # GERENCIAMENTO DE CONTAS
    # =========================================
    
    def get_all_accounts(self):
        """Lista todas as contas"""
        accounts_info = []
        for account_id, account in self.accounts.items():
            accounts_info.append({
                'id': account_id,
                'name': account.get('account_name', 'Sem nome'),
                'app_id': account.get('app_id', '')[:8] + '...' if account.get('app_id') else '',
                'has_token': bool(account.get('access_token')),
                'is_default': (account_id == self.current_account_id),
                'nickname': account.get('nickname', 'Não autenticada'),
                'status': account.get('status', 'active'),
                'created_at': account.get('created_at', '')
            })
        return accounts_info
    
    def set_current_account(self, account_id):
        """Define conta atual"""
        if account_id in self.accounts:
            self.current_account_id = account_id
            self.save_to_database()
            print(f"✅ Conta atual: {self.accounts[account_id].get('account_name')}")
            return True
        return False
    
    def remove_account(self, account_id):
        """Remove conta (não remove a conta atual)"""
        if account_id in self.accounts:
            # Não permite remover a conta atual
            if account_id == self.current_account_id:
                return False, "Não é possível remover a conta atual"
            
            account_name = self.accounts[account_id].get('account_name')
            del self.accounts[account_id]
            
            self.save_to_database()
            print(f"✅ Conta '{account_name}' removida")
            return True, f"Conta '{account_name}' removida"
        
        return False, "Conta não encontrada"

# Instância global
ml_token_manager = MercadoLivreTokenManager()

# FUNÇÃO DE COMPATIBILIDADE
def get_valid_ml_token():
    """Função de compatibilidade - mantém importações existentes"""
    return ml_token_manager.get_valid_token()