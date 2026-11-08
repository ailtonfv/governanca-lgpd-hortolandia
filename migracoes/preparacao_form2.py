"""Migração 23: preparação demonstrativa, sem Instrumento nuclear adicional."""
from sqlalchemy import inspect, text
from app.modelos import HabilitacaoForm2Preparacao, PreparacaoForm2


def aplicar(sessao):
    conexao = sessao.connection()
    HabilitacaoForm2Preparacao.__table__.create(conexao, checkfirst=True)
    PreparacaoForm2.__table__.create(conexao, checkfirst=True)


def reverter(sessao):
    conexao = sessao.connection()
    tabelas = set(inspect(conexao).get_table_names())
    for tabela in ("preparacao_form2", "habilitacao_form2_preparacao"):
        if tabela in tabelas and conexao.scalar(text(f"SELECT count(*) FROM {tabela}")):
            raise RuntimeError("reversão recusada: preparação ou habilitação FORM 2 existente")
    if conexao.scalar(text("SELECT count(*) FROM evento WHERE cadeia_tipo IN ('form2_preparacao', 'form2_habilitacao')")):
        raise RuntimeError("reversão recusada: histórico FORM 2 existente")
    PreparacaoForm2.__table__.drop(conexao, checkfirst=True)
    HabilitacaoForm2Preparacao.__table__.drop(conexao, checkfirst=True)
