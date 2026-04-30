# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()


# ============================================
# MODELOS EXISTENTES
# ============================================

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

    def __repr__(self):
        return f'<Processo {self.modulo} - {self.status}>'


class ItemProcessado(db.Model):
    __tablename__ = 'itens_processados'
    id = db.Column(db.Integer, primary_key=True)
    processo_id = db.Column(db.Integer, db.ForeignKey('processos.id'), nullable=False)
    ean = db.Column(db.String(50))
    nome = db.Column(db.String(255))
    status = db.Column(db.String(20))
    detalhes = db.Column(db.Text)
    data_processamento = db.Column(db.DateTime, default=datetime.now)

    processo = db.relationship('Processo', backref='itens')

    def __repr__(self):
        return f'<ItemProcessado {self.nome}>'


# ============================================
# MODELOS PARA AUTENTICAÇÃO E PERMISSÕES
# ============================================

class Perfil(db.Model):
    """Perfis predefinidos do sistema"""
    __tablename__ = 'perfis'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)  # Master, SAC, Cadastro, Financeiro
    descricao = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    usuarios = db.relationship('Usuario', backref='perfil_rel', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<Perfil {self.nome}>'


class Usuario(UserMixin, db.Model):
    """Modelo de usuário para autenticação"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfis.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relacionamentos
    permissoes_extras = db.relationship('Permissao', backref='usuario', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Cria hash da senha — método fixo para garantir compatibilidade entre versões do Werkzeug"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """Verifica senha"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def perfil(self):
        """Retorna o nome do perfil"""
        return self.perfil_rel.nome if self.perfil_rel else 'user'
    
    def is_master(self):
        """Verifica se é Master (admin total)"""
        return self.perfil == 'Master'
    
    def has_permission(self, modulo):
        """Verifica se o perfil tem acesso ao módulo"""
        permissoes = {
            'Master': ['todos'],
            'SAC': ['pedidos', 'clientes', 'dashboard'],
            'Cadastro': ['produtos', 'atributos', 'categorias', 'dashboard'],
            'Financeiro': ['financeiro', 'relatorios', 'dashboard']
        }
        
        if self.is_master():
            return True
        
        for p in self.permissoes_extras:
            if p.modulo == modulo:
                return p.pode_ler
        
        perfil_permissoes = permissoes.get(self.perfil, [])
        return modulo in perfil_permissoes or 'todos' in perfil_permissoes
    
    def get_modulos_acessos(self):
        """Retorna lista de módulos que o usuário pode acessar"""
        if self.is_master():
            return ['dashboard', 'pedidos', 'produtos', 'atributos', 'configuracoes', 'usuarios', 'financeiro', 'relatorios']
        
        modulos = ['dashboard']
        if self.has_permission('pedidos'):
            modulos.append('pedidos')
        if self.has_permission('produtos'):
            modulos.extend(['produtos', 'atributos'])
        if self.has_permission('financeiro'):
            modulos.append('financeiro')
        
        return modulos
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'perfil': self.perfil,
            'perfil_id': self.perfil_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'modulos_acesso': self.get_modulos_acessos()
        }
    
    def __repr__(self):
        return f'<Usuario {self.username} ({self.perfil})>'


