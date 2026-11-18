"""Migração explícita: novas tabelas e proteção limitada às cadeias 3/4.

Acrescenta um trigger à tabela evento existente, sem alterar suas colunas
ou o comportamento de outras cadeias. Não é uma migração só de tabelas/índices.
Não é chamada na importação, na inicialização web nem por create_all().
"""
from sqlalchemy import text
from app.modelos import ReferenciaParticipacaoForms34, IdentidadeForms34


def aplicar(motor):
    if not motor.url.database or not motor.url.database.endswith('_teste'):
        raise RuntimeError("Lote 11: executar somente na cópia terminada em _teste.")
    _instalar(motor)


def aplicar_copia_8013(motor):
    """Exceção nominal autorizada por Ailton para a vistoria do Lote 12."""
    if motor.url.database != "lgpd_lote12_3be0186939a7":
        raise RuntimeError("Migração da 8013 recusada: nome diferente da cópia autorizada.")
    _instalar(motor)


def _instalar(motor):
    with motor.begin() as conexao:
        if conexao.dialect.name != 'postgresql':
            raise RuntimeError("A base 3/4 exige PostgreSQL para integridade e concorrência.")
        ReferenciaParticipacaoForms34.__table__.create(conexao, checkfirst=True)
        IdentidadeForms34.__table__.create(conexao, checkfirst=True)
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
        # OLD impede escapar mudando cadeia_tipo. F1/F2 não executam a função.
        # Nenhum trigger de INSERT ou regra nova para as outras cadeias.
        conexao.execute(text("""
            CREATE OR REPLACE TRIGGER proteger_evento_forms34
            BEFORE UPDATE OR DELETE ON evento
            FOR EACH ROW WHEN (OLD.cadeia_tipo IN ('forms34_contexto','forms34_objeto'))
            EXECUTE FUNCTION proteger_base_forms34()
        """))


if __name__ == '__main__':
    from app.banco import motor
    aplicar(motor)
