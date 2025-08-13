import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
import csv

def configure_loggers():
    """Configura todos os loggers da aplicação"""
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, LOG_LEVEL, logging.INFO)
    # Configuração básica
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_directory = 'logs'
    
    # Cria diretório se não existir
    os.makedirs(log_directory, exist_ok=True)
    
    # Configuração dos loggers individuais
    loggers_config = {
        'main': {
            'filename': 'app.log',
            'level': logging.INFO
        },
        'cadastro': {
            'filename': 'cadastro.log',
            'level': logging.INFO
        },
        'atributos': {
            'filename': 'atributos.log',
            'level': logging.INFO
        },
        'prazos': {
            'filename': 'prazos.log',
            'level': logging.INFO
        },
        'uploads': {
            'filename': 'uploads.log',
            'level': logging.INFO
        }
    }
    
    # Configura cada logger
    for logger_name, config in loggers_config.items():
        config['level'] = log_level
        setup_logger(
            name=logger_name,
            filename=os.path.join(log_directory, config['filename']),
            level=config['level'],
            format=log_format
        )

def setup_logger(name, filename, level, format):
    """Configura um logger individual"""
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(format))

    # Cria o handler com rotação
    handler = RotatingFileHandler(
        filename,
        maxBytes=1024*1024,  # 1MB
        backupCount=5,
        encoding='utf-8'
    )
    
    # Formato das mensagens
    formatter = logging.Formatter(format)
    handler.setFormatter(formatter)
    
    # Configura o logger
    logger = logging.getLogger(name)
    logger.addHandler(console_handler)
    logger.setLevel(level)
    logger.addHandler(handler)
    
    # Evita que logs sejam propagados para o logger root
    logger.propagate = False

def get_logger(name):
    """Retorna um logger configurado"""
    return logging.getLogger(name)

def init_log_dirs():
    """Cria todas as pastas necessárias"""
    dirs = [
        'logs/processos',
        'logs/itens/cadastro',
        'logs/itens/atributos', 
        'logs/itens/prazos',
        'uploads'
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)