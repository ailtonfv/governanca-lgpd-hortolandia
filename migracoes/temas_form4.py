"""Migração explícita e aditiva: catálogo, sem tocar em ações existentes."""
from sqlalchemy.orm import Session
from app.modelos import Tema
from carga_ficticia.temas_form4 import semear

BANCO_8015 = 'lgpd_lote14_e5308b7f54cf'


def aplicar(motor, *, vistoria_8015=False):
    nome=motor.url.database or ''
    if not (nome==BANCO_8015 if vistoria_8015 else nome.endswith('_teste')):
        raise RuntimeError('Migração autorizada somente no banco de teste ou na cópia nominal da 8015.')
    with motor.begin() as c:
        Tema.__table__.create(c,checkfirst=True)
        with Session(bind=c) as s:
            semear(s)
            s.flush()
