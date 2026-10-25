"""Migração 12: rascunho separado do FORM 1 integral."""

from app.modelos import RascunhoForm1Integral


def aplicar(sessao):
    RascunhoForm1Integral.__table__.create(bind=sessao.connection(), checkfirst=True)
