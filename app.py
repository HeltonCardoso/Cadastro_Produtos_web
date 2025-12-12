from collections import defaultdict
from io import BytesIO
import sys
from pathlib import Path
import uuid
#from fastapi import responses
from flask import Flask, abort, current_app, json, make_response, render_template, request, send_file, send_from_directory, redirect, url_for, flash, jsonify
from gspread import service_account
import gspread
import requests
from models import Processo, db
from config import Config
import os
from datetime import datetime, timedelta
import pandas as pd
from werkzeug.utils import secure_filename
from processamento.cadastro_produto_web import executar_processamento
from processamento.extrair_atributos import extrair_atributos_processamento
from processamento.api_anymarket import obter_token_anymarket_seguro
from processamento.comparar_prazos import processar_comparacao
from processamento.google_sheets import ler_planilha_google
from token_manager_secure import ml_token_manager
from mercadolivre_api_secure import ml_api_secure
from utils.stats_utils import get_processing_stats, obter_dados_grafico_7dias
import logging
from logging.handlers import RotatingFileHandler
from log_utils import (registrar_processo,registrar_itens_processados,obter_historico_processos,contar_processos_hoje)
from processamento.api_anymarket import (consultar_api_anymarket, excluir_foto_anymarket, excluir_fotos_planilha_anymarket)
from google_sheets_utils import (carregar_configuracao_google_sheets, salvar_configuracao_google_sheets,listar_abas_google_sheets,testar_conexao_google_sheets)

sys.path.append(str(Path(__file__).parent))

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY
db.init_app(app)

handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

with app.app_context():
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    db.create_all()

def obter_ultima_planilha():
    try:
        upload_folder = app.config["UPLOAD_FOLDER"]
        
        if not os.path.exists(upload_folder):
            app.logger.warning(f"Pasta uploads não encontrada: {upload_folder}")
            return None, None

        planilhas = []
        for f in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, f)
            if os.path.isfile(file_path) and f.lower().endswith(('.xlsx', '.xls', '.csv')):
                planilhas.append((f, os.path.getmtime(file_path)))

        if not planilhas:
            return None, None

        # Ordena por data (mais recente primeiro)
        planilhas.sort(key=lambda x: x[1], reverse=True)
        ultima_planilha = planilhas[0][0]
        
        return ultima_planilha, datetime.fromtimestamp(planilhas[0][1]).strftime('%Y-%m-%d %H:%M:%S')
    
    except Exception as e:
        app.logger.error(f"Erro em obter_ultima_planilha: {str(e)}")
        return None, None
    
@app.route('/')
def home():
    try:
        stats = get_processing_stats()
        ultima_planilha, ultima_planilha_data = obter_ultima_planilha()
        
        # ========== MÉTRICAS ANYMARKET (ÚLTIMOS 30 DIAS) ==========
        anymarket_stats = obter_pedidos_anymarket_30_dias()
        
        # ========== ESTATÍSTICAS DO SISTEMA ==========
        from log_utils import obter_grafico_processos_7_dias
        grafico_processos = obter_grafico_processos_7_dias()
        
        return render_template(
            'home.html',
            active_page='home',
            total_processamentos=stats['total'],
            processos_sucesso=stats['sucessos_total'],
            processos_erro=stats['erros_total'],
            processamentos_hoje=stats['hoje'],
            hoje_sucesso=stats['sucessos_hoje'],
            hoje_erro=stats['erros_hoje'],
            ultima_execucao=stats['ultima'],
            ultima_planilha=ultima_planilha,
            ultima_planilha_data=ultima_planilha_data,
            total_itens_sucesso=stats['total_itens_sucesso'],
            total_itens_erro=stats['total_itens_erro'],
            
            # NOVAS VARIÁVEIS
            anymarket_stats=anymarket_stats,
            grafico_processos=grafico_processos,
            
            now=datetime.now()
        )
    except Exception as e:
        app.logger.error(f"Erro na rota home: {str(e)}")
        import traceback
        traceback.print_exc()
        return render_template('error.html'), 500


@app.route('/api/dashboard/atualizar-metricas')
def api_atualizar_metricas():
    """API para atualizar métricas do dashboard"""
    try:
        stats = get_processing_stats()
        
        # Métricas Mercado Livre
        ml_autenticado = ml_token_manager.is_authenticated()
        ml_metricas = {}
        if ml_autenticado:
            try:
                dados_ml = obter_dados_completos_perfil()
                ml_metricas = dados_ml.get('metricas', {})
            except:
                ml_metricas = {}
        
        # Métricas AnyMarket
        anymarket_stats = obter_estatisticas_anymarket_7_dias()
        
        return jsonify({
            'sucesso': True,
            'sistema': {
                'processamentos_hoje': stats['hoje'],
                'sucessos_hoje': stats['sucessos_hoje'],
                'erros_hoje': stats['erros_hoje'],
                'ultima_execucao': stats['ultima']
            },
            'mercadolivre': {
                'autenticado': ml_autenticado,
                'metricas': ml_metricas
            },
            'anymarket': anymarket_stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

        
@app.route('/api/mercadolivre/atualizar-manufacturing', methods=['POST'])
def atualizar_manufacturing():
    """Rota para atualizar manufacturing time"""
    try:
        data = request.get_json()
        mlb = data.get('mlb')
        dias = data.get('dias')
        atualizacoes = data.get('atualizacoes')  # Para múltiplos
        
        if atualizacoes:
            # Atualização em massa
            resultado = ml_api_secure.atualizar_multiplos_manufacturing(atualizacoes)
        elif mlb and dias:
            # Atualização única
            resultado = ml_api_secure.atualizar_manufacturing_time(mlb, dias)
        else:
            return jsonify({
                'sucesso': False,
                'erro': 'Parâmetros insuficientes. Forneça mlb/dias ou atualizacoes'
            })
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        })

@app.route('/api/mercadolivre/debug-mlb/<mlb>')
def debug_mlb(mlb):
    """Rota simples para debug de um MLB específico"""
    try:
        from mercadolivre_api_secure import ml_api_secure
        ml_api_secure.debug_json_completo(mlb)
        return jsonify({
            'sucesso': True,
            'mensagem': f'Debug do MLB {mlb} realizado - verifique o console do servidor'
        })
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        })

