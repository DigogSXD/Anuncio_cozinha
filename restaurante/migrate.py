"""
migrate.py — Aplica as colunas novas ao banco sem perder dados.
Execute: python migrate.py
"""
from app import app
from models import db
from sqlalchemy import text

sqls = [
    # Novas colunas na tabela comandas
    "ALTER TABLE comandas ADD COLUMN tipo ENUM('individual','coletiva') NOT NULL DEFAULT 'coletiva'",
    "ALTER TABLE comandas ADD COLUMN nome_cliente VARCHAR(100) NULL",
    # Adiciona status 'cancelado' no enum de pedidos
    "ALTER TABLE pedidos MODIFY COLUMN status ENUM('aguardando','em_preparo','pronto','entregue','cancelado') NOT NULL DEFAULT 'aguardando'",
    # Adiciona coluna ativo em usuarios (se ainda não existir)
    "ALTER TABLE usuarios ADD COLUMN ativo TINYINT(1) NOT NULL DEFAULT 1",
    # Adiciona coluna role em usuarios (se ainda não existir)
    "ALTER TABLE usuarios ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'admin'",
]

with app.app_context():
    with db.engine.connect() as conn:
        for sql in sqls:
            try:
                conn.execute(text(sql))
                print(f"OK  → {sql[:60]}...")
            except Exception as e:
                # Coluna já existe? ignora. Outro erro? mostra.
                msg = str(e)
                if "Duplicate column" in msg or "1060" in msg:
                    print(f"JÁ EXISTE → {sql[:60]}...")
                else:
                    print(f"ERRO → {msg[:120]}")
        conn.commit()
    print("\n✔  Migração concluída!")
