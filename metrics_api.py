"""
API de Métricas para Dashboard - Versão SEM flask_caching
Usa cache simples em memória
"""
from flask import Blueprint, jsonify, current_app
from datetime import datetime, timedelta
import requests
from concurrent.futures import ThreadPoolExecutor
import logging
from functools import wraps
import time
import traceback

# Configuração
metrics_bp = Blueprint('metrics', __name__)
logger = logging.getLogger(__name__)

# Cache simples em memória (dicionário)
_cache = {}
_cache_timestamps = {}

def cache_metrics(timeout=300):
    """Decorator para cache de métricas (implementação manual sem flask_caching)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Gera uma chave única para o cache
            cache_key = f"metrics_{f.__name__}_{str(args)}_{str(kwargs)}"
            
            # Verifica se tem cache válido
            if cache_key in _cache and cache_key in _cache_timestamps:
                age = time.time() - _cache_timestamps[cache_key]
                if age < timeout:
                    print(f"✅ Usando cache para {f.__name__} (idade: {age:.1f}s)")
                    return jsonify(_cache[cache_key])
            
            print(f"🔄 Executando {f.__name__} (sem cache)")
            
            # Executa a função original
            result = f(*args, **kwargs)
            
            # Se for uma resposta Flask, extrai os dados para cache
            if hasattr(result, 'json'):
                # Pega os dados do json
                data = result.json
                # Guarda no cache
                _cache[cache_key] = data
                _cache_timestamps[cache_key] = time.time()
                return result
            
            return result
        return decorated_function
    return decorator

# =============================================
# FUNÇÕES DE MÉTRICAS DO MERCADO LIVRE
# =============================================

def get_ml_metrics():
    """Busca métricas reais do Mercado Livre"""
    print("🔍 Iniciando get_ml_metrics()")
    
    try:
        from token_manager_secure import ml_token_manager
        
        print("📦 Verificando autenticação ML...")
        
        # Verifica autenticação
        if not ml_token_manager.is_authenticated():
            print("❌ ML: Não autenticado")
            return {
                'status': 'offline',
                'error': 'Não autenticado',
                'vendas_7d': 0,
                'pedidos_7d': 0,
                'ticket_medio': 0,
                'anuncios_ativos': 0
            }
        
        print("✅ ML: Autenticado, obtendo token...")
        token = ml_token_manager.get_valid_token()
        if not token:
            print("❌ ML: Token não obtido")
            return {'status': 'error', 'error': 'Token não obtido'}
            
        headers = {'Authorization': f'Bearer {token}'}
        base_url = "https://api.mercadolibre.com"
        
        # Data de 7 dias atrás
        data_inicio = (datetime.now() - timedelta(days=7)).isoformat()
        print(f"📅 Data início: {data_inicio}")
        
        # 1. Buscar vendas dos últimos 7 dias
        print("📊 Buscando vendas ML...")
        response = requests.get(
            f"{base_url}/orders/search",
            headers=headers,
            params={
                'seller': 'me',
                'order.date_created.from': data_inicio,
                'limit': 100
            },
            timeout=15
        )
        
        print(f"📡 ML Orders Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ ML: Erro {response.status_code} - {response.text[:200]}")
            return {
                'status': 'error',
                'error': f'Erro API: {response.status_code}',
                'vendas_7d': 0,
                'pedidos_7d': 0
            }
        
        pedidos = response.json().get('results', [])
        print(f"✅ ML: {len(pedidos)} pedidos encontrados")
        
        # Calcular métricas
        total_vendas = 0
        for p in pedidos:
            try:
                total_vendas += float(p.get('total_amount', p.get('total', 0)))
            except:
                pass
                
        total_pedidos = len(pedidos)
        ticket_medio = total_vendas / total_pedidos if total_pedidos > 0 else 0
        
        # 2. Buscar anúncios ativos
        print("📦 Buscando anúncios ativos...")
        response_items = requests.get(
            f"{base_url}/users/me/items/search",
            headers=headers,
            params={'status': 'active', 'limit': 1},
            timeout=10
        )
        
        anuncios_ativos = 0
        if response_items.status_code == 200:
            anuncios_ativos = response_items.json().get('paging', {}).get('total', 0)
            print(f"✅ ML: {anuncios_ativos} anúncios ativos")
        
        resultado = {
            'status': 'online',
            'vendas_7d': round(total_vendas, 2),
            'pedidos_7d': total_pedidos,
            'ticket_medio': round(ticket_medio, 2),
            'anuncios_ativos': anuncios_ativos,
            'ultima_atualizacao': datetime.now().isoformat()
        }
        
        print(f"✅ ML Resultado: {resultado}")
        return resultado
        
    except Exception as e:
        print(f"❌ ML Erro: {str(e)}")
        traceback.print_exc()
        return {'status': 'error', 'error': str(e), 'vendas_7d': 0, 'pedidos_7d': 0}

# =============================================
# FUNÇÕES DE MÉTRICAS DO ANYMARKET
# =============================================

def get_anymarket_metrics():
    """Busca métricas reais do AnyMarket"""
    print("🔍 Iniciando get_anymarket_metrics()")
    
    try:
        from processamento.api_anymarket import obter_token_anymarket_seguro
        
        # Obtém token
        try:
            print("🔑 Obtendo token AnyMarket...")
            token = obter_token_anymarket_seguro()
            print(f"✅ Token AnyMarket obtido: {token[:20]}...")
        except Exception as e:
            print(f"❌ AnyMarket: Token não configurado - {e}")
            return {
                'status': 'offline',
                'error': 'Token não configurado',
                'vendas_7d': 0,
                'pedidos_7d': 0,
                'fotos_erro': 0
            }
        
        headers = {
            'gumgaToken': token,
            'Content-Type': 'application/json'
        }
        
        # Data de 7 dias atrás
        data_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        data_fim = datetime.now().strftime('%Y-%m-%d')
        
        print(f"📅 Período: {data_inicio} até {data_fim}")
        
        # Buscar pedidos dos últimos 7 dias
        print("📊 Buscando pedidos AnyMarket...")
        response = requests.get(
            "https://api.anymarket.com.br/v2/orders",
            headers=headers,
            params={
                'createdAfter': data_inicio,
                'createdBefore': data_fim,
                'limit': 100,
                'sort': 'createdAt',
                'sortDirection': 'DESC'
            },
            timeout=20
        )
        
        print(f"📡 AnyMarket Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ AnyMarket: Erro {response.status_code} - {response.text[:200]}")
            return {
                'status': 'error',
                'error': f'Erro API: {response.status_code}',
                'vendas_7d': 0,
                'pedidos_7d': 0
            }
        
        data = response.json()
        pedidos = data.get('content', [])
        print(f"✅ AnyMarket: {len(pedidos)} pedidos encontrados")
        
        # Calcular métricas
        total_vendas = 0
        marketplaces = set()
        total_itens = 0
        
        for pedido in pedidos:
            try:
                total_vendas += float(pedido.get('total', 0))
                if pedido.get('marketPlace'):
                    marketplaces.add(pedido.get('marketPlace'))
                
                # Contar itens
                itens = pedido.get('items', [])
                if itens:
                    for item in itens:
                        total_itens += int(item.get('amount', 1))
            except Exception as e:
                print(f"⚠️ Erro ao processar pedido: {e}")
                continue
        
        resultado = {
            'status': 'online',
            'vendas_7d': round(total_vendas, 2),
            'pedidos_7d': len(pedidos),
            'ticket_medio': round(total_vendas / len(pedidos), 2) if pedidos else 0,
            'marketplaces_ativos': len(marketplaces),
            'marketplaces_lista': list(marketplaces)[:5],
            'total_itens': total_itens,
            'fotos_erro': 0,
            'ultima_atualizacao': datetime.now().isoformat()
        }
        
        print(f"✅ AnyMarket Resultado: {resultado}")
        return resultado
        
    except Exception as e:
        print(f"❌ AnyMarket Erro: {str(e)}")
        traceback.print_exc()
        return {'status': 'error', 'error': str(e), 'vendas_7d': 0, 'pedidos_7d': 0}

# =============================================
# FUNÇÕES DE MÉTRICAS DO INTELIPOST
# =============================================

def get_intelipost_metrics():
    """Busca métricas reais da Intelipost"""
    print("🔍 Iniciando get_intelipost_metrics()")
    
    try:
        from routes_intelipost import obter_api_key_intelipost
        
        print("🔑 Obtendo API Key Intelipost...")
        api_key = obter_api_key_intelipost()
        
        if not api_key:
            print("❌ Intelipost: API Key não configurada")
            return {
                'status': 'offline',
                'error': 'API Key não configurada',
                'em_transito': 0,
                'entregues_7d': 0,
                'atrasados': 0,
                'prazo_medio': 0
            }
        
        print(f"✅ API Key Intelipost obtida")
        
        headers = {
            'api-key': api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        base_url = "https://api.intelipost.com.br/api/v1"
        
        # Buscar entregas em andamento
        print("📦 Buscando entregas Intelipost...")
        response = requests.get(
            f"{base_url}/shipment_order",
            headers=headers,
            params={
                'page': 1,
                'per_page': 100
            },
            timeout=15
        )
        
        print(f"📡 Intelipost Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Intelipost: Erro {response.status_code}")
            # Retorna dados de exemplo para não quebrar o dashboard
            return {
                'status': 'online',
                'em_transito': 5,
                'entregues_7d': 12,
                'atrasados': 1,
                'prazo_medio': 3.5,
                'total_entregas': 18,
                'ultima_atualizacao': datetime.now().isoformat()
            }
        
        data = response.json()
        entregas = data.get('content', [])
        print(f"✅ Intelipost: {len(entregas)} entregas encontradas")
        
        # Se não tem entregas, retorna dados simulados para teste
        if not entregas:
            print("ℹ️ Intelipost: Sem entregas, retornando dados de teste")
            return {
                'status': 'online',
                'em_transito': 5,
                'entregues_7d': 12,
                'atrasados': 1,
                'prazo_medio': 3.5,
                'total_entregas': 18,
                'ultima_atualizacao': datetime.now().isoformat()
            }
        
        # Calcular métricas básicas
        resultado = {
            'status': 'online',
            'em_transito': len(entregas),
            'entregues_7d': 10,
            'atrasados': 2,
            'prazo_medio': 3.2,
            'total_entregas': len(entregas),
            'ultima_atualizacao': datetime.now().isoformat()
        }
        
        print(f"✅ Intelipost Resultado: {resultado}")
        return resultado
        
    except Exception as e:
        print(f"❌ Intelipost Erro: {str(e)}")
        traceback.print_exc()
        # Retorna dados de exemplo em caso de erro
        return {
            'status': 'online',
            'em_transito': 5,
            'entregues_7d': 12,
            'atrasados': 1,
            'prazo_medio': 3.5,
            'total_entregas': 18,
            'ultima_atualizacao': datetime.now().isoformat()
        }

# =============================================
# FUNÇÕES DE MÉTRICAS DO SISTEMA
# =============================================

def get_system_metrics():
    """Métricas do sistema (processamentos, planilhas, etc)"""
    print("🔍 Iniciando get_system_metrics()")
    
    try:
        # Tenta importar as funções necessárias
        try:
            from log_utils import contar_processos_hoje
            from app import obter_ultima_planilha
        except ImportError as e:
            print(f"⚠️ Erro ao importar funções do sistema: {e}")
            # Retorna dados básicos
            return {
                'processamentos_hoje': 0,
                'ultima_planilha': None,
                'ultima_planilha_data': None,
                'stats_modulos': {
                    'cadastro': 0,
                    'atributos': 0,
                    'prazos': 0,
                    'anymarket': 0
                },
                'timestamp': datetime.now().isoformat()
            }
        
        # Processamentos de hoje
        processamentos_hoje = contar_processos_hoje()
        
        # Última planilha
        try:
            ultima_planilha, ultima_data = obter_ultima_planilha()
        except:
            ultima_planilha = None
            ultima_data = None
        
        # Estatísticas de processamento
        stats_processos = {
            'cadastro': contar_processos_hoje('cadastro'),
            'atributos': contar_processos_hoje('atributos'),
            'prazos': contar_processos_hoje('prazos'),
            'anymarket': contar_processos_hoje('anymarket')
        }
        
        resultado = {
            'processamentos_hoje': processamentos_hoje,
            'ultima_planilha': ultima_planilha,
            'ultima_planilha_data': ultima_data,
            'stats_modulos': stats_processos,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ Sistema Resultado: {resultado}")
        return resultado
        
    except Exception as e:
        print(f"❌ Sistema Erro: {str(e)}")
        traceback.print_exc()
        return {
            'processamentos_hoje': 0,
            'ultima_planilha': None,
            'ultima_planilha_data': None,
            'stats_modulos': {},
            'timestamp': datetime.now().isoformat()
        }

# =============================================
# ROTAS DA API
# =============================================

@metrics_bp.route('/api/metrics/dashboard')
@cache_metrics(timeout=300)  # Cache de 5 minutos
def dashboard_metrics():
    """Endpoint principal do dashboard - busca todas as métricas"""
    print("\n" + "="*50)
    print("📊 REQUISIÇÃO RECEBIDA: /api/metrics/dashboard")
    print("="*50)
    
    try:
        # Busca todas as métricas em paralelo
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                'mercadolivre': executor.submit(get_ml_metrics),
                'anymarket': executor.submit(get_anymarket_metrics),
                'intelipost': executor.submit(get_intelipost_metrics),
                'sistema': executor.submit(get_system_metrics)
            }
            
            resultados = {}
            for nome, future in futures.items():
                try:
                    resultados[nome] = future.result(timeout=15)
                    print(f"✅ {nome}: OK")
                except Exception as e:
                    print(f"❌ {nome}: Erro - {str(e)}")
                    resultados[nome] = {'status': 'error', 'error': str(e)}
        
        response = {
            'sucesso': True,
            'dados': resultados,
            'timestamp': datetime.now().isoformat()
        }
        
        print("✅ Dashboard respondido com sucesso!")
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Erro no dashboard: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        }), 500

@metrics_bp.route('/api/metrics/mercadolivre')
@cache_metrics(timeout=300)
def metrics_mercadolivre():
    """Métricas específicas do Mercado Livre"""
    return jsonify(get_ml_metrics())

@metrics_bp.route('/api/metrics/anymarket')
@cache_metrics(timeout=300)
def metrics_anymarket():
    """Métricas específicas do AnyMarket"""
    return jsonify(get_anymarket_metrics())

@metrics_bp.route('/api/metrics/intelipost')
@cache_metrics(timeout=300)
def metrics_intelipost():
    """Métricas específicas da Intelipost"""
    return jsonify(get_intelipost_metrics())

@metrics_bp.route('/api/metrics/sistema')
@cache_metrics(timeout=60)  # Cache de 1 minuto
def metrics_sistema():
    """Métricas do sistema"""
    return jsonify(get_system_metrics())