import os
import json
from datetime import datetime
from pathlib import Path
from flask import session, url_for, redirect, request, jsonify
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import gspread
import requests as http_requests


class GoogleSheetsOAuth:
    """Gerencia autenticação OAuth 2.0 para Google Sheets"""
    
    def __init__(self, app=None):
        self.app = app
        self.SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa com o app Flask"""
        self.app = app
        
        # Configurações padrão
        app.config.setdefault('GOOGLE_CLIENT_ID', os.environ.get('GOOGLE_CLIENT_ID'))
        app.config.setdefault('GOOGLE_CLIENT_SECRET', os.environ.get('GOOGLE_CLIENT_SECRET'))
        app.config.setdefault('GOOGLE_REDIRECT_URI', os.environ.get('GOOGLE_REDIRECT_URI'))
        
        # Registra rotas
        self.register_routes(app)
    
    def register_routes(self, app):
        """Registra as rotas de autenticação"""
        
        @app.route('/google/auth')
        def google_auth():
            """Inicia o fluxo OAuth"""
            return self.authenticate()
        
        @app.route('/google/callback')
        def google_callback():
            """Callback do OAuth"""
            return self.callback()
        
        @app.route('/google/revoke')
        def google_revoke():
            """Revoga acesso"""
            return self.revoke()
        
        @app.route('/api/google/status')
        def google_status():
            """Verifica status da autenticação"""
            return self.get_status()
    
    def get_flow(self):
        """Cria o fluxo OAuth"""
        from google_auth_oauthlib.flow import Flow
        
        client_config = {
            "web": {
                "client_id": self.app.config['GOOGLE_CLIENT_ID'],
                "client_secret": self.app.config['GOOGLE_CLIENT_SECRET'],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.app.config['GOOGLE_REDIRECT_URI']]
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=self.SCOPES
        )
        flow.redirect_uri = self.app.config['GOOGLE_REDIRECT_URI']
        return flow
    
    def authenticate(self):
        """Inicia autenticação OAuth"""
        flow = self.get_flow()
        
        # Gera URL de autorização
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        # Salva o estado na sessão
        session['google_oauth_state'] = state
        
        return redirect(authorization_url)
    
    def callback(self):
        """Processa o callback do OAuth"""
        try:
            # Recupera o estado
            state = session.get('google_oauth_state')
            
            flow = self.get_flow()
            flow.fetch_token(authorization_response=request.url, state=state)
            
            credentials = flow.credentials
            
            # Salva os tokens
            from .token_manager import GoogleTokenManager
            token_manager = GoogleTokenManager()
            token_manager.save_tokens(credentials)
            
            # Limpa sessão
            session.pop('google_oauth_state', None)
            
            # Redireciona de volta para a página de configuração
            return redirect(url_for('configurar_tokens') + '?google_success=1')
            
        except Exception as e:
            print(f"Erro no callback OAuth: {e}")
            return redirect(url_for('configurar_tokens') + '?google_error=' + str(e))
    
    def revoke(self):
        """Revoga o token de acesso"""
        try:
            from .token_manager import GoogleTokenManager
            token_manager = GoogleTokenManager()
            credentials = token_manager.load_tokens()
            
            if credentials:
                # Revoga o token
                revoke_response = http_requests.post(
                    'https://oauth2.googleapis.com/revoke',
                    params={'token': credentials.token},
                    headers={'content-type': 'application/x-www-form-urlencoded'}
                )
                
                # Remove do arquivo
                token_manager.remove_tokens()
                
                return jsonify({
                    'success': True,
                    'message': 'Acesso revogado com sucesso'
                })
            
            return jsonify({'success': False, 'error': 'Nenhum token encontrado'})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    def get_status(self):
        """Verifica status da autenticação"""
        try:
            from .token_manager import GoogleTokenManager
            token_manager = GoogleTokenManager()
            credentials = token_manager.load_tokens()
            
            if credentials and credentials.valid:
                # Verifica se ainda está válido
                return jsonify({
                    'success': True,
                    'connected': True,
                    'expires_at': credentials.expiry.isoformat() if credentials.expiry else None
                })
            elif credentials and credentials.expired and credentials.refresh_token:
                # Tenta renovar
                try:
                    credentials.refresh(Request())
                    token_manager.save_tokens(credentials)
                    return jsonify({
                        'success': True,
                        'connected': True,
                        'refreshed': True,
                        'expires_at': credentials.expiry.isoformat() if credentials.expiry else None
                    })
                except:
                    return jsonify({
                        'success': True,
                        'connected': False,
                        'message': 'Token expirado e não foi possível renovar'
                    })
            else:
                return jsonify({
                    'success': True,
                    'connected': False,
                    'message': 'Não conectado'
                })
                
        except Exception as e:
            return jsonify({
                'success': False,
                'connected': False,
                'error': str(e)
            }), 500
    
    def get_client(self):
        """Retorna cliente autenticado do gspread"""
        try:
            from .token_manager import GoogleTokenManager
            token_manager = GoogleTokenManager()
            credentials = token_manager.load_tokens()
            
            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                    token_manager.save_tokens(credentials)
                else:
                    return None
            
            # Converte para o formato do gspread
            gc = gspread.authorize(credentials)
            return gc
            
        except Exception as e:
            print(f"Erro ao obter cliente Google Sheets: {e}")
            return None