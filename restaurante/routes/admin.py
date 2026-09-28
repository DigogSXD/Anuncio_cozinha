"""
routes/admin.py — Painel administrativo completo.

Cobre:
  - Dashboard com resumo
  - CRUD de TVs e associação com Playlists
  - CRUD de Playlists e upload de Mídias
  - CRUD de Categorias e Itens do Cardápio
  - Gerenciamento de Mesas
  - Visualização de Pedidos e Comandas
"""

import os
from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, current_app, jsonify
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from models import (
    db, TV, Playlist, Midia, Categoria, ItemCardapio,
    Mesa, Comanda, Pedido, PedidoItem, Usuario
)

bp = Blueprint("admin", __name__)


def _allowed(filename):
    ALLOWED = {"png", "jpg", "jpeg", "gif", "webp", "mp4", "webm", "ogg"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED


def _tipo(filename):
    ext = filename.rsplit(".", 1)[1].lower()
    return "video" if ext in {"mp4", "webm", "ogg"} else "imagem"


# ─────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────

@bp.route("/")
@login_required
def dashboard():
    total_pedidos_hoje = (
        Pedido.query
        .filter(db.func.date(Pedido.criado_em) == db.func.curdate())
        .count()
    )
    aguardando = Pedido.query.filter_by(status="aguardando").count()
    em_preparo = Pedido.query.filter_by(status="em_preparo").count()
    mesas_ativas = Comanda.query.filter_by(status="aberta").count()
    total_tvs = TV.query.filter_by(ativa=True).count()
    total_midias = Midia.query.filter_by(ativa=True).count()
    total_itens = ItemCardapio.query.filter_by(disponivel=True).count()

    return render_template(
        "admin/dashboard.html",
        total_pedidos_hoje=total_pedidos_hoje,
        aguardando=aguardando,
        em_preparo=em_preparo,
        mesas_ativas=mesas_ativas,
        total_tvs=total_tvs,
        total_midias=total_midias,
        total_itens=total_itens,
    )


# ─────────────────────────────────────────────────────────────
# TVs
# ─────────────────────────────────────────────────────────────

@bp.route("/tvs")
@login_required
def tvs():
    lista = TV.query.order_by(TV.id).all()
    playlists = Playlist.query.order_by(Playlist.nome).all()
    return render_template("admin/tvs.html", tvs=lista, playlists=playlists)


@bp.route("/tvs/criar", methods=["POST"])
@login_required
def criar_tv():
    nome = request.form.get("nome", "").strip()
    slug = request.form.get("slug", "").strip().lower().replace(" ", "-")

    if not nome or not slug:
        flash("Nome e slug são obrigatórios.", "danger")
        return redirect(url_for("admin.tvs"))

    if TV.query.filter_by(slug=slug).first():
        flash(f'Já existe uma TV com o slug "{slug}".', "warning")
        return redirect(url_for("admin.tvs"))

    tv = TV(nome=nome, slug=slug)
    db.session.add(tv)
    db.session.flush()

    playlist_id = request.form.get("playlist_id")
    if playlist_id:
        playlist = db.session.get(Playlist, int(playlist_id))
        if playlist:
            tv.playlist = playlist

    db.session.commit()
    flash(f'TV "{nome}" criada com sucesso.', "success")
    return redirect(url_for("admin.tvs"))


@bp.route("/tvs/<int:tv_id>/editar", methods=["POST"])
@login_required
def editar_tv(tv_id):
    tv = db.get_or_404(TV, tv_id)
    tv.nome = request.form.get("nome", tv.nome).strip()
    novo_slug = request.form.get("slug", tv.slug).strip().lower()

    conflito = TV.query.filter(TV.slug == novo_slug, TV.id != tv_id).first()
    if conflito:
        flash("Já existe outra TV com esse slug.", "warning")
        return redirect(url_for("admin.tvs"))

    tv.slug = novo_slug
    tv.ativa = "ativa" in request.form

    playlist_id = request.form.get("playlist_id")
    if playlist_id:
        playlist = db.session.get(Playlist, int(playlist_id))
        tv.playlist = playlist
    else:
        tv.playlist = None

    db.session.commit()
    flash("TV atualizada.", "success")
    return redirect(url_for("admin.tvs"))


@bp.route("/tvs/<int:tv_id>/excluir", methods=["POST"])
@login_required
def excluir_tv(tv_id):
    tv = db.get_or_404(TV, tv_id)
    db.session.delete(tv)
    db.session.commit()
    flash("TV removida.", "info")
    return redirect(url_for("admin.tvs"))


# ─────────────────────────────────────────────────────────────
# PLAYLISTS
# ─────────────────────────────────────────────────────────────

@bp.route("/playlists")
@login_required
def playlists():
    lista = Playlist.query.order_by(Playlist.nome).all()
    return render_template("admin/playlists.html", playlists=lista)


@bp.route("/playlists/criar", methods=["POST"])
@login_required
def criar_playlist():
    nome = request.form.get("nome", "").strip()
    descricao = request.form.get("descricao", "").strip()
    if not nome:
        flash("Nome é obrigatório.", "danger")
        return redirect(url_for("admin.playlists"))
    pl = Playlist(nome=nome, descricao=descricao)
    db.session.add(pl)
    db.session.commit()
    flash(f'Playlist "{nome}" criada.', "success")
    return redirect(url_for("admin.playlists"))


@bp.route("/playlists/<int:pl_id>")
@login_required
def ver_playlist(pl_id):
    pl = db.get_or_404(Playlist, pl_id)
    midias = Midia.query.filter_by(playlist_id=pl_id).order_by(Midia.ordem).all()
    return render_template("admin/playlist_detalhe.html", playlist=pl, midias=midias)


@bp.route("/playlists/<int:pl_id>/editar", methods=["POST"])
@login_required
def editar_playlist(pl_id):
    pl = db.get_or_404(Playlist, pl_id)
    pl.nome = request.form.get("nome", pl.nome).strip()
    pl.descricao = request.form.get("descricao", pl.descricao or "").strip()
    db.session.commit()
    flash("Playlist atualizada.", "success")
    return redirect(url_for("admin.ver_playlist", pl_id=pl_id))


@bp.route("/playlists/<int:pl_id>/excluir", methods=["POST"])
@login_required
def excluir_playlist(pl_id):
    pl = db.get_or_404(Playlist, pl_id)
    db.session.delete(pl)
    db.session.commit()
    flash("Playlist excluída.", "info")
    return redirect(url_for("admin.playlists"))


# ─────────────────────────────────────────────────────────────
# MÍDIAS
# ─────────────────────────────────────────────────────────────

@bp.route("/playlists/<int:pl_id>/midia/upload", methods=["POST"])
@login_required
def upload_midia(pl_id):
    pl = db.get_or_404(Playlist, pl_id)

    if "arquivo" not in request.files:
        flash("Nenhum arquivo enviado.", "danger")
        return redirect(url_for("admin.ver_playlist", pl_id=pl_id))

    arquivo = request.files["arquivo"]
    if arquivo.filename == "":
        flash("Arquivo vazio.", "danger")
        return redirect(url_for("admin.ver_playlist", pl_id=pl_id))

    if not _allowed(arquivo.filename):
        flash("Tipo de arquivo não permitido.", "danger")
        return redirect(url_for("admin.ver_playlist", pl_id=pl_id))

    tipo = _tipo(arquivo.filename)
    nome_seguro = secure_filename(arquivo.filename)
    # Evita colisão de nomes
    import time
    nome_final = f"{int(time.time())}_{nome_seguro}"

    if tipo == "video":
        destino = os.path.join(current_app.config["UPLOAD_VID"], nome_final)
        caminho_relativo = f"uploads/videos/{nome_final}"
    else:
        destino = os.path.join(current_app.config["UPLOAD_IMG"], nome_final)
        caminho_relativo = f"uploads/imagens/{nome_final}"

    arquivo.save(destino)

    duracao = int(request.form.get("duracao_seg", 10))
    ultima_ordem = db.session.query(db.func.max(Midia.ordem)).filter_by(
        playlist_id=pl_id
    ).scalar() or 0

    nome_exibicao = request.form.get("nome_exibicao", "").strip() or nome_seguro
    midia = Midia(
        playlist_id=pl_id,
        nome=nome_exibicao,
        tipo=tipo,
        arquivo=caminho_relativo,
        duracao_seg=duracao,
        ordem=ultima_ordem + 1,
    )
    db.session.add(midia)
    db.session.commit()
    flash(f'Mídia "{nome_exibicao}" adicionada.', "success")
    return redirect(url_for("admin.ver_playlist", pl_id=pl_id))


@bp.route("/midia/<int:midia_id>/editar", methods=["POST"])
@login_required
def editar_midia(midia_id):
    midia = db.get_or_404(Midia, midia_id)
    midia.nome = request.form.get("nome", midia.nome).strip()
    midia.duracao_seg = int(request.form.get("duracao_seg", midia.duracao_seg))
    midia.ordem = int(request.form.get("ordem", midia.ordem))
    midia.ativa = "ativa" in request.form
    db.session.commit()
    flash("Mídia atualizada.", "success")
    return redirect(url_for("admin.ver_playlist", pl_id=midia.playlist_id))


@bp.route("/midia/<int:midia_id>/excluir", methods=["POST"])
@login_required
def excluir_midia(midia_id):
    midia = db.get_or_404(Midia, midia_id)
    pl_id = midia.playlist_id
    # Remove o arquivo do disco
    caminho = os.path.join(current_app.root_path, "static", midia.arquivo)
    if os.path.exists(caminho):
        os.remove(caminho)
    db.session.delete(midia)
    db.session.commit()
    flash("Mídia excluída.", "info")
    return redirect(url_for("admin.ver_playlist", pl_id=pl_id))


@bp.route("/midias/reordenar", methods=["POST"])
@login_required
def reordenar_midias():
    """Recebe JSON: {"ordem": [id1, id2, id3, ...]} e salva a nova ordem."""
    data = request.get_json(silent=True)
    if not data or "ordem" not in data:
        return jsonify({"ok": False}), 400
    for idx, mid_id in enumerate(data["ordem"], start=1):
        midia = db.session.get(Midia, mid_id)
        if midia:
            midia.ordem = idx
    db.session.commit()
    return jsonify({"ok": True})


# ─────────────────────────────────────────────────────────────
# CARDÁPIO — CATEGORIAS
# ─────────────────────────────────────────────────────────────

@bp.route("/cardapio")
@login_required
def cardapio():
    categorias = (
        Categoria.query
        .order_by(Categoria.ordem, Categoria.nome)
        .all()
    )
    return render_template("admin/cardapio.html", categorias=categorias)


@bp.route("/cardapio/categoria/criar", methods=["POST"])
@login_required
def criar_categoria():
    nome = request.form.get("nome", "").strip()
    if not nome:
        flash("Nome da categoria é obrigatório.", "danger")
        return redirect(url_for("admin.cardapio"))
    ultima = db.session.query(db.func.max(Categoria.ordem)).scalar() or 0
    cat = Categoria(nome=nome, ordem=ultima + 1)
    db.session.add(cat)
    db.session.commit()
    flash(f'Categoria "{nome}" criada.', "success")
    return redirect(url_for("admin.cardapio"))


@bp.route("/cardapio/categoria/<int:cat_id>/excluir", methods=["POST"])
@login_required
def excluir_categoria(cat_id):
    cat = db.get_or_404(Categoria, cat_id)
    db.session.delete(cat)
    db.session.commit()
    flash("Categoria excluída.", "info")
    return redirect(url_for("admin.cardapio"))


# ─────────────────────────────────────────────────────────────
# CARDÁPIO — ITENS
# ─────────────────────────────────────────────────────────────

@bp.route("/cardapio/item/criar", methods=["POST"])
@login_required
def criar_item():
    nome = request.form.get("nome", "").strip()
    preco_str = request.form.get("preco", "0").replace(",", ".")
    categoria_id = request.form.get("categoria_id") or None
    descricao = request.form.get("descricao", "").strip()

    if not nome:
        flash("Nome do item é obrigatório.", "danger")
        return redirect(url_for("admin.cardapio"))

    try:
        preco = float(preco_str)
    except ValueError:
        flash("Preço inválido.", "danger")
        return redirect(url_for("admin.cardapio"))

    item = ItemCardapio(
        nome=nome,
        descricao=descricao,
        preco=preco,
        categoria_id=int(categoria_id) if categoria_id else None,
    )
    db.session.add(item)
    db.session.commit()
    flash(f'Item "{nome}" adicionado ao cardápio.', "success")
    return redirect(url_for("admin.cardapio"))


@bp.route("/cardapio/item/<int:item_id>/editar", methods=["POST"])
@login_required
def editar_item(item_id):
    item = db.get_or_404(ItemCardapio, item_id)
    item.nome = request.form.get("nome", item.nome).strip()
    item.descricao = request.form.get("descricao", item.descricao or "").strip()
    preco_str = request.form.get("preco", str(item.preco)).replace(",", ".")
    try:
        item.preco = float(preco_str)
    except ValueError:
        flash("Preço inválido.", "danger")
        return redirect(url_for("admin.cardapio"))
    cat_id = request.form.get("categoria_id")
    item.categoria_id = int(cat_id) if cat_id else None
    item.disponivel = "disponivel" in request.form
    db.session.commit()
    flash("Item atualizado.", "success")
    return redirect(url_for("admin.cardapio"))


@bp.route("/cardapio/item/<int:item_id>/excluir", methods=["POST"])
@login_required
def excluir_item(item_id):
    item = db.get_or_404(ItemCardapio, item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Item removido.", "info")
    return redirect(url_for("admin.cardapio"))


# ─────────────────────────────────────────────────────────────
# MESAS
# ─────────────────────────────────────────────────────────────

@bp.route("/mesas")
@login_required
def mesas():
    lista = Mesa.query.order_by(Mesa.numero).all()
    return render_template("admin/mesas.html", mesas=lista)


@bp.route("/mesas/definir-quantidade", methods=["POST"])
@login_required
def definir_quantidade_mesas():
    """
    Define o total de mesas do restaurante em um único passo.
    - Se o novo total > atual: cria as mesas que faltam.
    - Se o novo total < atual: desativa as mesas excedentes (sem apagar histórico).
    """
    try:
        quantidade = int(request.form.get("quantidade", 0))
    except ValueError:
        flash("Quantidade inválida.", "danger")
        return redirect(url_for("admin.mesas"))

    if quantidade < 1 or quantidade > 200:
        flash("Quantidade deve ser entre 1 e 200.", "warning")
        return redirect(url_for("admin.mesas"))

    # Garante que mesas 1..quantidade existem e estão ativas
    for n in range(1, quantidade + 1):
        mesa = Mesa.query.filter_by(numero=n).first()
        if mesa:
            mesa.ativa = True
        else:
            db.session.add(Mesa(numero=n, ativa=True))

    # Desativa mesas acima da quantidade definida
    Mesa.query.filter(Mesa.numero > quantidade).update({"ativa": False})

    db.session.commit()
    flash(f"Restaurante configurado com {quantidade} mesa(s).", "success")
    return redirect(url_for("admin.mesas"))


@bp.route("/mesas/criar", methods=["POST"])
@login_required
def criar_mesa():
    numero = request.form.get("numero")
    if not numero:
        flash("Número da mesa é obrigatório.", "danger")
        return redirect(url_for("admin.mesas"))
    if Mesa.query.filter_by(numero=int(numero)).first():
        flash(f"Mesa {numero} já existe.", "warning")
        return redirect(url_for("admin.mesas"))
    mesa = Mesa(numero=int(numero), descricao=request.form.get("descricao", ""))
    db.session.add(mesa)
    db.session.commit()
    flash(f"Mesa {numero} criada.", "success")
    return redirect(url_for("admin.mesas"))


@bp.route("/mesas/<int:mesa_id>/toggle", methods=["POST"])
@login_required
def toggle_mesa(mesa_id):
    mesa = db.get_or_404(Mesa, mesa_id)
    mesa.ativa = not mesa.ativa
    db.session.commit()
    estado = "ativada" if mesa.ativa else "desativada"
    flash(f"Mesa {mesa.numero} {estado}.", "info")
    return redirect(url_for("admin.mesas"))


@bp.route("/mesas/<int:mesa_id>/excluir", methods=["POST"])
@login_required
def excluir_mesa(mesa_id):
    mesa = db.get_or_404(Mesa, mesa_id)
    db.session.delete(mesa)
    db.session.commit()
    flash("Mesa removida.", "info")
    return redirect(url_for("admin.mesas"))


# ─────────────────────────────────────────────────────────────
# USUÁRIOS (garçom / cozinha)
# ─────────────────────────────────────────────────────────────

@bp.route("/usuarios")
@login_required
def usuarios():
    lista = Usuario.query.order_by(Usuario.role, Usuario.nome).all()
    return render_template("admin/usuarios.html", usuarios=lista)


@bp.route("/usuarios/criar", methods=["POST"])
@login_required
def criar_usuario():
    nome  = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()
    senha = request.form.get("senha", "").strip()
    role  = request.form.get("role", "garcom")

    if not nome or not email or not senha:
        flash("Nome, e-mail e senha são obrigatórios.", "danger")
        return redirect(url_for("admin.usuarios"))

    if role not in ("admin", "garcom", "cozinha"):
        flash("Tipo de usuário inválido.", "danger")
        return redirect(url_for("admin.usuarios"))

    if Usuario.query.filter_by(email=email).first():
        flash(f'E-mail "{email}" já está em uso.', "warning")
        return redirect(url_for("admin.usuarios"))

    u = Usuario(nome=nome, email=email, role=role)
    u.set_senha(senha)
    db.session.add(u)
    db.session.commit()
    flash(f'Usuário "{nome}" ({role}) criado.', "success")
    return redirect(url_for("admin.usuarios"))


@bp.route("/usuarios/<int:usuario_id>/editar", methods=["POST"])
@login_required
def editar_usuario(usuario_id):
    u = db.get_or_404(Usuario, usuario_id)
    u.nome  = request.form.get("nome", u.nome).strip()
    novo_email = request.form.get("email", u.email).strip().lower()
    role   = request.form.get("role", u.role)

    # Não permite remover o último admin
    if u.role == "admin" and role != "admin":
        outros_admins = Usuario.query.filter(
            Usuario.role == "admin", Usuario.id != u.id
        ).count()
        if outros_admins == 0:
            flash("Não é possível remover o último administrador.", "danger")
            return redirect(url_for("admin.usuarios"))

    conflito = Usuario.query.filter(
        Usuario.email == novo_email, Usuario.id != u.id
    ).first()
    if conflito:
        flash("E-mail já em uso por outro usuário.", "warning")
        return redirect(url_for("admin.usuarios"))

    u.email = novo_email
    u.role  = role
    u.ativo = "ativo" in request.form

    nova_senha = request.form.get("nova_senha", "").strip()
    if nova_senha:
        u.set_senha(nova_senha)
        flash(f'Senha de "{u.nome}" alterada.', "info")

    db.session.commit()
    flash(f'Usuário "{u.nome}" atualizado.', "success")
    return redirect(url_for("admin.usuarios"))


@bp.route("/usuarios/<int:usuario_id>/excluir", methods=["POST"])
@login_required
def excluir_usuario(usuario_id):
    u = db.get_or_404(Usuario, usuario_id)

    if u.id == current_user.id:
        flash("Você não pode excluir sua própria conta.", "danger")
        return redirect(url_for("admin.usuarios"))

    if u.role == "admin":
        outros = Usuario.query.filter(
            Usuario.role == "admin", Usuario.id != u.id
        ).count()
        if outros == 0:
            flash("Não é possível excluir o último administrador.", "danger")
            return redirect(url_for("admin.usuarios"))

    db.session.delete(u)
    db.session.commit()
    flash(f'Usuário "{u.nome}" removido.', "info")
    return redirect(url_for("admin.usuarios"))


# ─────────────────────────────────────────────────────────────
# PEDIDOS (visão admin)
# ─────────────────────────────────────────────────────────────

@bp.route("/pedidos")
@login_required
def pedidos():
    status_filtro = request.args.get("status", "todos")
    query = Pedido.query.order_by(Pedido.criado_em.desc())
    if status_filtro != "todos":
        query = query.filter_by(status=status_filtro)
    lista = query.limit(200).all()
    return render_template("admin/pedidos.html", pedidos=lista,
                           status_filtro=status_filtro)


# ─────────────────────────────────────────────────────────────
# RELATÓRIOS E GRÁFICOS
# ─────────────────────────────────────────────────────────────

@bp.route("/relatorios")
@login_required
def relatorios():
    """Dashboard de gráficos com dados mensais e anuais."""
    from datetime import datetime, timedelta
    from sqlalchemy import func, extract

    _MESES_PT = [
        "Janeiro","Fevereiro","Março","Abril","Maio","Junho",
        "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"
    ]
    def _nome_mes(mes: int, ano: int) -> str:
        return f"{_MESES_PT[mes - 1]} de {ano}"

    # ── Dados do mês atual ─────────────────────────────────────
    hoje = datetime.utcnow().date()
    inicio_mes = hoje.replace(day=1)
    
    pedidos_mes = (
        Pedido.query
        .filter(Pedido.criado_em >= inicio_mes)
        .all()
    )
    total_mes = len(pedidos_mes)
    
    # Status no mês
    status_mes = {}
    for p in pedidos_mes:
        status_mes[p.status] = status_mes.get(p.status, 0) + 1
    
    # Dias do mês (últimos 30 dias)
    dados_diarios = []
    for i in range(29, -1, -1):
        data = hoje - timedelta(days=i)
        count = (
            Pedido.query
            .filter(func.date(Pedido.criado_em) == data)
            .count()
        )
        dados_diarios.append({
            "data": data.strftime("%d/%m"),
            "pedidos": count,
        })
    
    # ── Dados do ano atual ─────────────────────────────────────
    ano_atual = hoje.year
    dados_mensais = []
    meses_nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                   "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    
    for mes in range(1, 13):
        count = (
            Pedido.query
            .filter(
                extract('year', Pedido.criado_em) == ano_atual,
                extract('month', Pedido.criado_em) == mes
            )
            .count()
        )
        dados_mensais.append({
            "mes": meses_nomes[mes - 1],
            "pedidos": count,
        })
    
    # ── Total do ano
    total_ano = sum(d["pedidos"] for d in dados_mensais)
    
    # ── Ticket médio (últimos 30 dias)
    total_vendas_mes = 0
    for p in pedidos_mes:
        total_vendas_mes += sum(
            float(pi.preco_unit) * pi.quantidade for pi in p.itens
        )
    ticket_medio = total_vendas_mes / total_mes if total_mes > 0 else 0
    
    return render_template(
        "admin/relatorios.html",
        dados_diarios=dados_diarios,
        dados_mensais=dados_mensais,
        total_mes=total_mes,
        total_ano=total_ano,
        ticket_medio=ticket_medio,
        status_mes=status_mes,
        mes_atual=_nome_mes(inicio_mes.month, inicio_mes.year),
        ano_atual=ano_atual,
    )
