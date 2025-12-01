from app import create_app, db
from app.models import User, Chamado, WorkflowAcao
from faker import Faker
import random
from datetime import datetime, timedelta

app = create_app()
faker = Faker()

with app.app_context():
    # Limpa tabelas
    WorkflowAcao.query.delete()
    Chamado.query.delete()
    User.query.delete()
    db.session.commit()

    # Usuário admin
    admin = User(
        nome="Admin OpenS",
        email="admin@opens.com",
        senha_hash="opens2025",
        role="admin"
    )
    db.session.add(admin)
    db.session.commit()

    # Marcas fictícias de logística
    marcas_exclusivas = [f"MarcaLog{i}" for i in range(1, 11)]
    marcas_renomadas = ["FedEx", "DHL", "UPS", "Maersk", "TNT"]

    prioridades = ["BAIXA", "MÉDIA", "ALTA", "CRÍTICA"]
    status_possiveis = ["ABERTO", "EM ANDAMENTO", "CONCLUÍDO", "PENDENTE"]

    # Criar 200 chamados
    for _ in range(200):
        titulo = f"{faker.word().capitalize()} - {random.choice(marcas_exclusivas + marcas_renomadas)}"
        descricao = faker.sentence(nb_words=12)
        prioridade = random.choice(prioridades)
        status = random.choice(status_possiveis)
        data_criacao = datetime.utcnow() - timedelta(days=random.randint(0, 30))

        chamado = Chamado(
            titulo=titulo,
            descricao=descricao,
            prioridade=prioridade,
            status=status,
            criado_por=admin.id,
            criado_em=data_criacao
        )
        db.session.add(chamado)
    
    db.session.commit()
    print("200 chamados populados com sucesso!")
