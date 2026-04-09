import os
import json
from pathlib import Path
from datetime import datetime
from google.oauth2.credentials import Credentials


class GoogleTokenManager:
    """Gerencia os tokens OAuth do Google de forma segura"""
    
    def __init__(self, user_id=None):
        self.user_id = user_id or 'default'
        self.tokens_dir = Path('google_tokens')
        self.tokens_dir.mkdir(exist_ok=True)
    
    def get_token_file(self):
        """Retorna o caminho do arquivo de token"""
        return self.tokens_dir / f'token_{self.user_id}.json'
    
    def save_tokens(self, credentials):
        """Salva os tokens no arquivo"""
        token_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None,
            'user_id': self.user_id,
            'created_at': datetime.now().isoformat()
        }
        
        with open(self.get_token_file(), 'w') as f:
            json.dump(token_data, f, indent=2)
        
        return True
    
    def load_tokens(self):
        """Carrega os tokens do arquivo"""
        token_file = self.get_token_file()
        
        if not token_file.exists():
            return None
        
        try:
            with open(token_file, 'r') as f:
                token_data = json.load(f)
            
            credentials = Credentials(
                token=token_data.get('token'),
                refresh_token=token_data.get('refresh_token'),
                token_uri=token_data.get('token_uri'),
                client_id=token_data.get('client_id'),
                client_secret=token_data.get('client_secret'),
                scopes=token_data.get('scopes')
            )
            
            # Restaura expiry se existir
            if token_data.get('expiry'):
                credentials.expiry = datetime.fromisoformat(token_data['expiry'])
            
            return credentials
            
        except Exception as e:
            print(f"Erro ao carregar tokens: {e}")
            return None
    
    def remove_tokens(self):
        """Remove os tokens do arquivo"""
        token_file = self.get_token_file()
        if token_file.exists():
            token_file.unlink()
            return True
        return False
    
    def is_connected(self):
        """Verifica se está conectado"""
        credentials = self.load_tokens()
        if credentials is None:
            return False
        
        if credentials.valid:
            return True
        
        # Tenta renovar se expirou
        if credentials.expired and credentials.refresh_token:
            try:
                from google.auth.transport.requests import Request
                credentials.refresh(Request())
                self.save_tokens(credentials)
                return True
            except:
                return False
        
        return False