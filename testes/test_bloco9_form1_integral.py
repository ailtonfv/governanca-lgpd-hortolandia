"""Bloco 9 do FORM 1 integral — acesso."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modelos import RascunhoForm1Integral
from app.rascunho_form1_integral import salvar_bloco_9_form1_integral
from testes.test_bloco7_form1_integral import _rascunho

cliente = TestClient(app)


def test_bloco_9_salva_diferenciacao_de_acesso(sessao):
    registro = _rascunho(sessao, "F19-OK")
    resultado = salvar_bloco_9_form1_integral(sessao, comando_id="F19-OK-S", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1, respostas={
            "9.1": ["AGENTE PÚBLICO AUTORIZADO da unidade responsável", "Tecnologia da Informação"],
            "9.2": "Não", "9.2.1": "Sim", "9.2.2": ["Dados de saúde"],
            "9.3": "Equipe técnica fictícia",
        })
    sessao.commit()
    assert resultado["permitido"]
    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo["respostas"]["9.2.2"] == ["Dados de saúde"]


@pytest.mark.parametrize("respostas", (
    {"9.2": "Sim", "9.2.1": "Sim"},
    {"9.2": "Não", "9.2.1": "Não", "9.2.2": ["Nome"]},
    {"9.2": "Sim", "9.2.1": "Sim", "9.2.2": ["Nome"]},
))
def test_bloco_9_recusa_condicionais_inativas(sessao, respostas):
    registro = _rascunho(sessao, "F19-COND")
    resultado = salvar_bloco_9_form1_integral(sessao, comando_id="F19-COND-S", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1, respostas=respostas)
    sessao.commit()
    assert not resultado["permitido"] and "condicional inativo" in resultado["motivo"]


def test_bloco_9_recusa_perfil_e_categoria_forjados(sessao):
    registro = _rascunho(sessao, "F19-INV")
    for indice, respostas in enumerate(({"9.1": ["Perfil forjado"]},
                                        {"9.2": "Não", "9.2.1": "Sim", "9.2.2": ["Categoria forjada"]})):
        resultado = salvar_bloco_9_form1_integral(sessao, comando_id=f"F19-INV-{indice}", conta_id="CONTA-A1",
            registro_id=registro["registro_id"], versao_lida=1, respostas=respostas)
        sessao.commit()
        assert not resultado["permitido"]


def test_interface_exibe_e_salva_bloco_9(sessao):
    registro = _rascunho(sessao, "F19-HTTP")
    pagina = cliente.get(f"/registros/{registro['registro_id']}?conta_id=CONTA-A1")
    resposta = cliente.post(f"/registros/{registro['registro_id']}/form1-integral/bloco-9/salvar",
        data={"conta_id": "CONTA-A1", "comando_id": "F19-HTTP-S", "versao_lida": "1",
              "campo__9.1": ["Tecnologia da Informação"], "campo__9.2": "Sim"})
    assert pagina.status_code == 200 and "9.2.2" in pagina.text
    assert resposta.status_code == 200 and "Bloco 9" in resposta.text
