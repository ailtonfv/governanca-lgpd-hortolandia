"""Migração 3: a versão submetida é imutável inclusive fora da aplicação."""

from sqlalchemy import text


def aplicar(sessao):
    sessao.execute(text("""
        CREATE OR REPLACE FUNCTION impedir_alteracao_versao_instrumento()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'versao_instrumento é imutável depois da submissão'
                USING ERRCODE = '55000';
        END;
        $$
    """))
    sessao.execute(text("""
        DROP TRIGGER IF EXISTS trg_versao_instrumento_imutavel ON versao_instrumento
    """))
    sessao.execute(text("""
        CREATE TRIGGER trg_versao_instrumento_imutavel
        BEFORE UPDATE OR DELETE ON versao_instrumento
        FOR EACH ROW EXECUTE FUNCTION impedir_alteracao_versao_instrumento()
    """))
