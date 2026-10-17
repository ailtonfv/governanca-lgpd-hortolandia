"""Migração 6: ação obrigatória sintética mínima do percurso com medidas."""

from app.modelos import AcaoObrigatoria


def aplicar(sessao):
    AcaoObrigatoria.__table__.create(bind=sessao.connection(), checkfirst=True)
