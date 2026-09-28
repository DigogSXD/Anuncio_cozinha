"""
routes/garcom.py — Painel do Garçom (mobile-first).

Fluxo:
  1. GET  /garcom/                          → Grid de mesas
  2. GET  /garcom/mesa/<n>                  → Detalhe da mesa (modal escolha ou controle)
  3. POST /garcom/mesa/<n>/abrir            → Abre comanda (individual ou coletiva)
  4. GET  /garcom/comanda/<id>              → Tela de controle da comanda
  5. POST /garcom/pedido                    → Envia novo pedido para a cozinha
  6. GET  /garcom/comanda/<id>/fechar       → Tela de fechamento com resumo de conta
  7. POST /garcom/comanda/<id>/fechar       → Confirma fechamento
  8. GET  /garcom/confirmacao/<pedido_id>   → Confirmação de pedido enviado
"""

from datetime import datetime
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Mesa, Comanda, Pedido, PedidoItem, ItemCardapio, Categoria

bp = Blueprint("garcom", __name__)


# ── Decorator de acesso ──────────────────────────────────────────
def garcom_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role not in ("garcom", "admin"):
            flash("Acesso restrito aos garçons.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


# ────────────────────────────────────────────────────────────────
# 1. GRID DE MESAS
# ────────────────────────────────────────────────────────────────
@bp.route("/")
@garcom_required
def index():
    mesas = Mesa.query.filter_by(ativa=True).order_by(Mesa.numero).all()

    mesas_status = []
    for mesa in mesas:
        comandas_abertas = (
            Comanda.query
            .filter_by(mesa_id=mesa.id, status="aberta")
            .all()
        )
        mesas_status.append({
            "mesa":            mesa,
            "tem_comanda":     len(comandas_abertas) > 0,
            "num_comandas":    len(comandas_abertas),
            "total_consumido": sum(c.total for c in comandas_abertas),
        })

    return render_template("garcom/index.html", mesas_status=mesas_status)


# ────────────────────────────────────────────────────────────────
# 2. DETALHE DA MESA
# ────────────────────────────────────────────────────────────────
@bp.route("/mesa/<int:numero>")
@garcom_required
def mesa(numero):
    """
    Se a mesa não tiver comanda aberta → mostra modal para escolher
    tipo de comanda (individual / coletiva).
    Se tiver → mostra a tela de controle com comandas em aberto.
    """
    mesa_obj = Mesa.query.filter_by(numero=numero, ativa=True).first_or_404()
    comandas_abertas = (
        Comanda.query
        .filter_by(mesa_id=mesa_obj.id, status="aberta")
        .order_by(Comanda.aberta_em)
        .all()
    )

    return render_template(
        "garcom/mesa.html",
        mesa=mesa_obj,
        comandas_abertas=comandas_abertas,
    )


# ────────────────────────────────────────────────────────────────
# 3. ABRIR COMANDA
# ────────────────────────────────────────────────────────────────
@bp.route("/mesa/<int:numero>/abrir", methods=["POST"])
@garcom_required
def abrir_comanda(numero):
    """Cria uma nova comanda (individual ou coletiva) para a mesa."""
    mesa_obj = Mesa.query.filter_by(numero=numero, ativa=True).first_or_404()
    tipo         = request.form.get("tipo", "coletiva")
    nome_cliente = request.form.get("nome_cliente", "").strip() or None

    if tipo not in ("individual", "coletiva"):
        tipo = "coletiva"

    comanda = Comanda(
        mesa_id=mesa_obj.id,
        tipo=tipo,
        nome_cliente=nome_cliente,
        status="aberta",
    )
    db.session.add(comanda)
    db.session.commit()

    label = f"individual — {nome_cliente}" if nome_cliente else tipo
    flash(f"Comanda {label} aberta para a Mesa {numero}.", "success")
    return redirect(url_for("garcom.controle_comanda", comanda_id=comanda.id))


# ────────────────────────────────────────────────────────────────
# 4. CONTROLE DA COMANDA (lançar pedidos, ver histórico)
# ────────────────────────────────────────────────────────────────
@bp.route("/comanda/<int:comanda_id>")
@garcom_required
def controle_comanda(comanda_id):
    comanda = db.get_or_404(Comanda, comanda_id)

    categorias = (
        Categoria.query
        .filter_by(ativa=True)
        .order_by(Categoria.ordem, Categoria.nome)
        .all()
    )

    pedidos = (
        Pedido.query
        .filter_by(comanda_id=comanda_id)
        .order_by(Pedido.criado_em.desc())
        .all()
    )

    # Todas as outras comandas abertas da mesma mesa
    outras_comandas = (
        Comanda.query
        .filter(
            Comanda.mesa_id == comanda.mesa_id,
            Comanda.status == "aberta",
            Comanda.id != comanda_id,
        )
        .all()
    )

    return render_template(
        "garcom/comanda.html",
        comanda=comanda,
        mesa=comanda.mesa,
        categorias=categorias,
        pedidos=pedidos,
        outras_comandas=outras_comandas,
    )


# ────────────────────────────────────────────────────────────────
# 5. ENVIAR PEDIDO
# ────────────────────────────────────────────────────────────────
@bp.route("/pedido", methods=["POST"])
@garcom_required
def enviar_pedido():
    comanda_id = request.form.get("comanda_id")
    observacao = request.form.get("observacao", "").strip()

    if not comanda_id:
        flash("Comanda não informada.", "danger")
        return redirect(url_for("garcom.index"))

    comanda = db.session.get(Comanda, int(comanda_id))
    if not comanda or comanda.status != "aberta":
        flash("Comanda inválida ou já fechada.", "danger")
        return redirect(url_for("garcom.index"))

    itens_pedido = []
    for key, value in request.form.items():
        if key.startswith("item_"):
            try:
                item_id    = int(key.split("_", 1)[1])
                quantidade = int(value)
                if quantidade > 0:
                    itens_pedido.append((item_id, quantidade))
            except (ValueError, IndexError):
                continue

    if not itens_pedido:
        flash("Selecione ao menos um item.", "warning")
        return redirect(url_for("garcom.controle_comanda", comanda_id=comanda_id))

    pedido = Pedido(
        comanda_id=comanda.id,
        mesa_numero=comanda.mesa.numero,
        observacao=observacao,
        status="aguardando",
    )
    db.session.add(pedido)
    db.session.flush()

    for item_id, quantidade in itens_pedido:
        item = db.session.get(ItemCardapio, item_id)
        if item and item.disponivel:
            db.session.add(PedidoItem(
                pedido_id=pedido.id,
                cardapio_id=item.id,
                nome_item=item.nome,
                preco_unit=item.preco,
                quantidade=quantidade,
            ))

    db.session.commit()
    flash("Pedido enviado para a cozinha!", "success")
    return redirect(url_for("garcom.confirmacao", pedido_id=pedido.id))


# ────────────────────────────────────────────────────────────────
# 6+7. FECHAR COMANDA (GET = resumo, POST = confirma)
# ────────────────────────────────────────────────────────────────
@bp.route("/comanda/<int:comanda_id>/fechar", methods=["GET", "POST"])
@garcom_required
def fechar_comanda(comanda_id):
    comanda = db.get_or_404(Comanda, comanda_id)

    if comanda.status == "fechada":
        flash("Esta comanda já foi fechada.", "info")
        return redirect(url_for("garcom.mesa", numero=comanda.mesa.numero))

    if request.method == "POST":
        comanda.status     = "fechada"
        comanda.fechada_em = datetime.utcnow()
        db.session.commit()
        flash(f"Comanda fechada! Total: R$ {comanda.total:.2f}".replace(".", ","), "success")
        return redirect(url_for("garcom.mesa", numero=comanda.mesa.numero))

    # GET → tela de resumo com tudo que foi consumido
    # Consolida itens: {nome: {qtd, subtotal}} — ignora cancelados
    itens_consolidados = {}
    for pedido in comanda.pedidos:
        if pedido.status == "cancelado":
            continue
        for pi in pedido.itens:
            key = pi.nome_item
            if key not in itens_consolidados:
                itens_consolidados[key] = {
                    "nome":     pi.nome_item,
                    "qtd":      0,
                    "unit":     float(pi.preco_unit),
                    "subtotal": 0.0,
                }
            itens_consolidados[key]["qtd"]      += pi.quantidade
            itens_consolidados[key]["subtotal"] += float(pi.preco_unit) * pi.quantidade

    itens_lista = sorted(itens_consolidados.values(), key=lambda x: x["nome"])

    return render_template(
        "garcom/fechar_comanda.html",
        comanda=comanda,
        mesa=comanda.mesa,
        itens_lista=itens_lista,
        total=comanda.total,
    )


# ────────────────────────────────────────────────────────────────
# 8. CONFIRMAÇÃO DE PEDIDO ENVIADO
# ────────────────────────────────────────────────────────────────
@bp.route("/confirmacao/<int:pedido_id>")
@garcom_required
def confirmacao(pedido_id):
    pedido = db.get_or_404(Pedido, pedido_id)
    return render_template("garcom/confirmacao.html", pedido=pedido)


# ────────────────────────────────────────────────────────────────
# 9. CANCELAR PEDIDO
# ────────────────────────────────────────────────────────────────
@bp.route("/pedido/<int:pedido_id>/cancelar", methods=["POST"])
@garcom_required
def cancelar_pedido(pedido_id):
    pedido = db.get_or_404(Pedido, pedido_id)

    # Só pode cancelar se ainda não foi entregue
    if pedido.status in ("entregue",):
        flash("Pedido já entregue — não pode ser cancelado.", "warning")
        return redirect(url_for("garcom.controle_comanda",
                                comanda_id=pedido.comanda_id))

    pedido.status = "cancelado"
    db.session.commit()
    flash(f"Pedido #{pedido.id} cancelado.", "info")
    return redirect(url_for("garcom.controle_comanda",
                            comanda_id=pedido.comanda_id))
