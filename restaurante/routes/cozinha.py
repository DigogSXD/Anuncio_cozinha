"""
routes/cozinha.py — KDS (Kitchen Display System).

GET  /cozinha/              → Painel da cozinha
GET  /cozinha/pedidos.json  → API JSON com pedidos em aberto
POST /cozinha/pedido/<id>/status → Atualiza status de um pedido
"""

from functools import wraps
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Pedido

bp = Blueprint("cozinha", __name__)

FLUXO = {
    "aguardando": "em_preparo",
    "em_preparo": "pronto",
    "pronto":     "entregue",
}


# ── Decorator: exige role cozinha ou admin ───────────────────────
def cozinha_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role not in ("cozinha", "admin"):
            flash("Acesso restrito à equipe da cozinha.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


@bp.route("/")
@cozinha_required
def index():
    return render_template("cozinha/index.html")


@bp.route("/pedidos.json")
@cozinha_required
def pedidos_json():
    tudo = request.args.get("tudo", "0") == "1"
    status_filtro = ["aguardando", "em_preparo", "pronto"] if tudo else ["aguardando", "em_preparo"]

    pedidos = (
        Pedido.query
        .filter(Pedido.status.in_(status_filtro))
        .order_by(Pedido.criado_em.asc())
        .all()
    )
    return jsonify([p.to_dict() for p in pedidos])


@bp.route("/pedido/<int:pedido_id>/status", methods=["POST"])
@cozinha_required
def atualizar_status(pedido_id):
    pedido = db.get_or_404(Pedido, pedido_id)

    if request.is_json:
        data       = request.get_json(silent=True) or {}
        novo_status = data.get("status")
    else:
        novo_status = request.form.get("status")

    if not novo_status:
        novo_status = FLUXO.get(pedido.status)

    if novo_status not in ["aguardando", "em_preparo", "pronto", "entregue"]:
        return jsonify({"erro": "Status inválido"}), 400

    pedido.status = novo_status
    db.session.commit()
    return jsonify({"ok": True, "pedido_id": pedido.id, "status": pedido.status})
