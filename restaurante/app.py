"""
app.py — Aplicação principal Flask do Sistema de Gestão de Restaurante.

Módulos cobertos:
  - Autenticação (login/logout)
  - Admin: Dashboard, TVs, Playlists, Mídias, Cardápio, Mesas
  - Digital Signage: rotas /tv/<slug> com API JSON para o player
  - Garçom: abertura de comanda e lançamento de pedidos (mobile-first)
  - Cozinha (KDS): visualização e atualização de status em tempo real
"""

import os
from datetime import datetime
from flask import (
    Flask, render_template, redirect, url_for,
    request, flash, jsonify, abort
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from models import (
    db, Usuario, TV, Playlist, Midia,
    Categoria, ItemCardapio, Mesa, Comanda, Pedido, PedidoItem,
    tv_playlist
)

# ── Carrega variáveis de ambiente ──────────────────────────────────────────
load_dotenv()

# ── Extensões de arquivo permitidas ───────────────────────────────────────
ALLOWED_IMG = {"png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_VID = {"mp4", "webm", "ogg"}
ALLOWED_ALL = ALLOWED_IMG | ALLOWED_VID


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_ALL


def tipo_midia(filename: str) -> str:
    ext = filename.rsplit(".", 1)[1].lower()
    return "video" if ext in ALLOWED_VID else "imagem"


# ── Factory da aplicação ───────────────────────────────────────────────────
def create_app() -> Flask:
    app = Flask(__name__)

    # Configurações gerais
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-inseguro-troque")
    app.config["MAX_CONTENT_LENGTH"] = 512 * 1024 * 1024  # 512 MB

    # Banco de dados MySQL via PyMySQL
    user     = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "")
    host     = os.getenv("MYSQL_HOST", "127.0.0.1")
    port     = os.getenv("MYSQL_PORT", "3306")
    dbname   = os.getenv("MYSQL_DATABASE", "restaurante_db")
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}?charset=utf8mb4"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Upload path
    upload_base = os.path.join(app.root_path, "static", "uploads")
    app.config["UPLOAD_IMG"] = os.path.join(upload_base, "imagens")
    app.config["UPLOAD_VID"] = os.path.join(upload_base, "videos")
    os.makedirs(app.config["UPLOAD_IMG"], exist_ok=True)
    os.makedirs(app.config["UPLOAD_VID"], exist_ok=True)

    # Inicializa extensões
    db.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Faça login para acessar esta página."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    # Registra blueprints
    from routes.auth    import bp as auth_bp
    from routes.admin   import bp as admin_bp
    from routes.tv      import bp as tv_bp
    from routes.garcom  import bp as garcom_bp
    from routes.cozinha import bp as cozinha_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp,   url_prefix="/admin")
    app.register_blueprint(tv_bp,      url_prefix="/tv")
    app.register_blueprint(garcom_bp,  url_prefix="/garcom")
    app.register_blueprint(cozinha_bp, url_prefix="/cozinha")

    # Rota raiz redireciona para o admin
    @app.route("/")
    def index():
        return redirect(url_for("admin.dashboard"))

    # Filtro Jinja para formatar moeda BRL
    @app.template_filter("brl")
    def brl_filter(value):
        try:
            return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (TypeError, ValueError):
            return value

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
