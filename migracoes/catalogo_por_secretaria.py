"""Migração 9: vínculo curado entre Secretarias e itens do catálogo operacional."""

from sqlalchemy import text


def aplicar(sessao):
    sessao.execute(text("""
        CREATE TABLE IF NOT EXISTS unidade_objeto_catalogo (
            id SERIAL PRIMARY KEY,
            unidade_id VARCHAR(50) NOT NULL REFERENCES unidade(id),
            objeto_id VARCHAR(50) NOT NULL REFERENCES objeto_catalogo(id),
            papel VARCHAR(20) NOT NULL DEFAULT 'RESPONSAVEL',
            fonte VARCHAR(150) NOT NULL,
            vigente_de TIMESTAMPTZ NOT NULL DEFAULT now(),
            vigente_ate TIMESTAMPTZ,
            CONSTRAINT ck_unidade_objeto_papel
                CHECK (papel IN ('RESPONSAVEL', 'PARTICIPANTE'))
        )
    """))
    sessao.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_unidade_objeto_vigente
        ON unidade_objeto_catalogo (unidade_id, objeto_id)
        WHERE vigente_ate IS NULL
    """))
