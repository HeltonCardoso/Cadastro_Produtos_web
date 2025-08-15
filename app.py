import uuid
from flask import Flask, abort, render_template, request, send_from_directory, redirect, url_for, flash, jsonify
from models import db
from config import Config
import os
from datetime import datetime, timedelta
import pandas as pd
from werkzeug.utils import secure_filename
from processamento.cadastro_produto_web import executar_processamento
from processamento.extrair_atributos import extrair_atributos_processamento
from processamento.comparar_prazos import processar_comparacao
from log_utils import (
    registrar_processo,
    registrar_itens_processados,
    obter_historico_processos,
    contar_processos_hoje
)
from utils.stats_utils import get_processing_stats, obter_dados_grafico_7dias
import logging
from logging.handlers import RotatingFileHandler

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
            valores_grafico=dados_grafico['valores'],
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
    """Retorna dados formatados de forma segura para o template"""
    datas = []
    valores = []
    
    for i in range(6, -1, -1):  # 7 dias (incluindo hoje)
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        count = contar_processos_por_dia(date)
        datas.append(date.split('-')[2] + '/' + date.split('-')[1])  # Formato DD/MM
        valores.append(count)
    
    return {
        'datas': datas,  # Lista simples não precisa de json.dumps
        'valores': valores
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


@app.route("/preencher-planilha", methods=["GET", "POST"])
def preencher_planilha():
    nome_arquivo_saida = None  # Inicializa como None

    if request.method == "POST":
        try:
            if 'arquivo_origem' not in request.files or 'arquivo_destino' not in request.files:
                flash("Nenhum arquivo enviado", "danger")
                registrar_processo(
                    modulo="cadastro",
                    qtd_itens=0,
                    tempo_execucao=0,
                    status="erro",
                    erro_mensagem="Nenhum arquivo enviado"
                )
                return redirect(url_for("preencher_planilha"))
            
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
                return redirect(url_for("preencher_planilha"))

            # Garante que o diretório de upload existe
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            nome_origem = secure_filename(origem.filename)
            nome_destino = secure_filename(destino.filename)
            caminho_origem = os.path.join(app.config['UPLOAD_FOLDER'], nome_origem)
            caminho_destino = os.path.join(app.config['UPLOAD_FOLDER'], nome_destino)
            
            origem.save(caminho_origem)
            destino.save(caminho_destino)

            # Processa os arquivos
            arquivo_saida, qtd_produtos, tempo_segundos, produtos_processados = executar_processamento(
                caminho_origem, caminho_destino
            )
            
            # Obtém apenas o nome do arquivo de saída
            nome_arquivo_saida = os.path.basename(arquivo_saida)
            
            # Registra o processo
            processo_id = registrar_processo(
                modulo="cadastro",
                qtd_itens=qtd_produtos,
                tempo_execucao=tempo_segundos,
                status="sucesso"
            )
            
            # Registra os itens processados
            registrar_itens_processados("cadastro", produtos_processados)
            
            flash("Planilha preenchida com sucesso!", "success")

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
            return redirect(url_for("preencher_planilha"))
    
    return render_template(
        "preencher_planilha.html",
        historico_processos=obter_historico_processos("cadastro"),
        processos_hoje=contar_processos_hoje("cadastro"),
        stats=get_processing_stats("cadastro"),
        nome_arquivo_saida=nome_arquivo_saida  # Passa o nome do arquivo para o template
    )

@app.route("/extrair-atributos", methods=["GET", "POST"])
def extrair_atributos():
    nome_arquivo_saida = None
    
    try:
        if request.method == "POST":
            if 'arquivo' not in request.files:
                flash("Nenhum arquivo enviado", "danger")
                registrar_processo(
                    modulo="atributos",
                    qtd_itens=0,
                    tempo_execucao=0,
                    status="erro",
                    erro_mensagem="Nenhum arquivo enviado"
                )
                return redirect(url_for("extrair_atributos"))
            
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
                return redirect(url_for("extrair_atributos"))

            # Garante que o diretório existe
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            nome_arquivo = secure_filename(arquivo.filename)
            caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
            arquivo.save(caminho_arquivo)

            # Processa o arquivo
            arquivo_saida, qtd_produtos, tempo_segundos, produtos_processados = extrair_atributos_processamento(
                caminho_arquivo
            )
            
            nome_arquivo_saida = os.path.basename(arquivo_saida)
            
            # Registra o processo
            registrar_processo(
                modulo="atributos",
                qtd_itens=qtd_produtos,
                tempo_execucao=tempo_segundos,
                status="sucesso"
            )
            
            flash("Extração concluída com sucesso!", "success")
        
        # Obter histórico (GET ou POST com sucesso)
        historico = obter_historico_processos("atributos")
        
        return render_template(
            "extrair_atributos.html",
            historico_processos=historico,
            processos_hoje=contar_processos_hoje("atributos"),
            stats=get_processing_stats("atributos"),
            nome_arquivo_saida=nome_arquivo_saida
        )
        
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
        return redirect(url_for("extrair_atributos"))

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

if __name__ == "__main__":
    app.run(debug=True)