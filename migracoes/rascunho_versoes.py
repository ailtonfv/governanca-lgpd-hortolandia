"""Migração 2: persistência do rascunho e das versões do Instrumento."""

from app.modelos import RascunhoInstrumento, VersaoInstrumento


def aplicar(sessao):
    conexao = sessao.connection()
    RascunhoInstrumento.__table__.create(bind=conexao, checkfirst=True)
    VersaoInstrumento.__table__.create(bind=conexao, checkfirst=True)
