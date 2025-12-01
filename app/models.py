from .extensions import db
from datetime import datetime
import json

# =========================
# USER
# =========================
class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default="usuario")  # admin / diretoria / analista

    chamados = db.relationship("Chamado", backref="criador", lazy=True)
    acoes = db.relationship("WorkflowAcao", backref="usuario", lazy=True)

    def __repr__(self):
        return f"<User {self.nome}>"

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "role": self.role
        }

# =========================
# CHAMADO
# =========================
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

    def __repr__(self):
        return f"<Chamado #{self.id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "prioridade": self.prioridade,
            "status": self.status,
            "criado_por": self.criado_por,
            "criado_em": self.criado_em.isoformat(),
        }

# =========================
# WORKFLOW AÇÕES
# =========================
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

    def __repr__(self):
        return f"<WorkflowAcao {self.acao} CH:{self.chamado_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "chamado_id": self.chamado_id,
            "usuario_id": self.usuario_id,
            "nome": self.nome,
            "gatilho": self.gatilho,
            "acao": self.acao,
            "ativo": self.ativo,
            "antes": self.antes,
            "depois": self.depois,
            "prioridade_cond": self.prioridade_cond,
            "status_cond": self.status_cond,
            "novo_status": self.novo_status,
            "criado_em": self.criado_em.isoformat(),
        }
