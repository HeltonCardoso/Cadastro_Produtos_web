# config.py
import os

# config.py
import os

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "helton-segredo")
    UPLOAD_FOLDER = "uploads"
    SQLALCHEMY_DATABASE_URI = 'sqlite:///logs.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DIRS_TO_CREATE = ["Uploads"]  # Apenas uploads, logs agora no banco