class Permissao(db.Model):
    """Permissões específicas por módulo (sobrescreve permissões do perfil)"""
    __tablename__ = 'permissoes'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    modulo = db.Column(db.String(50), nullable=False)
    pode_ler = db.Column(db.Boolean, default=True)
    pode_escrever = db.Column(db.Boolean, default=False)
    pode_excluir = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('usuario_id', 'modulo', name='unique_usuario_modulo'),)
    
    def to_dict(self):
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
    service = db.Column(db.String(50), unique=True, nullable=False)
    token_data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_data(self):
        try:
            return json.loads(self.token_data)
        except:
            return {}
    
    def set_data(self, data):
        self.token_data = json.dumps(data)
    
    def to_dict(self):
        return {
            'id': self.id,
            'service': self.service,
            'data': self.get_data(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
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
    acao = db.Column(db.String(50))
    recurso = db.Column(db.String(200))
    sucesso = db.Column(db.Boolean, default=True)
    detalhes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    usuario = db.relationship('Usuario', backref='logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'usuario_nome': self.usuario_nome,
            'ip': self.ip,
            'user_agent': self.user_agent,
            'acao': self.acao,
            'recurso': self.recurso,
            'sucesso': self.sucesso,
            'detalhes': self.detalhes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<LogAcesso {self.acao} - {self.usuario_nome}>'


# ============================================
# MERCADO LIVRE — EVENTOS DE WEBHOOK
# ============================================

class MLWebhookEvent(db.Model):
    """
    Salva cada notificação recebida do Mercado Livre via webhook.
    A tabela é criada automaticamente pelo db.create_all() no startup.
    """
    __tablename__ = 'ml_webhook_events'

    id             = db.Column(db.Integer, primary_key=True)
    topic          = db.Column(db.String(100), index=True)       # orders, items, questions, payments…
    resource       = db.Column(db.String(255))                    # ex: /orders/1234567890
    user_id        = db.Column(db.String(50), index=True)         # seller que gerou o evento
    attempts       = db.Column(db.Integer, default=1)             # quantas vezes o ML tentou entregar
    application_id = db.Column(db.String(50))                     # ID do app ML registrado
    payload        = db.Column(db.Text)                           # JSON bruto recebido
    received_at    = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    processed      = db.Column(db.Boolean, default=False)         # True quando sua lógica processou
    error_msg      = db.Column(db.Text, nullable=True)            # Erro de processamento, se houver

    def get_data(self) -> dict:
        """Desserializa o payload JSON armazenado.
        Retorna dict vazio em caso de erro — nunca levanta exceção.
        """
        try:
            return json.loads(self.payload or '{}')
        except Exception:
            return {}

    def to_dict(self):
        return {
            'id':             self.id,
            'topic':          self.topic,
            'resource':       self.resource,
            'user_id':        self.user_id,
            'attempts':       self.attempts,
            'application_id': self.application_id,
            'received_at':    self.received_at.isoformat() if self.received_at else None,
            'processed':      self.processed,
            'error_msg':      self.error_msg,
        }

    def __repr__(self):
        return f'<MLWebhookEvent {self.topic} - {self.resource}>'


# ============================================
# FUNÇÕES AUXILIARES PARA INICIALIZAÇÃO
# ============================================

def init_perfis_e_usuarios():
    """Cria perfis padrão e usuários de exemplo"""
    from app import app
    
    with app.app_context():
        perfis_padrao = [
            {'nome': 'Master', 'descricao': 'Acesso total ao sistema'},
            {'nome': 'SAC', 'descricao': 'Acesso a pedidos e clientes'},
            {'nome': 'Cadastro', 'descricao': 'Acesso a produtos e atributos'},
            {'nome': 'Financeiro', 'descricao': 'Acesso a relatórios financeiros'},
        ]
        
        for p in perfis_padrao:
            perfil = Perfil.query.filter_by(nome=p['nome']).first()
            if not perfil:
                perfil = Perfil(nome=p['nome'], descricao=p['descricao'])
                db.session.add(perfil)
        
        db.session.commit()
        
        usuarios_padrao = [
            {'username': 'master', 'email': 'master@sistema.com', 'perfil': 'Master', 'senha': 'master123'},
            {'username': 'sac', 'email': 'sac@sistema.com', 'perfil': 'SAC', 'senha': 'sac123'},
            {'username': 'cadastro', 'email': 'cadastro@sistema.com', 'perfil': 'Cadastro', 'senha': 'cadastro123'},
        ]
        
        for u in usuarios_padrao:
            perfil = Perfil.query.filter_by(nome=u['perfil']).first()
            if perfil:
                usuario = Usuario.query.filter_by(username=u['username']).first()
                if not usuario:
                    usuario = Usuario(
                        username=u['username'],
                        email=u['email'],
                        perfil_id=perfil.id,
                        is_active=True
                    )
                    usuario.set_password(u['senha'])
                    db.session.add(usuario)
        
        db.session.commit()
        print("✅ Perfis e usuários padrão criados com sucesso!")