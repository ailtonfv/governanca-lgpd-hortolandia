"""Bloco 12 do FORM 1 integral — guarda e destinação."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modelos import RascunhoForm1Integral
from app.rascunho_form1_integral import salvar_bloco_12_form1_integral
from testes.test_bloco7_form1_integral import _rascunho

cliente = TestClient(app)


def test_bloco_12_salva_prazo_destinacao_e_evidencias(sessao):
    registro = _rascunho(sessao, "F112-OK")
    respostas = {
        "12.1": "Sim", "12.1.1": "5", "12.1.2": "Anos",
        "12.1.3": ["Tabela de temporalidade"], "12.2": "Eliminação",
        "12.3": "Sim", "12.4": "Em alguns casos",
        "12.4.1": "Registro institucional fictício", "12.5": "Sim",
        "12.5.1": "Arquivo institucional fictício",
    }
    resultado = salvar_bloco_12_form1_integral(sessao, comando_id="F112-OK-S", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1, respostas=respostas)
    sessao.commit()
    assert resultado["permitido"]
    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo["respostas"]["12.1.1"] == "5"


@pytest.mark.parametrize("respostas", (
    {"12.1": "Não", "12.1.1": "5"},
    {"12.4": "Não", "12.4.1": "Indevido"},
    {"12.5": "Não", "12.5.1": "Indevido"},
))
def test_bloco_12_recusa_condicionais_inativas(sessao, respostas):
    registro = _rascunho(sessao, "F112-COND")
    resultado = salvar_bloco_12_form1_integral(sessao, comando_id="F112-COND-S", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1, respostas=respostas)
    sessao.commit()
    assert not resultado["permitido"] and "condicional inativo" in resultado["motivo"]


def test_bloco_12_recusa_prazo_nao_numerico_e_catalogo_forjado(sessao):
    registro = _rascunho(sessao, "F112-INV")
    casos = ({"12.1": "Sim", "12.1.1": "cinco"},
             {"12.1": "Sim", "12.1.2": "Décadas"},
             {"12.1": "Sim", "12.1.3": ["Referência forjada"]})
    for indice, respostas in enumerate(casos):
        resultado = salvar_bloco_12_form1_integral(sessao, comando_id=f"F112-INV-{indice}", conta_id="CONTA-A1",
            registro_id=registro["registro_id"], versao_lida=1, respostas=respostas)
        sessao.commit()
        assert not resultado["permitido"]


def test_bloco_12_ramo_desativado_vai_para_historico(sessao):
    registro = _rascunho(sessao, "F112-HIST")
    salvar_bloco_12_form1_integral(sessao, comando_id="F112-HIST-1", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"12.5": "Sim", "12.5.1": "Arquivo fictício"})
    sessao.commit()
    salvar_bloco_12_form1_integral(sessao, comando_id="F112-HIST-2", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=2, respostas={"12.5": "Não"})
    sessao.commit()
    conteudo = sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo
    assert "12.5.1" not in conteudo["respostas"]
    assert conteudo["respostas_inativas"]["12.5.1"][-1]["valor"] == "Arquivo fictício"


def test_interface_exibe_e_salva_bloco_12(sessao):
    registro = _rascunho(sessao, "F112-HTTP")
    pagina = cliente.get(f"/registros/{registro['registro_id']}?conta_id=CONTA-A1")
    resposta = cliente.post(f"/registros/{registro['registro_id']}/form1-integral/bloco-12/salvar",
        data={"conta_id": "CONTA-A1", "comando_id": "F112-HTTP-S", "versao_lida": "1",
              "campo__12.1": "Não", "campo__12.2": "A confirmar"})
    assert pagina.status_code == 200 and "12.5.1" in pagina.text
    assert resposta.status_code == 200 and "Bloco 12" in resposta.text
