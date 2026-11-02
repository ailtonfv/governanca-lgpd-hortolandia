"""Migração 20: projeção da conferência interna do FORM 1 integral."""

from sqlalchemy import text

from app.modelos import ConferenciaInternaForm1Integral


def aplicar(sessao):
    ConferenciaInternaForm1Integral.__table__.create(
        bind=sessao.connection(), checkfirst=True
    )


def reverter(sessao):
    quantidade = sessao.connection().scalar(text(
        "SELECT count(*) FROM conferencia_interna_form1_integral"
    ))
    if quantidade:
        raise RuntimeError(
            "reversão recusada: há solicitações de conferência interna preservadas"
        )
    ConferenciaInternaForm1Integral.__table__.drop(
        bind=sessao.connection(), checkfirst=True
    )
