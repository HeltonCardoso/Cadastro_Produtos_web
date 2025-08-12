from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash
import os
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
@app.route('/')
def home():
    logger = get_logger('main')
    logger.info("Acessando página home")
    
    log_path = 'logs/cadastro.log'
    stats = get_processing_stats(log_path)
    
    return render_template('home.html',
                         total_processamentos=stats['total'],
                         processamentos_hoje=stats['hoje'],
                         ultima_execucao=stats['ultima'],
                         now=datetime.now())

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

def registrar_processo(qtd_produtos, tempo_execucao, usuario="Sistema"):
    """Registra uma execução no log de processos"""
    log_dir = "logs/processos"
    os.makedirs(log_dir, exist_ok=True)
    
    with open(f"{log_dir}/cadastro.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {usuario} - {qtd_produtos} produtos - {tempo_execucao:.2f}s\n")

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
            origem = request.files["arquivo_origem"]
            destino = request.files["arquivo_destino"]

            # Validação e processamento
            nome_origem = secure_filename(origem.filename)
            nome_destino = secure_filename(destino.filename)
            caminho_origem = os.path.join(app.config["UPLOAD_FOLDER"], nome_origem)
            caminho_destino = os.path.join(app.config["UPLOAD_FOLDER"], nome_destino)

            origem.save(caminho_origem)
            destino.save(caminho_destino)
            logger.info(f"Iniciando processamento para arquivos: {nome_origem} e {nome_destino}")

            # Agora recebe 4 valores de retorno
            resultado, qtd_produtos, tempo_segundos, produtos_processados = executar_processamento(caminho_origem, caminho_destino)
            
            # Registrar o processo (execução completa)
            registrar_processo(qtd_produtos, tempo_segundos)
            
            # Registrar produtos individualmente
            registrar_produtos(produtos_processados)
            
            # Carregar logs para exibição
            with open('uploads/logs_processamento.txt', 'r', encoding='utf-8') as f:
                log_processamento = f.read().replace('\n', '<br>')
            
            # Carregar resumo de processos
            with open('logs/processos/cadastro.log', 'r', encoding='utf-8') as f:
                historico_processos = f.read().splitlines()[-10:]  # Últimas 10 execuções

            flash("✅ Planilha processada com sucesso!", "success")
            return render_template("preencher_planilha.html",
                                resultado="Processado com sucesso!",
                                log=log_processamento,
                                historico_processos=historico_processos,
                                arquivo_gerado=os.path.basename(resultado),
                                qtd_produtos=qtd_produtos,
                                tempo_processamento=format_time(tempo_segundos))

        except Exception as e:
            # Registrar erro no log de processos
            registrar_processo(0, 0, f"ERRO: {str(e)}")
            flash(f"ERRO: {str(e)}", "danger")
            return redirect(url_for("preencher_planilha"))
    
    return render_template("preencher_planilha.html")

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
            
            # Registro de logs
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
            
            # Carregar histórico
            historico_processos = obter_historico_processos("atributos")
            
            flash("Atributos extraídos com sucesso!", "success")
            return render_template("extrair_atributos.html",
                                historico_processos=historico_processos,
                                qtd_itens=qtd_itens,
                                tempo_processamento=format_time(tempo_segundos),
                                arquivo_gerado=os.path.basename(resultado))
            
        except Exception as e:
            registrar_processo(
                modulo="atributos",
                qtd_itens=0,
                tempo_execucao=0,
                status=f"ERRO: {str(e)}"
            )
            flash(f"Erro: {str(e)}", "danger")
    
    # GET request - mostrar histórico
    historico_processos = obter_historico_processos("atributos")
    return render_template("extrair_atributos.html",
                         historico_processos=historico_processos,
                         processos_hoje=contar_processos_hoje("atributos"))

@app.route('/comparar-prazos', methods=['GET', 'POST'])
def comparar_prazos():
    logger = get_logger('prazos')
    itens_comparados = []
    
    if request.method == 'POST':
        try:
            arquivo_erp = request.files['arquivo_erp']
            arquivo_marketplace = request.files['arquivo_marketplace']
            
            logger.info("Iniciando comparação de prazos")
            resultado, qtd_itens, tempo_segundos, itens_processados = processar_comparacao(
                arquivo_erp, 
                arquivo_marketplace, 
                app.config['UPLOAD_FOLDER']
            )
            
            # Registro de logs
            registrar_processo(
                modulo="prazos",
                qtd_itens=qtd_itens,
                tempo_execucao=tempo_segundos
            )
            
            # Registrar itens processados
            itens_processados = [{
                'ean': item['ean'],  # Adapte com seus campos
                'prazo_erp': item['prazo_erp'],
                'prazo_marketplace': item['prazo_marketplace'],
                'diferenca': item['diferenca'],
                'status': 'sucesso'
            } for item in itens_processados]  # Adapte com sua variável
            
            registrar_itens_processados(
                modulo="prazos",
                itens=itens_processados,
                campos=['ean', 'prazo_erp', 'prazo_marketplace', 'diferenca', 'status']
            )
            
            return jsonify({
                'status': 'success',
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

@app.route("/uploads/<filename>")
def baixar_arquivo(filename):
    """Rota para download de arquivos"""
    return send_from_directory(
        directory=app.config['UPLOAD_FOLDER'],
        path=filename,
        as_attachment=True
    )

# Funções auxiliares
def format_time(seconds):

    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}m {seconds}s"

def contar_processos_hoje(modulo="cadastro"):
    hoje = datetime.now().strftime("%Y-%m-%d")
    count = 0
    log_file = f"logs/processos/{modulo}.log"  # Usa o módulo para determinar o arquivo
    
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith(hoje):
                    count += 1
    return count

@app.context_processor
def inject_stats():
    return {
        'count_processos_hoje': contar_processos_hoje(),
        'now': datetime.now()
    }

def registrar_processo(qtd_produtos, tempo_execucao, status="sucesso"):
    """Registra uma execução no log de processos"""
    log_dir = "logs/processos"
    os.makedirs(log_dir, exist_ok=True)
    
    with open(f"{log_dir}/cadastro.log", "a", encoding="utf-8") as f:
        f.write(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
            f"Produtos: {qtd_produtos} | "
            f"Tempo: {tempo_execucao:.2f}s | "
            f"Status: {status}\n"
        )

def registrar_produtos(produtos):
    """Registra os produtos processados em arquivo por data"""
    data_dir = datetime.now().strftime("%Y-%m-%d")
    log_dir = f"logs/produtos/{data_dir}"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = f"{log_dir}/processamento_{datetime.now().strftime('%H%M%S')}.log"
    
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"=== Processamento em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} ===\n")
        f.write(f"Total de produtos: {len(produtos)}\n\n")
        f.write("Lista de produtos:\n")
        for produto in produtos:
            f.write(f"{produto['ean']} - {produto['nome']}\n")
    
    return log_file

def format_time(seconds):
    """Formata segundos em minutos e segundos"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}m {seconds}s"

if __name__ == "__main__":
    app.run(debug=True)