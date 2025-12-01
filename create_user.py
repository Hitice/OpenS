from app import create_app
from app.extensions import db, bcrypt
from app.models import User

app = create_app()

with app.app_context():
    # Remove usuário antigo se existir
    User.query.filter_by(email="admin@opens.com").delete()
    db.session.commit()

    # Cria o admin
    admin = User(
        nome="Admin OpenS",
        email="admin@opens.com",
        senha_hash=bcrypt.generate_password_hash("opens2025").decode("utf-8"),
        role="admin"
    )
    db.session.add(admin)
    db.session.commit()
    print("Usuário admin criado ou atualizado com sucesso")
