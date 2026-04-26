# ml_oauth.py
# ============================================================
# OAuth 2.0 Authorization Code Flow - Mercado Livre
#
# COMO FUNCIONA:
# 1. Usuário acessa /mercadolivre/oauth/iniciar
# 2. É redirecionado para tela de login do ML
# 3. ML redireciona de volta para /mercadolivre/oauth/callback?code=XXX
# 4. O código é trocado por access_token + refresh_token
# 5. Tokens são salvos via token_manager_secure
#
# PRÉ-REQUISITOS NO PAINEL DO ML:
# - Acesse: https://developers.mercadolivre.com.br/devcenter
# - Crie ou edite seu App
# - Em "URLs de redirecionamento" adicione: https://SEU_DOMINIO/mercadolivre/oauth/callback
# - Para testes locais use: http://localhost:5000/mercadolivre/oauth/callback
# ============================================================

import os
import requests
from flask import Blueprint, redirect, request, url_for, jsonify, session, flash
from datetime import datetime

# Importa o token manager existente
from token_manager_secure import ml_token_manager

# ── Blueprint ──────────────────────────────────────────────
ml_oauth_bp = Blueprint('ml_oauth', __name__)

# ── Configuração (lidos de variáveis de ambiente OU do token manager) ──
# Defina no .env ou nas variáveis de ambiente do servidor:
#   ML_CLIENT_ID     = seu App ID
#   ML_CLIENT_SECRET = seu Secret Key
#   ML_REDIRECT_URI  = URL completa do callback (ex: https://app.com/mercadolivre/oauth/callback)

ML_AUTH_URL    = "https://auth.mercadolivre.com.br/authorization"
ML_TOKEN_URL   = "https://api.mercadolibre.com/oauth/token"
ML_API_ME      = "https://api.mercadolibre.com/users/me"


def _get_credentials(account_id=None):
    """
    Retorna (client_id, client_secret, redirect_uri) para a conta informada.
    Prioridade: conta no token_manager → variáveis de ambiente.
    """
    client_id     = None
    client_secret = None

    # Tenta buscar da conta no token_manager
    if account_id and account_id in ml_token_manager.accounts:
        account       = ml_token_manager.accounts[account_id]
        client_id     = account.get('app_id')
        client_secret = account.get('secret_key')
    elif ml_token_manager.current_account_id:
        account       = ml_token_manager.accounts.get(ml_token_manager.current_account_id, {})
        client_id     = account.get('app_id')
        client_secret = account.get('secret_key')

    # Fallback para variáveis de ambiente
    client_id     = client_id     or os.environ.get('ML_CLIENT_ID')
    client_secret = client_secret or os.environ.get('ML_CLIENT_SECRET')

    redirect_uri  = os.environ.get(
        'ML_REDIRECT_URI',
        'http://localhost:5000/mercadolivre/oauth/callback'
    )

    return client_id, client_secret, redirect_uri


# ── ROTA 1: Iniciar autenticação ───────────────────────────
@ml_oauth_bp.route('/mercadolivre/oauth/iniciar')
def oauth_iniciar():
    """
    Redireciona o usuário para a tela de autorização do Mercado Livre.

    Query params opcionais:
        account_id  – ID da conta no token_manager a ser autenticada
        account_name – nome amigável para criar conta nova (se account_id não existir)
    """
    account_id   = request.args.get('account_id')
    account_name = request.args.get('account_name', 'Conta Principal')

    # Cria conta no token_manager se ainda não existir
    if account_id and account_id not in ml_token_manager.accounts:
        account_id = None   # ignora ID inválido

    if not account_id:
        # Usa conta atual ou cria uma nova
        if ml_token_manager.current_account_id:
            account_id = ml_token_manager.current_account_id
        else:
            account_id = 'conta_principal'
            if account_id not in ml_token_manager.accounts:
                ml_token_manager.accounts[account_id] = {
                    'account_name': account_name,
                    'created_at':   datetime.now().isoformat(),
                    'is_active':    True,
                    'is_default':   True,
                }
            ml_token_manager.current_account_id = account_id
            ml_token_manager.save_to_database()

    client_id, client_secret, redirect_uri = _get_credentials(account_id)

    if not client_id or not client_secret:
        return jsonify({
            'erro': (
                'Client ID e Secret Key não configurados. '
                'Configure-os em Configurações → Mercado Livre antes de autenticar.'
            )
        }), 400

    # Salva account_id na sessão para usar no callback
    session['ml_oauth_account_id'] = account_id

    # Monta a URL de autorização
    auth_url = (
        f"{ML_AUTH_URL}"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
    )

    print(f"🔐 Redirecionando para OAuth ML: {auth_url}")
    return redirect(auth_url)


