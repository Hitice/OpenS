# OpenS - Sistema de Gestão de Chamados

## História do App

O OpenS nasceu da necessidade de organizar de forma eficiente os chamados em uma empresa de tecnologia. Com o crescimento do time e o aumento das demandas, ficou claro que um sistema manual ou disperso entre planilhas não seria suficiente.

O objetivo do OpenS é centralizar todas as solicitações em um único lugar, permitindo que gestores acompanhem o andamento, priorizem tarefas e automatizem fluxos de trabalho. Desde o usuário final abrindo um chamado até o gestor analisando métricas, o sistema garante agilidade, transparência e organização.

## Descrição

OpenS é um sistema web de gestão de chamados, desenvolvido em Python com Flask, com suporte a PostgreSQL. O sistema permite:

* Cadastro e autenticação de usuários
* Criação e acompanhamento de chamados
* Fluxos de trabalho customizáveis (Workflows)
* Integração via API

## Tecnologias

* Python 3.13
* Flask 3.0
* Flask-JWT-Extended
* Flask-Bcrypt
* Flask-Mail
* Flask-SQLAlchemy
* PostgreSQL (produção) / SQLite (desenvolvimento)
* HTML + Jinja2 para templates
* Gunicorn para deploy

## Estrutura do Projeto

app/                 # Código principal da aplicação
**init**.py      # Inicialização do Flask e configurações
extensions.py    # Extensões do Flask (DB, JWT, Bcrypt, Mail)
models.py        # Models do SQLAlchemy
routes.py        # Rotas e blueprints
utils.py         # Funções utilitárias
workflows.py     # Lógica de workflows
templates/       # Templates HTML
base.html
login.html
dashboard.html
chamados.html
novo_chamado.html

wsgi.py              # Entry point para Gunicorn / Render
run.py               # Opcional para execução local

## Configuração

1. Criar arquivo `.env` na raiz com as variáveis:

   * SECRET_KEY
   * JWT_SECRET_KEY
   * DATABASE_URL (PostgreSQL para produção, SQLite opcional para dev)

2. Instalar dependências:

   ```
   pip install -r requirements.txt
   ```

3. Inicializar banco de dados:

   ```
   flask db init
   flask db migrate
   flask db upgrade
   ```

## Deploy

* Render:

  * Entry point: `wsgi:app`
  * Build command: `pip install -r requirements.txt`
  * Start command: `gunicorn wsgi:app --bind 0.0.0.0:$PORT`

## Licença

Projeto privado (sem licença pública definida).

## Autor

Hitice
