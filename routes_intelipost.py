"""
Rotas para módulo Intelipost - VERSÃO FUNCIONAL
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime
import logging
import json
import os

# Criação do blueprint
intelipost_bp = Blueprint('intelipost', __name__, 
                         url_prefix='/intelipost',
                         template_folder='templates/intelipost')

logger = logging.getLogger(__name__)

# Armazenamento simples para histórico
_historico_consultas = []

def carregar_token_intelipost():
    """Carrega o token Intelipost do arquivo seguro - VERSÃO DEBUG"""
    try:
        tokens_file = 'tokens_secure.json'
        print(f"🔍 [DEBUG] Procurando arquivo: {tokens_file}")
        print(f"🔍 [DEBUG] Caminho absoluto: {os.path.abspath(tokens_file)}")
        
        if not os.path.exists(tokens_file):
            print(f"❌ [DEBUG] Arquivo NÃO existe!")
            return None
        
        print(f"✅ [DEBUG] Arquivo encontrado")
        
        with open(tokens_file, 'r', encoding='utf-8') as f:
            tokens = json.load(f)
            print(f"✅ [DEBUG] JSON carregado")
            print(f"🔍 [DEBUG] Chaves no arquivo: {list(tokens.keys())}")
        
        # Procura por token intelipost
        if 'intelipost' in tokens:
            print(f"✅ [DEBUG] 'intelipost' encontrado")
            api_key = tokens['intelipost'].get('api_key')
            
            if api_key:
                print(f"✅ [DEBUG] API Key encontrada")
                print(f"🔍 [DEBUG] Tamanho: {len(api_key)} caracteres")
                print(f"🔍 [DEBUG] Primeiros 20 chars: {api_key[:20]}...")
                return api_key
            else:
                print(f"❌ [DEBUG] 'api_key' não encontrada em 'intelipost'")
                print(f"🔍 [DEBUG] Conteúdo de 'intelipost': {tokens['intelipost']}")
                return None
        
        print(f"❌ [DEBUG] Chave 'intelipost' não encontrada no JSON")
        return None
        
    except json.JSONDecodeError as e:
        print(f"❌ [DEBUG] Erro ao decodificar JSON: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ [DEBUG] Erro geral: {str(e)}")
        return None

@intelipost_bp.route('/')
def rastrear():
    """Página principal de rastreamento"""
    pedido = request.args.get('pedido', '')
    
    # Verificar se token está configurado
    token_configurado = bool(carregar_token_intelipost())
    
    if not token_configurado:
        flash('🔧 Configure o token Intelipost em Configurações > Tokens', 'warning')
    
    return render_template(
        'rastrear.html',
        active_page='intelipost',
        active_module='intelipost',
        page_title='Rastreamento Intelipost',
        pedido=pedido,
        token_configurado=token_configurado
    )

@intelipost_bp.route('/api/rastreio/<numero_pedido>')
def api_buscar_rastreio(numero_pedido):
    """API para buscar rastreio - VERSÃO CORRIGIDA"""
    print(f"\n🔍 ========== BUSCAR RASTREIO ==========")
    print(f"🔍 Pedido: {numero_pedido}")
    
    try:
        # 1. Carregar token
        api_key = carregar_token_intelipost()
        
        if not api_key:
            print(f"❌ Token NÃO carregado")
            return jsonify({
                'sucesso': False,
                'erro': 'Token Intelipost não configurado. Configure em Configurações > Tokens.'
            }), 400
        
        print(f"✅ Token carregado: {api_key[:20]}...")
        
        # 2. Criar API com a chave
        from processamento.intelipost_api import IntelipostAPI
        api = IntelipostAPI(api_key=api_key)
        
        # 3. Testar conexão primeiro
        print(f"🧪 Testando conexão...")
        teste = api.testar_conexao()
        print(f"📊 Resultado teste: {teste}")
        
        if not teste.get('sucesso'):
            return jsonify({
                'sucesso': False,
                'erro': f"Falha na conexão: {teste.get('mensagem', 'Erro desconhecido')}"
            }), 400
        
        # 4. Buscar rastreio
        print(f"🔍 Buscando rastreio na API...")
        dados_api = api.buscar_rastreio(numero_pedido)
        print(f"✅ Dados API recebidos")
        
        # 5. Formatar dados
        from processamento.intelipost_services import IntelipostService
        service = IntelipostService(api_key=api_key)  # Passe a chave aqui
        dados_formatados = service.formatar_dados_rastreio(dados_api)
        
        # Registrar histórico
        _historico_consultas.append({
            'numero_pedido': numero_pedido,
            'data_consulta': datetime.now(),
            'sucesso': True
        })
        
        print(f"✅ ========== SUCESSO ==========")
        return jsonify({
            'sucesso': True,
            'dados': dados_formatados,
            'teste_conexao': teste
        })
        
    except Exception as e:
        print(f"❌ ========== ERRO ==========")
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        
        _historico_consultas.append({
            'numero_pedido': numero_pedido,
            'data_consulta': datetime.now(),
            'sucesso': False,
            'erro': str(e)
        })
        
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        }), 400

@intelipost_bp.route('/api/buscar-pedido/<numero_pedido>')
def api_buscar_pedido(numero_pedido):
    """Alias para compatibilidade com JavaScript"""
    return api_buscar_rastreio(numero_pedido)

@intelipost_bp.route('/api/status')
def api_status():
    """API para verificar status da conexão"""
    try:
        api_key = carregar_token_intelipost()
        if not api_key:
            return jsonify({
                'sucesso': False,
                'conectado': False,
                'mensagem': 'Token não configurado'
            })
        
        from processamento.intelipost_api import IntelipostAPI
        api = IntelipostAPI(api_key=api_key)
        resultado = api.testar_conexao()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro: {str(e)}'
        })

@intelipost_bp.route('/historico')
def historico():
    """Página de histórico de consultas"""
    return render_template(
        'historico.html',
        active_page='intelipost',
        active_module='intelipost',
        page_title='Histórico Intelipost',
        historico_consultas=_historico_consultas[:50]  # Últimas 50
    )

@intelipost_bp.route('/api/testar')
def api_testar():
    """Rota de teste simples"""
    return jsonify({
        'sucesso': True,
        'mensagem': 'Módulo Intelipost funcionando!',
        'timestamp': datetime.now().isoformat()
    })