# ── ROTA 2: Callback (ML redireciona para cá após login) ──
@ml_oauth_bp.route('/mercadolivre/oauth/callback')
def oauth_callback():
    """
    Recebe o código de autorização do Mercado Livre e troca por tokens.
    O ML redireciona para esta URL com ?code=XXX após o usuário logar.
    """
    code  = request.args.get('code')
    error = request.args.get('error')

    if error:
        flash(f'Autenticação cancelada ou recusada pelo Mercado Livre: {error}', 'danger')
        return redirect(url_for('consultar_mercado_livre'))

    if not code:
        flash('Código de autorização não recebido.', 'danger')
        return redirect(url_for('consultar_mercado_livre'))

    # Recupera qual conta estava sendo autenticada
    account_id = session.pop('ml_oauth_account_id', ml_token_manager.current_account_id)

    client_id, client_secret, redirect_uri = _get_credentials(account_id)

    if not client_id or not client_secret:
        flash('Configuração incompleta. Defina Client ID e Secret Key.', 'danger')
        return redirect(url_for('consultar_mercado_livre'))

    # ── Troca code por tokens ──────────────────────────────
    print(f"🔄 Trocando código por tokens para conta: {account_id}")

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
            headers={'Accept': 'application/json',
                     'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=30,
        )

        if response.status_code != 200:
            erro_detalhe = response.json().get('error_description', response.text[:200])
            print(f"❌ Erro ao trocar código: {response.status_code} – {erro_detalhe}")
            flash(f'Erro na autenticação: {erro_detalhe}', 'danger')
            return redirect(url_for('consultar_mercado_livre'))

        token_data = response.json()
        access_token  = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_in    = token_data.get('expires_in', 21600)   # padrão 6h

        print(f"✅ Tokens recebidos! expires_in={expires_in}s")

        # ── Salva tokens na conta ──────────────────────────
        if account_id not in ml_token_manager.accounts:
            ml_token_manager.accounts[account_id] = {
                'account_name': 'Conta Principal',
                'created_at':   datetime.now().isoformat(),
                'is_active':    True,
                'is_default':   True,
            }

        account = ml_token_manager.accounts[account_id]
        account['app_id']        = client_id
        account['secret_key']    = client_secret
        account['access_token']  = access_token
        account['refresh_token'] = refresh_token
        account['expires_in']    = expires_in
        account['updated_at']    = datetime.now().isoformat()
        account['token_type']    = token_data.get('token_type', 'Bearer')
        account['scope']         = token_data.get('scope', '')

        # Busca dados do usuário (nickname, user_id)
        ml_token_manager.atualizar_dados_usuario(account_id)
        ml_token_manager.current_account_id = account_id
        ml_token_manager.save_to_database()

        nickname = account.get('nickname', 'desconhecido')
        flash(f'✅ Autenticado com sucesso! Conta: {nickname}', 'success')
        return redirect(url_for('consultar_mercado_livre'))

    except Exception as e:
        print(f"❌ Exceção no callback OAuth: {e}")
        flash(f'Erro interno na autenticação: {str(e)}', 'danger')
        return redirect(url_for('consultar_mercado_livre'))


# ── ROTA 3: Renovar token manualmente (opcional) ──────────
@ml_oauth_bp.route('/mercadolivre/oauth/renovar', methods=['POST'])
def oauth_renovar():
    """
    Força a renovação do access_token usando o refresh_token.
    Retorna JSON com sucesso/erro.
    """
    account_id = request.json.get('account_id') if request.is_json else None
    account_id = account_id or ml_token_manager.current_account_id

    if not account_id or account_id not in ml_token_manager.accounts:
        return jsonify({'sucesso': False, 'erro': 'Conta não encontrada'}), 404

    account       = ml_token_manager.accounts[account_id]
    refresh_token = account.get('refresh_token')

    if not refresh_token:
        return jsonify({'sucesso': False,
                        'erro': 'Refresh token não disponível. Re-autentique.'}), 400

    novo_token = ml_token_manager.refresh_token(account_id, refresh_token)

    if novo_token:
        return jsonify({'sucesso': True,
                        'mensagem': 'Token renovado com sucesso!',
                        'account_id': account_id})
    else:
        return jsonify({'sucesso': False,
                        'erro': 'Falha na renovação. Re-autentique via OAuth.'}), 400


# ── ROTA 4: Status da autenticação (JSON) ─────────────────
@ml_oauth_bp.route('/mercadolivre/oauth/status')
def oauth_status():
    """Retorna o status atual de autenticação de todas as contas."""
    contas = []
    for aid, acc in ml_token_manager.accounts.items():
        contas.append({
            'id':           aid,
            'nome':         acc.get('account_name', 'Sem nome'),
            'nickname':     acc.get('nickname'),
            'autenticada':  bool(acc.get('access_token')),
            'atual':        (aid == ml_token_manager.current_account_id),
            'atualizado_em': acc.get('updated_at'),
        })

    return jsonify({
        'sucesso': True,
        'conta_atual': ml_token_manager.current_account_id,
        'contas': contas,
    })


# ============================================================
# COMO INTEGRAR NO app.py
# ============================================================
# 1. Importe e registre o Blueprint:
#
#    from ml_oauth import ml_oauth_bp
#    app.register_blueprint(ml_oauth_bp)
#
# 2. No painel do Mercado Livre (https://developers.mercadolivre.com.br/devcenter):
#    - Adicione a URL de Redirect:
#      Produção: https://seudominio.com/mercadolivre/oauth/callback
#      Local:    http://localhost:5000/mercadolivre/oauth/callback
#
# 3. Defina as variáveis de ambiente (ou configure via interface):
#    ML_CLIENT_ID     = seu_app_id
#    ML_CLIENT_SECRET = seu_secret_key
#    ML_REDIRECT_URI  = http://localhost:5000/mercadolivre/oauth/callback
#
# 4. Adicione um botão na sua página para iniciar o OAuth:
#
#    <a href="/mercadolivre/oauth/iniciar" class="btn btn-warning">
#      🔐 Autenticar com Mercado Livre
#    </a>
#
# 5. Remova a rota /api/mercadolivre/autenticar do app.py (tokens manuais)
#    ou mantenha-a como fallback — o OAuth correto substituirá o fluxo.
# ============================================================