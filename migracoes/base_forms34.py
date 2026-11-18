"""Preparação aditiva somente no banco de teste; nenhum ingresso é executado."""
from app.integridade_forms34 import instalar_protecao
from app.modelos import ReferenciaParticipacaoForms34, IdentidadeForms34


def aplicar(motor):
    if not motor.url.database or not motor.url.database.endswith('_teste'):
        raise RuntimeError("Lote 11: executar somente na cópia terminada em _teste.")
    with motor.begin() as conexao:
        ReferenciaParticipacaoForms34.__table__.create(conexao, checkfirst=True)
        IdentidadeForms34.__table__.create(conexao, checkfirst=True)
        instalar_protecao(conexao)


if __name__ == '__main__':
    from app.banco import motor
    aplicar(motor)
