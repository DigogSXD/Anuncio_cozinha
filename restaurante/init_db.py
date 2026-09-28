"""
init_db.py — Inicializa o banco de dados e cria os usuários padrão.

Execute uma única vez após configurar o .env:
    python init_db.py
"""

from app import app
from models import db, Usuario, TV, Playlist, Categoria, Mesa


def init():
    with app.app_context():
        # Cria todas as tabelas definidas nos models
        db.create_all()
        print("✔  Tabelas criadas / verificadas.")

        # ── Usuários padrão ──────────────────────────────────────────
        usuarios_padrao = [
            ("Administrador", "admin@restaurante.com",  "admin123",  "admin"),
            ("Garçom",        "garcom@restaurante.com", "garcom123", "garcom"),
            ("Cozinha",       "cozinha@restaurante.com","cozinha123","cozinha"),
        ]
        for nome, email, senha, role in usuarios_padrao:
            if not Usuario.query.filter_by(email=email).first():
                u = Usuario(nome=nome, email=email, role=role)
                u.set_senha(senha)
                db.session.add(u)
                print(f"✔  Usuário '{role}' criado  ({email} / {senha})")
            else:
                print(f"ℹ  Usuário '{role}' já existe.")

        # ── TVs padrão ───────────────────────────────────────────────
        slugs_padrao = [("TV 1", "1"), ("TV 2", "2"), ("TV 3", "3"), ("Todas as TVs", "todos")]
        for nome, slug in slugs_padrao:
            if not TV.query.filter_by(slug=slug).first():
                db.session.add(TV(nome=nome, slug=slug))
        print("✔  TVs padrão verificadas.")

        # ── Playlist principal ───────────────────────────────────────
        pl = Playlist.query.filter_by(nome="Principal").first()
        if not pl:
            pl = Playlist(nome="Principal", descricao="Playlist padrão")
            db.session.add(pl)
            db.session.flush()
            for tv in TV.query.all():
                tv.playlist = pl
        print("✔  Playlist principal verificada.")

        # ── Categorias padrão ────────────────────────────────────────
        cats = ["Entradas", "Pratos Principais", "Bebidas", "Sobremesas"]
        for i, nome in enumerate(cats, start=1):
            if not Categoria.query.filter_by(nome=nome).first():
                db.session.add(Categoria(nome=nome, ordem=i))
        print("✔  Categorias do cardápio verificadas.")

        # ── Mesas de 1 a 10 (admin pode ajustar depois) ──────────────
        for n in range(1, 11):
            if not Mesa.query.filter_by(numero=n).first():
                db.session.add(Mesa(numero=n))
        print("✔  Mesas 1–10 verificadas.")

        db.session.commit()
        print("\n🚀  Banco inicializado com sucesso!")
        print("   Acesse: http://localhost:5000")
        print()
        print("   ADMIN   → admin@restaurante.com   / admin123")
        print("   GARÇOM  → garcom@restaurante.com  / garcom123")
        print("   COZINHA → cozinha@restaurante.com / cozinha123")
        print()
        print("   ⚠️  Troque as senhas após o primeiro login!\n")


if __name__ == "__main__":
    init()
