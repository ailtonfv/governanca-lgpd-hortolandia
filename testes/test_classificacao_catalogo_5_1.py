"""Classificação informativa e somente leitura do catálogo 5.1."""

from collections import Counter
from dataclasses import FrozenInstanceError

import pytest
from fastapi.testclient import TestClient

from app.classificacao_catalogo_5_1 import (
    AVALIAR_CONTEXTO,
    CLASSIFICACOES_CATALOGO_5_1,
    PESSOAL_COMUM,
    SENSIVEL,
    VERSAO_CLASSIFICACAO_CATALOGO_5_1,
    validar_classificacoes_catalogo_5_1,
)
from app.consultas_interface import carregar_registro
from app.form1_integral import campos_por_id
from app.main import app
from testes.test_bloco7_form1_integral import _rascunho


cliente = TestClient(app)


def test_matriz_versionada_cobre_as_35_alternativas_nas_quantidades_aprovadas():
    alternativas = campos_por_id()["5.1"].alternativas
    contagem = Counter(item.codigo for item in CLASSIFICACOES_CATALOGO_5_1.values())

    assert VERSAO_CLASSIFICACAO_CATALOGO_5_1 == "F1-CLASS-5.1-v1"
    assert set(CLASSIFICACOES_CATALOGO_5_1) == set(alternativas)
    assert contagem == {PESSOAL_COMUM: 19, SENSIVEL: 9, AVALIAR_CONTEXTO: 7}
    assert validar_classificacoes_catalogo_5_1(alternativas) == []


def test_rotulos_pendentes_e_cautelas_juridicas_sao_explicitos():
    outro = CLASSIFICACOES_CATALOGO_5_1["Outro"]
    confirmar = CLASSIFICACOES_CATALOGO_5_1["A confirmar"]
    roma = CLASSIFICACOES_CATALOGO_5_1[
        "Pertencimento a povos ciganos / Roma, quando efetivamente tratado"
    ]
    financeiro = CLASSIFICACOES_CATALOGO_5_1["Dados financeiros"]

    assert outro.rotulo == "Pendente de avaliação"
    assert confirmar.rotulo == "Pendente de identificação"
    assert roma.codigo == AVALIAR_CONTEXTO and "validação jurídica" in roma.alerta
    assert financeiro.codigo == PESSOAL_COMUM and "proteção reforçada" in financeiro.alerta


def test_classificacao_e_efetivamente_somente_leitura():
    item = CLASSIFICACOES_CATALOGO_5_1["Nome"]

    with pytest.raises(TypeError):
        CLASSIFICACOES_CATALOGO_5_1["Nome"] = item
    with pytest.raises(FrozenInstanceError):
        item.rotulo = "Alterado"


def test_integridade_recusa_catalogo_sem_classificacao_exata():
    alternativas = campos_por_id()["5.1"].alternativas

    problemas = validar_classificacoes_catalogo_5_1(alternativas[:-1])

    assert problemas and "classificações sem categoria" in problemas[0]


def test_projecao_reutiliza_a_mesma_matriz_nas_cinco_perguntas(sessao):
    registro = _rascunho(sessao, "F1-CLASS-PROJ")

    _, resumo = carregar_registro(sessao, "CONTA-A1", registro["registro_id"])

    integral = resumo["form1_integral"]
    campos = [
        integral["campos_bloco_4"]["4.2.5.1"],
        integral["campos_bloco_5"]["5.1"],
        integral["campos_bloco_6"]["6.2.2"],
        integral["campos_bloco_9"]["9.2.2"],
        integral["campos_bloco_10"]["10.4"],
    ]
    assert all(campo["classificacoes_dados"] is CLASSIFICACOES_CATALOGO_5_1
               for campo in campos)
    assert {campo["versao_classificacao_dados"] for campo in campos} == {
        VERSAO_CLASSIFICACAO_CATALOGO_5_1
    }


def test_interface_exibe_classificacao_sem_controle_de_edicao(sessao):
    registro = _rascunho(sessao, "F1-CLASS-HTTP")

    pagina = cliente.get(f"/registros/{registro['registro_id']}?conta_id=CONTA-A1")

    assert pagina.status_code == 200
    assert pagina.text.count('class="classificacao-dado ') == 35 * 5
    assert "Pendente de avaliação" in pagina.text
    assert "Pendente de identificação" in pagina.text
    assert "proteção reforçada" in pagina.text
    assert VERSAO_CLASSIFICACAO_CATALOGO_5_1 in pagina.text
    assert 'name="classificacao' not in pagina.text
