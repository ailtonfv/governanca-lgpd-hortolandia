"""Incremento 8L — orientação das ações e ponteiro da jornada."""

from fastapi.testclient import TestClient

from app.main import app
from testes.test_bloco5_form1_integral import _rascunho_pronto


cliente = TestClient(app)


def test_acao_principal_avanca_e_ponteiro_existe_somente_na_jornada(sessao):
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
    ) == 14
    assert pagina.text.count(
        'class="botao-secundario" type="submit" name="acao_pos_salvar" value="permanecer"'
    ) == 14
    assert pagina.text.count(
        'class="gauge-form1-ponteiro" data-gauge-ponteiro'
    ) == 1
    assert 'class="gauge-form1-ponteiro"' in pagina.text
    assert "O ponteiro indica somente a posição atual entre os 14 blocos" in pagina.text
    assert "var anguloPosicao = -90 + ((numero - 1) / 13) * 180;" in pagina.text
    assert 'class="gauge-pendencias-arco"' in pagina.text
