# ml_oauth.py — VERSÃO CORRIGIDA
# ============================================================
# OAuth 2.0 Authorization Code Flow - Mercado Livre
#
# COMO FUNCIONA:
# 1. Usuário acessa /mercadolivre/oauth/iniciar?account_name=MinhaLoja
# 2. É redirecionado para a tela de login/consentimento do ML
# 3. ML redireciona para /mercadolivre/oauth/callback?code=XXX
# 4. O código é trocado por access_token + refresh_token
# 5. Tokens são salvos em uma conta isolada no token_manager
#
# IMPORTANTE:
# - As credenciais do SEU APP (client_id / client_secret) ficam
#   fixas no .env — o usuário final NUNCA precisa digitá-las.
# - Cada conta OAuth recebe um account_id único (oauth_<timestamp>)
#   para não conflitar com contas legadas (token manual).
# - O método legado (/api/mercadolivre/autenticar) continua
#   funcionando normalmente em paralelo.
#
# PRÉ-REQUISITOS NO .env:
#   ML_CLIENT_ID     = seu App ID fixo do painel ML
#   ML_CLIENT_SECRET = seu Secret Key fixo do painel ML
#   ML_REDIRECT_URI  = https://seudominio.com/mercadolivre/oauth/callback
#
# NO PAINEL DO ML (https://developers.mercadolivre.com.br/devcenter):
#   Adicione em "URLs de redirecionamento":
#     Produção: https://seudominio.com/mercadolivre/oauth/callback
#     Local:    http://localhost:5000/mercadolivre/oauth/callback
# ============================================================

import os
import requests
from flask import Blueprint, redirect, request, url_for, jsonify, session, flash
from datetime import datetime

from token_manager_secure import ml_token_manager

ml_oauth_bp = Blueprint('ml_oauth', __name__)

ML_AUTH_URL = "https://auth.mercadolivre.com.br/authorization"
ML_TOKEN_URL = "https://api.mercadolibre.com/oauth/token"


def _get_app_credentials():
    """
    Retorna (client_id, client_secret, redirect_uri) do SEU aplicativo.
    Lê exclusivamente das variáveis de ambiente — o usuário nunca digita isso.
    """
    client_id     = os.environ.get('ML_CLIENT_ID')
    client_secret = os.environ.get('ML_CLIENT_SECRET')
    redirect_uri  = os.environ.get(
        'ML_REDIRECT_URI',
        'http://localhost:5000/mercadolivre/oauth/callback'
    )
    return client_id, client_secret, redirect_uri


# ── ROTA 1: Iniciar autenticação ───────────────────────────
@ml_oauth_bp.route('/mercadolivre/oauth/iniciar')
def oauth_iniciar():
    """
    Redireciona para a tela de autorização do Mercado Livre.

    Query params opcionais:
        account_name – nome amigável da conta (ex: "Minha Loja")
        account_id   – ID existente para re-autenticar uma conta já criada
    """
    account_name = request.args.get('account_name', 'Nova Conta')
    account_id   = request.args.get('account_id')

    client_id, client_secret, redirect_uri = _get_app_credentials()

    if not client_id or not client_secret:
        return jsonify({
            'erro': (
                'Credenciais do aplicativo não configuradas no servidor. '
                'Defina ML_CLIENT_ID e ML_CLIENT_SECRET no arquivo .env.'
            )
        }), 500  # 500 pois é erro de configuração do servidor, não do usuário

    # Gera account_id único para esta nova autenticação OAuth
    # (evita conflito com contas legadas ou outras contas OAuth)
    if not account_id:
        ts = datetime.now().strftime('%Y%m%d%H%M%S')
        account_id = f'oauth_{ts}'

    # Pré-cria o registro da conta para guardar o nome antes do callback
    if account_id not in ml_token_manager.accounts:
        ml_token_manager.accounts[account_id] = {
            'account_name': account_name,
            'auth_method':  'oauth',          # marca origem para não misturar
            'created_at':   datetime.now().isoformat(),
            'is_active':    True,
            'is_default':   not ml_token_manager.accounts,  # primeira conta vira padrão
        }
        ml_token_manager.save_to_database()

    # Salva na sessão para recuperar no callback
    session['ml_oauth_account_id']   = account_id
    session['ml_oauth_account_name'] = account_name

    # Monta URL de autorização
    # prompt=consent garante que a tela de aceitar o app apareça sempre
    auth_url = (
        f"{ML_AUTH_URL}"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=offline_access%20read%20write"
        f"&prompt=consent"
    )

    print(f"🔐 OAuth iniciado — conta: {account_id} ({account_name})")
    print(f"   Redirect: {auth_url}")
    return redirect(auth_url)


