# utils/stats_utils.py
from flask import current_app
from models import db, Processo, ItemProcessado
from datetime import datetime, date, timedelta

def get_processing_stats(modulo=None):
    """Obtém estatísticas de processamento, opcionalmente filtradas por módulo"""
    query = Processo.query
    if modulo:
        query = query.filter_by(modulo=modulo)
    
    # Obter totais gerais
    total = query.count()
    sucessos_total = query.filter_by(status="sucesso").count()
    erros_total = query.filter_by(status="erro").count()
    
    # Obter totais do dia atual
    hoje = datetime.now().date()
    hoje_total = query.filter(db.func.date(Processo.data) == hoje).count()
    hoje_sucesso = query.filter(
        db.func.date(Processo.data) == hoje,
        Processo.status == "sucesso"
    ).count()
    hoje_erro = hoje_total - hoje_sucesso
    
    # Obter última execução
    ultimo_processo = query.order_by(Processo.data.desc()).first()
    ultima_execucao = (
        f"{ultimo_processo.data.strftime('%d/%m/%Y %H:%M')} | "
        f"{ultimo_processo.modulo} | "
        f"{'Sucesso' if ultimo_processo.status == 'sucesso' else 'Erro'}"
    ) if ultimo_processo else "Nenhum registro"

    # Obter totais de itens processados
    query_itens = ItemProcessado.query
    if modulo:
        # Assumindo que ItemProcessado está relacionado com Processo
        query_itens = query_itens.join(Processo).filter(Processo.modulo == modulo)
    
    total_itens_sucesso = query_itens.filter_by(status="sucesso").count()
    total_itens_erro = query_itens.filter_by(status="erro").count()

    return {
        'total': total,
        'sucessos_total': sucessos_total,
        'erros_total': erros_total,
        'hoje': hoje_total,
        'sucessos_hoje': hoje_sucesso,
        'erros_hoje': hoje_erro,
        'ultima': ultima_execucao,
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