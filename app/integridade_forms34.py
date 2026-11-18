"""Proteção das novas bases imutáveis, inclusive contra UPDATE/DELETE direto."""
from sqlalchemy import event, text


def instalar_protecao(conexao):
    if conexao.dialect.name != 'postgresql':
        raise RuntimeError("A base 3/4 exige PostgreSQL para integridade e concorrência.")
    conexao.execute(text("""
        CREATE OR REPLACE FUNCTION proteger_base_forms34() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
          RAISE EXCEPTION 'Base 3/4 imutável; acrescentar novo evento'
            USING ERRCODE = '23514', CONSTRAINT = 'forms34_imutavel';
        END $$
    """))
    for tabela in ('referencia_participacao_forms34', 'identidade_forms34'):
        conexao.execute(text(f"""
            CREATE OR REPLACE TRIGGER proteger_forms34
            BEFORE UPDATE OR DELETE ON {tabela}
            FOR EACH ROW EXECUTE FUNCTION proteger_base_forms34()
        """))
    conexao.execute(text("""
        CREATE OR REPLACE TRIGGER proteger_evento_forms34
        BEFORE UPDATE OR DELETE ON evento
        FOR EACH ROW WHEN (OLD.cadeia_tipo IN ('forms34_contexto','forms34_objeto'))
        EXECUTE FUNCTION proteger_base_forms34()
    """))


def registrar_protecao(metadata):
    def depois_de_criar(target, connection, **kw):
        instalar_protecao(connection)
    event.listen(metadata, 'after_create', depois_de_criar)
