import sys
from pathlib import Path
import uuid
from flask import Flask, abort, current_app, make_response, render_template, request, send_from_directory, redirect, url_for, flash, jsonify
from gspread import service_account
import gspread
from models import Processo, db
from config import Config
import os
from datetime import datetime, timedelta
import pandas as pd
from werkzeug.utils import secure_filename
from processamento.cadastro_produto_web import executar_processamento
from processamento.extrair_atributos import extrair_atributos_processamento
from processamento.api_anymarket import atualizar_foto_anymarket, consultar_api_anymarket
from processamento.comparar_prazos import processar_comparacao
from processamento.google_sheets import ler_planilha_google
from log_utils import (
    registrar_processo,
    registrar_itens_processados,
    obter_historico_processos,
    contar_processos_hoje
)
from processamento.api_anymarket import (
    consultar_api_anymarket, 
    excluir_foto_anymarket, 
    excluir_fotos_planilha_anymarket
)
from utils.stats_utils import get_processing_stats, obter_dados_grafico_7dias
import logging
from logging.handlers import RotatingFileHandler
import processamento.validar_xml

# Adicione a raiz do projeto ao path do Python
sys.path.append(str(Path(__file__).parent))

# Agora importe o google_sheets_utils
from google_sheets_utils import (
    carregar_configuracao_google_sheets, 
    salvar_configuracao_google_sheets,
    listar_abas_google_sheets,
    testar_conexao_google_sheets
)
from processamento.api_anymarket import (
    consultar_api_anymarket, 
    excluir_foto_anymarket, 
    excluir_fotos_planilha_anymarket,
    definir_foto_principal_anymarket,
    reordenar_fotos_anymarket,
    atualizar_foto_anymarket
)

app = Flask(__name__)
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

@app.route("/testar-google")
def testar_google():
    try:
        from processamento.extrair_atributos import ler_planilha_google
        # Use uma planilha de teste pública do Google
        df = ler_planilha_google("1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms", "kitsparana")
        return f"Funcionou! Primeiros dados: {df.head().to_html()}"
    except Exception as e:
        return f"ERRO: {str(e)}"
    
@app.route('/')
def home():
    try:
        stats = get_processing_stats()
        dados_grafico = obter_dados_grafico_7dias()
        ultima_planilha, ultima_planilha_data = obter_ultima_planilha()
        
        # Debug - verifique os valores
        app.logger.info(f"Última planilha: {ultima_planilha}")
        app.logger.info(f"Dados gráfico: {dados_grafico}")
        
        return render_template(
            'home.html',
            total_processamentos=stats['total'],
            processos_sucesso=stats['sucessos_total'],
            processos_erro=stats['erros_total'],
            processamentos_hoje=stats['hoje'],
            hoje_sucesso=stats['sucessos_hoje'],
            hoje_erro=stats['erros_hoje'],
            ultima_execucao=stats['ultima'],
            ultima_planilha=ultima_planilha,
            ultima_planilha_data=ultima_planilha_data,
            datas_grafico=dados_grafico['datas'],
           # valores_grafico=dados_grafico['valores'],
            valores_grafico={
                'cadastro': dados_grafico['valores_cadastro'],
                'atributos': dados_grafico['valores_atributos'],
                'prazos': dados_grafico['valores_prazos']
            },
            total_itens_sucesso=stats['total_itens_sucesso'],
            total_itens_erro=stats['total_itens_erro'],
            now=datetime.now()
        )
    except Exception as e:
        app.logger.error(f"Erro na rota home: {str(e)}")
        return render_template('error.html'), 500

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

def contar_status_processos(log_file):
    """Conta processos por status em todo o arquivo de log"""
    sucesso = erro = 0
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if 'status: sucesso' in line.lower():
                    sucesso += 1
                elif 'status: erro' in line.lower():
                    erro += 1
    return sucesso, erro

def contar_processos_hoje_por_status(log_file):
    """Conta processos por status apenas no dia atual"""
    hoje = datetime.now().strftime('%Y-%m-%d')
    sucesso = erro = 0
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if hoje in line:
                    if 'status: sucesso' in line.lower():
                        sucesso += 1
                    elif 'status: erro' in line.lower():
                        erro += 1
    return sucesso, erro

