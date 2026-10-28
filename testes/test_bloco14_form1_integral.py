"""Bloco 14 do FORM 1 integral — achados e pendências."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modelos import RascunhoForm1Integral
from app.rascunho_form1_integral import salvar_bloco_14_form1_integral
from testes.test_bloco7_form1_integral import _rascunho

cliente = TestClient(app)


def test_bloco_14_salva_confirmacao_e_achado_com_evidencia(sessao):
    registro = _rascunho(sessao, "F114-OK")
    respostas = {
        "14.1": "Sim", "14.1.1": "Prazo institucional a confirmar",
        "14.1.2": "Unidade técnica fictícia", "14.2": "Sim",
        "14.2.1": "Armazenamento", "14.2.2": "Fato fictício observado no fluxo",
        "14.2.3": "Sim", "14.2.4": "Procedimento institucional fictício",
    }
    resultado = salvar_bloco_14_form1_integral(sessao, comando_id="F114-OK-S", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1, respostas=respostas)
    sessao.commit()
    assert resultado["permitido"]
    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo["respostas"]["14.2.4"] == "Procedimento institucional fictício"


@pytest.mark.parametrize("respostas", (
    {"14.1": "Não", "14.1.1": "Indevido"},
    {"14.1": "Não", "14.1.2": "Indevido"},
    {"14.2": "Não", "14.2.1": "Entrada"},
    {"14.2": "Sim", "14.2.3": "Não", "14.2.4": "Indevido"},
))
def test_bloco_14_recusa_condicionais_inativas(sessao, respostas):
    registro = _rascunho(sessao, "F114-COND")
    resultado = salvar_bloco_14_form1_integral(sessao, comando_id="F114-COND-S", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1, respostas=respostas)
    sessao.commit()
    assert not resultado["permitido"] and "condicional inativo" in resultado["motivo"]


def test_bloco_14_recusa_etapa_forjada(sessao):
    registro = _rascunho(sessao, "F114-INV")
    resultado = salvar_bloco_14_form1_integral(sessao, comando_id="F114-INV-S", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"14.2": "Sim", "14.2.1": "Etapa forjada"})
    sessao.commit()
    assert not resultado["permitido"] and "catálogo REV13" in resultado["motivo"]


def test_bloco_14_desativa_e_preserva_evidencia_no_historico(sessao):
    registro = _rascunho(sessao, "F114-HIST")
    salvar_bloco_14_form1_integral(sessao, comando_id="F114-HIST-1", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"14.2": "Sim", "14.2.3": "Sim", "14.2.4": "Evidência fictícia"})
    sessao.commit()
    salvar_bloco_14_form1_integral(sessao, comando_id="F114-HIST-2", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=2,
        respostas={"14.2": "Sim", "14.2.3": "Não"})
    sessao.commit()
    conteudo = sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo
    assert "14.2.4" not in conteudo["respostas"]
    assert conteudo["respostas_inativas"]["14.2.4"][-1]["valor"] == "Evidência fictícia"


def test_interface_exibe_e_salva_bloco_14(sessao):
    registro = _rascunho(sessao, "F114-HTTP")
    pagina = cliente.get(f"/registros/{registro['registro_id']}?conta_id=CONTA-A1")
    resposta = cliente.post(f"/registros/{registro['registro_id']}/form1-integral/bloco-14/salvar",
        data={"conta_id": "CONTA-A1", "comando_id": "F114-HTTP-S", "versao_lida": "1",
              "campo__14.1": "Não", "campo__14.2": "Não"})
    assert pagina.status_code == 200 and "14.2.4" in pagina.text
    assert resposta.status_code == 200 and "Bloco 14" in resposta.text