# ── ROTA 2: Callback ──────────────────────────────────────
@ml_oauth_bp.route('/mercadolivre/oauth/callback')
def oauth_callback():
    """
    Recebe o code do ML após o usuário autorizar o app,
    troca por tokens e salva na conta correspondente.
    """
    code  = request.args.get('code')
    error = request.args.get('error')

    if error:
        flash(f'Autorização recusada: {error}', 'danger')
        return redirect(url_for('consultar_mercado_livre'))

    if not code:
        flash('Código de autorização não recebido.', 'danger')
        return redirect(url_for('consultar_mercado_livre'))

    # Recupera dados da sessão
    account_id   = session.pop('ml_oauth_account_id',   None)
    account_name = session.pop('ml_oauth_account_name', 'Conta OAuth')

    if not account_id:
        # Segurança: se a sessão expirou, cria conta nova
        ts         = datetime.now().strftime('%Y%m%d%H%M%S')
        account_id = f'oauth_{ts}'

    client_id, client_secret, redirect_uri = _get_app_credentials()

    if not client_id or not client_secret:
        flash('Credenciais do aplicativo não configuradas no servidor.', 'danger')
        return redirect(url_for('consultar_mercado_livre'))

    print(f"🔄 Trocando code por tokens — conta: {account_id}")

    print(f"🔍 Debug credenciais:")
    print(f"   client_id: {client_id[:10]}... (len: {len(client_id) if client_id else 0})")
    print(f"   client_secret: {'*' * (len(client_secret)-4) if client_secret else 'None'}")
    print(f"   redirect_uri: {redirect_uri}")

    try:
        response = requests.post(
            ML_TOKEN_URL,
            data={
                'grant_type':    'authorization_code',
                'client_id':     client_id,
                'client_secret': client_secret,
                'code':          code,
                'redirect_uri':  redirect_uri,
            },
            headers={
                'Accept':       'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            timeout=30,
        )

        if response.status_code != 200:
            detalhe = response.json().get('error_description', response.text[:200])
            print(f"❌ Erro ao trocar code: {response.status_code} — {detalhe}")
            flash(f'Erro na autenticação: {detalhe}', 'danger')
            return redirect(url_for('consultar_mercado_livre'))

        token_data    = response.json()
        access_token  = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_in    = token_data.get('expires_in', 21600)

        print(f"✅ Tokens recebidos — expires_in={expires_in}s")

        # Garante que a conta existe no token_manager
        if account_id not in ml_token_manager.accounts:
            ml_token_manager.accounts[account_id] = {
                'account_name': account_name,
                'auth_method':  'oauth',
                'created_at':   datetime.now().isoformat(),
                'is_active':    True,
                'is_default':   not ml_token_manager.accounts,
            }

        # Atualiza tokens da conta (isolado — não afeta outras contas)
        account = ml_token_manager.accounts[account_id]
        account.update({
            'access_token':  access_token,
            'refresh_token': refresh_token,
            'expires_in':    expires_in,
            'token_type':    token_data.get('token_type', 'Bearer'),
            'scope':         token_data.get('scope', ''),
            'auth_method':   'oauth',
            'updated_at':    datetime.now().isoformat(),
        })

        # Busca nickname/user_id desta conta no ML
        ml_token_manager.atualizar_dados_usuario(account_id)

        # Define como conta ativa atual
        ml_token_manager.current_account_id = account_id
        ml_token_manager.save_to_database()

        nickname = account.get('nickname', account_name)
        flash(f'✅ Conta autenticada com sucesso: {nickname}', 'success')
        return redirect(url_for('consultar_mercado_livre'))

    except Exception as e:
        print(f"❌ Exceção no callback OAuth: {e}")
        flash(f'Erro interno na autenticação: {str(e)}', 'danger')
        return redirect(url_for('consultar_mercado_livre'))


# ── ROTA 3: Renovar token manualmente (opcional) ──────────
@ml_oauth_bp.route('/mercadolivre/oauth/renovar', methods=['POST'])
def oauth_renovar():
    """
    Força renovação do access_token de uma conta OAuth via refresh_token.
    Retorna JSON.
    """
    data       = request.get_json() or {}
    account_id = data.get('account_id') or ml_token_manager.current_account_id

    if not account_id or account_id not in ml_token_manager.accounts:
        return jsonify({'sucesso': False, 'erro': 'Conta não encontrada'}), 404

    account       = ml_token_manager.accounts[account_id]
    refresh_token = account.get('refresh_token')

    if not refresh_token:
        return jsonify({
            'sucesso': False,
            'erro': 'Refresh token não disponível. Re-autentique via OAuth.'
        }), 400

    novo_token = ml_token_manager.refresh_token(account_id, refresh_token)

    if novo_token:
        return jsonify({
            'sucesso':    True,
            'mensagem':   'Token renovado com sucesso!',
            'account_id': account_id,
        })
    else:
        return jsonify({
            'sucesso': False,
            'erro':    'Falha na renovação. Re-autentique via OAuth.',
        }), 400


# ── ROTA 4: Status de todas as contas (JSON) ──────────────
@ml_oauth_bp.route('/mercadolivre/oauth/status')
def oauth_status():
    """Retorna status de autenticação de todas as contas (OAuth e legadas)."""
    contas = []
    for aid, acc in ml_token_manager.accounts.items():
        contas.append({
            'id':           aid,
            'nome':         acc.get('account_name', 'Sem nome'),
            'nickname':     acc.get('nickname'),
            'metodo':       acc.get('auth_method', 'legado'),   # 'oauth' ou 'legado'
            'autenticada':  bool(acc.get('access_token')),
            'atual':        (aid == ml_token_manager.current_account_id),
            'atualizado_em': acc.get('updated_at'),
        })

    return jsonify({
        'sucesso':      True,
        'conta_atual':  ml_token_manager.current_account_id,
        'total_contas': len(contas),
        'contas':       contas,
    })


# ── ROTA 5: URL de iniciar OAuth (para o frontend saber qual usar) ─
@ml_oauth_bp.route('/mercadolivre/oauth/url-callback')
def oauth_url_callback():
    """Retorna a redirect_uri configurada no servidor para exibir no frontend."""
    _, _, redirect_uri = _get_app_credentials()
    return jsonify({'redirect_uri': redirect_uri})