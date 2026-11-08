"""Bloco 13 do FORM 1 integral — exposição física ou visual."""

from copy import deepcopy
from itertools import combinations
import re
from xml.etree import ElementTree

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modelos import RascunhoForm1Integral
from app.rascunho_form1_integral import salvar_bloco_13_form1_integral
from testes.test_bloco7_form1_integral import _rascunho

cliente = TestClient(app)

SITUACAO_TELA = "Tela com dados pessoais permanece visível ou desbloqueada quando o posto fica sem responsável"
SITUACAO_IMPRESSAO = "Impressões com dados pessoais podem permanecer em impressora, copiadora ou equipamento após a impressão"


def test_bloco_13_salva_situacoes_e_locais(sessao):
    registro = _rascunho(sessao, "F113-OK")
    respostas = {"13.1": [SITUACAO_TELA, SITUACAO_IMPRESSAO], "13.2": "Às vezes",
                 "13.3": "Não", "13.4": ["Atendimento", "Área de impressão"]}
    resultado = salvar_bloco_13_form1_integral(sessao, comando_id="F113-OK-S", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1, respostas=respostas)
    sessao.commit()
    assert resultado["permitido"]
    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo["respostas"]["13.4"] == respostas["13.4"]


@pytest.mark.parametrize("excludente", ("Nenhuma das situações acima", "A confirmar", "Não se aplica"))
def test_bloco_13_recusa_excludente_com_outra_situacao(sessao, excludente):
    registro = _rascunho(sessao, "F113-EXC")
    resultado = salvar_bloco_13_form1_integral(sessao, comando_id=f"F113-EXC-{excludente}", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"13.1": [excludente, SITUACAO_TELA]})
    sessao.commit()
    assert not resultado["permitido"] and "selecionada isoladamente" in resultado["motivo"]


@pytest.mark.parametrize("excludente", ("Nenhuma das situações acima", "A confirmar", "Não se aplica"))
def test_bloco_13_aceita_cada_excludente_isoladamente(sessao, excludente):
    registro = _rascunho(sessao, "F113-ISO")
    resultado = salvar_bloco_13_form1_integral(sessao, comando_id="F113-ISO-S", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"13.1": [excludente], "13.4": ["Não se aplica"]})
    sessao.commit()
    assert resultado["permitido"]
    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo["respostas"]["13.1"] == [excludente]


@pytest.mark.parametrize("alternativas", list(combinations(
    ("Nenhuma das situações acima", "A confirmar", "Não se aplica"), 2)))
def test_bloco_13_recusa_especiais_combinadas_sem_perder_resposta(sessao, alternativas):
    registro = _rascunho(sessao, "F113-ESPECIAIS")
    rid = registro["registro_id"]
    assert salvar_bloco_13_form1_integral(sessao, comando_id="F113-PREVIA", conta_id="CONTA-A1",
        registro_id=rid, versao_lida=1, respostas={"13.1": [SITUACAO_TELA]})["permitido"]
    sessao.commit()
    anterior = deepcopy(sessao.get(RascunhoForm1Integral, rid).conteudo)

    resultado = salvar_bloco_13_form1_integral(sessao, comando_id="F113-COMBINADAS", conta_id="CONTA-A1",
        registro_id=rid, versao_lida=2, respostas={"13.1": list(alternativas)})
    sessao.commit()

    assert not resultado["permitido"]
    assert "selecionada isoladamente" in resultado["motivo"]
    assert sessao.get(RascunhoForm1Integral, rid).conteudo == anterior


def test_ajuda_13_1_explica_alternativas_sem_inventar_referencia(sessao):
    registro = _rascunho(sessao, "F113-AJUDA")
    pagina = cliente.get(f"/registros/{registro['registro_id']}?conta_id=CONTA-A1")

    assert pagina.status_code == 200
    ajuda = pagina.text.split('id="ajuda-cartilha-13.1"', 1)[1].split('</details>', 1)[0]
    assert '<summary>Entenda esta pergunta</summary>' in ajuda
    assert "O fluxo foi examinado e nenhuma das situações de exposição apresentadas foi identificada." in ajuda
    assert "As situações investigadas não são pertinentes às características do fluxo analisado." in ajuda
    assert "Ainda não existem informações suficientes para concluir" in ajuda
    assert "isoladamente" in ajuda and "pré-validação" in ajuda
    assert "Referência:" not in ajuda and '<a ' not in ajuda
    assert 'aria-describedby="ajuda-cartilha-13.1"' in pagina.text
    # Cada título e sua explicação pertencem ao mesmo grupo semântico.
    from app.ajudas_cartilha_form1 import AJUDAS_ALTERNATIVAS_FORM1
    definicoes = ElementTree.fromstring(re.search(
        r'<dl class="definicoes-alternativas-form1">.*?</dl>', ajuda, re.S).group())
    assert len(definicoes) == 3
    for grupo, (titulo, explicacao) in zip(definicoes, AJUDAS_ALTERNATIVAS_FORM1['13.1']):
        assert grupo.tag == 'div'
        assert [filho.tag for filho in grupo] == ['dt', 'dd']
        assert ''.join(grupo.find('dt').itertext()) == titulo
        assert grupo.find('dd').text == explicacao


def test_bloco_13_recusa_opcao_forjada_e_repetida(sessao):
    registro = _rascunho(sessao, "F113-INV")
    for indice, respostas in enumerate(({"13.1": ["Situação forjada"]},
                                        {"13.4": ["Recepção", "Recepção"]})):
        resultado = salvar_bloco_13_form1_integral(sessao, comando_id=f"F113-INV-{indice}", conta_id="CONTA-A1",
            registro_id=registro["registro_id"], versao_lida=1, respostas=respostas)
        sessao.commit()
        assert not resultado["permitido"]


def test_interface_exibe_e_salva_bloco_13(sessao):
    registro = _rascunho(sessao, "F113-HTTP")
    pagina = cliente.get(f"/registros/{registro['registro_id']}?conta_id=CONTA-A1")
    resposta = cliente.post(f"/registros/{registro['registro_id']}/form1-integral/bloco-13/salvar",
        data={"conta_id": "CONTA-A1", "comando_id": "F113-HTTP-S", "versao_lida": "1",
              "campo__13.1": ["A confirmar"]})
    assert pagina.status_code == 200 and "13.4" in pagina.text
    assert resposta.status_code == 200 and "Bloco 13" in resposta.text
