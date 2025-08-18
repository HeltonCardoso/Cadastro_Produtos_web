from google.oauth2 import service_account
import gspread
import pandas as pd

def ler_planilha_google(sheet_id, aba_nome):
    # Autentica com o JSON
    credentials = service_account.Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    gc = gspread.authorize(credentials)

    # Abre a planilha pelo ID
    sh = gc.open_by_key(sheet_id)
    worksheet = sh.worksheet(aba_nome)

    # Lê todos os valores
    dados = worksheet.get_all_records()

    # Transforma em DataFrame para trabalhar igual ao Excel
    df = pd.DataFrame(dados)
    return df
