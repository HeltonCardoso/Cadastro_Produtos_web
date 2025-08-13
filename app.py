from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash
import os
import pandas as pd
from datetime import datetime, timedelta
import json
from werkzeug.utils import secure_filename
from processamento.cadastro_produto_web import executar_processamento
from processamento.extrair_atributos import extrair_atributos_processamento
from processamento.comparar_prazos import processar_comparacao
from datetime import datetime
from logging.handlers import RotatingFileHandler
from flask import jsonify
from datetime import datetime
from logging_config import configure_loggers, get_logger
import uuid
from log_utils import (
    registrar_processo,
    registrar_itens_processados,
    obter_historico_processos,
    contar_processos_hoje
)


# Configura os loggers
configure_loggers()

app = Flask(__name__)
app.secret_key = "helton-segredo"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# No início do app.py, após as configurações
os.makedirs("logs/processos", exist_ok=True)
os.makedirs("logs/itens/cadastro", exist_ok=True)
os.makedirs("logs/itens/atributos", exist_ok=True)
os.makedirs("logs/itens/prazos", exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Rotas atualizadas com loggers específicos
@app.route("/uploads/<filename>")
def baixar_arquivo(filename):
    """Rota para download de arquivos - DEVE ESTAR SEMPRE ATIVA"""
    return send_from_directory(
        directory=app.config['UPLOAD_FOLDER'],
        path=filename,
        as_attachment=True
    )

@app.route('/')
def home():
    logger = get_logger('main')
    
    # Estatísticas básicas
    log_path = 'logs/processos/cadastro.log'
    stats = get_processing_stats(log_path)
    
    # Contagem de sucessos/erros
    processos_sucesso, processos_erro = contar_status_processos(log_path)
    
    # Contagem de hoje
    hoje_sucesso, hoje_erro = contar_processos_hoje_por_status(log_path)
    
    # Última planilha processada
    ultima_planilha, ultima_planilha_data = obter_ultima_planilha()
    
    # Dados para gráficos (agora com tratamento seguro)
    dados_grafico = obter_dados_grafico_7dias()
    
    return render_template('home.html',
        total_processamentos=stats['total'],
        processamentos_hoje=stats['hoje'],
        ultima_execucao=stats['ultima'],
        processos_sucesso=processos_sucesso,
        processos_erro=processos_erro,
        hoje_sucesso=hoje_sucesso,
        hoje_erro=hoje_erro,
        ultima_planilha=ultima_planilha,
        ultima_planilha_data=ultima_planilha_data,
        datas_grafico=dados_grafico['datas'],  # Já convertido para lista segura
        valores_grafico=dados_grafico['valores'],  # Já convertido para lista segura
        now=datetime.now())

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

def obter_ultima_planilha():
    upload_folder = app.config['UPLOAD_FOLDER']
    planilhas = []
    
    for root, _, files in os.walk(upload_folder):
        for file in files:
            if file.lower().endswith(('.xlsx', '.xls')):
                path = os.path.join(root, file)
                planilhas.append((path, os.path.getmtime(path)))
    
    if planilhas:
        ultima = max(planilhas, key=lambda x: x[1])
        return (ultima[0], datetime.fromtimestamp(ultima[1]).strftime('%d/%m/%Y %H:%M'))
    return (None, None)

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

def get_processing_stats(log_path):
    stats = {'total': 0, 'hoje': 0, 'ultima': "—"}
    
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            linhas = f.readlines()
            stats['total'] = len(linhas)
            if linhas:
                stats['ultima'] = linhas[-1].strip()
            hoje_str = datetime.now().strftime('%Y-%m-%d')
            stats['hoje'] = sum(1 for l in linhas if hoje_str in l)
    
    return stats

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
    logger = get_logger('cadastro')
    
    if request.method == "POST":
        try:
            # Verifica se arquivos foram enviados
            if 'arquivo_origem' not in request.files or 'arquivo_destino' not in request.files:
                flash("Nenhum arquivo enviado", "danger")
                return redirect(url_for("preencher_planilha"))
                
            origem = request.files["arquivo_origem"]
            destino = request.files["arquivo_destino"]

            # Validação básica dos arquivos
            if origem.filename == '' or destino.filename == '':
                flash("Nenhum arquivo selecionado", "danger")
                return redirect(url_for("preencher_planilha"))

            # Processamento seguro dos nomes
            nome_origem = secure_filename(origem.filename)
            nome_destino = secure_filename(destino.filename)
            caminho_origem = os.path.join(app.config["UPLOAD_FOLDER"], nome_origem)
            caminho_destino = os.path.join(app.config["UPLOAD_FOLDER"], nome_destino)

            # Garante que a pasta de upload existe
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            
            # Salva os arquivos
            origem.save(caminho_origem)
            destino.save(caminho_destino)
            logger.info(f"Iniciando processamento para arquivos: {nome_origem} e {nome_destino}")

            try:
                # Processamento principal
                resultado, qtd_produtos, tempo_segundos, produtos_processados = executar_processamento(
                    caminho_origem, 
                    caminho_destino
                )
            except Exception as process_error:
                # Tratamento especial para erros de colunas faltantes
                error_msg = str(process_error)
                if "faltando as seguintes colunas" in error_msg:
                    colunas_faltando = error_msg.split(":")[1].strip()
                    error_msg = f"Planilha fora do padrão. Colunas faltantes: {colunas_faltando}"
                
                logger.error(f"Erro no processamento: {error_msg}")
                raise ValueError(error_msg) from process_error

            # Registro do processamento
            registrar_processo(
                modulo="cadastro",
                qtd_itens=qtd_produtos,
                tempo_execucao=tempo_segundos,
                status="sucesso"
            )
            
            # Registro dos produtos
            try:
                registrar_produtos(produtos_processados)
            except Exception as e:
                logger.error(f"Erro ao registrar produtos: {str(e)}")

            # Carrega logs para exibição (área reduzida)
            log_processamento = "Sem registros de log"
            log_path = 'uploads/logs_processamento.txt'
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8') as f:
                    log_lines = f.readlines()[-3:]  # Pega apenas as últimas 3 linhas
                    log_processamento = "<br>".join(line.strip() for line in log_lines)

            # Carrega histórico (apenas sucessos)
            historico_processos = []
            hist_path = 'logs/processos/cadastro.log'
            if os.path.exists(hist_path):
                with open(hist_path, 'r', encoding='utf-8') as f:
                    historico_processos = [
                        line.strip() for line in f.readlines()[-10:] 
                        if "status: sucesso" in line.lower()
                    ]

            flash("✅ Planilha processada com sucesso!", "success")
            return render_template("preencher_planilha.html",
                                resultado=f"{qtd_produtos} produtos processados",
                                log=log_processamento,
                                historico_processos=historico_processos,
                                arquivo_gerado=os.path.basename(resultado),
                                qtd_produtos=qtd_produtos,
                                tempo_processamento=format_time(tempo_segundos))

        except ValueError as ve:
            # Erros conhecidos/esperados
            flash(f"ERRO: {str(ve)}", "danger")
            return redirect(url_for("preencher_planilha"))
            
        except Exception as e:
            # Erros inesperados
            logger.critical(f"Erro crítico: {str(e)}", exc_info=True)
            flash("Ocorreu um erro interno durante o processamento", "danger")
            return redirect(url_for("preencher_planilha"))
    
    # GET request
    return render_template("preencher_planilha.html",
                         historico_processos=obter_historico_processos("cadastro"),
                         processos_hoje=contar_processos_hoje("cadastro"))

@app.route("/extrair-atributos", methods=["GET", "POST"])
def extrair_atributos():
    logger = get_logger('atributos')
    
    if request.method == "POST":
        try:
            arquivo = request.files['arquivo']
            
            # Validação do arquivo
            if not arquivo or arquivo.filename == '':
                raise ValueError("Nenhum arquivo selecionado")
                
            if not arquivo.filename.lower().endswith(('.xlsx', '.xls')):
                raise ValueError("Apenas arquivos Excel são aceitos")

            # Processamento
            nome_arquivo = secure_filename(arquivo.filename)
            caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
            os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
            arquivo.save(caminho_arquivo)
            
            logger.info(f"Iniciando extração de atributos: {nome_arquivo}")
            resultado, qtd_itens, tempo_segundos, itens_processados = extrair_atributos_processamento(caminho_arquivo)
            
            # Registrar processo
            registrar_processo(
                modulo="atributos",
                qtd_itens=qtd_itens,
                tempo_execucao=tempo_segundos
            )
            
            # Registrar itens processados
            registrar_itens_processados(
                modulo="atributos",
                itens=itens_processados,
                campos=['ean', 'nome', 'atributos_extraidos', 'status']
            )
            
            # Preparar logs para exibição (últimas 6 linhas)
            log_content = []
            try:
                with open('uploads/logs_atributos.txt', 'r', encoding='utf-8') as f:
                    log_content = f.read().splitlines()[-6:]  # Últimas 6 linhas
            except FileNotFoundError:
                log_content = ["Nenhum log disponível"]
            
            log_formatted = "<br>".join(log_content)
            
            # Carregar histórico
            historico_processos = obter_historico_processos("atributos")
            
            flash("✅ Atributos extraídos com sucesso!", "success")
            return render_template("extrair_atributos.html",
                                historico_processos=historico_processos,
                                qtd_itens=qtd_itens,
                                tempo_processamento=format_time(tempo_segundos),
                                arquivo_gerado=os.path.basename(resultado),
                                log=log_formatted)  # Adicionado parâmetro log
            
        except Exception as e:
            # Registrar erro
            registrar_processo(
                modulo="atributos",
                qtd_itens=0,
                tempo_execucao=0,
                status=f"ERRO: {str(e)}"
            )
            
            # Preparar log de erro
            log_content = [f"ERRO: {str(e)}"]
            try:
                with open('uploads/logs_atributos.txt', 'a', encoding='utf-8') as f:
                    f.write(f"\nERRO: {str(e)}")
                with open('uploads/logs_atributos.txt', 'r', encoding='utf-8') as f:
                    log_content = f.read().splitlines()[-6:]
            except:
                pass
                
            flash(f"Erro: {str(e)}", "danger")
            return render_template("extrair_atributos.html",
                                historico_processos=obter_historico_processos("atributos"),
                                log="<br>".join(log_content),
                                qtd_itens=0)
    
    # GET request - mostrar histórico
    historico_processos = obter_historico_processos("atributos")
    return render_template("extrair_atributos.html",
                         historico_processos=historico_processos,
                         processos_hoje=contar_processos_hoje("atributos"),
                         log="Aguardando processamento...")

@app.route('/comparar-prazos', methods=['GET', 'POST'])
def comparar_prazos():
    logger = get_logger('prazos')
     
    if request.method == 'POST':
        try:
            arquivo_erp = request.files['arquivo_erp']
            arquivo_marketplace = request.files['arquivo_marketplace']
            
            logger.info("Iniciando comparação de prazos")
            
            # 1. Recebemos o dicionário completo
            resultado = processar_comparacao(
                arquivo_erp, 
                arquivo_marketplace, 
                app.config['UPLOAD_FOLDER']
            )
            if not resultado['sucesso']:
                raise ValueError(resultado.get('erro', 'Erro desconhecido no processamento'))
            
            # 2. Extraímos os dados que precisamos
            qtd_itens = resultado['total_itens']
            tempo_segundos = 0  # Você pode calcular o tempo real se necessário
            
            itens_processados = []
            if resultado.get('divergencias', 0) > 0:
                # Lê o arquivo gerado para obter os itens
                df = pd.read_excel(os.path.join(app.config['UPLOAD_FOLDER'], resultado['arquivo']))
                itens_processados = [{
                    'ean': str(row['COD_COMPARACAO']),
                    'prazo_erp': row['DIAS_PRAZO_ERP'],
                    'prazo_marketplace': row['DIAS_PRAZO_MARKETPLACE'],
                    'diferenca': row['DIFERENCA_PRAZO'],
                    'status': 'divergente' if row['DIFERENCA_PRAZO'] != 0 else 'ok'
                } for _, row in df.iterrows()]
            else:
                # Adiciona um item vazio quando não há divergências
                itens_processados = [{
                    'ean': 'N/A',
                    'prazo_erp': 0,
                    'prazo_marketplace': 0,
                    'diferenca': 0,
                    'status': 'ok'
                }]
            
            # Registro de logs
            registrar_processo(
                modulo="prazos",
                qtd_itens=qtd_itens,
                tempo_execucao=tempo_segundos
            )
            
            # Registrar itens processados
            registrar_itens_processados(
                modulo="prazos",
                itens=itens_processados,
                campos=['ean', 'prazo_erp', 'prazo_marketplace', 'diferenca', 'status']
            )
            
            # Retorno JSON atualizado
            return jsonify({
                'status': 'success',
                'arquivo': resultado['arquivo'],
                'total_itens': qtd_itens,
                'divergencias': resultado['divergencias'],
                'log': resultado['log'],
                'resumo': resultado['resumo'],
                'marketplace': resultado['marketplace'],
                'historico': obter_historico_processos("prazos", 5),
                'processos_hoje': contar_processos_hoje("prazos")
            })
            
        except Exception as e:
            registrar_processo(
                modulo="prazos",
                qtd_itens=0,
                tempo_execucao=0,
                status=f"ERRO: {str(e)}"
            )
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    # GET request
    return render_template('comparar_prazos.html',
                         historico_processos=obter_historico_processos("prazos"),
                         processos_hoje=contar_processos_hoje("prazos"))

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