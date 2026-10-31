"""Incremento 8I — clareza institucional e identificação dos agentes."""

from fastapi.testclient import TestClient

from app.main import app
from testes.test_atribuicao_form1_integral import _registro


cliente = TestClient(app)


def test_cabecalho_institucional_separa_objetivo_e_situacao_operacional(sessao):
    # Arrange
    registro = _registro("F1-8I-CABECALHO-G1")

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )

    # Assert
    assert "FORM 1 — Levantamento Inicial do Tratamento de Dados Pessoais" in pagina.text
    assert "Ambiente de demonstração · somente dados fictícios" in pagina.text
    assert (
        "Descreva como este serviço, processo ou atividade coleta, utiliza, "
        "compartilha, armazena e protege dados pessoais."
    ) in pagina.text
    assert "Situação operacional:" in pagina.text
    assert "O rascunho pode ser salvo e retomado mesmo incompleto." in pagina.text
    assert "PoC ampliada · contrato 3 candidato" not in pagina.text


def test_contexto_exibe_nome_catalogado_acompanhado_do_codigo(sessao):
    # Arrange
    registro = _registro("F1-8I-CONTEXTO-G1")

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )

    # Assert
    assert "Gestão cadastral tributária (CTX-TRIB-01)" in pagina.text


def test_apa_de_abertura_e_em_exercicio_exibem_matricula_e_nome(sessao):
    # Arrange
    registro = _registro("F1-8I-APAS-G1")

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )

    # Assert
    identidade = "Matrícula MAT-FICT-0001 · Servidor Alfa (fictício)"
    assert "APA de abertura" in pagina.text
    assert "APA em exercício" in pagina.text
    assert pagina.text.count(identidade) >= 2

