"""
routes/auth.py — Autenticação: login e logout com redirecionamento por role.

Roles:
  admin   → /admin/
  garcom  → /garcom/
  cozinha → /cozinha/
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, Usuario

bp = Blueprint("auth", __name__)

# Destino de cada role após o login
_DESTINO = {
    "admin":   "admin.dashboard",
    "garcom":  "garcom.index",
    "cozinha": "cozinha.index",
}


def destino_por_role(usuario):
    """Retorna o endpoint de destino conforme o role do usuário."""
    return _DESTINO.get(usuario.role, "admin.dashboard")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(destino_por_role(current_user)))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario or not usuario.check_senha(senha):
            flash("E-mail ou senha incorretos.", "danger")
            return render_template("auth/login.html")

        if not usuario.ativo:
            flash("Usuário desativado. Fale com o administrador.", "warning")
            return render_template("auth/login.html")

        login_user(usuario, remember=True)
        next_page = request.args.get("next")
        return redirect(next_page or url_for(destino_por_role(usuario)))

    return render_template("auth/login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("auth.login"))
