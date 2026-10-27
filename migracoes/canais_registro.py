"""Migração 15: projeção histórica dos canais confirmados na abertura."""

from app.modelos import ConfirmacaoCanaisRegistro, RegistroCanal


def aplicar(sessao):
    conexao = sessao.connection()
    ConfirmacaoCanaisRegistro.__table__.create(bind=conexao, checkfirst=True)
    RegistroCanal.__table__.create(bind=conexao, checkfirst=True)
