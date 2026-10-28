"""Bloco 8 do FORM 1 integral — sistemas, canais e suportes."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modelos import RascunhoForm1Integral
from app.rascunho_form1_integral import salvar_bloco_8_form1_integral
from testes.test_bloco7_form1_integral import _rascunho

cliente = TestClient(app)


def test_bloco_8_salva_ramos_independentes_e_aninhado(sessao):
    registro = _rascunho(sessao, "F18-OK")
    respostas = {
        "8.1": "Ambos", "8.2": ["DOCS", "Processo administrativo físico"],
        "8.2.1": "Sim", "8.2.1.1": "Ambiente municipal fictício",
        "8.2.2": "Em alguns casos", "8.2.2.1": ["Sistema contratado"],
        "8.2.2.2": "Fornecedor fictício", "8.3": ["WhatsApp corporativo"],
        "8.7": "Institucional ou corporativo", "8.8": "Sempre",
        "8.8.1": "Protocolo fictício", "8.9": "Não",
    }
    resultado = salvar_bloco_8_form1_integral(sessao, comando_id="F18-OK-S", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1, respostas=respostas)
    sessao.commit()
    assert resultado["permitido"]
    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo["respostas"]["8.8.1"] == "Protocolo fictício"


@pytest.mark.parametrize("respostas", (
    {"8.2.1": "Não", "8.2.1.1": "Indevido"},
    {"8.4": "Não", "8.4.1": ["Ficha"]},
    {"8.6": "Não", "8.6.2": "Indevido"},
    {"8.3": ["Telefone"], "8.7": "Pessoal"},
    {"8.3": ["WhatsApp corporativo"], "8.8": "Não", "8.8.1": "Indevido"},
))
def test_bloco_8_recusa_ramo_inativo(sessao, respostas):
    registro = _rascunho(sessao, "F18-COND")
    resultado = salvar_bloco_8_form1_integral(sessao, comando_id="F18-COND-S", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1, respostas=respostas)
    sessao.commit()
    assert not resultado["permitido"] and "condicional inativo" in resultado["motivo"]


def test_bloco_8_desativa_resposta_preservando_historico(sessao):
    registro = _rascunho(sessao, "F18-HIST")
    salvar_bloco_8_form1_integral(sessao, comando_id="F18-HIST-1", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"8.5": "Sim", "8.5.1": "Procedimento fictício"})
    sessao.commit()
    salvar_bloco_8_form1_integral(sessao, comando_id="F18-HIST-2", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=2, respostas={"8.5": "Não"})
    sessao.commit()
    conteudo = sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo
    assert "8.5.1" not in conteudo["respostas"]
    assert conteudo["respostas_inativas"]["8.5.1"][-1]["valor"] == "Procedimento fictício"


def test_bloco_8_recusa_opcao_forjada_e_duplicada(sessao):
    registro = _rascunho(sessao, "F18-INV")
    for indice, respostas in enumerate(({"8.2": ["Sistema forjado"]}, {"8.3": ["Telefone", "Telefone"]})):
        resultado = salvar_bloco_8_form1_integral(sessao, comando_id=f"F18-INV-{indice}", conta_id="CONTA-A1",
            registro_id=registro["registro_id"], versao_lida=1, respostas=respostas)
        sessao.commit()
        assert not resultado["permitido"]


def test_interface_exibe_e_salva_bloco_8(sessao):
    registro = _rascunho(sessao, "F18-HTTP")
    pagina = cliente.get(f"/registros/{registro['registro_id']}?conta_id=CONTA-A1")
    resposta = cliente.post(f"/registros/{registro['registro_id']}/form1-integral/bloco-8/salvar",
        data={"conta_id": "CONTA-A1", "comando_id": "F18-HTTP-S", "versao_lida": "1",
              "campo__8.1": "Digital", "campo__8.3": ["E-mail institucional"]})
    assert pagina.status_code == 200 and "8.8.1" in pagina.text
    assert resposta.status_code == 200 and "Bloco 8" in resposta.text
