# utils/stats_utils.py
from flask import current_app
from models import db, Processo, ItemProcessado
from datetime import datetime, date, timedelta

def get_processing_stats(modulo: str = None) -> dict:
    """
    Retorna estatísticas de processos. Se modulo=None, retorna totais gerais.
    """
    with current_app.app_context():
        # Filtro por módulo ou geral
        query = Processo.query if modulo is None else Processo.query.filter_by(modulo=modulo)
        hoje = date.today()
        
        # Total de processos
        total = query.count()
        
        # Processos hoje
        processos_hoje = query.filter(db.func.date(Processo.data) == hoje).count()
        
        # Sucessos e erros (total e hoje)
        sucessos_total = query.filter_by(status='sucesso').count()
        erros_total = query.filter_by(status='erro').count()
        sucessos_hoje = query.filter(
            Processo.status == 'sucesso',
            db.func.date(Processo.data) == hoje
        ).count()
        erros_hoje = query.filter(
            Processo.status == 'erro',
            db.func.date(Processo.data) == hoje
        ).count()
        
        # Última execução (geral ou por módulo)
        ultima = query.order_by(Processo.data.desc()).first()
        ultima_exec = (
            f"{ultima.data.strftime('%Y-%m-%d %H:%M:%S')} | Módulo: {ultima.modulo} | "
            f"Itens: {ultima.qtd_itens} | Status: {ultima.status}"
        ) if ultima else None
        
        # Total de itens processados (sucesso e erro)
        total_itens_sucesso = db.session.query(db.func.sum(Processo.qtd_itens)).filter(
            Processo.status == 'sucesso'
        ).filter(Processo.modulo == modulo if modulo else True).scalar() or 0
        total_itens_erro = db.session.query(db.func.sum(Processo.qtd_itens)).filter(
            Processo.status == 'erro'
        ).filter(Processo.modulo == modulo if modulo else True).scalar() or 0
        
        return {
            'total': total,
            'hoje': processos_hoje,
            'sucessos_total': sucessos_total,
            'erros_total': erros_total,
            'sucessos_hoje': sucessos_hoje,
            'erros_hoje': erros_hoje,
            'ultima': ultima_exec,
            'total_itens_sucesso': total_itens_sucesso,
            'total_itens_erro': total_itens_erro
        }

def contar_processos_por_dia(modulo: str, data_str: str) -> int:
    """
    Conta processos em uma data específica para o módulo.
    """
    with current_app.app_context():
        return Processo.query.filter(
            Processo.modulo == modulo,
            db.func.date(Processo.data) == data_str
        ).count()

def obter_dados_grafico_7dias() -> dict:
    """
    Gera dados para gráfico dos últimos 7 dias, por módulo.
    """
    with current_app.app_context():
        datas = []
        valores = {'cadastro': [], 'atributos': [], 'prazos': []}
        for i in range(6, -1, -1):  # 7 dias, incluindo hoje
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            datas.append(date.split('-')[2] + '/' + date.split('-')[1])  # DD/MM
            for modulo in valores:
                count = contar_processos_por_dia(modulo, date)
                valores[modulo].append(count)
        return {'datas': datas, 'valores': valores}