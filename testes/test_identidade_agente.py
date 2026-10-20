"""Identidade mínima do agente: matrícula fictícia única e separada da conta técnica."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.banco import motor
from app.modelos import Pessoa


def test_carga_atribui_uma_matricula_unica_a_cada_pessoa():
    with Session(motor) as sessao:
        pessoas = sessao.query(Pessoa).order_by(Pessoa.id).all()

    matriculas = [pessoa.matricula for pessoa in pessoas]
    assert matriculas == [f"MAT-FICT-{numero:04d}" for numero in range(1, 7)]
    assert len(matriculas) == len(set(matriculas))


def test_banco_recusa_matricula_repetida():
    with pytest.raises(IntegrityError), Session(motor) as sessao, sessao.begin():
        sessao.add(Pessoa(
            id="PESSOA-REPETIDA", matricula="MAT-FICT-0001",
            nome="Servidor repetido (fictício)", ativa=True,
        ))
