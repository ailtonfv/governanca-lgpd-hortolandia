# Preparação dos testes automatizados (pytest). Somente dados fictícios.
#
# SEGURANÇA: os testes rodam num banco PRÓPRIO, cujo nome termina em "_teste"
# (padrão: lgpd_poc_teste). Nunca no banco da PoC. Antes de cada teste, as tabelas
# do banco de teste são esvaziadas e a carga fictícia é refeita: cada teste começa do zero.

import os

os.environ["BANCO_NOME"] = os.environ.get("LGPD_BANCO_TESTE", "lgpd_poc_teste")
if not os.environ["BANCO_NOME"].endswith("_teste"):
    raise SystemExit("Recusado: o banco de testes precisa ter nome terminado em '_teste'.")

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import Base
from carga_ficticia import pessoas, catalogos

assert motor.url.database.endswith("_teste"), "os testes só rodam no banco de teste"


@pytest.fixture(scope="session", autouse=True)
def esquema():
    """Recria o esquema do banco de TESTE uma vez por rodada."""
    Base.metadata.drop_all(motor)
    Base.metadata.create_all(motor)
    yield


@pytest.fixture(autouse=True)
def banco_limpo(esquema):
    """Esvazia todas as tabelas e refaz a carga fictícia antes de cada teste."""
    tabelas = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    with motor.begin() as conexao:
        conexao.execute(text(f"TRUNCATE {tabelas} RESTART IDENTITY CASCADE"))
    with Session(motor) as sessao, sessao.begin():
        pessoas.semear(sessao)
        catalogos.semear(sessao)
    yield


@pytest.fixture
def sessao():
    """Uma sessão do banco de teste; o teste decide quando confirmar (commit)."""
    with Session(motor, expire_on_commit=False) as s:
        yield s
