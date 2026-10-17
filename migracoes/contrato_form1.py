"""Migração 5: identifica o contrato usado por cada versão do FORM 1."""

from sqlalchemy import text


def aplicar(sessao):
    sessao.execute(text("""
        ALTER TABLE versao_instrumento
        ADD COLUMN IF NOT EXISTS versao_contrato INTEGER NOT NULL DEFAULT 1
    """))
