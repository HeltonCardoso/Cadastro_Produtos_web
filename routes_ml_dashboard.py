"""
routes_ml_dashboard.py
Rotas de API para os dashboards de webhook do Mercado Livre.

Registre no app.py:
    from routes_ml_dashboard import ml_dashboard_bp
    app.register_blueprint(ml_dashboard_bp)
"""

from flask import Blueprint, jsonify, render_template
from flask_login import login_required, current_user
from sqlalchemy import func, text
from datetime import datetime, timedelta
from models import db, MLWebhookEvent
import json

ml_dashboard_bp = Blueprint('ml_dashboard', __name__)


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

CATALOG_TOPICS = ['catalog_listing', 'catalog_product', 'catalog']
ITEM_TOPICS    = ['items', 'item']
ORDER_TOPICS   = ['orders', 'order']
PAYMENT_TOPICS = ['payments', 'payment']
QUESTION_TOPICS = ['questions', 'question']

def _match_topics(topic: str, keywords: list) -> bool:
    t = (topic or '').lower()
    return any(k in t for k in keywords)

def _sete_dias():
    return datetime.utcnow() - timedelta(days=7)

def _trinta_dias():
    return datetime.utcnow() - timedelta(days=30)

def _parse_payload(evento) -> dict:
    try:
        return json.loads(evento.payload or '{}')
    except Exception:
        return {}

def _status_from_payload(payload: dict, topic: str) -> str:
    """Tenta extrair o status/ação relevante do payload bruto."""
    # Para items (anúncios)
    if any(k in topic for k in ITEM_TOPICS):
        return payload.get('status') or payload.get('action', '')
    # Para catalog
    if any(k in topic for k in CATALOG_TOPICS):
        return payload.get('status') or payload.get('action', '')
    # Para orders
    if any(k in topic for k in ORDER_TOPICS):
        return payload.get('status') or ''
    return payload.get('status') or payload.get('action', '')


# ──────────────────────────────────────────────────────────────────────────────
# API MASTER — visão geral de catálogos, anúncios e monitoramento
# ──────────────────────────────────────────────────────────────────────────────

