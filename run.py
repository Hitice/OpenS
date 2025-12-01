import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Usa a porta do Render ou 5000 como fallback
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
