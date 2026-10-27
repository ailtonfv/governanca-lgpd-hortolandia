"""Migração 14: generaliza o vínculo de canais para qualquer objeto do catálogo.

A migração renomeia a estrutura existente, sem copiar ou apagar linhas. Assim,
os vínculos anteriormente cadastrados para serviços conservam identidade,
vigência e observação.
"""

from sqlalchemy import inspect, text

from app.modelos import ObjetoCanal


def aplicar(sessao):
    conexao = sessao.connection()
    tabelas = set(inspect(conexao).get_table_names())

    if "servico_canal" in tabelas and "objeto_canal" in tabelas:
        raise RuntimeError(
            "Migração recusada: servico_canal e objeto_canal coexistem; "
            "é necessária verificação manual antes de consolidar os vínculos."
        )

    if "servico_canal" in tabelas:
        conexao.execute(text("ALTER TABLE servico_canal RENAME TO objeto_canal"))
    elif "objeto_canal" not in tabelas:
        ObjetoCanal.__table__.create(bind=conexao, checkfirst=True)

    colunas = {coluna["name"] for coluna in inspect(conexao).get_columns("objeto_canal")}
    if "servico_id" in colunas and "objeto_id" in colunas:
        raise RuntimeError(
            "Migração recusada: servico_id e objeto_id coexistem em objeto_canal."
        )
    if "servico_id" in colunas:
        conexao.execute(text(
            "ALTER TABLE objeto_canal RENAME COLUMN servico_id TO objeto_id"
        ))

    # Os nomes antigos podem permanecer após o RENAME do PostgreSQL. Renomeá-los
    # melhora a leitura do esquema sem alterar dados ou regras.
    conexao.execute(text("""
        DO $$ BEGIN
          ALTER INDEX uq_servico_canal_vigente RENAME TO uq_objeto_canal_vigente;
        EXCEPTION
          WHEN undefined_table OR duplicate_table THEN NULL;
        END $$
    """))
    conexao.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_objeto_canal_vigente
        ON objeto_canal (objeto_id, canal_id)
        WHERE vigente_ate IS NULL
    """))

    conexao.execute(text("""
        DO $$ BEGIN
          ALTER TABLE objeto_canal
            RENAME CONSTRAINT servico_canal_pkey TO objeto_canal_pkey;
        EXCEPTION
          WHEN undefined_object OR duplicate_object THEN NULL;
        END $$
    """))
    conexao.execute(text("""
        DO $$ BEGIN
          ALTER TABLE objeto_canal
            RENAME CONSTRAINT servico_canal_servico_id_fkey
            TO objeto_canal_objeto_id_fkey;
        EXCEPTION
          WHEN undefined_object OR duplicate_object THEN NULL;
        END $$
    """))
    conexao.execute(text("""
        DO $$ BEGIN
          ALTER TABLE objeto_canal
            RENAME CONSTRAINT servico_canal_canal_id_fkey
            TO objeto_canal_canal_id_fkey;
        EXCEPTION
          WHEN undefined_object OR duplicate_object THEN NULL;
        END $$
    """))
    conexao.execute(text("""
        DO $$ BEGIN
          ALTER SEQUENCE servico_canal_id_seq RENAME TO objeto_canal_id_seq;
        EXCEPTION
          WHEN undefined_table OR duplicate_table THEN NULL;
        END $$
    """))
