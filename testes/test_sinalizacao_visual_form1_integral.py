"""Sinalização visual declarativa e acessível do FORM 1 integral."""

from fastapi.testclient import TestClient

from app.form1_integral import campos_por_id
from app.main import app
from app.pre_validacao_form1_integral import (
    carregar_matriz_obrigatoriedade, metadado_visual_obrigatoriedade,
)
from testes.test_bloco7_form1_integral import _rascunho


cliente = TestClient(app)


def _luminancia(cor: str) -> float:
    canais = [int(cor[indice:indice + 2], 16) / 255 for indice in (1, 3, 5)]
    lineares = [
        canal / 12.92 if canal <= .04045 else ((canal + .055) / 1.055) ** 2.4
        for canal in canais
    ]
    return .2126 * lineares[0] + .7152 * lineares[1] + .0722 * lineares[2]


def _contraste(frente: str, fundo: str) -> float:
    valores = sorted((_luminancia(frente), _luminancia(fundo)), reverse=True)
    return (valores[0] + .05) / (valores[1] + .05)


def test_matriz_inteira_possui_apresentacao_visual_sem_inventar_recomendados():
    matriz = carregar_matriz_obrigatoriedade()

    apresentacoes = {
        campo_id: metadado_visual_obrigatoriedade(campo_id)
        for campo_id in campos_por_id()
    }

    assert set(apresentacoes) == set(matriz)
    assert {item["marcador"] for item in apresentacoes.values()} <= {"*", "**", "****"}
    assert not any(item["marcador"] == "***" for item in apresentacoes.values())
    assert all(
        item["marcador_ativo"] == "*"
        for item in apresentacoes.values() if item["condicional"]
    )


def test_interface_explica_marcadores_e_separa_dp_de_dps(sessao):
    registro = _rascunho(sessao, "F1-VISUAL-HTTP")

    pagina = cliente.get(f"/registros/{registro['registro_id']}?conta_id=CONTA-A1")

    assert pagina.status_code == 200
    assert "Como ler as sinalizações" in pagina.text
    assert "categoria reservada; nenhum campo possui essa classificação" in pagina.text
    assert 'data-obrigatoriedade-classe="Obrigatória essencial"' in pagina.text
    assert 'data-obrigatoriedade-classe="Obrigatória condicional"' in pagina.text
    assert 'data-marcador-base="****"' in pagina.text
    assert "DP</strong> · Pessoal comum" in pagina.text
    assert "DPS</strong> · Dado pessoal sensível" in pagina.text
    assert "sincronizarSinalizacaoObrigatoriedade" in pagina.text
    assert "Submeter FORM 1 Integral" not in pagina.text


def test_contrastes_dos_indicadores_atendem_wcag_aa():
    pares = (
        ("#7f1d1d", "#fff1f2"),
        ("#78350f", "#fffbeb"),
        ("#334155", "#f4f7f9"),
        ("#075985", "#ffffff"),
        ("#17212b", "#ffffff"),
    )

    assert all(_contraste(frente, fundo) >= 4.5 for frente, fundo in pares)
