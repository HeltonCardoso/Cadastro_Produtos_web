# log_utils.py
from flask import current_app
from models import db, Processo, ItemProcessado
from datetime import datetime, timedelta
import json

def registrar_processo(modulo: str, qtd_itens: int, tempo_execucao: float, 
                     status: str = "sucesso", usuario: str = "Sistema", erro_mensagem: str = None) -> int:
    """
    Registra uma execução no banco de dados e retorna o ID do processo.
    """
    with current_app.app_context():
        processo = Processo(
            modulo=modulo,
            status=status,
            qtd_itens=qtd_itens,
            tempo_execucao=tempo_execucao,
            usuario=usuario,
            erro_mensagem=erro_mensagem
        )
        db.session.add(processo)
        db.session.commit()
        return processo.id  # Usado para ligar itens processados

def registrar_itens_processados(modulo: str, itens: list, campos: list = None) -> None:
    """
    Registra itens processados no banco, ligados ao último processo do módulo.
    """
    if not itens:
        raise ValueError("Lista de itens vazia")
    
    with current_app.app_context():
        # Encontra o último processo do módulo
        ultimo_processo = Processo.query.filter_by(modulo=modulo).order_by(Processo.id.desc()).first()
        if not ultimo_processo:
            raise ValueError("Nenhum processo registrado para este módulo")
        
        for item in itens:
            # Valida campos obrigatórios
            if not all(c in item for c in ['ean', 'nome', 'status']):
                raise KeyError(f"Campos faltantes no item: {item}")
            item_db = ItemProcessado(
                processo_id=ultimo_processo.id,
                ean=str(item.get('ean', '')),
                nome=item.get('nome', ''),
                status=item.get('status', ''),
                detalhes=json.dumps(item) if campos else None  # Armazena todos os campos como JSON
            )
            db.session.add(item_db)
        db.session.commit()

def obter_historico_processos(modulo: str, dias: int = 30) -> list:
    """
    Retorna o histórico de processos do módulo nos últimos N dias.
    """
    with current_app.app_context():
        cutoff = datetime.now() - timedelta(days=dias)
        historico = Processo.query.filter(
            Processo.modulo == modulo,
            Processo.data >= cutoff
        ).order_by(Processo.data.desc()).all()
        return [
            f"{p.data.strftime('%Y-%m-%d %H:%M:%S')} | Módulo: {p.modulo} | "
            f"Itens: {p.qtd_itens} | Tempo: {p.tempo_execucao:.2f}s | "
            f"Status: {p.status} | Usuário: {p.usuario}"
            for p in historico
        ]

def contar_processos_hoje(modulo: str) -> int:
    """
    Conta processos do dia atual para o módulo.
    """
    with current_app.app_context():
        hoje = datetime.now().date()
        return Processo.query.filter(
            Processo.modulo == modulo,
            db.func.date(Processo.data) == hoje
        ).count()

def contar_status_processos(modulo: str, hoje_only: bool = False) -> tuple:
    """
    Conta processos por status (sucesso/erro), opcionalmente só do dia atual.
    """
    with current_app.app_context():
        query = Processo.query.filter_by(modulo=modulo)
        if hoje_only:
            hoje = datetime.now().date()
            query = query.filter(db.func.date(Processo.data) == hoje)
        sucesso = query.filter_by(status='sucesso').count()
        erro = query.filter_by(status='erro').count()
        return sucesso, erro