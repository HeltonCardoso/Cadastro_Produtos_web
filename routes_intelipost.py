"""
Rotas para módulo Intelipost
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime, timedelta
import logging
from processamento.intelipost_services import IntelipostService
from log_utils import registrar_processo, obter_historico_processos, contar_processos_hoje

# Criação do blueprint
intelipost_bp = Blueprint('intelipost', __name__, 
                         url_prefix='/intelipost',
                         template_folder='templates/intelipost')

logger = logging.getLogger(__name__)
service = IntelipostService()

# Armazenamento simples para histórico (em produção use banco de dados)
_historico_consultas = []

@intelipost_bp.route('/')
def rastrear():
    """Página principal de rastreamento"""
    pedido = request.args.get('pedido', '')
    
    # Estatísticas básicas
    stats = {
        'total_consultas': len(_historico_consultas),
        'consultas_hoje': sum(1 for c in _historico_consultas 
                            if c['data_consulta'].date() == datetime.now().date()),
        'consultas_sucesso': sum(1 for c in _historico_consultas if c['sucesso'])
    }
    
    return render_template(
        'rastrear.html',
        active_page='intelipost',
        active_module='intelipost',
        page_title='Rastreamento Intelipost',
        pedido=pedido,
        stats=stats
    )

@intelipost_bp.route('/api/rastreio/<numero_pedido>')
def api_buscar_rastreio(numero_pedido):
    """API para buscar rastreio"""
    try:
        inicio = datetime.now()
        
        # Busca dados na API Intelipost
        dados_api = service.api.buscar_rastreio(numero_pedido)
        
        # Formata dados
        dados_formatados = service.formatar_dados_rastreio(dados_api)
        
        tempo_segundos = (datetime.now() - inicio).total_seconds()
        
        # Registrar consulta
        consulta = {
            'numero_pedido': numero_pedido,
            'data_consulta': datetime.now(),
            'sucesso': True,
            'tempo_execucao': tempo_segundos,
            'dados': dados_formatados.get('pedido', {}).get('numero')
        }
        _historico_consultas.append(consulta)
        
        # Limitar histórico a 100 consultas
        if len(_historico_consultas) > 100:
            _historico_consultas.pop(0)
        
        # Registrar no sistema de logs
        try:
            registrar_processo(
                modulo="intelipost",
                qtd_itens=1,
                tempo_execucao=tempo_segundos,
                status="sucesso"
            )
        except:
            pass
        
        return jsonify({
            'sucesso': True,
            'dados': dados_formatados,
            'tempo_resposta': f"{tempo_segundos:.2f}s"
        })
        
    except Exception as e:
        # Registrar consulta com erro
        consulta = {
            'numero_pedido': numero_pedido,
            'data_consulta': datetime.now(),
            'sucesso': False,
            'erro': str(e)
        }
        _historico_consultas.append(consulta)
        
        # Registrar no sistema de logs
        try:
            registrar_processo(
                modulo="intelipost",
                qtd_itens=0,
                tempo_execucao=0,
                status="erro",
                erro_mensagem=str(e)
            )
        except:
            pass
        
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        }), 400

@intelipost_bp.route('/api/status')
def api_status():
    """API para verificar status da conexão"""
    try:
        resultado = service.api.testar_conexao()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro: {str(e)}'
        })

@intelipost_bp.route('/api/limpar-cache', methods=['POST'])
def api_limpar_cache():
    """API para limpar cache da API"""
    try:
        service.api.limpar_cache()
        return jsonify({
            'sucesso': True,
            'mensagem': 'Cache limpo com sucesso'
        })
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        })

@intelipost_bp.route('/historico')
def historico():
    """Página de histórico de consultas"""
    # Ordenar do mais recente para o mais antigo
    historico_ordenado = sorted(_historico_consultas, 
                               key=lambda x: x['data_consulta'], 
                               reverse=True)
    
    stats = {
        'total_consultas': len(_historico_consultas),
        'consultas_hoje': sum(1 for c in _historico_consultas 
                            if c['data_consulta'].date() == datetime.now().date()),
        'consultas_sucesso': sum(1 for c in _historico_consultas if c['sucesso'])
    }
    
    return render_template(
        'historico.html',
        active_page='intelipost',
        active_module='intelipost',
        page_title='Histórico Intelipost',
        historico_consultas=historico_ordenado,
        **stats
    )

@intelipost_bp.route('/api/limpar-historico', methods=['POST'])
def api_limpar_historico():
    """API para limpar histórico de consultas"""
    try:
        _historico_consultas.clear()
        return jsonify({
            'sucesso': True,
            'mensagem': 'Histórico limpo com sucesso'
        })
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        })

@intelipost_bp.route('/api/estatisticas')
def api_estatisticas():
    """API para obter estatísticas"""
    try:
        estatisticas_uso = service.obter_estatisticas_uso()
        
        return jsonify({
            'sucesso': True,
            'estatisticas': {
                'historico': {
                    'total': len(_historico_consultas),
                    'hoje': sum(1 for c in _historico_consultas 
                              if c['data_consulta'].date() == datetime.now().date()),
                    'sucesso': sum(1 for c in _historico_consultas if c['sucesso'])
                },
                'cache': estatisticas_uso['cache'],
                'api_configurada': estatisticas_uso['api_configurada']
            }
        })
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        })

@intelipost_bp.route('/api/multiplos', methods=['POST'])
def api_processar_multiplos():
    """API para processar múltiplos pedidos"""
    try:
        data = request.get_json()
        lista_pedidos = data.get('pedidos', [])
        
        if not lista_pedidos:
            return jsonify({
                'sucesso': False,
                'erro': 'Nenhum pedido fornecido'
            }), 400
        
        inicio = datetime.now()
        resultado = service.processar_multiplos_pedidos(lista_pedidos)
        tempo_segundos = (datetime.now() - inicio).total_seconds()
        
        # Registrar processo
        try:
            registrar_processo(
                modulo="intelipost",
                qtd_itens=len(lista_pedidos),
                tempo_execucao=tempo_segundos,
                status="sucesso" if resultado['taxa_sucesso'] > 50 else "parcial",
                erro_mensagem=f"{resultado['erros']} erro(s)" if resultado['erros'] > 0 else None
            )
        except:
            pass
        
        return jsonify({
            'sucesso': True,
            'resultado': resultado,
            'tempo_total': f"{tempo_segundos:.2f}s"
        })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        }), 500