"""Migração 4: projeção da análise vigente de cada versão do Instrumento."""

from app.modelos import AnaliseInstrumento


def aplicar(sessao):
    AnaliseInstrumento.__table__.create(bind=sessao.connection(), checkfirst=True)
