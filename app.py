# app.py — OpenS – Central de Operações Industriais
# Versão final: JWT + Gmail + Dashboard BI + Deploy Render.com
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, render_template
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity
)
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
import sqlite3
import os
from datetime import datetime, timedelta

# ========================== CONFIGURAÇÃO ==========================
app = Flask(__name__, template_folder="templates", static_folder="static")

app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "opens_mude_isso_em_producao_2025"),
    JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "opens_jwt_super_forte_2025"),
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=12),

    # Configuração do Gmail
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_DEFAULT_SENDER=os.getenv("MAIL_USERNAME")
)

jwt = JWTManager(app)
bcrypt = Bcrypt(app)
mail = Mail(app)

# ========================== BANCO DE DADOS ==========================
def init_db():
    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()

        # Tabela de usuários
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL
            )
        """)

        # Tabela de chamados
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chamados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descricao TEXT NOT NULL,
                prioridade TEXT DEFAULT 'MÉDIA',
                status TEXT DEFAULT 'ABERTO',
                criado_por INTEGER,
                criado_em TIMESTAMP DEFAULT (datetime('now')),
                FOREIGN KEY (criado_por) REFERENCES usuarios(id)
            )
        """)

        conn.commit()

        # Cria usuário admin padrão se não existir
        cur.execute("SELECT COUNT(*) FROM usuarios")
        if cur.fetchone()[0] == 0:
            hash_senha = bcrypt.generate_password_hash("opens2025").decode("utf-8")
            cur.execute(
                "INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)",
                ("Administrador OpenS", "admin@opens.com", hash_senha)
            )
            conn.commit()
            print("\nOpenS PRONTO!")
            print("Login: admin@opens.com")
            print("Senha: opens2025\n")

init_db()

# ========================== E-MAIL ==========================
def enviar_email(destinatario, assunto, corpo):
    if not app.config["MAIL_USERNAME"] or not app.config["MAIL_PASSWORD"]:
        print("E-mail desativado (preencha .env)")
        return
    try:
        msg = Message(
            subject=assunto,
            recipients=[destinatario],
            body=corpo
        )
        mail.send(msg)
        print(f"E-mail enviado → {destinatario}")
    except Exception as e:
        print(f"Falha no envio de e-mail: {e}")

# ========================== ROTAS ==========================
@app.route("/")
def index():
    return render_template("index.html")

# Login
@app.route("/api/login", methods=["POST"])
def login():
    dados = request.get_json() or {}
    email = dados.get("email", "").strip()
    senha = dados.get("senha", "")

    with sqlite3.connect("database.db") as conn:
        conn.row_factory = sqlite3.Row
        usuario = conn.execute(
            "SELECT * FROM usuarios WHERE email = ?", (email,)
        ).fetchone()

    if usuario and bcrypt.check_password_hash(usuario["senha_hash"], senha):
        token = create_access_token(
            identity={"id": usuario["id"], "nome": usuario["nome"]}
        )
        return jsonify({"token": token})

    return jsonify({"erro": "E-mail ou senha incorretos"}), 401

# Listar chamados
@app.route("/api/chamados")
@jwt_required()
def listar_chamados():
    with sqlite3.connect("database.db") as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT c.*, u.nome AS autor 
            FROM chamados c 
            JOIN usuarios u ON c.criado_por = u.id 
            ORDER BY c.id DESC
        """).fetchall()
        return jsonify([dict(row) for row in rows])

# Criar chamado
@app.route("/api/chamados", methods=["POST"])
@jwt_required()
def criar_chamado():
    usuario = get_jwt_identity()
    dados = request.get_json() or {}

    titulo = dados.get("titulo", "").strip()
    descricao = dados.get("descricao", "").strip()
    prioridade = dados.get("prioridade", "MÉDIA").upper()

    if not titulo or not descricao:
        return jsonify({"erro": "Título e descrição são obrigatórios"}), 400
    if prioridade not in ["BAIXA", "MÉDIA", "ALTA"]:
        prioridade = "MÉDIA"

    with sqlite3.connect("database.db") as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO chamados 
               (titulo, descricao, prioridade, criado_por) 
               VALUES (?, ?, ?, ?)""",
            (titulo, descricao, prioridade, usuario["id"])
        )
        chamado_id = cur.lastrowid
        conn.commit()

    # Envia e-mail automático
    enviar_email(
        destinatario="suporte@opens.com",
        assunto=f"OpenS | Novo Chamado #{chamado_id} – {prioridade}",
        corpo=f"""
Novo chamado criado por {usuario['nome']}:

Título: {titulo}
Prioridade: {prioridade}
Descrição:
{descricao}

Acesse o OpenS: https://opens.onrender.com
        """
    )

    return jsonify({"id": chamado_id, "mensagem": "Chamado criado com sucesso"}), 201

# ========================== INÍCIO ==========================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("     OpenS – Central de Operações Industriais")
    print("   URL: http://localhost:5000")
    print("   Login: admin@opens.com")
    print("   Senha: opens2025")
    print("="*60 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False)