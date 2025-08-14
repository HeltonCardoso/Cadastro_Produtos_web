# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Processo(db.Model):
    __tablename__ = 'processos'
    id = db.Column(db.Integer, primary_key=True)
    modulo = db.Column(db.String(50), nullable=False)
    data = db.Column(db.DateTime, default=datetime.now, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    qtd_itens = db.Column(db.Integer, default=0, nullable=False)
    tempo_execucao = db.Column(db.Float, default=0.0, nullable=False)
    usuario = db.Column(db.String(50), default='Sistema', nullable=False)
    erro_mensagem = db.Column(db.Text)

class ItemProcessado(db.Model):
    __tablename__ = 'itens_processados'
    id = db.Column(db.Integer, primary_key=True)
    processo_id = db.Column(db.Integer, db.ForeignKey('processos.id'), nullable=False)
    ean = db.Column(db.String(50))
    nome = db.Column(db.String(255))
    status = db.Column(db.String(20))
    detalhes = db.Column(db.Text)
    data_processamento = db.Column(db.DateTime, default=datetime.now)