# google_sheets.py
from google.oauth2 import service_account
import gspread
import pandas as pd
from pathlib import Path
import os

def ler_planilha_google(sheet_id, aba_nome):
    """Lê uma planilha do Google Sheets e retorna um DataFrame"""
    try:
        # Encontra o caminho correto para o credentials.json
        current_dir = Path(__file__).parent
        credentials_path = current_dir / "credentials.json"
        
        # Verifica se o arquivo existe
        if not credentials_path.exists():
            raise FileNotFoundError(f"Arquivo credentials.json não encontrado em: {credentials_path}")
        
        # Autentica com o JSON
        credentials = service_account.Credentials.from_service_account_file(
            str(credentials_path),
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        gc = gspread.authorize(credentials)

        # Abre a planilha pelo ID
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.worksheet(aba_nome)

        # Lê todos os valores e transforma em DataFrame
        dados = worksheet.get_all_records()
        return pd.DataFrame(dados)
        
    except FileNotFoundError as e:
        raise e
    except Exception as e:
        raise Exception(f"Erro ao acessar Google Sheets: {str(e)}")