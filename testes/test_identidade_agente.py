"""Identidade mínima do agente: matrícula fictícia única e separada da conta técnica."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.banco import motor
from app.modelos import (Pessoa, Unidade, UnidadeObjetoCatalogo,
                         ObjetoContextoCatalogo)
from carga_ficticia.pessoas import SECRETARIAS


def test_carga_atribui_uma_matricula_unica_a_cada_pessoa():
    with Session(motor) as sessao:
        pessoas = sessao.query(Pessoa).order_by(Pessoa.id).all()

    matriculas = [pessoa.matricula for pessoa in pessoas]
    assert matriculas == [f"MAT-FICT-{numero:04d}" for numero in range(1, 9)]
    assert len(matriculas) == len(set(matriculas))


def test_banco_recusa_matricula_repetida():
    with pytest.raises(IntegrityError), Session(motor) as sessao, sessao.begin():
        sessao.add(Pessoa(
            id="PESSOA-REPETIDA", matricula="MAT-FICT-0001",
            nome="Servidor repetido (fictício)", ativa=True,
        ))


def test_catalogo_institucional_tem_as_18_secretarias_sem_hortoprev():
    assert len(SECRETARIAS) == 18
    assert len({identificador for identificador, _ in SECRETARIAS}) == 18
    assert len({nome for _, nome in SECRETARIAS}) == 18
    assert all("Hortoprev" not in nome for _, nome in SECRETARIAS)
    with Session(motor) as sessao:
        assert all(
            sessao.get(Unidade, identificador).nome == nome
            for identificador, nome in SECRETARIAS
        )


def test_vinculos_ficticios_do_catalogo_identificam_secretaria_e_fonte():
    with Session(motor) as sessao:
        saude = sessao.scalars(select(UnidadeObjetoCatalogo).where(
            UnidadeObjetoCatalogo.unidade_id == "SEC-SAUDE",
            UnidadeObjetoCatalogo.objeto_id == "OBJ-SRV-020",
            UnidadeObjetoCatalogo.vigente_ate.is_(None),
        )).one()
        assert saude.papel == "RESPONSAVEL"
        assert saude.fonte == "carga fictícia da PoC"
        contexto = sessao.scalars(select(ObjetoContextoCatalogo).where(
            ObjetoContextoCatalogo.objeto_id == "OBJ-SRV-020",
            ObjetoContextoCatalogo.contexto_id == "CTX-SAU-01",
            ObjetoContextoCatalogo.vigente_ate.is_(None),
        )).one()
        assert contexto.fonte == "carga fictícia da PoC"
