from app.models import WorkflowAcao
from app.extensions import mail
from flask_mail import Message

def processar_workflow(chamado):
    regras = WorkflowAcao.query.filter_by(ativo=True).all()

    for r in regras:
        campo, valor = r.gatilho.split("=")
        if getattr(chamado, campo, None) == valor:

            if r.acao == "enviar_alerta":
                enviar_alerta(chamado)

            if r.acao == "enviar_email":
                enviar_email_simples(
                    titulo="Chamado atualizado",
                    msg=f"Chamado {chamado.id} atualizado com {campo}={valor}"
                )

def enviar_alerta(chamado):
    print(f"[ALERTA] Chamado crítico detectado: {chamado.id}")

def enviar_email_simples(titulo, msg):
    m = Message(titulo, recipients=["admin@empresa.com"], body=msg)
    mail.send(m)
