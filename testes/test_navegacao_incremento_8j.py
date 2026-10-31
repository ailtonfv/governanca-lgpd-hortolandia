"""Incremento 8J — navegação sequencial e orientação do FORM 1 integral."""

from urllib.parse import unquote

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.banco import motor
from app.main import app
from app.modelos import RascunhoForm1Integral
from testes.test_bloco5_form1_integral import _rascunho_pronto


cliente = TestClient(app)


def _postar_bloco(registro_id, bloco, comando_id, versao, **dados):
    return cliente.post(
        f"/registros/{registro_id}/form1-integral/bloco-{bloco}/salvar",
        data={
            "conta_id": "CONTA-A1",
            "comando_id": comando_id,
            "versao_lida": str(versao),
            **dados,
        },
        follow_redirects=False,
    )


def test_salvar_bloco_preserva_posicao_e_acao_sequencial_avanca(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F1-8J-ACOES")

    # Act
    ficar = _postar_bloco(
        registro["registro_id"], 5, "F1-8J-FICAR-B5", 1,
        **{"campo__5.1": ["Nome"]},
    )
    avancar = _postar_bloco(
        registro["registro_id"], 5, "F1-8J-AVANCAR-B5", 2,
        acao_pos_salvar="proximo", **{"campo__5.1": ["Nome"]},
    )

    # Assert
    assert unquote(ficar.headers["location"]).endswith("#titulo-bloco-5")
    assert unquote(avancar.headers["location"]).endswith("#titulo-bloco-6")
    with Session(motor) as verificacao:
        assert verificacao.get(
            RascunhoForm1Integral, registro["registro_id"]
        ).versao_rascunho == 3


def test_avanco_entre_etapas_preserva_rascunho_incompleto(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F1-8J-ETAPA")

    # Act
    resposta = _postar_bloco(
        registro["registro_id"], 8, "F1-8J-ETAPA-B8", 1,
        acao_pos_salvar="proximo",
    )

    # Assert
    assert resposta.status_code == 303
    assert unquote(resposta.headers["location"]).endswith("#titulo-bloco-9")
    pagina = cliente.get(resposta.headers["location"])
    assert "FORM 1 — Etapa 3 de 4 — Bloco 9 de 14" in pagina.text
    assert "destinoInicial.focus({ preventScroll: true });" in pagina.text
    with Session(motor) as verificacao:
        rascunho = verificacao.get(RascunhoForm1Integral, registro["registro_id"])
        assert rascunho.versao_rascunho == 2


def test_falha_de_validacao_nao_avanca_para_o_proximo_bloco(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F1-8J-INVALIDO")

    # Act
    resposta = _postar_bloco(
        registro["registro_id"], 5, "F1-8J-INVALIDO-B5", 1,
        acao_pos_salvar="proximo", **{"campo__5.1": ["Categoria forjada"]},
    )

    # Assert
    assert resposta.status_code == 303
    assert unquote(resposta.headers["location"]).endswith("#titulo-bloco-5")
    with Session(motor) as verificacao:
        rascunho = verificacao.get(RascunhoForm1Integral, registro["registro_id"])
        assert rascunho.versao_rascunho == 1


def test_ultimo_bloco_conduz_a_pre_validacao_consultiva(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F1-8J-FINAL")

    # Act
    resposta = _postar_bloco(
        registro["registro_id"], 14, "F1-8J-FINAL-B14", 1,
        acao_pos_salvar="proximo",
    )

    # Assert
    assert resposta.status_code == 303
    assert unquote(resposta.headers["location"]).endswith(
        "#titulo-pre-validacao-form1"
    )
    pagina = cliente.get(resposta.headers["location"])
    assert "Pendências antes da futura submissão" in pagina.text
    assert "preValidacaoDaUrl" in pagina.text
    assert "não submete o formulário" in pagina.text


def test_interface_orienta_os_14_blocos_dados_volumes_e_instrumentos(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F1-8J-ORIENTA")

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )

    # Assert
    assert pagina.status_code == 200
    assert pagina.text.count('name="acao_pos_salvar" value="proximo"') == 14
    assert "Salvar e ir para o próximo bloco" in pagina.text
    assert "Salvar e revisar pré-validação" in pagina.text
    assert "FORM 1 — Etapa 1 de 4 — Bloco 1 de 14" in pagina.text
    assert "FORM 1 — Etapa 4 de 4 — Bloco 14 de 14" in pagina.text
    assert "Dado Pessoal:" in pagina.text
    assert "informação relativa a pessoa identificada ou identificável" in pagina.text
    assert "Dado Pessoal Sensível:" in pagina.text
    assert "incluindo dados de saúde e convicção religiosa" in pagina.text
    assert "Atendimentos: quantidade de atendimentos realizados em um período." in pagina.text
    assert "Registros: estoque de registros administrativos existente em uma data de referência." in pagina.text
    assert "Ocorrências: eventos que geram atuações, em determinado período." in pagina.text
    assert "Fim das quatro etapas do FORM 1" in pagina.text
    assert "O instrumento sintético da PoC nuclear começa abaixo." in pagina.text
    assert pagina.text.index("Fim das quatro etapas do FORM 1") < pagina.text.index(
        "Instrumento sintético · contrato 2"
    )
