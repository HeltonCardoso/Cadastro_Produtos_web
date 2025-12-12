# log_utils.py
from flask import current_app
from models import db, Processo, ItemProcessado
from datetime import datetime, timedelta
import json
from sqlalchemy import text

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

def obter_grafico_processos_7_dias():
    """Retorna dados para gráfico de processos dos últimos 7 dias"""
    try:
        # Conecta ao banco
        from app import db  # Importa o db do app
        db.session.execute(text("PRAGMA foreign_keys = ON"))
        
        # Calcula data de 7 dias atrás
        from datetime import datetime, timedelta
        data_limite = datetime.now() - timedelta(days=7)
        
        # Query para agrupar por dia
        query = text("""
            SELECT DATE(data_hora) as dia, 
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'sucesso' THEN 1 ELSE 0 END) as sucessos,
                   SUM(CASE WHEN status = 'erro' THEN 1 ELSE 0 END) as erros
            FROM processo
            WHERE data_hora >= :data_limite
            GROUP BY DATE(data_hora)
            ORDER BY dia
        """)
        
        resultados = db.session.execute(query, {'data_limite': data_limite})
        
        # Prepara arrays de dias
        dias = []
        total_processos = []
        sucessos = []
        erros = []
        
        for i in range(7):
            data = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            dias.append(data)
            total_processos.append(0)
            sucessos.append(0)
            erros.append(0)
        
        # Preenche com dados reais
        for row in resultados:
            data_str = row[0] if isinstance(row[0], str) else row[0].strftime('%Y-%m-%d')
            if data_str in dias:
                idx = dias.index(data_str)
                total_processos[idx] = row[1]
                sucessos[idx] = row[2] or 0
                erros[idx] = row[3] or 0
        
        # Inverte para ordem cronológica
        dias.reverse()
        total_processos.reverse()
        sucessos.reverse()
        erros.reverse()
        
        # Formata datas para exibição
        labels = []
        for data_str in dias:
            try:
                data_obj = datetime.strptime(data_str, '%Y-%m-%d')
                labels.append(data_obj.strftime('%d/%m'))
            except:
                labels.append(data_str)
        
        return {
            'labels': labels,
            'valores': total_processos,
            'sucessos': sucessos,
            'erros': erros
        }
        
    except Exception as e:
        print(f"Erro ao obter gráfico de processos: {str(e)}")
        return {
            'labels': [],
            'valores': [],
            'sucessos': [],
            'erros': []
        }