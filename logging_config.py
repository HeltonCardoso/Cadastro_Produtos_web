import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
import csv

def configure_loggers():
    """Configura todos os loggers da aplicação"""
    
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
        setup_logger(
            name=logger_name,
            filename=os.path.join(log_directory, config['filename']),
            level=config['level'],
            format=log_format
        )

def setup_logger(name, filename, level, format):
    """Configura um logger individual"""
    
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
    logger.setLevel(level)
    logger.addHandler(handler)
    
    # Evita que logs sejam propagados para o logger root
    logger.propagate = False

def get_logger(name):
    """Retorna um logger configurado"""
    return logging.getLogger(name)

def registrar_processo(modulo, qtd_itens, tempo_execucao, status="sucesso", usuario="Sistema"):
    """Registra uma execução no log de processos"""
    log_dir = f"logs/processos"
    os.makedirs(log_dir, exist_ok=True)
    
    with open(f"{log_dir}/{modulo}.log", "a", encoding="utf-8") as f:
        f.write(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
            f"Módulo: {modulo} | "
            f"Itens: {qtd_itens} | "
            f"Tempo: {tempo_execucao:.2f}s | "
            f"Status: {status} | "
            f"Usuário: {usuario}\n"
        )

def registrar_itens_processados(modulo, itens, campos=None):
    """Registra itens processados em arquivo CSV"""
    data_dir = datetime.now().strftime("%Y-%m-%d")
    log_dir = f"logs/itens/{modulo}/{data_dir}"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = f"{log_dir}/processamento_{datetime.now().strftime('%H%M%S')}.csv"
    
    # Campos padrão se não forem especificados
    if campos is None:
        campos = ['ean', 'nome', 'status', 'data_processamento']
    
    with open(log_file, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(itens)
    
    return log_file

def obter_historico_processos(modulo, dias=30):
    """Obtém o histórico de processos de um módulo"""
    log_file = f"logs/processos/{modulo}.log"
    historico = []
    
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            historico = f.read().splitlines()[-dias:]
    
    return historico

def contar_processos_hoje(modulo):
    """Conta processos executados hoje para um módulo"""
    hoje = datetime.now().strftime("%Y-%m-%d")
    count = 0
    log_file = f"logs/processos/{modulo}.log"
    
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith(hoje):
                    count += 1
    return count