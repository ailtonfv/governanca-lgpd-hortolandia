"""Migração 7: pendência mínima do percurso de devolução do M1a."""

from app.modelos import Pendencia


def aplicar(sessao):
    Pendencia.__table__.create(bind=sessao.connection(), checkfirst=True)
