"""Migração 16: classificação estável dos canais condicionais do FORM 1.

As colunas são opcionais e não recebem preenchimento retroativo. Assim, um
Registro anterior não é reinterpretado a partir do catálogo atual. Novas
confirmações copiam a classificação para o retrato histórico do Registro.
"""

from sqlalchemy import inspect, text


def _adicionar_coluna_se_ausente(conexao, tabela, coluna, definicao):
    colunas = {item["name"] for item in inspect(conexao).get_columns(tabela)}
    if coluna not in colunas:
        conexao.execute(text(
            f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}"
        ))


def aplicar(sessao):
    conexao = sessao.connection()
    _adicionar_coluna_se_ausente(
        conexao, "canal", "classificacao_form1", "VARCHAR(20)"
    )
    _adicionar_coluna_se_ausente(
        conexao, "registro_canal", "classificacao_form1_snapshot", "VARCHAR(20)"
    )
    conexao.execute(text("""
        DO $$ BEGIN
          ALTER TABLE canal ADD CONSTRAINT ck_canal_classificacao_form1
          CHECK (classificacao_form1 IS NULL OR
                 classificacao_form1 IN ('Ouvidoria', 'e-SIC'));
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """))
    conexao.execute(text("""
        DO $$ BEGIN
          ALTER TABLE registro_canal
          ADD CONSTRAINT ck_registro_canal_classificacao_form1
          CHECK (classificacao_form1_snapshot IS NULL OR
                 classificacao_form1_snapshot IN ('Ouvidoria', 'e-SIC'));
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
    """))
