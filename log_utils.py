# log_utils.py
import os
import csv
from datetime import datetime

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