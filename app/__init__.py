# app/__init__.py
import os
from flask import Flask
from dotenv import load_dotenv
from flasgger import Swagger

# Carrega variáveis do .env
load_dotenv()

# Importa extensões globais
from .extensions import db, bcrypt, jwt, mail


def create_app():
    app = Flask(__name__)
    # suas configs
    Swagger(app)  # inicializa o Swagger
    return app

def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static")
    )

    # --------------------------
    # Configurações gerais
    # --------------------------
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL",
        "sqlite:///opens.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "minha_chave_secreta")
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "jwt_chave_secreta")
    app.config["WEBHOOK_KEY"] = os.environ.get("WEBHOOK_KEY")

    # Configurações de email
    app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USE_SSL"] = False

    # --------------------------
    # JWT via cookies
    # --------------------------
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    app.config['JWT_COOKIE_SECURE'] = False       # True se for HTTPS
    app.config['JWT_ACCESS_COOKIE_PATH'] = '/'    # Disponível em todas as rotas
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False # Simplifica para teste de conceito

    # --------------------------
    # Inicializa extensões
    # --------------------------
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)

    # --------------------------
    # Registra blueprints
    # --------------------------
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    # --------------------------
    # Criação de tabelas e admin inicial
    # --------------------------
    with app.app_context():
        db.create_all()

        from .models import User

        admin_email = "admin@opens.com"
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(
                nome="Admin OpenS",
                email=admin_email,
                senha_hash=bcrypt.generate_password_hash("opens2025").decode("utf-8"),
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()
            print("Usuário admin criado automaticamente")

    return app
