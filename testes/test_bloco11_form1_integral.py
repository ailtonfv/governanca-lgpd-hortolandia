"""Bloco 11 do FORM 1 integral — armazenamento e dependência de terceiro."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modelos import RascunhoForm1Integral
from app.rascunho_form1_integral import salvar_bloco_11_form1_integral
from testes.test_bloco7_form1_integral import _rascunho

cliente = TestClient(app)


def test_bloco_11_salva_repositorios_e_dependencia_de_terceiro(sessao):
    registro = _rascunho(sessao, "F111-OK")
    respostas = {
        "11.1": ["Sistema institucional", "Arquivo físico"],
        "11.2": "Ambas", "11.2.1": "Sim", "11.2.2": "Parcialmente",
        "11.2.3": "Não", "11.2.4": "Em alguns casos",
        "11.3": "Sim", "11.3.1": "Ambiente externo fictício controlado",
    }
    resultado = salvar_bloco_11_form1_integral(
        sessao, comando_id="F111-OK-S", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1, respostas=respostas,
    )
    sessao.commit()
    assert resultado["permitido"]
    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo["respostas"]["11.2.4"] == "Em alguns casos"


@pytest.mark.parametrize("respostas", (
    {"11.2": "Infraestrutura da Prefeitura", "11.2.1": "Sim"},
    {"11.3": "Não", "11.3.1": "Local indevido"},
))
def test_bloco_11_recusa_condicionais_inativas(sessao, respostas):
    registro = _rascunho(sessao, "F111-COND")
    resultado = salvar_bloco_11_form1_integral(
        sessao, comando_id="F111-COND-S", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1, respostas=respostas,
    )
    sessao.commit()
    assert not resultado["permitido"] and "condicional inativo" in resultado["motivo"]


def test_bloco_11_recusa_repositorio_forjado_e_repetido(sessao):
    registro = _rascunho(sessao, "F111-INV")
    for indice, respostas in enumerate((
        {"11.1": ["Repositório forjado"]},
        {"11.1": ["Arquivo digital", "Arquivo digital"]},
    )):
        resultado = salvar_bloco_11_form1_integral(
            sessao, comando_id=f"F111-INV-{indice}", conta_id="CONTA-A1",
            registro_id=registro["registro_id"], versao_lida=1, respostas=respostas,
        )
        sessao.commit()
        assert not resultado["permitido"]


def test_bloco_11_autorizacao_idempotencia_e_versao(sessao):
    registro = _rascunho(sessao, "F111-SEG")
    negado = salvar_bloco_11_form1_integral(
        sessao, comando_id="F111-SEG-N", conta_id="CONTA-G1",
        registro_id=registro["registro_id"], versao_lida=1, respostas={},
    )
    sessao.commit()
    parametros = dict(comando_id="F111-SEG-S", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"11.1": ["A confirmar"]})
    primeiro = salvar_bloco_11_form1_integral(sessao, **parametros)
    sessao.commit()
    repetido = salvar_bloco_11_form1_integral(sessao, **parametros)
    antigo = salvar_bloco_11_form1_integral(
        sessao, comando_id="F111-SEG-V", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1, respostas={},
    )
    sessao.commit()
    assert not negado["permitido"]
    assert primeiro["permitido"] and repetido["reexecutado"]
    assert not antigo["permitido"] and "desatualizado" in antigo["motivo"]


def test_interface_exibe_e_salva_bloco_11(sessao):
    registro = _rascunho(sessao, "F111-HTTP")
    pagina = cliente.get(f"/registros/{registro['registro_id']}?conta_id=CONTA-A1")
    resposta = cliente.post(
        f"/registros/{registro['registro_id']}/form1-integral/bloco-11/salvar",
        data={"conta_id": "CONTA-A1", "comando_id": "F111-HTTP-S",
              "versao_lida": "1", "campo__11.1": ["A confirmar"]},
    )
    assert pagina.status_code == 200 and "11.3.1" in pagina.text
    assert resposta.status_code == 200 and "Bloco 11" in resposta.text
