# google_sheets_utils.py - CORRIJA O NOME DA FUNÇÃO
import json
from pathlib import Path
from datetime import datetime
from flask import current_app
import gspread
from google.oauth2 import service_account

def carregar_configuracao_google_sheets():  # CORRIGIDO: 'carregar' em vez de 'carregar'
    """Carrega a configuração do Google Sheets do arquivo JSON"""
    config_file = Path('config/google_sheets_config.json')
    
    config_padrao = {
        'sheet_id': '',
        'aba_nome': '',
        'ultima_atualizacao': None
    }
    
    if not config_file.exists():
        return config_padrao
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # Garante que todas as chaves existam
        for key in config_padrao.keys():
            if key not in config:
                config[key] = config_padrao[key]
                
        return config
        
    except Exception as e:
        if current_app:
            current_app.logger.error(f"Erro ao ler configuração Google Sheets: {str(e)}")
        else:
            print(f"Erro ao ler configuração Google Sheets: {str(e)}")
        return config_padrao

def salvar_configuracao_google_sheets(sheet_id, aba_nome):
    """Salva a configuração do Google Sheets em arquivo JSON"""
    config_dir = Path('config')
    config_dir.mkdir(exist_ok=True)  # Corrigido: mkdir em vez de mkdir
    
    config = {
        'sheet_id': sheet_id,
        'aba_nome': aba_nome,
        'ultima_atualizacao': datetime.now().isoformat()
    }
    
    try:
        with open(config_dir / 'google_sheets_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        if current_app:
            current_app.logger.error(f"Erro ao salvar configuração Google Sheets: {str(e)}")
        else:
            print(f"Erro ao salvar configuração Google Sheets: {str(e)}")
        return False

def listar_abas_google_sheets(sheet_id):
    """Lista todas as abas disponíveis em uma planilha do Google Sheets"""
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
        
        abas = []
        for worksheet in planilha.worksheets():
            abas.append({
                'id': worksheet.id,
                'title': worksheet.title,
                'row_count': worksheet.row_count,
                'col_count': worksheet.col_count
            })
        
        return abas
        
    except Exception as e:
        if current_app:
            current_app.logger.error(f"Erro ao listar abas: {str(e)}")
        else:
            print(f"Erro ao listar abas: {str(e)}")
        raise Exception(f"Erro ao conectar com Google Sheets: {str(e)}")

def obter_dados_aba(sheet_id, aba_nome, limite_linhas=5):
    """Obtém os primeiros dados de uma aba específica para preview"""
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
        
        # Obtém todas as linhas
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
        
        # Converte as linhas seguintes para dicionários
        dados = []
        for i, linha in enumerate(todas_linhas[1:limite_linhas+1], 1):
            if i > limite_linhas:
                break
            linha_dict = {}
            for j, valor in enumerate(linha):
                nome_coluna = colunas[j] if j < len(colunas) else f"Coluna_{j+1}"
                linha_dict[nome_coluna] = valor
            dados.append(linha_dict)
        
        return {
            'colunas': colunas,
            'dados': dados,
            'total_linhas': worksheet.row_count,
            'total_colunas': worksheet.col_count
        }
        
    except Exception as e:
        if current_app:
            current_app.logger.error(f"Erro ao obter dados da aba: {str(e)}")
        else:
            print(f"Erro ao obter dados da aba: {str(e)}")
        raise Exception(f"Erro ao obter dados da aba: {str(e)}")
    
def testar_conexao_google_sheets(sheet_id, aba_nome=None):
    """Testa a conexão com o Google Sheets"""
    try:
        # Encontra o caminho correto para o credentials.json
        current_dir = Path(__file__).parent
        credentials_path = current_dir / "credentials.json"
        
        if not credentials_path.exists():
            return False, "Arquivo credentials.json não encontrado"
        
        credentials = service_account.Credentials.from_service_account_file(
            str(credentials_path),
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        
        gc = gspread.authorize(credentials)
        planilha = gc.open_by_key(sheet_id)
        
        if aba_nome:
            worksheet = planilha.worksheet(aba_nome)
            # Tenta ler algumas linhas para testar
            dados = worksheet.get_all_values()[:5]
            return True, f"Conexão bem-sucedida! {len(dados)} linhas encontradas."
        else:
            return True, f"Conexão bem-sucedida! Planilha encontrada: {planilha.title}"
            
    except Exception as e:
        return False, f"Erro na conexão: {str(e)}"
    
  