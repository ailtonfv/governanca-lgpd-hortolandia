"""Incremento 8AD — progresso objetivo, designação condicional e navegação."""

from fastapi.testclient import TestClient

from app.main import app
from testes.test_bloco5_form1_integral import _rascunho_pronto


cliente = TestClient(app)


def test_progresso_substitui_velocimetros_por_indicadores_objetivos(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F1-8AD-PROGRESSO")

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )

    # Assert
    assert pagina.status_code == 200
    assert "blocos possuem respostas salvas" in pagina.text
    assert "blocos visitados nesta sessão" in pagina.text
    assert "pendências segundo a política atualmente configurada" in pagina.text
    assert "gauge-form1" not in pagina.text
    assert "salvar um bloco vazio não representa conclusão" in pagina.text
    assert "não significam conferência, submissão ou conformidade" in pagina.text


def test_designacao_arp_exibe_somente_controles_pertinentes_ao_modo(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F1-8AD-ARP")

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )

    # Assert
    assert 'data-painel-modo-arp="proprio" hidden' in pagina.text
    assert 'data-painel-modo-arp="outro" hidden' in pagina.text
    assert "Confirmar que assumirei o preenchimento" in pagina.text
    assert "Confirmar designação do ARP" in pagina.text
    assert 'id="arp_pessoa_id" name="arp_pessoa_id" disabled' in pagina.text
    assert "selecao.disabled = valor !== 'outro'" in pagina.text
    assert "selecao.required = valor === 'outro'" in pagina.text
    assert "A designação atual permanece válida até a confirmação" in pagina.text


def test_acoes_dos_blocos_respeitam_primeiro_intermediarios_e_ultimo(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F1-8AD-ACOES")

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )

    # Assert
    assert pagina.text.count('data-bloco-anterior="') == 13
    assert pagina.text.count('name="acao_pos_salvar" value="permanecer"') == 14
    assert pagina.text.count('name="acao_pos_salvar" value="proximo"') == 13
    assert pagina.text.count("Salvar e avançar") == 13
    assert "Consultar pré-validação" in pagina.text
    assert "Nenhuma alteração para salvar." in pagina.text
    assert "formulario.dataset.enviando === 'true'" in pagina.text
    assert "if (destino) destino.click();" in pagina.text
    assert "Os valores digitados foram preservados para nova tentativa." in pagina.text
    assert "preservarTentativa(formulario);" in pagina.text
