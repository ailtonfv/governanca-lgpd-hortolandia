"""C8: Secretarias da lista institucional demonstrativa já utilizada no painel."""
from sqlalchemy import select
from app.modelos import Unidade
from carga_ficticia.pessoas import SECRETARIAS


def secretarias_ativas(sessao):
    return sessao.scalars(select(Unidade).where(Unidade.ativa.is_(True),
        Unidade.id.in_([codigo for codigo, _ in SECRETARIAS])).order_by(Unidade.nome)).all()
