"""Instalação explícita; exceção exclusiva da cópia nominal da porta 8013."""
from sqlalchemy import text
from migracoes.base_forms34 import aplicar as base_teste, aplicar_copia_8013
from app.modelos import ReferenciaRestritaForms34

BANCO_8013 = 'lgpd_lote12_3be0186939a7'


def aplicar(motor, *, vistoria_8013=False):
    if vistoria_8013:
        if motor.url.database != BANCO_8013:
            raise RuntimeError('Cópia diferente da 8013 autorizada.')
        aplicar_copia_8013(motor)
    else:
        base_teste(motor)
    with motor.begin() as c:
        ReferenciaRestritaForms34.__table__.create(c, checkfirst=True)
        c.execute(text('''CREATE OR REPLACE TRIGGER proteger_referencia_restrita34
            BEFORE UPDATE OR DELETE ON referencia_restrita_forms34
            FOR EACH ROW EXECUTE FUNCTION proteger_base_forms34()'''))
