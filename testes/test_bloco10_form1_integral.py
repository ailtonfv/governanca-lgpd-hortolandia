"""Bloco 10 do FORM 1 integral — envio, disponibilização e saída."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modelos import RascunhoForm1Integral
from app.rascunho_form1_integral import salvar_bloco_10_form1_integral
from testes.test_bloco7_form1_integral import _rascunho

cliente = TestClient(app)


def test_bloco_10_salva_fluxo_de_saida_e_ramos_aninhados(sessao):
    registro = _rascunho(sessao, "F110-OK")
    respostas = {
        "10.1": "Em alguns casos", "10.2": ["Outra Secretaria"],
        "10.3": ["Sistema", "Protocolo"],
        "10.4": ["Nome", "Número de protocolo, processo ou cadastro"],
        "10.5": "Sob demanda", "10.6": "Atendimento institucional fictício",
        "10.7": "Sim", "10.7.1": "Protocolo fictício", "10.8": "Sim",
        "10.8.1": ["Site institucional"], "10.9": "Titular",
    }
    resultado = salvar_bloco_10_form1_integral(sessao, comando_id="F110-OK-S", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1, respostas=respostas)
    sessao.commit()
    assert resultado["permitido"]
    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo["respostas"]["10.4"] == respostas["10.4"]


@pytest.mark.parametrize("respostas", (
    {"10.1": "Não", "10.2": ["Outra Secretaria"]},
    {"10.1": "Sim", "10.7": "Não", "10.7.1": "Indevido"},
    {"10.1": "Sim", "10.8": "Não", "10.8.1": ["Site institucional"]},
))
def test_bloco_10_recusa_condicionais_inativas(sessao, respostas):
    registro = _rascunho(sessao, "F110-COND")
    resultado = salvar_bloco_10_form1_integral(sessao, comando_id="F110-COND-S", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1, respostas=respostas)
    sessao.commit()
    assert not resultado["permitido"] and "condicional inativo" in resultado["motivo"]


def test_bloco_10_preserva_destinatario_final_sem_saida(sessao):
    registro = _rascunho(sessao, "F110-FIM")
    resultado = salvar_bloco_10_form1_integral(sessao, comando_id="F110-FIM-S", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"10.1": "Não", "10.9": "Não se aplica"})
    sessao.commit()
    assert resultado["permitido"]


def test_bloco_10_recusa_catalogos_forjados_e_duplicados(sessao):
    registro = _rascunho(sessao, "F110-INV")
    casos = ({"10.1": "Sim", "10.2": ["Destino forjado"]},
             {"10.1": "Sim", "10.4": ["Nome", "Nome"]},
             {"10.9": "Destinatário forjado"})
    for indice, respostas in enumerate(casos):
        resultado = salvar_bloco_10_form1_integral(sessao, comando_id=f"F110-INV-{indice}", conta_id="CONTA-A1",
            registro_id=registro["registro_id"], versao_lida=1, respostas=respostas)
        sessao.commit()
        assert not resultado["permitido"]


def test_interface_exibe_e_salva_bloco_10(sessao):
    registro = _rascunho(sessao, "F110-HTTP")
    pagina = cliente.get(f"/registros/{registro['registro_id']}?conta_id=CONTA-A1")
    resposta = cliente.post(f"/registros/{registro['registro_id']}/form1-integral/bloco-10/salvar",
        data={"conta_id": "CONTA-A1", "comando_id": "F110-HTTP-S", "versao_lida": "1",
              "campo__10.1": "Não", "campo__10.9": "Não se aplica"})
    assert pagina.status_code == 200 and "10.8.1" in pagina.text
    assert resposta.status_code == 200 and "Bloco 10" in resposta.text
