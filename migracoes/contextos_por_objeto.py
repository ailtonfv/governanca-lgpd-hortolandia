"""Migração 10: vínculo curado entre itens do catálogo e contextos de atuação."""

from sqlalchemy import text


def aplicar(sessao):
    sessao.execute(text("""
        CREATE TABLE IF NOT EXISTS objeto_contexto_catalogo (
            id SERIAL PRIMARY KEY,
            objeto_id VARCHAR(50) NOT NULL REFERENCES objeto_catalogo(id),
            contexto_id VARCHAR(20) NOT NULL REFERENCES contexto_atuacao(id),
            fonte VARCHAR(150) NOT NULL,
            vigente_de TIMESTAMPTZ NOT NULL DEFAULT now(),
            vigente_ate TIMESTAMPTZ
        )
    """))
    sessao.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_objeto_contexto_catalogo_vigente
        ON objeto_contexto_catalogo (objeto_id, contexto_id)
        WHERE vigente_ate IS NULL
    """))
