"""Migração 18: canais do catálogo geral declarados pelo APA no G1.

A evolução preserva os retratos existentes, identifica sua origem como vínculo
do objeto e permite que novas linhas referenciem diretamente um canal ativo do
catálogo geral. A reversão só é segura antes de existir conteúdo que dependa da
nova semântica.
"""

from sqlalchemy import inspect, text


def _colunas(conexao, tabela):
    return {item["name"] for item in inspect(conexao).get_columns(tabela)}


def aplicar(sessao):
    conexao = sessao.connection()
    colunas_confirmacao = _colunas(conexao, "confirmacao_canais_registro")
    if "situacao" not in colunas_confirmacao:
        conexao.execute(text(
            "ALTER TABLE confirmacao_canais_registro "
            "ADD COLUMN situacao VARCHAR(30)"
        ))
    if "versao_contrato_g1" not in colunas_confirmacao:
        conexao.execute(text(
            "ALTER TABLE confirmacao_canais_registro "
            "ADD COLUMN versao_contrato_g1 INTEGER"
        ))
    conexao.execute(text("""
        UPDATE confirmacao_canais_registro AS confirmacao
           SET situacao = CASE WHEN EXISTS (
                 SELECT 1 FROM registro_canal AS item
                  WHERE item.registro_id = confirmacao.registro_id
               ) THEN 'identificados' ELSE 'nenhum' END
         WHERE situacao IS NULL
    """))
    conexao.execute(text("""
        UPDATE confirmacao_canais_registro
           SET versao_contrato_g1 = 3
         WHERE versao_contrato_g1 IS NULL
    """))
    conexao.execute(text("""
        ALTER TABLE confirmacao_canais_registro
        ALTER COLUMN situacao SET NOT NULL,
        ALTER COLUMN situacao SET DEFAULT 'nenhum',
        ALTER COLUMN versao_contrato_g1 SET NOT NULL,
        ALTER COLUMN versao_contrato_g1 SET DEFAULT 4
    """))
    conexao.execute(text("""
        DO $$ BEGIN
          ALTER TABLE confirmacao_canais_registro
          ADD CONSTRAINT ck_confirmacao_canais_situacao
          CHECK (situacao IN ('identificados', 'nenhum', 'informacao_insuficiente'));
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """))

    colunas_item = _colunas(conexao, "registro_canal")
    if "canal_id_catalogo" not in colunas_item:
        conexao.execute(text(
            "ALTER TABLE registro_canal ADD COLUMN canal_id_catalogo VARCHAR(50)"
        ))
    if "origem_confirmacao" not in colunas_item:
        conexao.execute(text(
            "ALTER TABLE registro_canal ADD COLUMN origem_confirmacao VARCHAR(30)"
        ))
    conexao.execute(text("""
        UPDATE registro_canal AS item
           SET canal_id_catalogo = vinculo.canal_id,
               origem_confirmacao = 'VINCULO_OBJETO'
          FROM objeto_canal AS vinculo
         WHERE item.objeto_canal_id = vinculo.id
           AND (item.canal_id_catalogo IS NULL OR item.origem_confirmacao IS NULL)
    """))
    conexao.execute(text("""
        ALTER TABLE registro_canal
        ALTER COLUMN objeto_canal_id DROP NOT NULL,
        ALTER COLUMN canal_id_catalogo SET NOT NULL,
        ALTER COLUMN origem_confirmacao SET NOT NULL
    """))
    conexao.execute(text("""
        DO $$ BEGIN
          ALTER TABLE registro_canal
          ADD CONSTRAINT fk_registro_canal_catalogo
          FOREIGN KEY (canal_id_catalogo) REFERENCES canal(id);
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """))
    conexao.execute(text("""
        DO $$ BEGIN
          ALTER TABLE registro_canal
          ADD CONSTRAINT ck_registro_canal_origem
          CHECK (
            (origem_confirmacao = 'VINCULO_OBJETO' AND objeto_canal_id IS NOT NULL)
            OR
            (origem_confirmacao = 'DECLARACAO_APA' AND objeto_canal_id IS NULL)
          );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """))


def reverter(sessao):
    """Reverte apenas quando nenhuma informação exclusiva da versão 4 existe."""

    conexao = sessao.connection()
    dependencias = conexao.execute(text("""
        SELECT
          EXISTS (
            SELECT 1 FROM registro_canal
             WHERE origem_confirmacao = 'DECLARACAO_APA'
          )
          OR EXISTS (
            SELECT 1 FROM confirmacao_canais_registro
             WHERE situacao = 'informacao_insuficiente'
          )
    """)).scalar_one()
    if dependencias:
        raise RuntimeError(
            "migração 18 não pode ser revertida: existem declarações exclusivas do contrato G1 v4"
        )
    conexao.execute(text("""
        ALTER TABLE registro_canal
        DROP CONSTRAINT IF EXISTS ck_registro_canal_origem,
        DROP CONSTRAINT IF EXISTS fk_registro_canal_catalogo,
        ALTER COLUMN objeto_canal_id SET NOT NULL,
        DROP COLUMN IF EXISTS origem_confirmacao,
        DROP COLUMN IF EXISTS canal_id_catalogo
    """))
    conexao.execute(text("""
        ALTER TABLE confirmacao_canais_registro
        DROP CONSTRAINT IF EXISTS ck_confirmacao_canais_situacao,
        DROP COLUMN IF EXISTS versao_contrato_g1,
        DROP COLUMN IF EXISTS situacao
    """))
