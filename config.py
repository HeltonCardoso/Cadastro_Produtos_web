# config.py
import os
from pathlib import Path

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "segredo-desenvolvimento")
    UPLOAD_FOLDER = os.path.abspath('uploads')
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

    # ── Banco de dados ─────────────────────────────────────────────────────
    _db_url = os.environ.get('DATABASE_URL', 'sqlite:///logs.db')
    
    # Corrige postgres:// para postgresql://
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    
    # Adiciona o driver psycopg 3 se estiver usando PostgreSQL
    if 'postgresql://' in _db_url and 'postgresql+psycopg://' not in _db_url:
        _db_url = _db_url.replace('postgresql://', 'postgresql+psycopg://', 1)

    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Evita conexões mortas após inatividade no Render
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # ── Google Sheets ──────────────────────────────────────────────────────
    GOOGLE_SHEET_ID          = os.environ.get('GOOGLE_SHEET_ID', '')
    GOOGLE_SHEET_ABA         = os.environ.get('GOOGLE_SHEET_ABA', '')
    GOOGLE_SHEET_CONFIG_FILE = Path('config/google_sheets_config.json')

    # ── Intelipost ─────────────────────────────────────────────────────────
    INTELIPOST_API_KEY       = os.environ.get('INTELIPOST_API_KEY', 'sua_chave_api_aqui')
    INTELIPOST_BASE_URL      = 'https://api.intelipost.com.br/api/v1'
    INTELIPOST_CACHE_TIMEOUT = 300