from . import db
from datetime import datetime

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default="usuario")
    chamados = db.relationship("Chamado", backref="criador", lazy=True)
    acoes = db.relationship("WorkflowAcao", backref="usuario", lazy=True)

class Chamado(db.Model):
    __tablename__ = "chamado"
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, default="")
    prioridade = db.Column(db.String(20), default="MÉDIA")
    status = db.Column(db.String(20), default="ABERTO")
    criado_por = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    workflow = db.relationship("WorkflowAcao", backref="chamado", lazy=True)

class WorkflowAcao(db.Model):
    __tablename__ = "workflow_acao"
    id = db.Column(db.Integer, primary_key=True)
    chamado_id = db.Column(db.Integer, db.ForeignKey("chamado.id"), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    nome = db.Column(db.String(100), nullable=False)
    gatilho = db.Column(db.String(50), nullable=False)
    acao = db.Column(db.String(50), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    antes = db.Column(db.JSON)
    depois = db.Column(db.JSON)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    prioridade_cond = db.Column(db.String(20))
    status_cond = db.Column(db.String(20))
    novo_status = db.Column(db.String(20))