def obter_dados_grafico_7dias():
    datas = []
    valores_cadastro = []
    valores_atributos = []
    valores_prazos = []
    
    for i in range(6, -1, -1):  # 7 dias (incluindo hoje)
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        datas.append(date.split('-')[2] + '/' + date.split('-')[1])  # Formato DD/MM
        
        # Contar processos por módulo para cada dia
        cadastro = Processo.query.filter(
            db.func.date(Processo.data) == date,
            Processo.modulo == 'cadastro'
        ).count()
        
        atributos = Processo.query.filter(
            db.func.date(Processo.data) == date,
            Processo.modulo == 'atributos'
        ).count()
        
        prazos = Processo.query.filter(
            db.func.date(Processo.data) == date,
            Processo.modulo == 'prazos'
        ).count()
        
        valores_cadastro.append(cadastro)
        valores_atributos.append(atributos)
        valores_prazos.append(prazos)
    
    return {
        'datas': datas,
        'valores_cadastro': valores_cadastro,
        'valores_atributos': valores_atributos,
        'valores_prazos': valores_prazos
    }

def contar_processos_por_dia(date):
    log_file = 'logs/processos/cadastro.log'
    count = 0
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if date in line:
                    count += 1
    return count

def registrar_produtos(produtos_processados):
    """Registra os produtos processados em arquivo separado"""
    data_dir = datetime.now().strftime("%Y-%m-%d")
    hora_dir = datetime.now().strftime("%H-%M-%S")
    log_dir = f"logs/produtos/{data_dir}/{hora_dir}"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = f"{log_dir}/execucao_{str(uuid.uuid4())[:8]}.log"
    with open(log_file, "w", encoding="utf-8") as f:
        for produto in produtos_processados:
            f.write(f"{produto['nome']} - {produto['ean']} - {produto['status']}\n")
    return log_file

@app.route("/consultar-anymarket", methods=["GET", "POST"])
def consultar_anymarket():
    resultado = None
    acao = None
    
    if request.method == "POST":
        acao = request.form.get('action', 'consultar')
        
        if acao == 'consultar':
            try:
                product_id = request.form.get('product_id', '').strip()
                api_token = request.form.get('api_token', '').strip() or None
                
                if not product_id:
                    flash("ID do produto é obrigatório", "danger")
                    return redirect(url_for('consultar_anymarket'))
                
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
        resultado=resultado,
        acao=acao,
        historico_processos=obter_historico_processos("anymarket"),
        processos_hoje=contar_processos_hoje("anymarket"),
        stats=get_processing_stats("anymarket")
    )

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

@app.route("/definir-foto-principal", methods=["POST"])
def definir_foto_principal_route():
    """API para definir uma foto como principal"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        photo_id = data.get('photo_id')
        
        if not product_id or not photo_id:
            return jsonify({'sucesso': False, 'erro': 'ID do produto e da foto são obrigatórios'}), 400
        
        resultado = definir_foto_principal_anymarket(product_id, photo_id)
        
        registrar_processo(
            modulo="anymarket_principal",
            qtd_itens=1,
            tempo_execucao=0,
            status="sucesso" if resultado.get('sucesso') else "erro",
            erro_mensagem=resultado.get('erro') if not resultado.get('sucesso') else None
        )
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@app.route("/reordenar-fotos", methods=["POST"])
def reordenar_fotos_route():
    """API para reordenar fotos de um produto"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        nova_ordem = data.get('nova_ordem', [])
        
        if not product_id:
            return jsonify({'sucesso': False, 'erro': 'ID do produto é obrigatório'}), 400
        
        if not nova_ordem:
            return jsonify({'sucesso': False, 'erro': 'Nova ordem não especificada'}), 400
        
        resultado = reordenar_fotos_anymarket(product_id, nova_ordem)
        
        registrar_processo(
            modulo="anymarket_reordenar",
            qtd_itens=len(nova_ordem),
            tempo_execucao=0,
            status="sucesso" if resultado.get('sucesso') else "erro",
            erro_mensagem=resultado.get('erro') if not resultado.get('sucesso') else None
        )
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500
    
