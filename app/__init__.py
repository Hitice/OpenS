from flask import Flask
import os
from dotenv import load_dotenv
from flask_migrate import Migrate

load_dotenv()

def create_app():
    # STATIC e TEMPLATES
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    # CONFIGURAÇÕES
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "jwtdev")
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_SECURE"] = False
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False

    # BANCO DE DADOS - PostgreSQL no Render
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(os.path.dirname(__file__), "..", "instance", "opens.db")
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # EXTENSÕES
    from .extensions import db, bcrypt, jwt
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # MIGRATIONS
    Migrate(app, db)

    # IMPORT MODELS
    from .models import User, Chamado, WorkflowAcao

    # BLUEPRINTS
    from .routes import bp
    app.register_blueprint(bp)

    return app
