"""Regressão do 8L após a simplificação visual aprovada no 8AD."""

from fastapi.testclient import TestClient

from app.main import app
from testes.test_bloco5_form1_integral import _rascunho_pronto


cliente = TestClient(app)


def test_acao_principal_avanca_e_indicadores_sao_objetivos(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F1-8L-PONTEIRO")

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )

    # Assert
    assert pagina.status_code == 200
    assert pagina.text.count(
        'class="botao-primario" type="submit" name="acao_pos_salvar" value="proximo"'
    ) == 13
    assert pagina.text.count(
        'type="submit" name="acao_pos_salvar" value="permanecer"'
    ) == 14
    assert pagina.text.count("Salvar e avançar") == 13
    assert pagina.text.count('data-bloco-anterior="') == 13
    assert 'class="indicadores-compactos-form1"' in pagina.text
    assert "gauge-form1" not in pagina.text
    assert "salvar um bloco vazio não representa conclusão" in pagina.text
