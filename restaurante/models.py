"""
models.py — Modelos SQLAlchemy do sistema de gestão de restaurante.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# =============================================================
# AUTENTICAÇÃO
# =============================================================

class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id         = db.Column(db.Integer, primary_key=True)
    nome       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(150), nullable=False, unique=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    # role: 'admin' | 'garcom' | 'cozinha'
    role       = db.Column(db.String(20), nullable=False, default="admin")
    ativo      = db.Column(db.Boolean, default=True)
    criado_em  = db.Column(db.DateTime, default=datetime.utcnow)

    def set_senha(self, senha: str):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_garcom(self):
        return self.role == "garcom"

    @property
    def is_cozinha(self):
        return self.role == "cozinha"

    def __repr__(self):
        return f"<Usuario {self.email} [{self.role}]>"


# =============================================================
# DIGITAL SIGNAGE — TVs e Playlists
# =============================================================

class TV(db.Model):
    __tablename__ = "tvs"

    id        = db.Column(db.Integer, primary_key=True)
    nome      = db.Column(db.String(100), nullable=False)
    slug      = db.Column(db.String(50), nullable=False, unique=True)
    ativa     = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Relação com playlist via tv_playlist
    playlist  = db.relationship("Playlist", secondary="tv_playlist",
                                back_populates="tvs", uselist=False)

    def __repr__(self):
        return f"<TV {self.slug}>"


class Playlist(db.Model):
    __tablename__ = "playlists"

    id        = db.Column(db.Integer, primary_key=True)
    nome      = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    midias    = db.relationship("Midia", back_populates="playlist",
                                order_by="Midia.ordem", cascade="all, delete-orphan")
    tvs       = db.relationship("TV", secondary="tv_playlist",
                                back_populates="playlist")

    def __repr__(self):
        return f"<Playlist {self.nome}>"


# Tabela de associação TV <-> Playlist
tv_playlist = db.Table(
    "tv_playlist",
    db.Column("tv_id",       db.Integer, db.ForeignKey("tvs.id"),       primary_key=True),
    db.Column("playlist_id", db.Integer, db.ForeignKey("playlists.id")),
)


class Midia(db.Model):
    __tablename__ = "midias"

    id          = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey("playlists.id"), nullable=False)
    nome        = db.Column(db.String(150), nullable=False)
    tipo        = db.Column(db.Enum("imagem", "video"), nullable=False)
    arquivo     = db.Column(db.String(255), nullable=False)
    duracao_seg = db.Column(db.Integer, default=10)
    ordem       = db.Column(db.Integer, default=0)
    ativa       = db.Column(db.Boolean, default=True)
    criado_em   = db.Column(db.DateTime, default=datetime.utcnow)

    playlist    = db.relationship("Playlist", back_populates="midias")

    def to_dict(self):
        return {
            "id":          self.id,
            "nome":        self.nome,
            "tipo":        self.tipo,
            "arquivo":     self.arquivo,
            "duracao_seg": self.duracao_seg,
            "ordem":       self.ordem,
        }

    def __repr__(self):
        return f"<Midia {self.nome} ({self.tipo})>"


# =============================================================
# CARDÁPIO
# =============================================================

class Categoria(db.Model):
    __tablename__ = "categorias"

    id    = db.Column(db.Integer, primary_key=True)
    nome  = db.Column(db.String(100), nullable=False)
    ordem = db.Column(db.Integer, default=0)
    ativa = db.Column(db.Boolean, default=True)

    itens = db.relationship("ItemCardapio", back_populates="categoria",
                            order_by="ItemCardapio.nome")

    def __repr__(self):
        return f"<Categoria {self.nome}>"


class ItemCardapio(db.Model):
    __tablename__ = "cardapio"

    id           = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"))
    nome         = db.Column(db.String(150), nullable=False)
    descricao    = db.Column(db.String(255))
    preco        = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    disponivel   = db.Column(db.Boolean, default=True)
    criado_em    = db.Column(db.DateTime, default=datetime.utcnow)

    categoria    = db.relationship("Categoria", back_populates="itens")

    def __repr__(self):
        return f"<ItemCardapio {self.nome}>"


# =============================================================
# MESAS E PEDIDOS
# =============================================================

class Mesa(db.Model):
    __tablename__ = "mesas"

    id       = db.Column(db.Integer, primary_key=True)
    numero   = db.Column(db.Integer, nullable=False, unique=True)
    descricao = db.Column(db.String(100))
    ativa    = db.Column(db.Boolean, default=True)

    comandas = db.relationship("Comanda", back_populates="mesa")

    def __repr__(self):
        return f"<Mesa {self.numero}>"


class Comanda(db.Model):
    __tablename__ = "comandas"

    id         = db.Column(db.Integer, primary_key=True)
    mesa_id    = db.Column(db.Integer, db.ForeignKey("mesas.id"), nullable=False)
    status     = db.Column(db.Enum("aberta", "fechada"), default="aberta")
    # individual = cada pessoa paga o seu | coletiva = a mesa paga junto
    tipo       = db.Column(db.Enum("individual", "coletiva"), default="coletiva")
    nome_cliente = db.Column(db.String(100))   # opcional: nome para comanda individual
    aberta_em  = db.Column(db.DateTime, default=datetime.utcnow)
    fechada_em = db.Column(db.DateTime)

    mesa       = db.relationship("Mesa", back_populates="comandas")
    pedidos    = db.relationship("Pedido", back_populates="comanda",
                                 order_by="Pedido.criado_em")

    @property
    def total(self):
        """Soma de todos os itens de todos os pedidos NÃO cancelados desta comanda."""
        valor = 0
        for p in self.pedidos:
            if p.status != "cancelado":
                for i in p.itens:
                    valor += float(i.preco_unit) * i.quantidade
        return valor

    def __repr__(self):
        return f"<Comanda mesa={self.mesa_id} tipo={self.tipo} status={self.status}>"


class Pedido(db.Model):
    __tablename__ = "pedidos"

    id           = db.Column(db.Integer, primary_key=True)
    comanda_id   = db.Column(db.Integer, db.ForeignKey("comandas.id"), nullable=False)
    mesa_numero  = db.Column(db.Integer, nullable=False)
    status       = db.Column(
        db.Enum("aguardando", "em_preparo", "pronto", "entregue", "cancelado"),
        default="aguardando"
    )
    observacao   = db.Column(db.String(255))
    criado_em    = db.Column(db.DateTime, default=datetime.utcnow)

    comanda      = db.relationship("Comanda", back_populates="pedidos")
    itens        = db.relationship("PedidoItem", back_populates="pedido",
                                   cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id":          self.id,
            "mesa_numero": self.mesa_numero,
            "status":      self.status,
            "observacao":  self.observacao,
            "criado_em":   self.criado_em.strftime("%H:%M"),
            "itens": [
                {
                    "nome":       i.nome_item,
                    "quantidade": i.quantidade,
                    "preco_unit": float(i.preco_unit),
                }
                for i in self.itens
            ],
        }

    def __repr__(self):
        return f"<Pedido {self.id} mesa={self.mesa_numero}>"


class PedidoItem(db.Model):
    __tablename__ = "pedido_itens"

    id          = db.Column(db.Integer, primary_key=True)
    pedido_id   = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=False)
    cardapio_id = db.Column(db.Integer, db.ForeignKey("cardapio.id"), nullable=False)
    nome_item   = db.Column(db.String(150), nullable=False)
    preco_unit  = db.Column(db.Numeric(10, 2), nullable=False)
    quantidade  = db.Column(db.Integer, nullable=False, default=1)

    pedido      = db.relationship("Pedido", back_populates="itens")
    item        = db.relationship("ItemCardapio")

    def __repr__(self):
        return f"<PedidoItem {self.nome_item} x{self.quantidade}>"
