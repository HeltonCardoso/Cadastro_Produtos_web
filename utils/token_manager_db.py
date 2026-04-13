# utils/token_manager_db.py
from datetime import datetime
import json
from models import db, TokenConfig

def salvar_token(service, token_data):
    """
    Salva token de um serviço no banco de dados.
    
    Args:
        service: 'anymarket', 'intelipost', 'mercadolivre', 'google'
        token_data: dict com os dados do token
    """
    try:
        config = TokenConfig.query.filter_by(service=service).first()
        
        if config:
            config.set_data(token_data)
            config.updated_at = datetime.utcnow()
        else:
            config = TokenConfig(service=service)
            config.set_data(token_data)
            db.session.add(config)
        
        db.session.commit()
        print(f"✅ Token {service} salvo no banco de dados")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar token {service}: {e}")
        db.session.rollback()
        return False

def obter_token(service):
    """
    Obtém token de um serviço do banco de dados.
    
    Args:
        service: 'anymarket', 'intelipost', 'mercadolivre', 'google'
    
    Returns:
        dict com os dados do token ou None
    """
    try:
        config = TokenConfig.query.filter_by(service=service).first()
        if config:
            return config.get_data()
        return None
    except Exception as e:
        print(f"❌ Erro ao obter token {service}: {e}")
        return None

def remover_token(service):
    """Remove token de um serviço do banco de dados"""
    try:
        config = TokenConfig.query.filter_by(service=service).first()
        if config:
            db.session.delete(config)
            db.session.commit()
            print(f"✅ Token {service} removido do banco")
            return True
        return False
    except Exception as e:
        print(f"❌ Erro ao remover token {service}: {e}")
        db.session.rollback()
        return False

def token_existe(service):
    """Verifica se o token existe no banco"""
    config = TokenConfig.query.filter_by(service=service).first()
    return config is not None