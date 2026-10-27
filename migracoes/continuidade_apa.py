"""Migração 13: designação e substituição institucional do APA."""

from sqlalchemy import text

from app.modelos import SubstituicaoApa


def aplicar(sessao):
    conexao = sessao.connection()
    conexao.execute(text(
        "ALTER TABLE designacao ADD COLUMN IF NOT EXISTS tipo_apa VARCHAR(20)"
    ))
    conexao.execute(text(
        "ALTER TABLE designacao ADD COLUMN IF NOT EXISTS vigente_de TIMESTAMPTZ"
    ))
    conexao.execute(text(
        "ALTER TABLE designacao ADD COLUMN IF NOT EXISTS vigente_ate TIMESTAMPTZ"
    ))
    conexao.execute(text(
        "ALTER TABLE designacao ADD COLUMN IF NOT EXISTS fundamento_administrativo VARCHAR(250)"
    ))
    conexao.execute(text(
        "ALTER TABLE designacao ADD COLUMN IF NOT EXISTS autorizado_por_id VARCHAR(50)"
    ))
    conexao.execute(text("""
        DO $$ BEGIN
          ALTER TABLE designacao ADD CONSTRAINT fk_designacao_apa_autorizador
            FOREIGN KEY (autorizado_por_id) REFERENCES pessoa(id);
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """))
    conexao.execute(text("""
        DO $$ BEGIN
          ALTER TABLE designacao ADD CONSTRAINT ck_designacao_tipo_apa
            CHECK (tipo_apa IS NULL OR tipo_apa IN ('titular', 'suplente'));
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """))
    conexao.execute(text("""
        DO $$ BEGIN
          ALTER TABLE designacao ADD CONSTRAINT ck_designacao_apa_vigencia
            CHECK (vigente_ate IS NULL OR vigente_de IS NULL OR vigente_ate > vigente_de);
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """))
    conexao.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_designacao_apa_titular_ativa
        ON designacao (unidade_id)
        WHERE papel = 'responsavel_registro' AND tipo_apa = 'titular' AND ativa IS TRUE
    """))
    SubstituicaoApa.__table__.create(bind=conexao, checkfirst=True)