@ml_dashboard_bp.route('/api/ml/master/resumo')
@login_required
def api_master_resumo():
    """
    Resumo para o Dashboard Master.
    Retorna KPIs de catálogos, anúncios pausados/excluídos, sugestões e timeline.
    """
    if not current_user.is_master():
        return jsonify({'erro': 'Acesso negado'}), 403

    sete = _sete_dias()
    trinta = _trinta_dias()

    # ── Todos os eventos relevantes (últimos 30 dias) ──────────────────────────
    eventos = (
        MLWebhookEvent.query
        .filter(MLWebhookEvent.received_at >= trinta)
        .order_by(MLWebhookEvent.received_at.desc())
        .all()
    )

    # ── KPIs por categoria ─────────────────────────────────────────────────────
    kpis = {
        'catalogos_novos': 0,
        'sugestoes_catalogo': 0,
        'anuncios_pausados': 0,
        'anuncios_excluidos': 0,
        'anuncios_reativados': 0,
        'total_items_eventos': 0,
        'total_catalog_eventos': 0,
        'total_orders': 0,
        'total_payments': 0,
        'total_questions': 0,
        'total_7d': 0,
        'total_30d': len(eventos),
    }

    # Listas para tabelas
    catalogos = []
    anuncios_alertas = []
    sugestoes = []
    timeline = []  # últimos 100 eventos para linha do tempo

    for e in eventos:
        topic = (e.topic or '').lower()
        payload = _parse_payload(e)
        status = _status_from_payload(payload, topic)
        status_lower = (status or '').lower()

        # Contagem 7 dias
        if e.received_at >= sete:
            kpis['total_7d'] += 1

        # ── Catálogos ────────────────────────────────────────────────────────
        if _match_topics(topic, CATALOG_TOPICS):
            kpis['total_catalog_eventos'] += 1

            if 'suggestion' in topic or 'suggestion' in status_lower or 'sugest' in status_lower:
                kpis['sugestoes_catalogo'] += 1
                sugestoes.append({
                    'id': e.id,
                    'resource': e.resource,
                    'user_id': e.user_id,
                    'status': status,
                    'received_at': e.received_at.isoformat() if e.received_at else None,
                })
            else:
                kpis['catalogos_novos'] += 1
                catalogos.append({
                    'id': e.id,
                    'topic': e.topic,
                    'resource': e.resource,
                    'user_id': e.user_id,
                    'status': status,
                    'received_at': e.received_at.isoformat() if e.received_at else None,
                })

        # ── Anúncios (items) ─────────────────────────────────────────────────
        elif _match_topics(topic, ITEM_TOPICS):
            kpis['total_items_eventos'] += 1

            if any(x in status_lower for x in ['paused', 'pausado', 'pause']):
                kpis['anuncios_pausados'] += 1
                anuncios_alertas.append({
                    'id': e.id,
                    'tipo': 'pausado',
                    'resource': e.resource,
                    'user_id': e.user_id,
                    'status': status,
                    'received_at': e.received_at.isoformat() if e.received_at else None,
                })
            elif any(x in status_lower for x in ['deleted', 'excluido', 'removed', 'closed']):
                kpis['anuncios_excluidos'] += 1
                anuncios_alertas.append({
                    'id': e.id,
                    'tipo': 'excluido',
                    'resource': e.resource,
                    'user_id': e.user_id,
                    'status': status,
                    'received_at': e.received_at.isoformat() if e.received_at else None,
                })
            elif any(x in status_lower for x in ['active', 'ativo', 'reactivated']):
                kpis['anuncios_reativados'] += 1

        # ── Pedidos / Pagamentos / Perguntas ─────────────────────────────────
        elif _match_topics(topic, ORDER_TOPICS):
            kpis['total_orders'] += 1
        elif _match_topics(topic, PAYMENT_TOPICS):
            kpis['total_payments'] += 1
        elif _match_topics(topic, QUESTION_TOPICS):
            kpis['total_questions'] += 1

    # Timeline — últimos 80 eventos (todos os tópicos)
    timeline_eventos = (
        MLWebhookEvent.query
        .order_by(MLWebhookEvent.received_at.desc())
        .limit(80)
        .all()
    )
    for e in timeline_eventos:
        timeline.append({
            'id': e.id,
            'topic': e.topic,
            'resource': e.resource,
            'user_id': e.user_id,
            'attempts': e.attempts,
            'processed': e.processed,
            'received_at': e.received_at.isoformat() if e.received_at else None,
        })

    # Gráfico de volume diário (últimos 7 dias)
    volume_diario = _volume_diario(7)

    # Sellers únicos
    sellers = (
        db.session.query(MLWebhookEvent.user_id, func.count(MLWebhookEvent.id).label('total'))
        .filter(MLWebhookEvent.received_at >= sete)
        .group_by(MLWebhookEvent.user_id)
        .order_by(func.count(MLWebhookEvent.id).desc())
        .limit(10)
        .all()
    )

    return jsonify({
        'kpis': kpis,
        'catalogos': catalogos[:50],
        'sugestoes': sugestoes[:50],
        'anuncios_alertas': anuncios_alertas[:50],
        'timeline': timeline,
        'volume_diario': volume_diario,
        'top_sellers': [{'user_id': s.user_id, 'total': s.total} for s in sellers],
    })


# ──────────────────────────────────────────────────────────────────────────────
# API SAC — perguntas, pedidos e atendimento ao cliente
# ──────────────────────────────────────────────────────────────────────────────

