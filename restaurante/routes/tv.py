"""
routes/tv.py — Rotas para o player das Smart TVs (Digital Signage).

/tv/1        → player para a TV com slug "1"
/tv/todos    → player sincronizado para todas as TVs
/tv/<slug>/playlist.json → API que retorna as mídias da playlist em JSON
"""

from flask import Blueprint, render_template, jsonify, abort
from models import db, TV, Midia

bp = Blueprint("tv", __name__)


@bp.route("/<slug>")
def player(slug):
    """Renderiza o player HTML para a TV identificada pelo slug."""
    tv = TV.query.filter_by(slug=slug, ativa=True).first_or_404()
    return render_template("tv/player.html", tv=tv)


@bp.route("/<slug>/playlist.json")
def playlist_json(slug):
    """
    Retorna a playlist da TV em JSON para o player JavaScript.
    Formato:
    {
      "tv": "1",
      "midias": [
        {"id": 1, "tipo": "imagem", "arquivo": "uploads/imagens/foto.jpg",
         "duracao_seg": 8, "ordem": 1},
        {"id": 2, "tipo": "video",  "arquivo": "uploads/videos/promo.mp4",
         "duracao_seg": 0, "ordem": 2},
        ...
      ]
    }
    Apenas mídias ativas, ordenadas pelo campo `ordem`.
    """
    tv = TV.query.filter_by(slug=slug, ativa=True).first_or_404()

    if tv.playlist is None:
        return jsonify({"tv": slug, "midias": []})

    midias = (
        Midia.query
        .filter_by(playlist_id=tv.playlist.id, ativa=True)
        .order_by(Midia.ordem)
        .all()
    )

    return jsonify({
        "tv": slug,
        "midias": [m.to_dict() for m in midias],
    })
