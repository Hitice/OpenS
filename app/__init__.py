from flask import Flask
import os

def create_app():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # pasta raiz

    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "app", "templates"),
        static_folder=os.path.join(BASE_DIR, "static")
    )

    # Rotas simples só para servir HTML
    @app.route("/")
    def index():
        return app.send_static_file("index.html")  # ou "login.html"

    @app.route("/dashboard")
    def dashboard():
        return app.send_static_file("dashboard.html")

    return app