@ml_dashboard_bp.route('/api/ml/sac/resumo')
@login_required
def api_sac_resumo():
    """
    Resumo para o Dashboard SAC.
    Foca em perguntas (respondidas/pendentes) e pedidos recentes.
    """
    if not current_user.has_permission('dashboard'):
        return jsonify({'erro': 'Acesso negado'}), 403

    sete = _sete_dias()
    trinta = _trinta_dias()

    # ── Eventos de perguntas ───────────────────────────────────────────────────
    perguntas_eventos = (
        MLWebhookEvent.query
        .filter(
            MLWebhookEvent.received_at >= trinta,
            MLWebhookEvent.topic.ilike('%question%')
        )
        .order_by(MLWebhookEvent.received_at.desc())
        .all()
    )

    # ── Eventos de pedidos ─────────────────────────────────────────────────────
    pedidos_eventos = (
        MLWebhookEvent.query
        .filter(
            MLWebhookEvent.received_at >= sete,
            MLWebhookEvent.topic.ilike('%order%')
        )
        .order_by(MLWebhookEvent.received_at.desc())
        .limit(100)
        .all()
    )

    # ── Eventos de pagamentos ──────────────────────────────────────────────────
    pagamentos_eventos = (
        MLWebhookEvent.query
        .filter(
            MLWebhookEvent.received_at >= sete,
            MLWebhookEvent.topic.ilike('%payment%')
        )
        .order_by(MLWebhookEvent.received_at.desc())
        .limit(100)
        .all()
    )

    # ── KPIs ──────────────────────────────────────────────────────────────────
    kpis = {
        'perguntas_total': len(perguntas_eventos),
        'perguntas_pendentes': 0,
        'perguntas_respondidas': 0,
        'pedidos_7d': len(pedidos_eventos),
        'pagamentos_7d': len(pagamentos_eventos),
        'perguntas_hoje': 0,
        'tempo_medio_resposta': '—',  # placeholder (depende de API ML)
    }

    hoje = datetime.utcnow().date()
    perguntas_lista = []

    for e in perguntas_eventos:
        payload = _parse_payload(e)
        status = _status_from_payload(payload, e.topic or '')
        status_lower = (status or '').lower()

        if e.received_at and e.received_at.date() == hoje:
            kpis['perguntas_hoje'] += 1

        is_pendente = any(x in status_lower for x in ['unanswered', 'pending', 'aberta', 'open', ''])
        if not status_lower or is_pendente:
            kpis['perguntas_pendentes'] += 1
        else:
            kpis['perguntas_respondidas'] += 1

        perguntas_lista.append({
            'id': e.id,
            'resource': e.resource,
            'user_id': e.user_id,
            'status': status or 'pendente',
            'attempts': e.attempts,
            'processed': e.processed,
            'received_at': e.received_at.isoformat() if e.received_at else None,
        })

    # Pedidos para exibição
    pedidos_lista = []
    for e in pedidos_eventos:
        payload = _parse_payload(e)
        status = _status_from_payload(payload, e.topic or '')
        pedidos_lista.append({
            'id': e.id,
            'resource': e.resource,
            'user_id': e.user_id,
            'status': status or '—',
            'attempts': e.attempts,
            'received_at': e.received_at.isoformat() if e.received_at else None,
        })

    # Volume de perguntas por dia (últimos 7 dias)
    volume_perguntas = _volume_diario(7, topic_filter='question')

    return jsonify({
        'kpis': kpis,
        'perguntas': perguntas_lista[:100],
        'pedidos': pedidos_lista[:50],
        'volume_perguntas': volume_perguntas,
    })


# ──────────────────────────────────────────────────────────────────────────────
# HELPER INTERNO — volume diário
# ──────────────────────────────────────────────────────────────────────────────

def _volume_diario(days: int = 7, topic_filter: str = None) -> list:
    """Retorna lista de {data, total} para os últimos N dias."""
    result = []
    base = datetime.utcnow().date()
    for i in range(days - 1, -1, -1):
        dia = base - timedelta(days=i)
        inicio = datetime(dia.year, dia.month, dia.day, 0, 0, 0)
        fim    = datetime(dia.year, dia.month, dia.day, 23, 59, 59)
        q = MLWebhookEvent.query.filter(
            MLWebhookEvent.received_at >= inicio,
            MLWebhookEvent.received_at <= fim,
        )
        if topic_filter:
            q = q.filter(MLWebhookEvent.topic.ilike(f'%{topic_filter}%'))
        total = q.count()
        result.append({'data': dia.strftime('%d/%m'), 'total': total})
    return result


# ──────────────────────────────────────────────────────────────────────────────
# PÁGINAS HTML
# ──────────────────────────────────────────────────────────────────────────────

@ml_dashboard_bp.route('/dashboard/master')
@login_required
def dashboard_master():
    if not current_user.is_master():
        from flask import flash, redirect, url_for
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))

    from models import Usuario, Processo

    try:
        total_usuarios  = Usuario.query.count()
    except Exception:
        total_usuarios  = 0

    try:
        total_processos = Processo.query.count()
    except Exception:
        total_processos = 0

    try:
        from log_utils import contar_processos_hoje
        processos_hoje = contar_processos_hoje()
    except Exception:
        hoje_inicio = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        try:
            processos_hoje = Processo.query.filter(
                Processo.created_at >= hoje_inicio
            ).count()
        except Exception:
            processos_hoje = 0

    stats = {
        'total_usuarios':  total_usuarios,
        'total_processos': total_processos,
        'processos_hoje':  processos_hoje,
    }

    return render_template('dashboard_master.html', stats=stats)


@ml_dashboard_bp.route('/dashboard/sac')
@login_required
def dashboard_sac():
    if not current_user.has_permission('dashboard'):
        from flask import flash, redirect, url_for
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    return render_template('dashboard_sac.html')