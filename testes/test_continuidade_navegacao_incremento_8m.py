"""Incremento 8M — continuidade segura entre os 14 blocos."""

from urllib.parse import unquote

import pytest
from fastapi.testclient import TestClient

from app.main import app
from testes.test_bloco5_form1_integral import _rascunho_pronto


cliente = TestClient(app)


def _salvar_e_avancar(registro_id: str, bloco: int, comando_id: str):
    return cliente.post(
        f"/registros/{registro_id}/form1-integral/bloco-{bloco}/salvar",
        data={
            "conta_id": "CONTA-A1",
            "comando_id": comando_id,
            "versao_lida": "1",
            "acao_pos_salvar": "proximo",
        },
        follow_redirects=False,
    )


@pytest.mark.parametrize(
    ("bloco_origem", "bloco_destino"),
    [(3, 4), (4, 5), (5, 6), (13, 14)],
)
def test_salvar_avanca_exatamente_um_bloco_sem_salto(
    sessao, bloco_origem, bloco_destino
):
    # Arrange
    registro = _rascunho_pronto(
        sessao, f"F1-8M-{bloco_origem}-{bloco_destino}"
    )

    # Act
    resposta = _salvar_e_avancar(
        registro["registro_id"], bloco_origem, f"F1-8M-CMD-{bloco_origem}"
    )

    # Assert
    assert resposta.status_code == 303
    assert unquote(resposta.headers["location"]).endswith(
        f"#titulo-bloco-{bloco_destino}"
    )


def test_bloco_14_avanca_somente_para_pre_validacao_consultiva(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F1-8M-14-PRE")

    # Act
    resposta = _salvar_e_avancar(registro["registro_id"], 14, "F1-8M-CMD-14")

    # Assert
    assert resposta.status_code == 303
    assert unquote(resposta.headers["location"]).endswith(
        "#titulo-pre-validacao-form1"
    )


def test_interface_nomeia_destinos_e_prioriza_um_bloco_sem_perder_navegacao(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F1-8M-INTERFACE")

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )

    # Assert
    assert pagina.status_code == 200
    assert "Próximo: Bloco 4 — Pessoas a quem os dados se referem" in pagina.text
    assert "Próximo: Bloco 5 — Categorias de dados" in pagina.text
    assert "Próximo: Bloco 6 — Origem dos dados" in pagina.text
    assert "Próximo: Bloco 14 — Achados e pendências" in pagina.text
    assert pagina.text.count("Salvar rascunho") >= 14
    assert pagina.text.count(">Anterior</button>") == 13
    assert "bloco.hidden = oculto || numeroDoBloco !== numeroBlocoAlvo;" in pagina.text
    assert "Use o mapa da jornada para consultar ou editar qualquer outro bloco." in pagina.text
    assert "posicionarDestinoForm1(destinoInicial);" in pagina.text
