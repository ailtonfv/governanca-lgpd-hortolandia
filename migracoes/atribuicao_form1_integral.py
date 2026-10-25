"""Migração 11: projeção do ARP atual na preparação do FORM 1 integral."""

from app.modelos import AtribuicaoForm1Integral


def aplicar(sessao):
    AtribuicaoForm1Integral.__table__.create(bind=sessao.connection(), checkfirst=True)
