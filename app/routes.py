# app/routes.py
from datetime import date, datetime
from io import StringIO
import csv

from flask import Blueprint, render_template, jsonify, request, current_app, Response, abort
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies,
    get_jwt_identity
)
from sqlalchemy import func
from .extensions import db, bcrypt
from .models import User, Chamado, WorkflowAcao  # WorkflowAcao pode não existir — crie se pedido
from .utils import sanitize_dict
from .workflows import processar_workflow  # módulo opcional; se não existir, remova a chamada
import typing

bp = Blueprint("main", __name__)


# --------------------------
# PÁGINAS
# --------------------------
@bp.route("/")
def login_page():
    return render_template("login.html")


@bp.route("/dashboard")
@jwt_required()
def dashboard():
    return render_template("dashboard.html")


@bp.route("/chamados")
@jwt_required()
def chamados_page():
    return render_template("chamados.html")


@bp.route("/novo-chamado")
@jwt_required()
def novo_chamado_page():
    return render_template("novo_chamado.html", hoje=date.today().isoformat())


# --------------------------
# AUTH
# --------------------------
@bp.route("/api/login", methods=["POST"])
def api_login():
    data = sanitize_dict(request.get_json() or {})
    email = data.get("email", "").strip().lower()
    senha = data.get("senha", "").strip()

    if not email or not senha:
        return jsonify({"erro": "Credenciais incompletas"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.senha_hash, senha):
        return jsonify({"erro": "E-mail ou senha incorretos"}), 401

    access_token = create_access_token(identity=str(user.id))
    resp = jsonify({"msg": "Login realizado com sucesso"})
    set_access_cookies(resp, access_token)
    return resp, 200


@bp.route("/logout", methods=["POST"])
@jwt_required()
def api_logout():
    resp = jsonify({"msg": "Logout realizado"})
    unset_jwt_cookies(resp)
    return resp


# --------------------------
# HELPER: serialização de Chamado
# --------------------------
def chamado_to_dict(c: Chamado, usuarios_cache: dict):
    uid = c.criado_por
    # usa None key coerente
    cache_key = uid if uid is not None else 0
    if cache_key not in usuarios_cache:
        u = User.query.get(uid) if uid else None
        usuarios_cache[cache_key] = u.nome if u else "Sistema"
    autor = usuarios_cache[cache_key]
    return {
        "id": c.id,
        "titulo": c.titulo,
        "descricao": c.descricao or "",
        "prioridade": c.prioridade,
        "status": c.status,
        "autor": autor,
        "criado_por": uid,
        "data_iso": c.criado_em.isoformat(),
        "data": c.criado_em.strftime("%d/%m/%Y %H:%M")
    }


# --------------------------
# CHAMADOS — LIST / FILTER / PAGINATION (GET) + EXPORT CSV
# --------------------------
@bp.route("/api/chamados")
@jwt_required()
def api_chamados():
    # parâmetros
    q = (request.args.get("q") or "").strip()
    prioridade = (request.args.get("prioridade") or "").strip().upper()
    status = (request.args.get("status") or "").strip().upper()
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = max(1, min(200, int(request.args.get("per_page", 25))))
    except Exception:
        page, per_page = 1, 25

    query = Chamado.query

    if q:
        if q.isdigit():
            query = query.filter(Chamado.id == int(q))
        else:
            like = f"%{q}%"
            query = query.filter(Chamado.titulo.ilike(like) | Chamado.descricao.ilike(like))

    if prioridade:
        query = query.filter(Chamado.prioridade == prioridade)

    if status:
        query = query.filter(Chamado.status == status)

    total = query.count()
    total_pages = (total // per_page) + (1 if total % per_page else 0)

    items_q = (
        query.order_by(Chamado.id.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
        .all()
    )

    usuarios_cache = {}
    items = [chamado_to_dict(c, usuarios_cache) for c in items_q]

    # all_items curta (para gráficos): limit 500
    all_items_q = query.order_by(Chamado.id.desc()).limit(500).all()
    all_items = [chamado_to_dict(c, usuarios_cache) for c in all_items_q]

    return jsonify({
        "items": items,
        "all_items": all_items,
        "meta": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages
        }
    })


@bp.route("/api/chamados/export")
@jwt_required()
def api_chamados_export():
    fmt = (request.args.get("format") or "csv").lower()
    query = Chamado.query.order_by(Chamado.id.desc()).limit(2000).all()

    usuarios_cache = {}
    rows = [chamado_to_dict(c, usuarios_cache) for c in query]

    if fmt == "csv":
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(["id", "titulo", "descricao", "prioridade", "status", "autor", "data"])
        for r in rows:
            writer.writerow([r["id"], r["titulo"], r["descricao"], r["prioridade"], r["status"], r["autor"], r["data"]])
        output = si.getvalue()
        return Response(output, mimetype="text/csv", headers={
            "Content-Disposition": f"attachment; filename=chamados-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
        })
    else:
        return jsonify(rows)


# --------------------------
# GET single Chamado
# --------------------------
@bp.route("/api/chamados/<int:cid>")
@jwt_required()
def api_chamado_get(cid):
    c = Chamado.query.get_or_404(cid)
    usuarios_cache = {}
    return jsonify(chamado_to_dict(c, usuarios_cache))


# --------------------------
# UPDATE chamando (PATCH) — permite mudar: titulo, descricao, prioridade, status
# --------------------------
@bp.route("/api/chamados/<int:cid>", methods=["PATCH"])
@jwt_required()
def api_chamado_patch(cid):
    data = sanitize_dict(request.get_json() or {})
    allowed = {"titulo", "descricao", "prioridade", "status"}
    payload = {k: v for k, v in data.items() if k in allowed}

    if not payload:
        return jsonify({"erro": "Nada para atualizar"}), 400

    c = Chamado.query.get_or_404(cid)
    if "titulo" in payload and len(payload["titulo"]) < 3:
        return jsonify({"erro": "Título inválido"}), 400

    if "prioridade" in payload:
        payload["prioridade"] = payload["prioridade"].upper()
        if payload["prioridade"] not in ["BAIXA", "MÉDIA", "ALTA", "CRÍTICA"]:
            payload["prioridade"] = "MÉDIA"

    if "status" in payload:
        payload["status"] = payload["status"].upper()

    for k, v in payload.items():
        setattr(c, k, v)

    db.session.commit()

    # processa workflows após atualização
    try:
        processar_workflow(c)
    except Exception as e:
        current_app.logger.exception("Erro ao processar workflow após PATCH: %s", e)

    usuarios_cache = {}
    return jsonify(chamado_to_dict(c, usuarios_cache))

# --------------------------
# WORKFLOW / REGRAS
# --------------------------
@bp.route("/api/workflow/regras")
@jwt_required()
def api_workflow_regras():
    regras = WorkflowAcao.query.filter_by(ativo=True).all()
    lista = []
    for r in regras:
        lista.append({
            "id": r.id,
            "nome": r.nome,
            "prioridade_cond": r.prioridade_cond,
            "status_cond": r.status_cond,
            "acao": r.acao,
            "novo_status": r.novo_status
        })
    return jsonify(lista)


# --------------------------
# DELETE chamando
# --------------------------
@bp.route("/api/chamados/<int:cid>", methods=["DELETE"])
@jwt_required()
def api_chamado_delete(cid):
    c = Chamado.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()
    return jsonify({"msg": "Removido"}), 200


# --------------------------
# STATS (mantido)
# --------------------------
@bp.route("/api/stats")
@jwt_required()
def api_stats():
    total = Chamado.query.count()
    abertos = Chamado.query.filter_by(status="ABERTO").count()
    alta_critica = Chamado.query.filter(Chamado.prioridade.in_(["ALTA", "CRÍTICA"])).count()
    hoje = Chamado.query.filter(func.date(Chamado.criado_em) == date.today()).count()

    return jsonify({
        "total": total,
        "abertos": abertos,
        "alta": alta_critica,
        "hoje": hoje
    })


# --------------------------
# CRIAÇÃO NOVO CHAMADO (mantido)
# --------------------------
@bp.route("/api/chamados/novo", methods=["POST"])
@jwt_required()
def api_novo_chamado():
    data = sanitize_dict(request.get_json() or {})
    user_id = int(get_jwt_identity() or 0)

    titulo = data.get("titulo", "").strip()
    if not titulo:
        return jsonify({"erro": "Título é obrigatório"}), 400

    chamado = Chamado(
        titulo=titulo,
        descricao=data.get("descricao", "").strip(),
        prioridade=data.get("prioridade", "MÉDIA").upper(),
        status="ABERTO",
        criado_por=user_id
    )
    db.session.add(chamado)
    db.session.commit()

    # processa workflows após criação
    try:
        processar_workflow(chamado)
    except Exception as e:
        current_app.logger.exception("Erro ao processar workflow após criação: %s", e)

    usuarios_cache = {}
    return jsonify(chamado_to_dict(chamado, usuarios_cache)), 201


# --------------------------
# WEBHOOK externo (Power Automate / integração)
# --------------------------
@bp.route("/api/webhook", methods=["POST"])
def api_webhook():
    """
    Webhook público protegido por chave (config: WEBHOOK_KEY).
    Exemplo: POST /api/webhook?k=MINHA_CHAVE  ou enviar header X-Webhook-Key
    Body JSON: { "titulo": "...", "descricao": "...", "prioridade": "ALTA", "criado_por": 1 }
    """
    key_cfg = current_app.config.get("WEBHOOK_KEY")
    provided = request.args.get("k") or request.headers.get("X-Webhook-Key")
    if key_cfg:
        if not provided or provided != key_cfg:
            return jsonify({"erro": "Chave do webhook inválida"}), 403

    # aceita JSON ou form-data
    data_raw = request.get_json(silent=True) or request.form.to_dict() or {}
    data = sanitize_dict(data_raw)

    titulo = (data.get("titulo") or "").strip()
    if not titulo:
        return jsonify({"erro": "Título obrigatório"}), 400

    prioridade = (data.get("prioridade") or "MÉDIA").upper()
    if prioridade not in ["BAIXA", "MÉDIA", "ALTA", "CRÍTICA"]:
        prioridade = "MÉDIA"

    criado_por = None
    try:
        if data.get("criado_por"):
            criado_por = int(data.get("criado_por"))
    except Exception:
        criado_por = None

    chamado = Chamado(
        titulo=titulo,
        descricao=data.get("descricao", "").strip(),
        prioridade=prioridade,
        status=data.get("status", "ABERTO").upper(),
        criado_por=criado_por
    )
    db.session.add(chamado)
    db.session.commit()

    # aciona workflows
    try:
        processar_workflow(chamado)
    except Exception as e:
        current_app.logger.exception("Erro processar workflow via webhook: %s", e)

    usuarios_cache = {}
    return jsonify(chamado_to_dict(chamado, usuarios_cache)), 201


# --------------------------
# WORKFLOWS CRUD (simples)
# --------------------------
@bp.route("/api/workflows")
@jwt_required()
def api_workflows_list():
    # lista todas regras
    try:
        items = WorkflowAcao.query.order_by(WorkflowAcao.id.desc()).all()
    except Exception:
        return jsonify({"items": []})
    data = [
        {"id": w.id, "nome": w.nome, "gatilho": w.gatilho, "acao": w.acao, "ativo": bool(w.ativo)}
        for w in items
    ]
    return jsonify({"items": data})


@bp.route("/api/workflows", methods=["POST"])
@jwt_required()
def api_workflows_create():
    data = sanitize_dict(request.get_json() or {})
    nome = (data.get("nome") or "").strip()
    gatilho = (data.get("gatilho") or "").strip()
    acao = (data.get("acao") or "").strip()
    ativo = bool(data.get("ativo", True))

    if not nome or not gatilho or not acao:
        return jsonify({"erro": "nome, gatilho e acao são obrigatórios"}), 400

    w = WorkflowAcao(nome=nome, gatilho=gatilho, acao=acao, ativo=ativo)
    db.session.add(w)
    db.session.commit()
    return jsonify({"id": w.id, "nome": w.nome, "gatilho": w.gatilho, "acao": w.acao, "ativo": w.ativo}), 201


@bp.route("/api/workflows/<int:wid>", methods=["PATCH"])
@jwt_required()
def api_workflows_patch(wid):
    w = WorkflowAcao.query.get_or_404(wid)
    data = sanitize_dict(request.get_json() or {})
    if "nome" in data: w.nome = data["nome"].strip()
    if "gatilho" in data: w.gatilho = data["gatilho"].strip()
    if "acao" in data: w.acao = data["acao"].strip()
    if "ativo" in data: w.ativo = bool(data["ativo"])
    db.session.commit()
    return jsonify({"ok": True})


@bp.route("/api/workflows/<int:wid>", methods=["DELETE"])
@jwt_required()
def api_workflows_delete(wid):
    w = WorkflowAcao.query.get_or_404(wid)
    db.session.delete(w)
    db.session.commit()
    return jsonify({"ok": True}), 200
