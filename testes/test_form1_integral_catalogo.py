"""Provas estruturais do incremento F1-0, sem ativar o contrato candidato."""

from app.form1_integral import (
    QUANTIDADE_CAMPOS_REV13,
    REVISAO_FONTE_FORM1_INTEGRAL,
    VERSAO_CONTRATO_FORM1_INTEGRAL_CANDIDATA,
    campos_por_id,
    carregar_catalogo_form1_integral,
)
from app.form1_sintetico import VERSAO_CONTRATO_FORM1


def test_catalogo_rev13_preserva_os_128_identificadores_unicos():
    campos = carregar_catalogo_form1_integral()

    assert len(campos) == QUANTIDADE_CAMPOS_REV13 == 128
    assert len({campo.id for campo in campos}) == 128
    assert campos[0].id == "0.1"
    assert campos[-1].id == "14.2.4"


def test_catalogo_rev13_preserva_pergunta_opcoes_e_orientacao():
    campos = campos_por_id()

    assert REVISAO_FONTE_FORM1_INTEGRAL == "REV13-2026-09-20"
    assert campos["2.1"].pergunta == "Por qual porta de entrada a demanda chega inicialmente?"
    assert "Ouvidoria" in campos["2.1"].alternativas
    assert "e-SIC" in campos["2.1"].alternativas
    assert campos["2.8"].instrucao.endswith("Campo opcional.")
    assert "Não inserir dado pessoal" in campos["14.2.4"].instrucao


def test_contrato_integral_permanece_candidato_e_nao_substitui_o_nuclear():
    assert VERSAO_CONTRATO_FORM1 == 2
    assert VERSAO_CONTRATO_FORM1_INTEGRAL_CANDIDATA == 3