@app.route('/api/dashboard/metricas-gerais')
def api_metricas_gerais():
    """API para obter métricas gerais para dashboard"""
    try:
        stats = get_processing_stats()
        
        # Métricas Mercado Livre
        ml_autenticado = ml_token_manager.is_authenticated()
        ml_metricas = {}
        if ml_autenticado:
            try:
                dados_ml = obter_dados_completos_perfil()
                ml_metricas = dados_ml.get('metricas', {})
            except:
                ml_metricas = {}
        
        # Métricas AnyMarket
        anymarket_token_configurado = verificar_token_anymarket_configurado()
        anymarket_metricas = {}
        
        return jsonify({
            'sucesso': True,
            'sistema': {
                'processamentos_hoje': stats['hoje'],
                'sucessos_hoje': stats['sucessos_hoje'],
                'erros_hoje': stats['erros_hoje'],
                'ultima_execucao': stats['ultima']
            },
            'mercadolivre': {
                'autenticado': ml_autenticado,
                'metricas': ml_metricas
            },
            'anymarket': {
                'token_configurado': anymarket_token_configurado
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@app.route('/api/dashboard/atualizar-planilhas')
def api_atualizar_planilhas():
    """API para atualizar lista de planilhas"""
    try:
        ultima_planilha, ultima_planilha_data = obter_ultima_planilha()
        
        return jsonify({
            'sucesso': True,
            'ultima_planilha': ultima_planilha,
            'ultima_planilha_data': ultima_planilha_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500
     
@app.route('/pedidos-anymarket')  ####Esta rota apenas chama a função abaixo api_pedidos_anymarket
def pedidos_anymarket():
    """Página principal de pedidos do AnyMarket"""
    return render_template('pedidos_anymarket.html',
                            active_page='pedidos',
                            active_module='anymarket',
                            page_title='Pedidos - Anymarket'
                            )

@app.route('/api/anymarket/pedidos')
def api_pedidos_anymarket():
    """API para buscar pedidos do AnyMarket - CORREÇÃO DO FILTRO DE DATA"""
    try:
        # Obter token do header Authorization
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Token de autenticação não fornecido'}), 401
        
        token = auth_header.replace('Bearer ', '')
        
        # Parâmetros da requisição
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        status = request.args.get('status')
        marketplace = request.args.get('marketplace')
        data_inicio = request.args.get('createdAfter')  # ✅ Note: createAfter (sem 'd')
        data_fim = request.args.get('createdBefore')
        
        
        # ✅ VALIDAÇÃO DA PÁGINA
        if page < 1:
            page = 1
        
        sort_field = request.args.get('sort', 'createdAt')
        sort_direction = request.args.get('sortDirection', 'DESC')

        # Construir URL da API AnyMarket
        url = "https://api.anymarket.com.br/v2/orders"
        
        # ✅ CORREÇÃO: Usar offset em vez de page
        offset = (page - 1) * limit
        
        params = {
            'offset': offset,
            'limit': limit,
        }
        
        if sort_field and sort_direction:
            params['sort'] = sort_field
            params['sortDirection'] = sort_direction

        # Adicionar filtros APENAS se fornecidos
        if status and status.strip():
            params['status'] = status.strip()
            
        if marketplace and marketplace.strip():
            params['marketplace'] = marketplace.strip()
        
        # ✅ CORREÇÃO CRÍTICA: Processar datas INDEPENDENTEMENTE
        if data_inicio and data_inicio.strip():
            try:
                # Validar e formatar data início
                datetime.strptime(data_inicio, '%Y-%m-%d')
                params['createdAfter'] = f"{data_inicio}T00:00:00-03:00"
                print(f"✅ Filtro data início: {data_inicio} -> {params['createdAfter']}")
            except ValueError as e:
                print(f"⚠️ Data início em formato inválido: {data_inicio}, erro: {e}")
        else:
            print("ℹ️ Data início não fornecida")
        
        if data_fim and data_fim.strip():
            try:
                # Validar e formatar data fim
                datetime.strptime(data_fim, '%Y-%m-%d')
                params['createdBefore'] = f"{data_fim}T23:59:59-03:00"
                print(f"✅ Filtro data fim: {data_fim} -> {params['createdBefore']}")
            except ValueError as e:
                print(f"⚠️ Data fim em formato inválido: {data_fim}, erro: {e}")
        else:
            print("ℹ️ Data fim não fornecida")
        
        # Fazer requisição para a API AnyMarket
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'gumgaToken': token
        }
        
        print(f"🔍 SOLICITANDO PÁGINA {page} (offset: {offset}) para AnyMarket")
        print(f"📋 Parâmetros FINAIS: {params}")
        
        response = requests.get(url, params=params, headers=headers, timeout=60)
        
        print(f"📡 Resposta da API: {response.status_code}")
        
        if response.status_code != 200:
            error_detail = response.text
            print(f"❌ Erro {response.status_code}: {error_detail}")
            return jsonify({
                'success': False, 
                'error': f'Erro na API AnyMarket: {response.status_code}',
                'details': error_detail[:500] if error_detail else 'Sem detalhes'
            }), response.status_code
        
        data = response.json()
        
        # Processar resposta
        orders = data.get('content', [])
        pagination_data = data.get('page', {})
        
        # ✅ CORREÇÃO CRÍTICA: Calcular paginação corretamente
        total_elements = pagination_data.get('totalElements', 0)
        page_size = pagination_data.get('size', limit)
        
        # ✅ CÁLCULO CORRETO DA PAGINAÇÃO
        total_pages = max(1, (total_elements + page_size - 1) // page_size)
        current_page = page  # Usar a página solicitada
        
        print(f"📊 PAGINAÇÃO CALCULADA:")
        print(f"   - Total elementos: {total_elements}")
        print(f"   - Tamanho da página: {page_size}")
        print(f"   - Total de páginas: {total_pages}")
        print(f"   - Página atual: {current_page}")
        
        # ✅ CORREÇÃO: Calcular navegação baseado nos cálculos
        has_next = current_page < total_pages
        has_prev = current_page > 1
        
        pagination = {
            'currentPage': current_page,
            'totalPages': total_pages,
            'totalElements': total_elements,
            'hasNext': has_next,
            'hasPrev': has_prev,
            'pageSize': page_size
        }
        
        # Calcular estatísticas
        stats = {
            'total': len(orders),
            'pendentes': len([o for o in orders if o.get('status') == 'PENDING']),
            'valorTotal': sum(float(o.get('total', 0)) for o in orders),
            'totalGeral': total_elements
        }
        
        return jsonify({
            'success': True,
            'orders': orders,
            'stats': stats,
            'pagination': pagination,
            'filters': {
                'createdAfter': data_inicio or '',
                'createdBefore': data_fim or '',
                'status': status or '',
                'marketplace': marketplace or '',
                'sort': sort_field,
                'sortDirection': sort_direction
            },
            'debug': {
                'pagina_solicitada': page,
                'offset_calculado': offset,
                'total_pages_calculado': total_pages,
                'api_url': response.url,
                'ordenacao': f'{sort_field} {sort_direction}'
            }
        })
        
    except Exception as e:
        print(f"❌ Erro na API pedidos: {str(e)}")
        return jsonify({'success': False, 'error': f'Erro interno: {str(e)}'}), 500
 
# ========================================
# ROTAS MERCADO LIVRE (MLB)
# ========================================

@app.route('/consultar-mercado-livre')
def consultar_mercado_livre():
    """Página principal para consulta de MLBs"""
    # Obtém informações da conta atual
    accounts = ml_token_manager.get_all_accounts()
    current_account = None
    conta_atual_id = ml_token_manager.current_account_id
    
    if conta_atual_id and conta_atual_id in ml_token_manager.accounts:
        current_account = ml_token_manager.accounts[conta_atual_id]
    
    # Verifica se tem alguma conta autenticada
    esta_autenticado = False
    for account in accounts:
        if account.get('has_token'):
            esta_autenticado = True
            break
    
    return render_template(
        'consultar_mercado_livre.html',
        active_page='consultar_mercado_livre',
        active_module='mercadolivre',
        page_title='Consulta Mercado Livre',
        esta_autenticado=esta_autenticado,
        conta_atual=current_account,
        conta_atual_id=conta_atual_id,
        todas_contas=accounts
    )

@app.route('/api/mercadolivre/configurar', methods=['POST'])
def api_configurar_mercadolivre():
    """API para configurar Client ID e Secret"""
    try:
        data = request.get_json()
        client_id = data.get('client_id')
        client_secret = data.get('client_secret')
        
        if not client_id or not client_secret:
            return jsonify({'sucesso': False, 'erro': 'Client ID e Client Secret são obrigatórios'}), 400
        
        ml_token_manager.set_config(client_id, client_secret)
        
        return jsonify({
            'sucesso': True, 
            'mensagem': 'Configuração salva com sucesso!'
        })
            
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


@app.route('/api/mercadolivre/forcar-renovacao', methods=['POST'])
def api_forcar_renovacao():
    """Força a renovação do token"""
    try:
        token_data = ml_token_manager.load_tokens()
        if not token_data or not token_data.get('refresh_token'):
            return jsonify({'sucesso': False, 'erro': 'Nenhum refresh token disponível'}), 400
        
        print("🔄 Forçando renovação do token...")
        novo_token = ml_token_manager.refresh_token(token_data['refresh_token'])
        
        if novo_token:
            # Testa o novo token
            if ml_token_manager.testar_token_api(novo_token):
                return jsonify({
                    'sucesso': True, 
                    'mensagem': 'Token renovado com sucesso!'
                })
            else:
                return jsonify({
                    'sucesso': False, 
                    'erro': 'Token renovado mas não funciona na API'
                })
        else:
            return jsonify({
                'sucesso': False, 
                'erro': 'Falha na renovação do token. É necessário nova autenticação.'
            })
            
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500
    

@app.route('/api/mercadolivre/autenticar', methods=['POST'])
def api_autenticar_mercadolivre():
    """API para autenticar no Mercado Livre"""
    try:
        data = request.get_json()
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')
        
        if not access_token or not refresh_token:
            return jsonify({'sucesso': False, 'erro': 'Access token e refresh token são obrigatórios'}), 400
        
        # Salva os tokens
        token_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 21600  # 6 horas
        }
        
        if ml_token_manager.save_tokens(token_data):
            # Testa a conexão
            if ml_api_secure.testar_conexao():
                return jsonify({
                    'sucesso': True, 
                    'mensagem': 'Autenticação realizada com sucesso!'
                })
            else:
                return jsonify({
                    'sucesso': False, 
                    'erro': 'Tokens inválidos ou sem permissão'
                })
        else:
            return jsonify({
                'sucesso': False, 
                'erro': 'Erro ao salvar tokens'
            })
            
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@app.route('/api/mercadolivre/status')
def api_status_mercadolivre():
    """API para verificar status da autenticação"""
    try:
        esta_autenticado = ml_token_manager.is_authenticated()
        conexao_ativa = False
        
        if esta_autenticado:
            conexao_ativa = ml_api_secure.testar_conexao()
        
        return jsonify({
            'sucesso': True,
            'autenticado': esta_autenticado,
            'conexao_ativa': conexao_ativa
        })
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@app.route('/api/mercadolivre/buscar-mlb', methods=['POST'])
def api_buscar_mlb():
    """API para buscar anúncios por MLB"""
    try:
        if not ml_token_manager.is_authenticated():
            return jsonify({'sucesso': False, 'erro': 'Não autenticado no Mercado Livre'}), 401
        
        data = request.get_json()
        mlbs = data.get('mlbs', [])
        tipo_busca = data.get('tipo_busca', 'mlbs')
        
        if tipo_busca == 'mlbs' and not mlbs:
            return jsonify({'sucesso': False, 'erro': 'Nenhum MLB fornecido'}), 400
        
        # Limpar e validar MLBs
        mlbs_validos = []
        for mlb in mlbs:
            mlb_limpo = mlb.strip().upper()
            if mlb_limpo.startswith('MLB'):
                mlbs_validos.append(mlb_limpo)
            else:
                # Tentar adicionar MLB se não tiver
                if mlb_limpo.replace('MLB', '').isalnum():
                    mlb_formatado = f"MLB{mlb_limpo.replace('MLB', '')}"
                    mlbs_validos.append(mlb_formatado)
        
        if tipo_busca == 'mlbs' and not mlbs_validos:
            return jsonify({'sucesso': False, 'erro': 'Nenhum MLB válido encontrado'}), 400
        
        # Buscar dados
        if tipo_busca == 'mlbs':
            resultado = ml_api_secure.buscar_anuncios_mlbs(mlbs_validos)
        elif tipo_busca == 'meus_anuncios':
            resultado = ml_api_secure.buscar_meus_anuncios()
        else:
            return jsonify({'sucesso': False, 'erro': 'Tipo de busca não suportado'}), 400
        
        return jsonify(resultado)
        
    except Exception as e:
        print(f"❌ Erro ao buscar MLBs: {str(e)}")
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@app.route('/api/mercadolivre/analisar-envio-manufacturing', methods=['POST'])
def api_analisar_envio_manufacturing():
    """API para análise específica de envio e manufacturing time"""
    try:
        if not ml_token_manager.is_authenticated():
            return jsonify({'sucesso': False, 'erro': 'Não autenticado no Mercado Livre'}), 401
        
        data = request.get_json()
        mlbs = data.get('mlbs', [])
        tipo_busca = data.get('tipo_busca', 'mlbs')
        
        # Buscar dados
        if tipo_busca == 'mlbs':
            resultado_busca = ml_api_secure.buscar_anuncios_mlbs(mlbs)
        elif tipo_busca == 'meus_anuncios':
            resultado_busca = ml_api_secure.buscar_meus_anuncios()
        else:
            return jsonify({'sucesso': False, 'erro': 'Tipo de busca não suportado'}), 400
        
        if not resultado_busca['sucesso']:
            return jsonify(resultado_busca)
        
        resultados = resultado_busca['resultados']
        resultados_validos = [r for r in resultados if 'error' not in r]
        
        # Estatísticas
        total_me2 = sum(1 for r in resultados_validos if r.get('shipping_mode') == 'me2')
        total_me1 = sum(1 for r in resultados_validos if r.get('shipping_mode') == 'me1')
        com_manufacturing = sum(1 for r in resultados_validos if r.get('manufacturing_time') not in [0, '0', 'N/A', None, ''])
        
        return jsonify({
            'sucesso': True,
            'estatisticas': {
                'total_analisado': len(resultados_validos),
                'me2': total_me2,
                'me1': total_me1,
                'com_manufacturing': com_manufacturing,
                'sem_manufacturing': len(resultados_validos) - com_manufacturing
            },
            'resultados': resultados,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Erro na análise: {str(e)}")
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@app.route('/api/mercadolivre/desautenticar', methods=['POST'])
def api_desautenticar_mercadolivre():
    """API para remover autenticação"""
    try:
        if ml_token_manager.remove_tokens():
            return jsonify({
                'sucesso': True,
                'mensagem': 'Desautenticado com sucesso'
            })
        else:
            return jsonify({
                'sucesso': False,
                'erro': 'Erro ao remover tokens'
            })
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@app.route('/api/mercadolivre/configuracao')
def api_configuracao_mercadolivre():
    """API para obter configuração atual (sem dados sensíveis)"""
    try:
        configurado = ml_token_manager.client_id is not None and ml_token_manager.client_secret is not None
        
        return jsonify({
            'sucesso': True,
            'configurado': configurado
        })
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500
    

@app.route('/api/anymarket/pedidos/<int:order_id>')
def api_detalhes_pedido_anymarket(order_id):
    """API para buscar detalhes de um pedido específico"""
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Token de autenticação não fornecido'}), 401
        
        token = auth_header.replace('Bearer ', '')
        
        url = f"https://api.anymarket.com.br/v2/orders/{order_id}"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'gumgaToken': token
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            return jsonify({
                'success': False, 
                'error': f'Erro na API AnyMarket: {response.status_code}'
            }), response.status_code
        
        order_data = response.json()
        
        return jsonify({
            'success': True,
            'order': order_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/tokens/anymarket/obter')
def api_obter_token():
    """API para obter token do AnyMarket - VERSÃO TOLERANTE"""
    try:
        tokens_file = 'tokens_secure.json'
        
        # 🔹 CORREÇÃO: Se o arquivo não existe, retorna que não há token
        if not os.path.exists(tokens_file):
            return jsonify({
                'success': False, 
                'error': 'Token não configurado',
                'arquivo_existe': False
            }), 404
        
        with open(tokens_file, 'r', encoding='utf-8') as f:
            tokens = json.load(f)
        
        # Tenta estrutura nova primeiro
        token_data = tokens.get('anymarket')
        if token_data and token_data.get('token'):
            return jsonify({
                'success': True,
                'token': token_data['token'],
                'criado_em': token_data.get('criado_em'),
                'arquivo_existe': True
            })
        
        # Tenta estrutura antiga com IDs aleatórios
        for key, value in tokens.items():
            if isinstance(value, dict) and value.get('tipo') == 'anymarket' and value.get('token'):
                return jsonify({
                    'success': True,
                    'token': value['token'],
                    'criado_em': value.get('criado_em'),
                    'arquivo_existe': True,
                    'estrutura_antiga': True
                })
        
        return jsonify({
            'success': False, 
            'error': 'Token não encontrado',
            'arquivo_existe': True
        }), 404
        
    except json.JSONDecodeError:
        return jsonify({
            'success': False, 
            'error': 'Arquivo de tokens corrompido',
            'arquivo_existe': True
        }), 500
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': str(e),
            'arquivo_existe': os.path.exists('tokens_secure.json')
        }), 500

    
@app.route('/uploads/<filename>')
def baixar_arquivo(filename):
    try:
        # Decodifica caracteres especiais na URL
        from urllib.parse import unquote
        filename = unquote(filename)
        
        upload_folder = app.config['UPLOAD_FOLDER']
        safe_filename = secure_filename(os.path.basename(filename))
        file_path = os.path.join(upload_folder, safe_filename)
        
        if not os.path.exists(file_path):
            # Tenta encontrar o arquivo sem sanitização (para compatibilidade)
            for f in os.listdir(upload_folder):
                if f.startswith(os.path.splitext(safe_filename)[0]):
                    file_path = os.path.join(upload_folder, f)
                    break
            
            if not os.path.exists(file_path):
                abort(404)
        
        return send_from_directory(
            upload_folder,
            os.path.basename(file_path),
            as_attachment=True,
            download_name=safe_filename  # Força o nome no download
        )
        
    except Exception as e:
        app.logger.error(f"Erro ao baixar {filename}: {str(e)}")
        abort(500)

@app.route('/configuracoes/tokens')
def configurar_tokens():
    config = carregar_configuracao_google_sheets()
    
    # Verifica se tem token do AnyMarket configurado
    token_configurado = verificar_token_anymarket_configurado()
    
    return render_template(
        "config_tokens.html",
        active_page='configuracao',
        config=config,
        token_configurado=token_configurado,
        page_title='Configuração de Tokens'
    )

def verificar_token_anymarket_configurado():
    """Verifica se o token do AnyMarket está configurado (sem retornar o token)"""
    try:
        tokens_file = 'tokens_secure.json'
        if not os.path.exists(tokens_file):
            return False
        
        with open(tokens_file, 'r') as f:
            tokens = json.load(f)
        
        return 'anymarket' in tokens and 'token' in tokens['anymarket']
        
    except Exception:
        return False
    
@app.route('/api/anymarket/testar-token', methods=['POST'])
def testar_token_anymarket():
    """API para testar o token do AnyMarket - VERSÃO ROBUSTA"""
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Token de autenticação não fornecido'}), 401
        
        token = auth_header.replace('Bearer ', '')
        
        # 🔹 MÚLTIPLAS TENTATIVAS COM DIFERENTES PARÂMETROS
        test_cases = [
            # Caso 1: Com datas específicas e limit=5
            {
                'params': {
                    'page': 1,
                    'limit': 5,
                    'createdAt.start': '2024-01-01T00:00:00-03:00',
                    'createdAt.end': '2024-12-31T23:59:59-03:00'
                },
                'description': 'Com datas fixas'
            },
            # Caso 2: Apenas paginação básica
            {
                'params': {
                    'page': 1,
                    'limit': 5
                },
                'description': 'Paginação básica'
            },
            # Caso 3: Sem parâmetros (API usa defaults)
            {
                'params': {},
                'description': 'Sem parâmetros'
            }
        ]
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'gumgaToken': token
        }
        
        url = "https://api.anymarket.com.br/v2/orders"
        
        for i, test_case in enumerate(test_cases):
            try:
                print(f"🧪 Teste {i+1}: {test_case['description']}")
                response = requests.get(url, params=test_case['params'], headers=headers, timeout=10)
                
                if 200 <= response.status_code < 300:
                    return jsonify({
                        'success': True, 
                        'message': f'Token válido! Conexão estabelecida com a API AnyMarket',
                        'status_code': response.status_code,
                        'test_used': test_case['description']
                    })
                
            except requests.exceptions.RequestException:
                continue  # Tenta o próximo caso se houver erro de conexão
        
        # Se nenhum caso funcionou, retorna o último erro
        return jsonify({
            'success': False, 
            'error': f'Não foi possível conectar à API AnyMarket. Status: {response.status_code}',
            'status_code': response.status_code
        }), response.status_code
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Erro ao testar token: {str(e)}'
        }), 500
        

@app.route("/consultar-anymarket", methods=["GET", "POST"])
def consultar_anymarket():
    resultado = None
    acao = None
    
    if request.method == "POST":
        acao = request.form.get('action', 'consultar')
        
        if acao == 'consultar':
            try:
                product_id = request.form.get('product_id', '').strip()
                api_token = request.form.get('api_token', '').strip()
                
                if not product_id:
                    flash("ID do produto é obrigatório", "danger")
                    return redirect(url_for('consultar_anymarket'))
                
                # ✅ Se não forneceu token, usa o seguro
                if not api_token:
                    from processamento.api_anymarket import obter_token_anymarket_seguro
                    api_token = obter_token_anymarket_seguro()
                
                inicio = datetime.now()
                resultado = consultar_api_anymarket(product_id, api_token)
                tempo_segundos = (datetime.now() - inicio).total_seconds()
                
                registrar_processo(
                    modulo="anymarket",
                    qtd_itens=resultado.get('quantidade_fotos', 0),
                    tempo_execucao=tempo_segundos,
                    status="sucesso" if resultado.get('sucesso') else "erro",
                    erro_mensagem=resultado.get('erro') if not resultado.get('sucesso') else None
                )
                
                if resultado.get('sucesso'):
                    flash(f"Consulta realizada com sucesso! {resultado.get('quantidade_fotos', 0)} fotos encontradas.", "success")
                else:
                    flash(f"Erro na consulta: {resultado.get('erro', 'Erro desconhecido')}", "danger")
                    
            except Exception as e:
                flash(f"Erro ao consultar API: {str(e)}", "danger")
        
        elif acao == 'excluir_lote':
            try:
                if 'planilha' not in request.files:
                    flash("Nenhum arquivo enviado", "danger")
                    return redirect(url_for('consultar_anymarket'))
                
                planilha = request.files['planilha']
                if planilha.filename == '':
                    flash("Nenhum arquivo selecionado", "danger")
                    return redirect(url_for('consultar_anymarket'))
                
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                nome_arquivo = secure_filename(planilha.filename)
                caminho_planilha = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
                planilha.save(caminho_planilha)
                
                inicio = datetime.now()
                resultado = excluir_fotos_planilha_anymarket(caminho_planilha)
                tempo_segundos = (datetime.now() - inicio).total_seconds()
                
                registrar_processo(
                    modulo="anymarket_exclusao",
                    qtd_itens=resultado.get('total_processado', 0),
                    tempo_execucao=tempo_segundos,
                    status="sucesso" if resultado.get('sucesso') else "erro",
                    erro_mensagem=resultado.get('erro') if not resultado.get('sucesso') else None
                )
                
                if resultado.get('sucesso'):
                    flash(f"Exclusão em lote concluída! {resultado.get('total_sucesso', 0)} de {resultado.get('total_processado', 0)} fotos excluídas.", "success")
                else:
                    flash(f"Erro na exclusão em lote: {resultado.get('erro', 'Erro desconhecido')}", "danger")
                    
            except Exception as e:
                flash(f"Erro ao processar planilha: {str(e)}", "danger")
    
    return render_template(
        "consultar_anymarket.html",
        active_page='consultar_anymarket',
        active_module='anymarket',
        resultado=resultado,
        acao=acao,
        historico_processos=obter_historico_processos("anymarket"),
        processos_hoje=contar_processos_hoje("anymarket"),
        stats=get_processing_stats("anymarket"),
        page_title='Consulta Fotos'
    )

@app.route('/api/tokens/anymarket/obter', methods=['GET'])
def obter_token_anymarket():
    """Obtém token do AnyMarket do arquivo seguro"""
    try:
        tokens_file = 'tokens_secure.json'
        if not os.path.exists(tokens_file):
            return jsonify({'success': False, 'error': 'Token não configurado'}), 404
        
        with open(tokens_file, 'r', encoding='utf-8') as f:
            tokens = json.load(f)
        
        token_data = tokens.get('anymarket')
        if not token_data or not token_data.get('token'):
            return jsonify({'success': False, 'error': 'Token não encontrado'}), 404
        
        return jsonify({
            'success': True,
            'token': token_data['token'],
            'criado_em': token_data.get('criado_em')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tokens/anymarket/salvar', methods=['POST'])
def salvar_token_anymarket():
    """Salva token do AnyMarket no arquivo seguro - VERSÃO QUE CRIA ARQUIVO"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'success': False, 'error': 'Token não fornecido'}), 400
        
        tokens_file = 'tokens_secure.json'
        tokens = {}
        
        # 🔹 CORREÇÃO: Se o arquivo existe, carrega. Se não, cria estrutura vazia.
        if os.path.exists(tokens_file):
            try:
                with open(tokens_file, 'r', encoding='utf-8') as f:
                    tokens = json.load(f)
            except json.JSONDecodeError:
                # Se o arquivo estiver corrompido, recria
                tokens = {}
        else:
            # Arquivo não existe - cria estrutura vazia
            tokens = {}
            print("📁 Arquivo tokens_secure.json não encontrado - criando novo...")
        
        # Garante que a estrutura tenha o objeto anymarket
        tokens['anymarket'] = {
            'token': token,
            'criado_em': datetime.now().isoformat(),
            'ultimo_uso': datetime.now().isoformat()
        }
        
        # 🔹 CORREÇÃO: Garante que o diretório existe
        os.makedirs(os.path.dirname(tokens_file) or '.', exist_ok=True)
        
        # Salva o arquivo
        with open(tokens_file, 'w', encoding='utf-8') as f:
            json.dump(tokens, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Token salvo com segurança em {tokens_file}")
        
        return jsonify({
            'success': True, 
            'message': 'Token salvo com segurança',
            'arquivo_criado': not os.path.exists(tokens_file)  # Indica se foi criado agora
        })
        
    except Exception as e:
        print(f"❌ Erro ao salvar token: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tokens/anymarket/remover', methods=['POST'])
def remover_token_anymarket():
    """Remove token do AnyMarket"""
    try:
        tokens_file = 'tokens_secure.json'
        
        if os.path.exists(tokens_file):
            with open(tokens_file, 'r', encoding='utf-8') as f:
                tokens = json.load(f)
            
            if 'anymarket' in tokens:
                del tokens['anymarket']
                
                with open(tokens_file, 'w', encoding='utf-8') as f:
                    json.dump(tokens, f, indent=2, ensure_ascii=False)
        
        return jsonify({'success': True, 'message': 'Token removido'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route("/excluir-foto-anymarket", methods=["POST"])
def excluir_foto_anymarket_route():
    """API para exclusão individual de foto"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        photo_id = data.get('photo_id')
        
        if not product_id or not photo_id:
            return jsonify({'sucesso': False, 'erro': 'ID do produto e da foto são obrigatórios'}), 400
        
        resultado = excluir_foto_anymarket(product_id, photo_id)
        
        registrar_processo(
            modulo="anymarket_exclusao",
            qtd_itens=1,
            tempo_execucao=0,
            status="sucesso" if resultado.get('sucesso') else "erro",
            erro_mensagem=resultado.get('erro') if not resultado.get('sucesso') else None
        )
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@app.route("/excluir-fotos-lote", methods=["POST"])
def excluir_fotos_lote_route():
    """API para exclusão em lote de fotos"""
    try:
        data = request.get_json()
        fotos = data.get('fotos', [])
        
        if not fotos:
            return jsonify({'sucesso': False, 'erro': 'Nenhuma foto selecionada'}), 400
        
        total_sucesso = 0
        total_erro = 0
        resultados = []
        
        for foto in fotos:
            product_id = foto.get('product_id')
            photo_id = foto.get('photo_id')
            
            if product_id and photo_id:
                resultado = excluir_foto_anymarket(product_id, photo_id)
                resultados.append(resultado)
                
                if resultado.get('sucesso'):
                    total_sucesso += 1
                else:
                    total_erro += 1
        
        registrar_processo(
            modulo="anymarket_exclusao",
            qtd_itens=len(fotos),
            tempo_execucao=0,
            status="sucesso" if total_erro == 0 else "parcial",
            erro_mensagem=f"{total_erro} erro(s)" if total_erro > 0 else None
        )
        
        return jsonify({
            'sucesso': True,
            'total_processado': len(fotos),
            'total_sucesso': total_sucesso,
            'total_erro': total_erro,
            'resultados': resultados
        })
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500
   

@app.route("/preencher-planilha", methods=["GET", "POST"])
def preencher_planilha():
    nome_arquivo_saida = None
    config = carregar_configuracao_google_sheets()
    abas = []
    sheet_id_input = request.form.get('sheet_id', config.get('sheet_id', ''))
    aba_selecionada = request.form.get('aba_nome', '')
    preview_data = None

    # Aba ativa (upload ou google)
    aba_ativa = request.args.get('aba', 'upload')

    if request.method == "POST":
        action_type = request.form.get('action_type', '')

        try:
            # ====================================
            # 🔹 LISTAR ABAS DO GOOGLE SHEETS
            # ====================================
            if action_type == "listar_abas":
                sheet_id = request.form.get('sheet_id', '').strip()
                if not sheet_id:
                    flash("Informe o ID da planilha Google", "danger")
                    return redirect(url_for("preencher_planilha", aba="google"))

                abas = listar_abas_google_sheets(sheet_id)
                config = carregar_configuracao_google_sheets()

                return render_template(
                    "preencher_planilha.html",
                    historico_processos=obter_historico_processos("cadastro"),
                    processos_hoje=contar_processos_hoje("cadastro"),
                    stats=get_processing_stats("cadastro"),
                    nome_arquivo_saida=None,
                    config=config,
                    abas=abas,
                    sheet_id_input=sheet_id,
                    aba_selecionada=None,
                    aba_ativa="google",
                    page_title='Cadastro Produto'
                )

            # ====================================
            # 🔹 PREVIEW DA ABA
            # ====================================
            elif action_type == "preview_aba":
                sheet_id = request.form.get('sheet_id', '').strip()
                aba_nome = request.form.get('aba_nome', '').strip()

                if not sheet_id or not aba_nome:
                    flash("ID da planilha e aba são obrigatórios para preview", "danger")
                    return redirect(url_for("preencher_planilha", aba="google"))

                df_preview = ler_planilha_google(sheet_id, aba_nome)
                preview_data = {
                    "total_linhas": len(df_preview),
                    "total_colunas": len(df_preview.columns),
                    "colunas": df_preview.columns.tolist(),
                    "linhas": df_preview.head(10).to_dict(orient="records")
                }

                return render_template(
                    "preencher_planilha.html",
                    historico_processos=obter_historico_processos("cadastro"),
                    processos_hoje=contar_processos_hoje("cadastro"),
                    stats=get_processing_stats("cadastro"),
                    nome_arquivo_saida=None,
                    config=config,
                    abas=listar_abas_google_sheets(sheet_id),
                    sheet_id_input=sheet_id,
                    aba_selecionada=aba_nome,
                    aba_ativa="google",
                    preview_data=preview_data,
                    page_title='Cadastro Produto'
                )

            # ====================================
            # 🔹 PROCESSAR (GOOGLE SHEETS) - AGORA SEM ARQUIVO DESTINO
            # ====================================
            elif action_type == "conectar_google":
                sheet_id = request.form.get('sheet_id', '').strip()
                aba_nome = request.form.get('aba_nome', '').strip()

                if not sheet_id or not aba_nome:
                    flash("ID da planilha e aba são obrigatórios", "danger")
                    return redirect(url_for("preencher_planilha", aba="google"))

                salvar_configuracao_google_sheets(sheet_id, aba_nome)
                config = carregar_configuracao_google_sheets()

                # 🔹 AGORA USA O MODELO FIXO - NÃO PRECISA DE UPLOAD
                # Processa usando apenas o Google Sheets como origem
                arquivo_saida, qtd_produtos, tempo_segundos, produtos_processados = executar_processamento(
                    {"sheet_id": sheet_id, "aba": aba_nome}
                    # 🔹 Não passa planilha_destino - usa o modelo fixo
                )

                nome_arquivo_saida = os.path.basename(arquivo_saida)

                registrar_processo(
                    modulo="cadastro",
                    qtd_itens=qtd_produtos,
                    tempo_execucao=tempo_segundos,
                    status="sucesso"
                )
                registrar_itens_processados("cadastro", produtos_processados)

                flash("Cadastro concluído com sucesso a partir do Google Sheets!", "success")
                aba_ativa = "google"

            # ====================================
            # 🔹 PROCESSAR (UPLOAD LOCAL) - AGORA APENAS ARQUIVO ORIGEM
            # ====================================
            elif 'arquivo_origem' in request.files:
                origem = request.files["arquivo_origem"]

                if origem.filename == '':
                    flash("Nenhum arquivo de origem selecionado", "danger")
                    registrar_processo(
                        modulo="cadastro",
                        qtd_itens=0,
                        tempo_execucao=0,
                        status="erro",
                        erro_mensagem="Nenhum arquivo de origem selecionado"
                    )
                    return redirect(url_for("preencher_planilha", aba="upload"))

                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

                nome_origem = secure_filename(origem.filename)
                caminho_origem = os.path.join(app.config['UPLOAD_FOLDER'], nome_origem)
                origem.save(caminho_origem)

                # 🔹 AGORA USA O MODELO FIXO - NÃO PRECISA DE ARQUIVO DESTINO
                arquivo_saida, qtd_produtos, tempo_segundos, produtos_processados = executar_processamento(
                    caminho_origem
                    # 🔹 Não passa planilha_destino - usa o modelo fixo
                )

                nome_arquivo_saida = os.path.basename(arquivo_saida)

                registrar_processo(
                    modulo="cadastro",
                    qtd_itens=qtd_produtos,
                    tempo_execucao=tempo_segundos,
                    status="sucesso"
                )
                registrar_itens_processados("cadastro", produtos_processados)

                flash("Planilha preenchida com sucesso usando modelo fixo!", "success")
                aba_ativa = "upload"

        except Exception as e:
            erro_msg = str(e)
            if "faltando as seguintes colunas" in erro_msg:
                colunas_faltando = erro_msg.split(":")[1].strip()
                erro_msg = f"Planilha fora do padrão. Colunas faltantes: {colunas_faltando}"

            registrar_processo(
                modulo="cadastro",
                qtd_itens=0,
                tempo_execucao=0,
                status="erro",
                erro_mensagem=erro_msg
            )
            flash(f"Erro: {erro_msg}", "danger")
            return redirect(url_for("preencher_planilha", aba=aba_ativa))

    return render_template(
        "preencher_planilha.html",
        active_page='preencher_planilha',
        active_module='cadastro',
        historico_processos=obter_historico_processos("cadastro"),
        processos_hoje=contar_processos_hoje("cadastro"),
        stats=get_processing_stats("cadastro"),
        nome_arquivo_saida=nome_arquivo_saida,
        config=config,
        abas=abas,
        sheet_id_input=sheet_id_input,
        aba_selecionada=aba_selecionada,
        aba_ativa=aba_ativa,
        preview_data=preview_data,
        page_title='Cadastro Produto'
    )

@app.route("/extrair-atributos", methods=["GET", "POST"])
def extrair_atributos():
    nome_arquivo_saida = None
    config = carregar_configuracao_google_sheets()
    abas = []
    preview_data = None
    sheet_id_input = request.form.get('sheet_id', config.get('sheet_id', ''))
    aba_selecionada = request.form.get('aba_nome', '')
    
    # Verifica se deve manter a aba Google ativa
    aba_ativa = request.args.get('aba', 'upload')  # 'upload' ou 'google'
    
    try:
        if request.method == "POST":
            action_type = request.form.get('action_type', '')
            
            # Se for para listar abas - USA FUNÇÃO COMPATÍVEL
            if action_type == 'listar_abas':
                sheet_id = request.form.get('sheet_id', '').strip()
                if sheet_id:
                    try:
                        # CORREÇÃO: Usa a função original para compatibilidade
                        from google_sheets_utils import listar_abas_google_sheets
                        abas = listar_abas_google_sheets(sheet_id)
                        flash(f"{len(abas)} abas encontradas", "success")
                        sheet_id_input = sheet_id
                        aba_ativa = 'google'  # Mantém na aba Google
                    except Exception as e:
                        flash(f"Erro ao listar abas: {str(e)}", "danger")
                else:
                    flash("Informe o ID da planilha primeiro", "warning")
            
            # Se for para fazer preview de uma aba
            elif action_type == 'preview_aba':
                sheet_id = request.form.get('sheet_id', '').strip()
                aba_nome = request.form.get('aba_nome', '').strip()
                if sheet_id and aba_nome:
                    try:
                        from google_sheets_utils import obter_dados_aba
                        preview_data = obter_dados_aba(sheet_id, aba_nome)
                        flash(f"Preview da aba '{aba_nome}' carregado", "success")
                        sheet_id_input = sheet_id
                        aba_selecionada = aba_nome
                        aba_ativa = 'google'  # Mantém na aba Google
                    except Exception as e:
                        flash(f"Erro ao carregar preview: {str(e)}", "danger")
                else:
                    flash("Selecione uma aba para visualizar", "warning")
            
            # Se for para fazer preview de uma aba
            elif action_type == 'preview_aba':
                sheet_id = request.form.get('sheet_id', '').strip()
                aba_nome = request.form.get('aba_nome', '').strip()
                if sheet_id and aba_nome:
                    try:
                        from google_sheets_utils import obter_dados_aba
                        preview_data = obter_dados_aba(sheet_id, aba_nome)
                        flash(f"Preview da aba '{aba_nome}' carregado", "success")
                        sheet_id_input = sheet_id
                        aba_selecionada = aba_nome
                        aba_ativa = 'google'  # Mantém na aba Google
                    except Exception as e:
                        flash(f"Erro ao carregar preview: {str(e)}", "danger")
                else:
                    flash("Selecione uma aba para visualizar", "warning")
            
            # Se for para processar com Google Sheets
            elif action_type == 'conectar_google':
                sheet_id = request.form.get('sheet_id', '').strip()
                aba_nome = request.form.get('aba_nome', '').strip()
                
                if not sheet_id or not aba_nome:
                    flash("ID da planilha e aba são obrigatórios", "danger")
                    return redirect(url_for("extrair_atributos", aba='google'))
                
                # Salva a configuração completa
                salvar_configuracao_google_sheets(sheet_id, aba_nome)
                config = carregar_configuracao_google_sheets()
                
                inicio = datetime.now()
                caminho_saida, qtd_itens, tempo_segundos, _ = extrair_atributos_processamento({
                    'sheet_id': sheet_id,
                    'aba': aba_nome
                })
                
                nome_arquivo_saida = os.path.basename(caminho_saida)
                
                registrar_processo(
                    modulo="atributos",
                    qtd_itens=qtd_itens,
                    tempo_execucao=tempo_segundos,
                    status="sucesso"
                )
                
                flash("Extração do Google Sheets concluída com sucesso!", "success")
                aba_ativa = 'google'  # Mantém na aba Google
            
            # Modo upload de arquivo (apenas se for submit do formulário de upload)
            elif 'arquivo' in request.files:
                arquivo = request.files["arquivo"]
                if arquivo.filename == '':
                    flash("Nenhum arquivo selecionado", "danger")
                    registrar_processo(
                        modulo="atributos",
                        qtd_itens=0,
                        tempo_execucao=0,
                        status="erro",
                        erro_mensagem="Nenhum arquivo selecionado"
                    )
                    return redirect(url_for("extrair_atributos", aba='upload'))
                
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                nome_arquivo = secure_filename(arquivo.filename)
                caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
                arquivo.save(caminho_arquivo)

                caminho_saida, qtd_itens, tempo_segundos, _ = extrair_atributos_processamento(
                    caminho_arquivo
                )
                
                nome_arquivo_saida = os.path.basename(caminho_saida)
                
                registrar_processo(
                    modulo="atributos",
                    qtd_itens=qtd_itens,
                    tempo_execucao=tempo_segundos,
                    status="sucesso"
                )
                
                flash("Extração concluída com sucesso!", "success")
                aba_ativa = 'upload'  # Mantém na aba Upload
    
    except Exception as e:
        erro_msg = str(e)
        if "faltando as seguintes colunas" in erro_msg:
            colunas_faltando = erro_msg.split(":")[1].strip()
            erro_msg = f"Planilha fora do padrão. Colunas faltantes: {colunas_faltando}"
        
        registrar_processo(
            modulo="atributos",
            qtd_itens=0,
            tempo_execucao=0,
            status="erro",
            erro_mensagem=erro_msg
        )
        flash(f"Erro: {erro_msg}", "danger")
    
    return render_template(
        "extrair_atributos.html",
        active_page='extrair_atributos',
        active_module='cadastro',
        historico_processos=obter_historico_processos("atributos"),
        processos_hoje=contar_processos_hoje("atributos"),
        stats=get_processing_stats("atributos"),
        nome_arquivo_saida=nome_arquivo_saida,
        config=config,
        abas=abas,
        preview_data=preview_data,
        sheet_id_input=sheet_id_input,
        aba_selecionada=aba_selecionada,
        aba_ativa=aba_ativa,
        page_title='Extração de Atributos'
    )

def obter_dados_aba(sheet_id, aba_nome, limite_linhas=None):
    """Obtém TODOS os dados de uma aba específica para preview"""
    try:
        # Encontra o caminho correto para o credentials.json
        current_dir = Path(__file__).parent
        credentials_path = current_dir / "credentials.json"
        
        if not credentials_path.exists():
            raise FileNotFoundError("Arquivo credentials.json não encontrado")
        
        credentials = service_account.Credentials.from_service_account_file(
            str(credentials_path),
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        
        gc = gspread.authorize(credentials)
        planilha = gc.open_by_key(sheet_id)
        worksheet = planilha.worksheet(aba_nome)
        
        # Obtém TODAS as linhas (sem limite)
        todas_linhas = worksheet.get_all_values()
        
        if not todas_linhas:
            return {
                'colunas': [],
                'dados': [],
                'total_linhas': 0,
                'total_colunas': 0
            }
        
        # A primeira linha são os cabeçalhos
        colunas = todas_linhas[0] if todas_linhas else []
        
        # Converte TODAS as linhas seguintes para dicionários
        dados = []
        for i, linha in enumerate(todas_linhas[1:], 1):
            linha_dict = {}
            for j, valor in enumerate(linha):
                nome_coluna = colunas[j] if j < len(colunas) else f"Coluna_{j+1}"
                linha_dict[nome_coluna] = valor
            dados.append(linha_dict)
        
        return {
            'colunas': colunas,
            'dados': dados,  # TODAS as linhas
            'total_linhas': worksheet.row_count,
            'total_colunas': worksheet.col_count
        }
        
    except Exception as e:
        if current_app:
            current_app.logger.error(f"Erro ao obter dados da aba: {str(e)}")
        else:
            print(f"Erro ao obter dados da aba: {str(e)}")
        raise Exception(f"Erro ao obter dados da aba: {str(e)}")

@app.route("/api/abas-google-sheets")
def api_abas_google_sheets():
    """API para listar abas de uma planilha - AGORA APENAS VISÍVEIS"""
    sheet_id = request.args.get('sheet_id')
    if not sheet_id:
        return jsonify({'error': 'sheet_id é obrigatório'}), 400
    
    try:
        # ALTERAÇÃO: Usa a nova função para abas visíveis
        from google_sheets_utils import listar_abas_visiveis_google_sheets
        abas = listar_abas_visiveis_google_sheets(sheet_id)
        return jsonify({'success': True, 'abas': abas})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route("/api/abas-google-sheets-visiveis")
def api_abas_google_sheets_visiveis():
    """API para listar apenas abas visíveis de uma planilha"""
    sheet_id = request.args.get('sheet_id')
    if not sheet_id:
        return jsonify({'error': 'sheet_id é obrigatório'}), 400
    
    try:
        from google_sheets_utils import listar_abas_visiveis_google_sheets
        abas = listar_abas_visiveis_google_sheets(sheet_id)
        return jsonify({'success': True, 'abas': abas})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/preview-aba")
def api_preview_aba():
    """API para preview de uma aba"""
    sheet_id = request.args.get('sheet_id')
    aba_nome = request.args.get('aba_nome')
    
    if not sheet_id or not aba_nome:
        return jsonify({'error': 'sheet_id e aba_nome são obrigatórios'}), 400
    
    try:
        from google_sheets_utils import obter_dados_aba
        preview_data = obter_dados_aba(sheet_id, aba_nome)
        return jsonify({'success': True, 'data': preview_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route("/comparar-prazos", methods=["POST"])
def comparar_prazos():
    try:
        if ('arquivo_erp' not in request.files) or ('arquivo_marketplace' not in request.files):
            registrar_processo(
                modulo="prazos",
                qtd_itens=0,
                tempo_execucao=0,
                status="erro",
                erro_mensagem="Nenhum arquivo enviado"
            )
            return jsonify({'sucesso': False, 'erro': "Nenhum arquivo enviado"}), 400

        arquivo_erp = request.files['arquivo_erp']
        arquivo_marketplace = request.files['arquivo_marketplace']

        if arquivo_erp.filename == '' or arquivo_marketplace.filename == '':
            registrar_processo(
                modulo="prazos",
                qtd_itens=0,
                tempo_execucao=0,
                status="erro",
                erro_mensagem="Nenhum arquivo selecionado"
            )
            return jsonify({'sucesso': False, 'erro': "Nenhum arquivo selecionado"}), 400

        inicio = datetime.now()
        resultado = processar_comparacao(arquivo_erp, arquivo_marketplace, app.config['UPLOAD_FOLDER'])
        
        if not resultado.get('sucesso', False):
            registrar_processo(
                modulo="prazos",
                qtd_itens=0,
                tempo_execucao=0,
                status="erro",
                erro_mensagem=resultado.get('erro', 'Erro desconhecido')
            )
            raise Exception(resultado.get('erro', 'Erro desconhecido no processamento'))

        # Registrar processo com sucesso
        tempo_segundos = (datetime.now() - inicio).total_seconds()
        registrar_processo(
            modulo="prazos",
            qtd_itens=resultado['total_itens'],
            tempo_execucao=tempo_segundos,
            status="sucesso"
        )

        return jsonify(resultado)

    except Exception as e:
        registrar_processo(
            modulo="prazos",
            qtd_itens=0,
            tempo_execucao=0,
            status="erro",
            erro_mensagem=str(e)
        )
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@app.route("/comparar-prazos", methods=["GET"])
def mostrar_tela_comparacao():
    return render_template(
        "comparar_prazos.html",
        active_page='comparar-prazos',
        active_module='cadastro',
        historico_processos=obter_historico_processos("prazos"),
        processos_hoje=contar_processos_hoje("prazos"),
        stats=get_processing_stats("prazos"),
        page_title='Comparação de Prazos'  # Agora aceita o parâmetro
    )

def contar_processos_hoje(modulo="cadastro"):
    """Função local necessária para o template (não remova!)."""
    from log_utils import contar_processos_hoje as contar_logs  # Importa a função original
    return contar_logs(modulo)  # Delega para a função de log_utils.py

@app.context_processor
def inject_stats():
    return {
        'count_processos_hoje': contar_processos_hoje(),
        'now': datetime.now()
    }

def format_time(seconds):
    """Formata segundos em minutos e segundos"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}m {seconds}s"

@app.errorhandler(500)
def handle_500_error(e):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error',
        'details': str(e) if app.debug else None
    }), 500

@app.route("/configuracoes/google-sheets", methods=["GET", "POST"])
def configurar_google_sheets():
    """Tela de configuração do Google Sheets - Agora mostra apenas abas visíveis"""
    config = carregar_configuracao_google_sheets()
    abas = []
    mensagem = None
    tipo_mensagem = "info"
    erro = None
    
    try:
        if request.method == "POST":
            sheet_id = request.form.get('sheet_id', '').strip()
            acao = request.form.get('acao')
            
            if acao == 'testar':
                sucesso, msg = testar_conexao_google_sheets(sheet_id)
                mensagem = msg
                tipo_mensagem = "success" if sucesso else "danger"
                
            elif acao == 'listar_abas':
                if sheet_id:
                    # ALTERAÇÃO: Usa a nova função para abas visíveis
                    from google_sheets_utils import listar_abas_visiveis_google_sheets
                    abas = listar_abas_visiveis_google_sheets(sheet_id)
                    mensagem = f"{len(abas)} abas visíveis encontradas"
                    tipo_mensagem = "success"
                else:
                    mensagem = "Informe o ID da planilha primeiro"
                    tipo_mensagem = "warning"
                
            elif acao == 'salvar':
                if not sheet_id:
                    mensagem = "ID da planilha é obrigatório"
                    tipo_mensagem = "danger"
                else:
                    # Salva apenas o ID, a aba será selecionada na tela de extração
                    if salvar_configuracao_google_sheets(sheet_id, ''):
                        config = carregar_configuracao_google_sheets()
                        mensagem = "ID da planilha salvo com sucesso! Selecione a aba na tela de extração."
                        tipo_mensagem = "success"
                    else:
                        mensagem = "Erro ao salvar configuração"
                        tipo_mensagem = "danger"
    
    except Exception as e:
        erro = str(e)
        mensagem = f"Erro: {erro}"
        tipo_mensagem = "danger"
    
    return render_template(
        "config_google_sheets.html",
        active_page='configuracao',
        config=config,
        abas=abas,
        mensagem=mensagem,
        tipo_mensagem=tipo_mensagem,
        erro=erro,
        page_title='Extração de Atributos'
    )

@app.route("/validar-xml", methods=["GET", "POST"])
def validar_xml():
    resultado = None
    if request.method == "POST":
        if "arquivo_xml" not in request.files:
            return jsonify({"sucesso": False, "erro": "Nenhum arquivo enviado"}), 400

        arquivo = request.files["arquivo_xml"]
        if arquivo.filename == "":
            return jsonify({"sucesso": False, "erro": "Nenhum arquivo selecionado"}), 400

        resultado = validar_xml_nfe(arquivo) # type: ignore

        return jsonify(resultado)

    return render_template(
        "validar_xml.html",
        historico_processos=obter_historico_processos("xml"),
        processos_hoje=contar_processos_hoje("xml"),
        stats=get_processing_stats("xml")
        
    )

@app.route("/salvar-ordem-fotos", methods=["POST"])
def salvar_ordem_fotos():
    """API para salvar a ordem das fotos - IMPLEMENTAÇÃO INICIAL"""
    try:
        data = request.get_json()
        fotos = data.get('fotos', [])
        
        print(f"📝 Recebida solicitação para salvar ordem de {len(fotos)} fotos")
        
        # ✅ CORREÇÃO: Log para debug
        for i, foto in enumerate(fotos):
            print(f"Foto {i+1}: Produto {foto.get('product_id')}, Foto {foto.get('photo_id')}, Index: {foto.get('new_index')}")
        
        # ⚠️ ATENÇÃO: Esta é uma implementação básica
        # Você precisará implementar a lógica real de atualização na API AnyMarket
        # A API AnyMarket pode não suportar reordenação via REST
        
        return jsonify({
            'sucesso': True,
            'message': f'Ordem de {len(fotos)} fotos processada (implementação em desenvolvimento)',
            'total_fotos': len(fotos)
        })
        
    except Exception as e:
        print(f"❌ Erro ao salvar ordem: {str(e)}")
        return jsonify({
            'sucesso': False,
            'erro': f'Erro ao salvar ordem: {str(e)}'
        }), 500

@app.route('/consultar-produto')
def consultar_produto():
    """Página para consultar produtos por SKU"""
    return render_template(
        'consultar_produto.html',
        active_page='consultar_produto',
        active_module='anymarket',
        page_title='Produtos'
    )

@app.route('/api/anymarket/exportar-excel')
def api_exportar_excel():
    """API para exportar pedidos para Excel - COM TODOS OS FILTROS"""
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Token de autenticação não fornecido'}), 401
        
        token = auth_header.replace('Bearer ', '')
        
        # Coletar todos os filtros
        data_inicio = request.args.get('dataInicio')
        data_fim = request.args.get('dataFim')
        status = request.args.get('status')
        marketplace = request.args.get('marketplace')
        numero_pedido = request.args.get('numeroPedido')  # ✅ NOVO FILTRO
        
        # Buscar TODOS os pedidos com os filtros
        all_orders = []
        page = 1
        limit = 100  # Máximo por página
        
        while True:
            # Construir parâmetros igual à API normal
            params = {
                'offset': (page - 1) * limit,
                'limit': limit,
            }
            
            if status and status.strip():
                params['status'] = status.strip()
                
            if marketplace and marketplace.strip():
                params['marketplace'] = marketplace.strip()
            
            if data_inicio and data_inicio.strip():
                try:
                    datetime.strptime(data_inicio, '%Y-%m-%d')
                    params['createdAfter'] = f"{data_inicio}T00:00:00-03:00"
                except ValueError:
                    pass
            
            if data_fim and data_fim.strip():
                try:
                    datetime.strptime(data_fim, '%Y-%m-%d')
                    params['createdBefore'] = f"{data_fim}T23:59:59-03:00"
                except ValueError:
                    pass
            
            # ✅ FILTRO POR NÚMERO DO PEDIDO
            if numero_pedido and numero_pedido.strip():
                params['marketPlaceNumber'] = numero_pedido.strip()
            
            # Fazer requisição
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'gumgaToken': token
            }
            
            response = requests.get(
                "https://api.anymarket.com.br/v2/orders", 
                params=params, 
                headers=headers, 
                timeout=60
            )
            
            if response.status_code != 200:
                break
                
            data = response.json()
            orders = data.get('content', [])
            
            if not orders:
                break
                
            all_orders.extend(orders)
            
            # Verificar se há mais páginas
            pagination = data.get('page', {})
            if len(orders) < limit:
                break
                
            page += 1
        
        # Criar DataFrame para exportação
        df_data = []
        for order in all_orders:
            df_data.append({
                'ID': order.get('id'),
                'Marketplace': order.get('marketPlace'),
                'Status': order.get('status'),
                'Nº Marketplace': order.get('marketPlaceNumber'),
                'Comprador': order.get('buyer', {}).get('name'),
                'Email': order.get('buyer', {}).get('email'),
                'Telefone': order.get('buyer', {}).get('phone'),
                'Data Criação': order.get('createdAt'),
                'Data Pagamento': order.get('paymentDate'),
                'Quantidade Itens': len(order.get('items', [])),
                'Valor Total': order.get('total'),
                'Frete': order.get('freight'),
                'Desconto': order.get('discount'),
                'Cidade': order.get('buyer', {}).get('city'),
                'Estado': order.get('buyer', {}).get('state')
            })
        
        df = pd.DataFrame(df_data)
        
        # Criar arquivo Excel em memória
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Pedidos', index=False)
            
            # Formatar a planilha
            worksheet = writer.sheets['Pedidos']
            
            # Ajustar largura das colunas
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        
        # Retornar arquivo
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'pedidos_anymarket_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        )
        
    except Exception as e:
        print(f"❌ Erro na exportação Excel: {str(e)}")
        return jsonify({'success': False, 'error': f'Erro na exportação: {str(e)}'}), 500
    
@app.route('/api/anymarket/produtos/buscar-sku', methods=['POST'])
def api_buscar_produto_sku():
    """API para buscar produto por SKU - ROTA NOVA"""
    try:
        # ✅ USA APENAS A FUNÇÃO NOVA, SEM MEXER NO EXISTENTE
        from processamento.api_anymarket import buscar_produto_por_sku
        
        data = request.get_json()
        sku = data.get('sku', '').strip()
        
        if not sku:
            return jsonify({'sucesso': False, 'erro': 'SKU é obrigatório'}), 400
        
        # Chama a função nova
        resultado = buscar_produto_por_sku(sku)
        
        return jsonify(resultado)
        
    except Exception as e:
        print(f"❌ Erro ao buscar produto por SKU: {str(e)}")
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@app.route('/api/anymarket/produtos/<product_id>')
def api_buscar_produto_id(product_id):
    """API para buscar produto por ID"""
    try:
        from processamento.api_anymarket import obter_cliente_anymarket
        
        client = obter_cliente_anymarket()
        resultado = client.buscar_produto_por_id(product_id)
        
        return jsonify(resultado)
        
    except Exception as e:
        print(f"❌ Erro ao buscar produto por ID: {str(e)}")
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@app.route('/api/anymarket/produtos')
def api_listar_produtos():
    """API para listar produtos com paginação"""
    try:
        from processamento.api_anymarket import obter_cliente_anymarket
        
        pagina = request.args.get('page', 1, type=int)
        limite = request.args.get('limit', 50, type=int)
        filtro = request.args.get('filtro', '')
        
        client = obter_cliente_anymarket()
        
        params = {
            'limit': limite,
            'offset': (pagina - 1) * limite
        }
        
        if filtro:
            params['title'] = filtro
        
        resultado = client.buscar_produtos_com_filtros(params)
        
        return jsonify(resultado)
        
    except Exception as e:
        print(f"❌ Erro ao listar produtos: {str(e)}")
        return jsonify({'sucesso': False, 'erro': str(e)}), 500
    
@app.route('/perfil-mercado-livre')
def perfil_mercado_livre():
    """Dashboard com dados do perfil do Mercado Livre"""
    esta_autenticado = ml_token_manager.is_authenticated()
    
    dados_perfil = None
    if esta_autenticado:
        dados_perfil = obter_dados_completos_perfil()
    
    return render_template(
        'perfil_mercadolivre.html',
        active_page='perfil_mercado_livre',
        active_module='mercadolivre',
        page_title='Dashboard - Mercado Livre',
        esta_autenticado=esta_autenticado,
        dados_perfil=dados_perfil
    )

@app.route('/api/mercadolivre/exportar-excel', methods=['POST'])
def api_exportar_mlb_excel():
    """API para exportar resultados de MLB para Excel - ESTRUTURA MELHORADA"""
    try:
        from openpyxl.styles import PatternFill
        
        data = request.get_json()
        dados_exportacao = data.get('dados', [])
        
        if not dados_exportacao:
            return jsonify({'sucesso': False, 'erro': 'Nenhum dado para exportar'}), 400
        
        # Criar DataFrame
        df = pd.DataFrame(dados_exportacao)
        
        # Reordenar colunas para melhor visualização
        colunas_ordenadas = [
            'MLB Principal', 'MLB Variação', 'Tipo', 'SKU', 'Título', 'Preço', 
            'Estoque', 'Prazo Fabricação', 'Modo Envio', 'Frete Grátis', 'Status',
            'Catálogo', 'Variações', 'Quantidade Variações', 'Tipo Anúncio', 'Tipo Premium',
            'Condição', 'Vendidos', 'Categoria', 'ID Catálogo', 'Data Criação', 'Link',
            'Atributos Variação', 'Erro'
        ]
        
        # Manter apenas as colunas que existem nos dados
        colunas_finais = [col for col in colunas_ordenadas if col in df.columns]
        
        # Reordenar o DataFrame
        df = df[colunas_finais]
        
        # Criar arquivo Excel em memória
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Planilha principal com todos os dados
            df.to_excel(writer, sheet_name='Resultados MLB', index=False)
            
            # Planilha resumida com estatísticas
            estatisticas_data = {
                'Métrica': [
                    'Total de Anúncios Principais',
                    'Total de Variações',
                    'Total Geral',
                    'Encontrados',
                    'Não Encontrados',
                    'Data da Exportação'
                ],
                'Valor': [
                    data.get('total_principais', 0),
                    data.get('total_variações', 0),
                    data.get('total_geral', 0),
                    data.get('total_encontrado', 0),
                    data.get('total_nao_encontrado', 0),
                    datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                ]
            }
            df_estatisticas = pd.DataFrame(estatisticas_data)
            df_estatisticas.to_excel(writer, sheet_name='Estatísticas', index=False)
            
            # Formatar planilha principal
            worksheet = writer.sheets['Resultados MLB']
            
            # Destacar variações com cor diferente
            if data.get('total_variações', 0) > 0:
                light_blue_fill = PatternFill(start_color='E6F3FF', end_color='E6F3FF', fill_type='solid')
                light_yellow_fill = PatternFill(start_color='FFF2CC', end_color='FFF2CC', fill_type='solid')
                
                for row_idx in range(2, len(dados_exportacao) + 2):
                    tipo_cell = worksheet[f'C{row_idx}']  # Coluna Tipo
                    if tipo_cell.value == 'Variação':
                        # Aplicar cor azul clara para variações
                        for col_idx in range(1, worksheet.max_column + 1):
                            cell = worksheet.cell(row=row_idx, column=col_idx)
                            cell.fill = light_blue_fill
                    elif tipo_cell.value == 'Principal':
                        # Aplicar cor amarela clara para principais
                        for col_idx in range(1, worksheet.max_column + 1):
                            cell = worksheet.cell(row=row_idx, column=col_idx)
                            cell.fill = light_yellow_fill
            
            # Ajustar largura das colunas automaticamente
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 35)  # Limite de 35 para não ficar muito largo
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Formatar planilha de estatísticas
            worksheet_stats = writer.sheets['Estatísticas']
            for column in worksheet_stats.columns:
                column_letter = column[0].column_letter
                worksheet_stats.column_dimensions[column_letter].width = 30
            
            # Adicionar filtros na planilha principal
            worksheet.auto_filter.ref = worksheet.dimensions
        
        output.seek(0)
        
        # Nome do arquivo com timestamp
        nome_arquivo = f"consulta_mlb_estruturada_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=nome_arquivo
        )
        
    except Exception as e:
        print(f"❌ Erro na exportação Excel MLB: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'sucesso': False, 'erro': f'Erro na exportação: {str(e)}'}), 500
@app.route('/api/mercadolivre/contas')
def api_listar_contas():
    """Lista todas as contas"""
    try:
        accounts = ml_token_manager.get_all_accounts()
        return jsonify({
            'sucesso': True,
            'contas': accounts,
            'conta_atual': ml_token_manager.current_account_id
        })
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@app.route('/api/mercadolivre/contas/adicionar', methods=['POST'])
def api_adicionar_conta_auto():
    """Adiciona nova conta e tenta obter tokens AUTOMATICAMENTE"""
    try:
        data = request.get_json()
        
        account_name = data.get('account_name')
        app_id = data.get('app_id')
        secret_key = data.get('secret_key')
        
        if not account_name or not app_id or not secret_key:
            return jsonify({'sucesso': False, 'erro': 'Nome, App ID e Secret Key são obrigatórios'}), 400
        
        print(f"📥 Tentando adicionar conta: {account_name}")
        
        # Chama o método que tenta obter tokens automaticamente
        account_id, sucesso, mensagem = ml_token_manager.add_account_with_app_credentials(
            account_name, app_id, secret_key
        )
        
        if account_id:
            return jsonify({
                'sucesso': sucesso,
                'mensagem': mensagem,
                'account_id': account_id,
                'autenticada_automaticamente': sucesso
            })
        else:
            return jsonify({'sucesso': False, 'erro': mensagem}), 500
            
    except Exception as e:
        print(f"❌ Erro na API: {str(e)}")
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@app.route('/api/mercadolivre/contas/<account_id>/adicionar-tokens-manual', methods=['POST'])
def api_adicionar_tokens_manual(account_id):
    """Fallback: Adiciona tokens manualmente"""
    try:
        data = request.get_json()
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')
        
        if not access_token or not refresh_token:
            return jsonify({'sucesso': False, 'erro': 'Ambos os tokens são obrigatórios'}), 400
        
        sucesso, mensagem = ml_token_manager.add_tokens_manually(
            account_id, access_token, refresh_token
        )
        
        if sucesso:
            return jsonify({
                'sucesso': True,
                'mensagem': mensagem
            })
        else:
            return jsonify({'sucesso': False, 'erro': mensagem}), 400
            
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@app.route('/api/mercadolivre/contas/<account_id>/selecionar', methods=['POST'])
def api_selecionar_conta(account_id):
    """Seleciona conta para uso"""
    try:
        if ml_token_manager.set_current_account(account_id):
            return jsonify({
                'sucesso': True,
                'mensagem': 'Conta selecionada com sucesso!'
            })
        else:
            return jsonify({'sucesso': False, 'erro': 'Conta não encontrada'}), 404
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@app.route('/api/mercadolivre/contas/<account_id>/testar')
def api_testar_conta(account_id):
    """Testa se uma conta está funcionando"""
    try:
        if account_id not in ml_token_manager.accounts:
            return jsonify({'sucesso': False, 'erro': 'Conta não encontrada'}), 404
        
        account = ml_token_manager.accounts[account_id]
        token = account.get('access_token')
        
        if not token:
            return jsonify({
                'sucesso': False,
                'autenticada': False,
                'erro': 'Conta não tem token configurado'
            })
        
        # Testa o token
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(
            'https://api.mercadolibre.com/users/me',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            return jsonify({
                'sucesso': True,
                'autenticada': True,
                'nickname': user_data.get('nickname'),
                'user_id': user_data.get('id')
            })
        else:
            return jsonify({
                'sucesso': False,
                'autenticada': False,
                'erro': f'Token inválido (status: {response.status_code})'
            })
            
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@app.route('/api/mercadolivre/contas/<account_id>', methods=['DELETE'])
def api_remover_conta(account_id):
    """Remove conta (não permite remover a atual)"""
    try:
        sucesso, mensagem = ml_token_manager.remove_account(account_id)
        
        if sucesso:
            return jsonify({
                'sucesso': True,
                'mensagem': mensagem
            })
        else:
            return jsonify({'sucesso': False, 'erro': mensagem}), 400
            
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500
    
def obter_pedidos_anymarket_30_dias():
    """Obtém todos os pedidos dos últimos 30 dias do AnyMarket"""
    try:
        # Verifica se tem token configurado
        if not verificar_token_anymarket_configurado():
            return {
                'sucesso': False,
                'erro': 'Token do AnyMarket não configurado',
                'token_configurado': False
            }
        
        # Obtém o token
        from processamento.api_anymarket import obter_token_anymarket_seguro
        token = obter_token_anymarket_seguro()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'gumgaToken': token
        }
        
        # Calcula datas dos últimos 30 dias
        hoje = datetime.now()
        data_30_dias_atras = (hoje - timedelta(days=30)).strftime('%Y-%m-%d')
        data_hoje = hoje.strftime('%Y-%m-%d')
        
        # Configurações da API
        url = "https://api.anymarket.com.br/v2/orders"
        limit = 100  # Máximo por página
        offset = 0
        all_orders = []
        
        print(f"📊 Buscando TODOS os pedidos AnyMarket de {data_30_dias_atras} até {data_hoje}")
        
        # Loop para paginação - busca TODOS os pedidos
        while True:
            params = {
                'limit': limit,
                'offset': offset,
                'createdAfter': f'{data_30_dias_atras}',
                'createdBefore': f'{data_hoje}',
                'sort': 'createdAt',
                'sortDirection': 'DESC'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ Erro API AnyMarket: {response.status_code} - {response.text[:200]}")
                break
            
            data = response.json()
            orders = data.get('content', [])
            
            if orders:
                all_orders.extend(orders)
                print(f"✅ Página {offset//limit + 1}: {len(orders)} pedidos (total: {len(all_orders)})")
            
            # Verifica se há mais páginas
            if len(orders) < limit:
                break
            
            offset += limit
            
            # Safety limit - máximo de 500 pedidos
            if offset >= 500:
                print(f"⚠️ Limite de 500 pedidos atingido")
                break
        
        print(f"📦 Total de pedidos coletados: {len(all_orders)}")
        
        # Processa estatísticas detalhadas
        estatisticas = processar_estatisticas_detalhadas_pedidos(all_orders)
        
        return {
            'sucesso': True,
            'token_configurado': True,
            'total_pedidos': len(all_orders),
            'periodo': f'{data_30_dias_atras} até {data_hoje}',
            'estatisticas': estatisticas,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Erro ao buscar pedidos AnyMarket: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'sucesso': False,
            'erro': str(e),
            'token_configurado': verificar_token_anymarket_configurado()
        }

def processar_estatisticas_detalhadas_pedidos(orders):
    """Processa estatísticas detalhadas dos pedidos - VERSÃO CORRIGIDA"""
    if not orders:
        return {
            'total_pedidos': 0,
            'valor_total': 0,
            'total_itens': 0,
            'pedidos_por_dia': [],
            'top_produtos_quantidade': [],
            'top_produtos_valor': [],
            'status_distribuicao': {},
            'marketplace_distribuicao': {},
            'resumo': {
                'valor_total': 0,
                'total_pedidos': 0,
                'total_itens': 0,
                'ticket_medio_pedido': 0,
                'ticket_medio_item': 0,
                'media_itens_por_pedido': 0,
                'pedidos_concluidos': 0,
                'pedidos_pendentes': 0,
                'pedidos_cancelados': 0,
                'pedidos_faturados': 0,
                'marketplace_principal': 'N/A'
            }
        }
    
    # Dicionários para agrupamentos
    pedidos_por_dia = defaultdict(int)
    status_distribuicao = defaultdict(int)
    marketplace_distribuicao = defaultdict(int)
    
    # Dicionários para produtos - VERSÃO CORRIGIDA
    produtos_por_quantidade = defaultdict(int)
    produtos_por_valor = defaultdict(float)
    produtos_info = {}
    
    # Variáveis para estatísticas básicas
    valor_total = 0
    total_itens = 0
    
    for order in orders:
        # Valor total do pedido - CORRIGIDO
        try:
            valor_pedido = float(order.get('total', 0) or 0)
            valor_total += valor_pedido
        except:
            valor_pedido = 0
        
        # Data do pedido
        created_at = order.get('createdAt', '')
        if created_at:
            try:
                # Extrai apenas a data
                data_dia = created_at.split('T')[0] if 'T' in created_at else created_at[:10]
                pedidos_por_dia[data_dia] += 1
            except:
                pass
        
        # Status
        status = order.get('status', 'DESCONHECIDO')
        status_distribuicao[status] += 1
        
        # Marketplace
        marketplace = order.get('marketPlace', 'DESCONHECIDO')
        marketplace_distribuicao[marketplace] += 1
        
        # Itens do pedido - VERSÃO CORRIGIDA
        items = order.get('items', [])
        if not items:
            # Tenta obter itens de outra forma
            items = order.get('orderItems', [])
        
        for item in items:
            try:
                # Quantidade - CORRIGIDO
                quantidade = int(item.get('amount', 1) or 1)
                total_itens += quantidade
                
                # Preço - CORRIGIDO
                preco_unitario = 0
                try:
                    preco_unitario = float(item.get('price', 0) or 0)
                except:
                    # Tenta outros campos de preço
                    preco_unitario = float(item.get('value', 0) or 0)
                
                valor_item = preco_unitario * quantidade
                
                # Informações do produto - CORRIGIDO
                nome_produto = 'Produto Desconhecido'
                sku = 'SKU Desconhecido'
                
                # Tenta obter nome do produto de várias formas
                if item.get('product'):
                    nome_produto = item['product'].get('title', 'Produto Desconhecido')
                    sku = item['product'].get('partnerId', 'SKU Desconhecido')
                elif item.get('sku'):
                    nome_produto = item['sku'].get('title', 'Produto Desconhecido')
                    sku = item['sku'].get('partnerId', 'SKU Desconhecido')
                elif item.get('description'):
                    nome_produto = item['description']
                
                # Tenta obter SKU de várias formas
                if sku == 'SKU Desconhecido':
                    sku = item.get('partnerId', 'SKU Desconhecido')
                
                # Chave única para o produto
                chave_produto = f"{sku}|{nome_produto}"
                
                # DEBUG: Mostra informações do produto
                print(f"🔍 Produto encontrado: {nome_produto[:30]}... - Quantidade: {quantidade} - Preço: {preco_unitario}")
                
                # Atualiza contadores
                produtos_por_quantidade[chave_produto] += quantidade
                produtos_por_valor[chave_produto] += valor_item
                
                # Armazena informações detalhadas
                if chave_produto not in produtos_info:
                    produtos_info[chave_produto] = {
                        'nome': nome_produto,
                        'sku': sku,
                        'preco_medio': preco_unitario
                    }
                    
            except Exception as e:
                print(f"⚠️ Erro ao processar item: {str(e)}")
                continue
    
    print(f"📊 Total de itens processados: {total_itens}")
    print(f"📊 Total de produtos únicos: {len(produtos_por_quantidade)}")
    
    # Prepara top produtos por quantidade
    top_produtos_quantidade = []
    for chave, quantidade in sorted(produtos_por_quantidade.items(), key=lambda x: x[1], reverse=True)[:15]:
        info = produtos_info.get(chave, {})
        preco_medio = info.get('preco_medio', 0)
        valor_total_produto = produtos_por_valor.get(chave, 0)
        
        top_produtos_quantidade.append({
            'nome': info.get('nome', 'Desconhecido'),
            'sku': info.get('sku', 'N/A'),
            'quantidade': quantidade,
            'valor_total': valor_total_produto,
            'preco_medio': valor_total_produto / quantidade if quantidade > 0 else preco_medio
        })
    
    # Prepara top produtos por valor
    top_produtos_valor = []
    for chave, valor_total_produto in sorted(produtos_por_valor.items(), key=lambda x: x[1], reverse=True)[:15]:
        info = produtos_info.get(chave, {})
        quantidade = produtos_por_quantidade.get(chave, 0)
        
        top_produtos_valor.append({
            'nome': info.get('nome', 'Desconhecido'),
            'sku': info.get('sku', 'N/A'),
            'valor_total': valor_total_produto,
            'quantidade': quantidade,
            'preco_medio': valor_total_produto / quantidade if quantidade > 0 else info.get('preco_medio', 0)
        })
    
    # Prepara dados para gráfico de pedidos por dia (últimos 30 dias)
    pedidos_por_dia_lista = []
    for i in range(30):
        data = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        quantidade = pedidos_por_dia.get(data, 0)
        pedidos_por_dia_lista.append({
            'data': data,
            'quantidade': quantidade,
            'dia_semana': ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'][
                (datetime.now() - timedelta(days=i)).weekday()
            ]
        })
    
    # Inverte para ordem cronológica
    pedidos_por_dia_lista.reverse()
    
    # Resumo geral
    resumo = {
        'valor_total': valor_total,
        'total_pedidos': len(orders),
        'total_itens': total_itens,
        'ticket_medio_pedido': valor_total / len(orders) if orders else 0,
        'ticket_medio_item': valor_total / total_itens if total_itens else 0,
        'media_itens_por_pedido': total_itens / len(orders) if orders else 0,
        'pedidos_concluidos': sum(1 for o in orders if str(o.get('status', '')).upper() == 'CONCLUDED'),
        'pedidos_pendentes': sum(1 for o in orders if str(o.get('status', '')).upper() == 'PENDING'),
        'pedidos_cancelados': sum(1 for o in orders if str(o.get('status', '')).upper() == 'CANCELED'),
        'pedidos_faturados': sum(1 for o in orders if str(o.get('status', '')).upper() == 'INVOICED'),
        'marketplace_principal': max(marketplace_distribuicao.items(), key=lambda x: x[1])[0] if marketplace_distribuicao else 'N/A'
    }
    
    print(f"🎯 RESUMO:")
    print(f"   Valor Total: R$ {resumo['valor_total']:.2f}")
    print(f"   Total Pedidos: {resumo['total_pedidos']}")
    print(f"   Total Itens: {resumo['total_itens']}")
    print(f"   Ticket Médio: R$ {resumo['ticket_medio_pedido']:.2f}")
    print(f"   Itens/Pedido: {resumo['media_itens_por_pedido']:.1f}")
    
    return {
        'total_pedidos': len(orders),
        'valor_total': valor_total,
        'total_itens': total_itens,
        'pedidos_por_dia': pedidos_por_dia_lista,
        'top_produtos_quantidade': top_produtos_quantidade,
        'top_produtos_valor': top_produtos_valor,
        'status_distribuicao': dict(status_distribuicao),
        'marketplace_distribuicao': dict(marketplace_distribuicao),
        'resumo': resumo
    }

def obter_estatisticas_anymarket_7_dias():
    """Obtém estatísticas dos últimos 7 dias do AnyMarket"""
    try:
        # Verifica se tem token configurado
        if not verificar_token_anymarket_configurado():
            return {
                'sucesso': False,
                'erro': 'Token do AnyMarket não configurado',
                'token_configurado': False
            }
        
        # Obtém o token
        from processamento.api_anymarket import obter_token_anymarket_seguro
        token = obter_token_anymarket_seguro()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'gumgaToken': token
        }
        
        # Calcula datas dos últimos 7 dias
        hoje = datetime.now()
        data_7_dias_atras = (hoje - timedelta(days=7)).strftime('%Y-%m-%d')
        data_hoje = hoje.strftime('%Y-%m-%d')
        
        # Faz a requisição para pedidos dos últimos 7 dias
        url = "https://api.anymarket.com.br/v2/orders"
        params = {
            'limit': 100,  # Aumentei o limite para pegar mais pedidos
            'offset': 0,
            'createdAfter': f'{data_7_dias_atras}T00:00:00-03:00',
            'createdBefore': f'{data_hoje}T23:59:59-03:00',
            'sort': 'createdAt',
            'sortDirection': 'DESC'
        }
        
        print(f"📊 Buscando pedidos AnyMarket de {data_7_dias_atras} até {data_hoje}")
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Erro API AnyMarket: {response.status_code} - {response.text[:200]}")
            return {
                'sucesso': False,
                'erro': f'Erro na API AnyMarket: {response.status_code}',
                'status_code': response.status_code,
                'token_configurado': True
            }
        
        data = response.json()
        orders = data.get('content', [])
        total_elements = data.get('page', {}).get('totalElements', 0)
        
        print(f"✅ {len(orders)} pedidos encontrados (total: {total_elements})")
        
        # Se não encontrou pedidos, pode ser problema de timezone
        if not orders:
            # Tenta sem timezone específico
            params_sem_tz = {
                'limit': 100,
                'offset': 0,
                'createdAfter': f'{data_7_dias_atras}',
                'createdBefore': f'{data_hoje}',
                'sort': 'createdAt',
                'sortDirection': 'DESC'
            }
            
            print("🔄 Tentando sem timezone específico...")
            response_sem_tz = requests.get(url, params=params_sem_tz, headers=headers, timeout=30)
            
            if response_sem_tz.status_code == 200:
                data_sem_tz = response_sem_tz.json()
                orders = data_sem_tz.get('content', [])
                total_elements = data_sem_tz.get('page', {}).get('totalElements', 0)
                print(f"✅ {len(orders)} pedidos encontrados (sem timezone)")
        
        # Processa as estatísticas
        estatisticas = processar_estatisticas_pedidos(orders)
        
        return {
            'sucesso': True,
            'token_configurado': True,
            'total_pedidos': total_elements,
            'pedidos_ultimos_7_dias': len(orders),
            'estatisticas': estatisticas,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Erro ao buscar estatísticas AnyMarket: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'sucesso': False,
            'erro': str(e),
            'token_configurado': verificar_token_anymarket_configurado() if 'verificar_token_anymarket_configurado' in locals() else False
        }

def processar_estatisticas_pedidos(orders):
    """Processa estatísticas dos pedidos"""
    if not orders:
        return {
            'total_pedidos': 0,
            'valor_total': 0,
            'pedidos_por_dia': [],
            'top_produtos': [],
            'status_distribuicao': {},
            'marketplace_distribuicao': {}
        }
    
    # Cálculo de estatísticas
    valor_total = sum(float(order.get('total', 0)) for order in orders)
    
    # Agrupa por data
    pedidos_por_dia = {}
    for order in orders:
        created_at = order.get('createdAt', '')
        if created_at:
            # Extrai apenas a data (YYYY-MM-DD)
            data = created_at.split('T')[0] if 'T' in created_at else created_at[:10]
            pedidos_por_dia[data] = pedidos_por_dia.get(data, 0) + 1
    
    # Distribuição por status
    status_distribuicao = {}
    for order in orders:
        status = order.get('status', 'DESCONHECIDO')
        status_distribuicao[status] = status_distribuicao.get(status, 0) + 1
    
    # Distribuição por marketplace
    marketplace_distribuicao = {}
    for order in orders:
        marketplace = order.get('marketPlace', 'DESCONHECIDO')
        marketplace_distribuicao[marketplace] = marketplace_distribuicao.get(marketplace, 0) + 1
    
    # Top produtos (baseado em itens dos pedidos)
    top_produtos = {}
    for order in orders:
        items = order.get('items', [])
        for item in items:
            product_id = item.get('sku', {}).get('partnerId') or item.get('product', {}).get('title', 'Produto Desconhecido')
            quantidade = item.get('amount', 1)
            top_produtos[product_id] = top_produtos.get(product_id, 0) + quantidade
    
    # Ordena top produtos
    top_produtos_lista = sorted(top_produtos.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Formata pedidos por dia para gráfico
    pedidos_por_dia_lista = []
    for i in range(7):
        data = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        quantidade = pedidos_por_dia.get(data, 0)
        pedidos_por_dia_lista.append({
            'data': data,
            'quantidade': quantidade,
            'dia_semana': ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'][
                (datetime.now() - timedelta(days=i)).weekday()
            ]
        })
    
    # Inverte para ordem cronológica
    pedidos_por_dia_lista.reverse()
    
    return {
        'total_pedidos': len(orders),
        'valor_total': valor_total,
        'pedidos_por_dia': pedidos_por_dia_lista,
        'top_produtos': top_produtos_lista,
        'status_distribuicao': status_distribuicao,
        'marketplace_distribuicao': marketplace_distribuicao,
        'ticket_medio': valor_total / len(orders) if orders else 0,
        'pedidos_pendentes': sum(1 for o in orders if o.get('status') == 'PENDING'),
        'pedidos_concluidos': sum(1 for o in orders if o.get('status') == 'CONCLUDED'),
        'pedidos_cancelados': sum(1 for o in orders if o.get('status') == 'CANCELED')
    }


def obter_dados_completos_perfil():
    """Obtém dados básicos do perfil - VERSÃO CORRIGIDA"""
    try:
        token = ml_token_manager.get_valid_token()
        if not token:
            return {'erro': 'Token não disponível'}
        
        headers = {'Authorization': f'Bearer {token}'}
        base_url = "https://api.mercadolibre.com"
        
        # Dados básicos do usuário
        response_user = requests.get(f"{base_url}/users/me", headers=headers, timeout=10)
        if response_user.status_code != 200:
            return {'erro': 'Erro ao buscar dados do usuário'}
        
        user_data = response_user.json()
        user_id = user_data['id']
        print(f"👤 Usuário: {user_data.get('nickname')} (ID: {user_id})")
        
        # Buscar seller_reputation para nível da conta - MAIS CONFIÁVEL
        nivel_conta = "Não identificado"
        try:
            response_reputation = requests.get(
                f"{base_url}/users/{user_id}/seller_reputation",
                headers=headers,
                timeout=10
            )
            if response_reputation.status_code == 200:
                reputation_data = response_reputation.json()
                print(f"📊 Seller reputation: {reputation_data}")
                
                # Extrair nível de diferentes campos possíveis
                if 'level_id' in reputation_data:
                    nivel_conta = reputation_data['level_id']
                elif 'seller_level' in reputation_data:
                    nivel_conta = reputation_data['seller_level']
                elif 'power_seller_status' in reputation_data:
                    nivel_conta = reputation_data['power_seller_status']
                    
                print(f"✅ Nível da conta: {nivel_conta}")
            else:
                print(f"❌ Erro seller_reputation: {response_reputation.status_code}")
        except Exception as e:
            print(f"❌ Erro nível: {e}")
        
        # Buscar vendas com PAGINAÇÃO para pegar mais de 50
        data_30_dias_atras = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S.000-03:00')
        
        todas_vendas = []
        offset = 0
        limit = 50
        
        while True:
            params_vendas = {
                'seller': user_id,
                'order.date_created.from': data_30_dias_atras,
                'sort': 'date_desc',
                'limit': limit,
                'offset': offset
            }
            
            response_vendas = requests.get(
                f"{base_url}/orders/search", 
                headers=headers, 
                params=params_vendas, 
                timeout=20
            )
            
            if response_vendas.status_code != 200:
                print(f"❌ Erro vendas (offset {offset}): {response_vendas.status_code}")
                break
            
            vendas_data = response_vendas.json()
            vendas_lote = vendas_data.get('results', [])
            
            if not vendas_lote:
                break
                
            todas_vendas.extend(vendas_lote)
            print(f"✅ Lote {offset//limit + 1}: {len(vendas_lote)} vendas")
            
            # Se veio menos que o limite, é a última página
            if len(vendas_lote) < limit:
                break
                
            offset += limit
            
            # Limitar a 200 vendas máximo para não sobrecarregar
            if offset >= 200:
                break
        
        print(f"📈 Total de vendas encontradas: {len(todas_vendas)}")
        
        # Buscar anúncios ativos
        anuncios_ativos = 0
        try:
            response_anuncios = requests.get(
                f"{base_url}/users/{user_id}/items/search?status=active&limit=50",
                headers=headers,
                timeout=10
            )
            if response_anuncios.status_code == 200:
                anuncios_data = response_anuncios.json()
                anuncios_ativos = len(anuncios_data.get('results', []))
                print(f"✅ Anúncios ativos: {anuncios_ativos}")
        except Exception as e:
            print(f"❌ Erro anúncios: {e}")
        
        # Calcular métricas básicas
        total_vendas = len(todas_vendas)
        valor_total_vendas = sum(float(order.get('total_amount', order.get('total', 0))) for order in todas_vendas)
        
        # Processar últimas vendas
        ultimas_vendas_detalhadas = []
        for venda in todas_vendas[:10]:  # Apenas 10 últimas para mostrar
            total_venda = venda.get('total_amount') or venda.get('total') or 0
            
            ultimas_vendas_detalhadas.append({
                'id': venda.get('id', 'N/A'),
                'data': venda.get('date_created', 'N/A'),
                'status': venda.get('status', 'N/A'),
                'total': float(total_venda),
                'itens': len(venda.get('order_items', [])),
                'comprador': venda.get('buyer', {}).get('nickname', 'N/A')
            })
        
        return {
            'dados_usuario': user_data,
            'nivel_conta': nivel_conta,
            'metricas': {
                'total_vendas_30_dias': total_vendas,
                'valor_total_vendas': valor_total_vendas,
                'ticket_medio': valor_total_vendas / total_vendas if total_vendas > 0 else 0,
                'anuncios_ativos': anuncios_ativos,
                'vendas_por_dia': round(total_vendas / 30, 2) if total_vendas > 0 else 0,
                'total_vendas_encontradas': total_vendas  # Para mostrar no template
            },
            'ultimas_vendas': ultimas_vendas_detalhadas,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Erro ao buscar dados: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'erro': f'Erro interno: {str(e)}'}
    
if __name__ == "__main__":
    app.run(debug=True)