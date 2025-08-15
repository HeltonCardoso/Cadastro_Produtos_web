# config.py
import os

# config.py
import os

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "segredo-desenvolvimento")
    UPLOAD_FOLDER = os.path.abspath('uploads')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///logs.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True  # Mude para False em produção