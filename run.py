from app import create_app
import os

app = create_app()

# Porta padrão do Render ou fallback para 5000 local
port = int(os.environ.get("PORT", 5000))

if __name__ == "__main__":
    # host="0.0.0.0" permite acesso externo no Render
    app.run(host="0.0.0.0", port=port, debug=True)
