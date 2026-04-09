# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
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

# ============================================
# NOVOS MODELOS PARA AUTENTICAÇÃO E PERMISSÕES
# ============================================

class Usuario(UserMixin, db.Model):
    """Modelo de usuário para autenticação"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin', 'user', 'viewer'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relacionamentos
    permissoes = db.relationship('Permissao', backref='usuario', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Cria hash da senha"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica senha"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Verifica se é administrador"""
        return self.role == 'admin'
    
    def has_permission(self, modulo, acao='ler'):
        """Verifica permissão específica"""
        if self.is_admin():
            return True
        
        for permissao in self.permissoes:
            if permissao.modulo == modulo:
                if acao == 'ler' and permissao.pode_ler:
                    return True
                elif acao == 'escrever' and permissao.pode_escrever:
                    return True
                elif acao == 'excluir' and permissao.pode_excluir:
                    return True
        
        return False
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<Usuario {self.username}>'


class Permissao(db.Model):
    """Permissões específicas por módulo"""
    __tablename__ = 'permissoes'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    modulo = db.Column(db.String(50), nullable=False)  # 'mercadolivre', 'anymarket', 'cadastro', 'configuracoes', 'pedidos'
    pode_ler = db.Column(db.Boolean, default=True)
    pode_escrever = db.Column(db.Boolean, default=False)
    pode_excluir = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Garantir que não haja duplicidade (um usuário não pode ter duas permissões para o mesmo módulo)
    __table_args__ = (db.UniqueConstraint('usuario_id', 'modulo', name='unique_usuario_modulo'),)
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'modulo': self.modulo,
            'pode_ler': self.pode_ler,
            'pode_escrever': self.pode_escrever,
            'pode_excluir': self.pode_excluir
        }
    
    def __repr__(self):
        return f'<Permissao {self.modulo} - Usuario:{self.usuario_id}>'


class TokenConfig(db.Model):
    """Armazena tokens de integração configurados pelo usuário (persistente)"""
    __tablename__ = 'token_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(50), unique=True, nullable=False)  # 'mercadolivre', 'anymarket', 'intelipost', 'google'
    token_data = db.Column(db.Text, nullable=False)  # JSON com os tokens
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_data(self):
        """Retorna os dados do token como dicionário"""
        return json.loads(self.token_data)
    
    def set_data(self, data):
        """Define os dados do token a partir de um dicionário"""
        self.token_data = json.dumps(data)
    
    def to_dict(self):
        return {
            'id': self.id,
            'service': self.service,
            'data': self.get_data(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<TokenConfig {self.service}>'


class LogAcesso(db.Model):
    """Log de acessos para auditoria"""
    __tablename__ = 'logs_acesso'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    usuario_nome = db.Column(db.String(80))
    ip = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))
    acao = db.Column(db.String(50))  # 'login', 'logout', 'acesso_recurso', 'alteracao'
    recurso = db.Column(db.String(200))  # URL ou recurso acessado
    sucesso = db.Column(db.Boolean, default=True)
    detalhes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'usuario_nome': self.usuario_nome,
            'ip': self.ip,
            'acao': self.acao,
            'recurso': self.recurso,
            'sucesso': self.sucesso,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }