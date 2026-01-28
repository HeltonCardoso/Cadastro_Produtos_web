# google_sheets.py
from google.oauth2 import service_account
import gspread
import pandas as pd
from pathlib import Path
import os


def ler_planilha_google(sheet_id, aba_nome):
    """Lê uma planilha do Google Sheets preservando vírgula decimal"""
    try:
        current_dir = Path(__file__).parent
        credentials_path = current_dir / "credentials.json"

        if not credentials_path.exists():
            raise FileNotFoundError(f"Arquivo credentials.json não encontrado em: {credentials_path}")

        credentials = service_account.Credentials.from_service_account_file(
            str(credentials_path),
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )

        gc = gspread.authorize(credentials)
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.worksheet(aba_nome)

        # 🔥 Lê tudo como TEXTO (sem conversão automática)
        valores = worksheet.get_all_values()

        if not valores or len(valores) < 2:
            raise Exception("Planilha vazia ou sem dados")

        cabecalho = valores[0]
        linhas = valores[1:]

        df = pd.DataFrame(linhas, columns=cabecalho)

        return df

    except Exception as e:
        raise Exception(f"Erro ao acessar Google Sheets: {str(e)}")