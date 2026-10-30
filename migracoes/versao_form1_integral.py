"""Migração 17: snapshots técnicos imutáveis do FORM 1 integral."""

from sqlalchemy import text

from app.modelos import VersaoForm1Integral


def aplicar(sessao):
    conexao = sessao.connection()
    VersaoForm1Integral.__table__.create(bind=conexao, checkfirst=True)
    conexao.execute(text("""
        CREATE OR REPLACE FUNCTION impedir_alteracao_versao_form1_integral()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'versao_form1_integral é imutável depois da preparação'
                USING ERRCODE = '55000';
        END;
        $$
    """))
    conexao.execute(text("""
        DROP TRIGGER IF EXISTS trg_versao_form1_integral_imutavel
        ON versao_form1_integral
    """))
    conexao.execute(text("""
        CREATE TRIGGER trg_versao_form1_integral_imutavel
        BEFORE UPDATE OR DELETE ON versao_form1_integral
        FOR EACH ROW EXECUTE FUNCTION impedir_alteracao_versao_form1_integral()
    """))


def reverter(sessao):
    """Remove somente a infraestrutura vazia desta migração em desenvolvimento."""

    conexao = sessao.connection()
    quantidade = conexao.scalar(text(
        "SELECT count(*) FROM versao_form1_integral"
    ))
    if quantidade:
        raise RuntimeError(
            "reversão recusada: versao_form1_integral contém snapshots"
        )
    conexao.execute(text("DROP TABLE IF EXISTS versao_form1_integral"))
    conexao.execute(text(
        "DROP FUNCTION IF EXISTS impedir_alteracao_versao_form1_integral()"
    ))