@app.route("/atualizar-foto-anymarket", methods=["POST"])
def atualizar_foto_anymarket_route():
    """API para atualizar índice e status principal de uma foto"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        photo_id = data.get('photo_id')
        index = data.get('index')
        main = data.get('main', False)
        
        if not product_id or not photo_id or index is None:
            return jsonify({'sucesso': False, 'erro': 'ID do produto, ID da foto e índice são obrigatórios'}), 400
        
        resultado = atualizar_foto_anymarket(product_id, photo_id, index, main)
        
        registrar_processo(
            modulo="anymarket_atualizar",
            qtd_itens=1,
            tempo_execucao=0,
            status="sucesso" if resultado.get('sucesso') else "erro",
            erro_mensagem=resultado.get('erro') if not resultado.get('sucesso') else None
        )
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500
    
    
@app.route("/testar-endpoints-anymarket")
def testar_endpoints_anymarket_route():
    """Rota para testar quais endpoints são suportados"""
    product_id = request.args.get('product_id', '347730532')
    photo_id = request.args.get('photo_id', '')
    
    if not photo_id:
        return jsonify({'erro': 'ID da foto é necessário'}), 400
    
    from processamento.api_anymarket import testar_endpoints_anymarket
    resultado = testar_endpoints_anymarket(product_id, photo_id)
    
    return jsonify(resultado)


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
                    aba_ativa="google"
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
                    preview_data=preview_data
                )

            # ====================================
            # 🔹 PROCESSAR (GOOGLE SHEETS)
            # ====================================
            elif action_type == "conectar_google":
                sheet_id = request.form.get('sheet_id', '').strip()
                aba_nome = request.form.get('aba_nome', '').strip()

                if not sheet_id or not aba_nome:
                    flash("ID da planilha e aba são obrigatórios", "danger")
                    return redirect(url_for("preencher_planilha", aba="google"))

                salvar_configuracao_google_sheets(sheet_id, aba_nome)
                config = carregar_configuracao_google_sheets()

                # precisa do template destino
                destino = request.files.get("arquivo_destino")
                if not destino or destino.filename == "":
                    flash("Envie também o arquivo de destino (template)", "danger")
                    return redirect(url_for("preencher_planilha", aba="google"))

                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                nome_destino = secure_filename(destino.filename)
                caminho_destino = os.path.join(app.config['UPLOAD_FOLDER'], nome_destino)
                destino.save(caminho_destino)

                # Processa
                arquivo_saida, qtd_produtos, tempo_segundos, produtos_processados = executar_processamento(
                    {"sheet_id": sheet_id, "aba": aba_nome},
                    caminho_destino
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
            # 🔹 PROCESSAR (UPLOAD LOCAL)
            # ====================================
            elif 'arquivo_origem' in request.files and 'arquivo_destino' in request.files:
                origem = request.files["arquivo_origem"]
                destino = request.files["arquivo_destino"]

                if origem.filename == '' or destino.filename == '':
                    flash("Nenhum arquivo selecionado", "danger")
                    registrar_processo(
                        modulo="cadastro",
                        qtd_itens=0,
                        tempo_execucao=0,
                        status="erro",
                        erro_mensagem="Nenhum arquivo selecionado"
                    )
                    return redirect(url_for("preencher_planilha", aba="upload"))

                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

                nome_origem = secure_filename(origem.filename)
                nome_destino = secure_filename(destino.filename)
                caminho_origem = os.path.join(app.config['UPLOAD_FOLDER'], nome_origem)
                caminho_destino = os.path.join(app.config['UPLOAD_FOLDER'], nome_destino)

                origem.save(caminho_origem)
                destino.save(caminho_destino)

                arquivo_saida, qtd_produtos, tempo_segundos, produtos_processados = executar_processamento(
                    caminho_origem, caminho_destino
                )

                nome_arquivo_saida = os.path.basename(arquivo_saida)

                registrar_processo(
                    modulo="cadastro",
                    qtd_itens=qtd_produtos,
                    tempo_execucao=tempo_segundos,
                    status="sucesso"
                )
                registrar_itens_processados("cadastro", produtos_processados)

                flash("Planilha preenchida com sucesso!", "success")
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
        historico_processos=obter_historico_processos("cadastro"),
        processos_hoje=contar_processos_hoje("cadastro"),
        stats=get_processing_stats("cadastro"),
        nome_arquivo_saida=nome_arquivo_saida,
        config=config,
        abas=abas,
        sheet_id_input=sheet_id_input,
        aba_selecionada=aba_selecionada,
        aba_ativa=aba_ativa,
        preview_data=preview_data
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
        historico_processos=obter_historico_processos("atributos"),
        processos_hoje=contar_processos_hoje("atributos"),
        stats=get_processing_stats("atributos"),
        nome_arquivo_saida=nome_arquivo_saida,
        config=config,
        abas=abas,
        preview_data=preview_data,
        sheet_id_input=sheet_id_input,
        aba_selecionada=aba_selecionada,
        aba_ativa=aba_ativa
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
        historico_processos=obter_historico_processos("prazos"),
        processos_hoje=contar_processos_hoje("prazos"),
        stats=get_processing_stats("prazos")  # Agora aceita o parâmetro
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
        config=config,
        abas=abas,
        mensagem=mensagem,
        tipo_mensagem=tipo_mensagem,
        erro=erro
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

if __name__ == "__main__":
    app.run(debug=True)