# config.py
import os
from pathlib import Path

# config.py
import os

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "segredo-desenvolvimento")
    UPLOAD_FOLDER = os.path.abspath('uploads')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///logs.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True  # Mude para False em produção
    # Configurações do Google Sheets
    GOOGLE_SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '')
    GOOGLE_SHEET_ABA = os.environ.get('GOOGLE_SHEET_ABA', '')
    GOOGLE_SHEET_CONFIG_FILE = Path('config/google_sheets_config.json')