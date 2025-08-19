import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
import csv

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