"""Regressão rápida do gerador usado pelo ensaio formal POC-TS-009."""

from sqlalchemy.orm import Session

from app.banco import motor
from demonstracoes.poc_ts_009 import (carregar_volume, verificar_integridade,
                                      verificar_reconstrucao)


def test_gerador_de_volume_preserva_cadeias_e_reconstroi_projecoes():
    with Session(motor) as sessao, sessao.begin():
        carregar_volume(sessao, total_registros=2, eventos_por_registro=3)

    with Session(motor) as sessao:
        por_cadeia = verificar_integridade(sessao, total_registros=2)
        amostra = verificar_reconstrucao(sessao, por_cadeia, tamanho_amostra=2)

    assert len(por_cadeia) == 2
    assert sum(len(eventos) for eventos in por_cadeia.values()) == 6
    assert len(amostra) == 2
