import os
import json
import time
import requests
from datetime import datetime
import hashlib
from typing import Dict, Optional

class MercadoLivreAccountManager:
    def __init__(self, accounts_file='mercado_livre_accounts.json'):
        self.accounts_file = accounts_file
        self.accounts = self._load_accounts()
        self.current_account_id = self._load_current_account()
    
    def _load_accounts(self) -> Dict:
        """Carrega as contas do arquivo"""
        if os.path.exists(self.accounts_file):
            try:
                with open(self.accounts_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_accounts(self):
        """Salva as contas no arquivo"""
        with open(self.accounts_file, 'w', encoding='utf-8') as f:
            json.dump(self.accounts, f, indent=2, ensure_ascii=False)
    
    def _load_current_account(self) -> Optional[str]:
        """Carrega a conta atual do arquivo"""
        if os.path.exists('current_ml_account.json'):
            try:
                with open('current_ml_account.json', 'r') as f:
                    data = json.load(f)
                    return data.get('current_account_id')
            except:
                pass
        return None
    
    def _save_current_account(self, account_id: str):
        """Salva a conta atual"""
        with open('current_ml_account.json', 'w') as f:
            json.dump({'current_account_id': account_id}, f)
    
    def add_account(self, client_id: str, client_secret: str, account_name: str = None) -> str:
        """Adiciona uma nova conta"""
        account_id = hashlib.md5(f"{client_id}_{client_secret}".encode()).hexdigest()[:8]
        
        if account_id not in self.accounts:
            self.accounts[account_id] = {
                'client_id': client_id,
                'client_secret': client_secret,
                'account_name': account_name or f"Conta_{account_id}",
                'tokens': None,
                'created_at': datetime.now().isoformat(),
                'last_used': None
            }
            self._save_accounts()
            
        return account_id
    
    def remove_account(self, account_id: str) -> bool:
        """Remove uma conta"""
        if account_id in self.accounts:
            del self.accounts[account_id]
            self._save_accounts()
            
            # Se era a conta atual, limpa
            if self.current_account_id == account_id:
                self.current_account_id = None
                self._save_current_account(None)
            
            return True
        return False
    
    def update_tokens(self, account_id: str, tokens: Dict) -> bool:
        """Atualiza os tokens de uma conta"""
        if account_id in self.accounts:
            self.accounts[account_id]['tokens'] = tokens
            self.accounts[account_id]['last_used'] = datetime.now().isoformat()
            self._save_accounts()
            return True
        return False
    
    def get_account(self, account_id: str) -> Optional[Dict]:
        """Obtém dados de uma conta"""
        return self.accounts.get(account_id)
    
    def get_all_accounts(self) -> Dict:
        """Retorna todas as contas"""
        return self.accounts
    
    def get_valid_token(self, account_id: str = None) -> Optional[str]:
        """Obtém um token válido para a conta, renovando se necessário"""
        acc_id = account_id or self.current_account_id
        if not acc_id:
            return None
        
        account = self.get_account(acc_id)
        if not account or not account.get('tokens'):
            return None
        
        tokens = account['tokens']
        
        # Verifica se o token está expirado
        if tokens.get('expires_at') and time.time() > tokens['expires_at']:
            print(f"🔁 Token expirado para conta {acc_id}, renovando...")
            new_tokens = self.refresh_token(acc_id)
            if new_tokens:
                return new_tokens.get('access_token')
            return None
        
        return tokens.get('access_token')
    
    def refresh_token(self, account_id: str) -> Optional[Dict]:
        """Renova o token usando o refresh_token"""
        account = self.get_account(account_id)
        if not account:
            return None
        
        tokens = account.get('tokens')
        if not tokens or not tokens.get('refresh_token'):
            return None
        
        try:
            response = requests.post(
                'https://api.mercadolibre.com/oauth/token',
                data={
                    'grant_type': 'refresh_token',
                    'client_id': account['client_id'],
                    'client_secret': account['client_secret'],
                    'refresh_token': tokens['refresh_token']
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                new_tokens = {
                    'access_token': data['access_token'],
                    'refresh_token': data.get('refresh_token', tokens['refresh_token']),
                    'expires_in': data['expires_in'],
                    'expires_at': time.time() + data['expires_in']
                }
                
                self.update_tokens(account_id, new_tokens)
                return new_tokens
        except Exception as e:
            print(f"❌ Erro ao renovar token: {e}")
        
        return None
    
    def authenticate_with_code(self, account_id: str, authorization_code: str, redirect_uri: str) -> bool:
        """Autentica usando o código de autorização"""
        account = self.get_account(account_id)
        if not account:
            return False
        
        try:
            response = requests.post(
                'https://api.mercadolibre.com/oauth/token',
                data={
                    'grant_type': 'authorization_code',
                    'client_id': account['client_id'],
                    'client_secret': account['client_secret'],
                    'code': authorization_code,
                    'redirect_uri': redirect_uri
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                tokens = {
                    'access_token': data['access_token'],
                    'refresh_token': data['refresh_token'],
                    'expires_in': data['expires_in'],
                    'expires_at': time.time() + data['expires_in']
                }
                
                self.update_tokens(account_id, tokens)
                return True
        except Exception as e:
            print(f"❌ Erro na autenticação: {e}")
        
        return False
    
    def set_current_account(self, account_id: str):
        """Define a conta atualmente selecionada"""
        if account_id in self.accounts:
            self.current_account_id = account_id
            self.accounts[account_id]['last_used'] = datetime.now().isoformat()
            self._save_accounts()
            self._save_current_account(account_id)
    
    def get_current_account_id(self) -> Optional[str]:
        """Retorna o ID da conta atual"""
        return self.current_account_id

# Instância global
ml_account_manager = MercadoLivreAccountManager()