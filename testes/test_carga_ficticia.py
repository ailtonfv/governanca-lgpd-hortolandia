"""POC-TS-008: a carga da PoC rejeita dados com aparência pessoal."""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.banco import motor
from app.modelos import ObjetoCatalogo, Pessoa
from carga_ficticia import catalogos, pessoas
from carga_ficticia.seguranca import MassaFicticiaInvalida


def test_poc_ts_008_rejeita_identidade_sem_marcadores_antes_da_carga(monkeypatch):
    tentativa_controlada = (
        "PESSOA-X", "12345678", "Nome sem marcador de ficção", ["CONTA-X1"]
    )
    monkeypatch.setattr(pessoas, "PESSOAS", [*pessoas.PESSOAS, tentativa_controlada])

    with Session(motor) as sessao, pytest.raises(
        MassaFicticiaInvalida, match="matrícula fora do padrão sintético"
    ):
        pessoas.semear(sessao)

    with Session(motor) as sessao:
        assert sessao.get(Pessoa, "PESSOA-X") is None


@pytest.mark.parametrize(("rotulo", "marcador_controlado"), [
    ("CPF", "000.000.000-00"),
    ("e-mail", "usuario@example.invalid"),
    ("telefone", "(00) 0000-0000"),
])
def test_poc_ts_008_rejeita_identificador_pessoal_sem_o_repetir(
        monkeypatch, rotulo, marcador_controlado):
    objeto_suspeito = (
        "OBJ-SRV-X", "servico", f"Entrada controlada {marcador_controlado}"
    )
    monkeypatch.setattr(catalogos, "OBJETOS", [*catalogos.OBJETOS, objeto_suspeito])

    with Session(motor) as sessao, pytest.raises(MassaFicticiaInvalida) as erro:
        catalogos.semear(sessao)

    assert f"possível {rotulo}" in str(erro.value)
    assert marcador_controlado not in str(erro.value)
    with Session(motor) as sessao:
        assert sessao.get(ObjetoCatalogo, "OBJ-SRV-X") is None
