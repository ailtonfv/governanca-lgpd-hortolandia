"""Incremento 8P — régua horizontal e clareza do FORM 1 Integral."""

from fastapi.testclient import TestClient

from app.consultas_interface import carregar_registro
from app.form1_integral import campos_por_id
from app.main import app
from app.rascunho_form1_integral import (
    salvar_bloco_5_form1_integral,
    salvar_bloco_6_form1_integral,
)
from testes.test_bloco5_form1_integral import _rascunho_pronto


cliente = TestClient(app)


def test_regua_horizontal_oferece_quatorze_destinos_e_foco_acessivel(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F18P-REGUA")

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}?conta_id=CONTA-A1"
    )
    estilo = cliente.get("/estaticos/estilo.css")

    # Assert
    assert pagina.status_code == 200
    assert 'class="regua-navegacao-blocos"' in pagina.text
    assert 'aria-label="Navegação horizontal pelos 14 blocos do FORM 1"' in pagina.text
    assert pagina.text.count('<button type="button" data-painel-bloco="') == 14
    assert pagina.text.count('class="numero-bloco"') == 14
    assert "aria-current', 'step'" in pagina.text
    assert "destino.focus({ preventScroll: true })" in pagina.text
    assert "destino.scrollIntoView({ block: 'start' })" in pagina.text
    assert estilo.status_code == 200
    assert ".regua-navegacao-blocos" in estilo.text
    assert "overflow-x: auto" in estilo.text
    assert "min-width: max-content" in estilo.text


def test_navegacao_alerta_alteracoes_nao_salvas_sem_remover_respostas(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F18P-NAO-SALVO")

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}?conta_id=CONTA-A1"
    )

    # Assert
    assert "Há alterações não salvas neste bloco" in pagina.text
    assert "confirmarNavegacaoComAlteracoes()" in pagina.text
    assert "beforeunload" in pagina.text
    assert "formulario.addEventListener('submit'" in pagina.text
    assert "alteracoesNaoSalvas = false" in pagina.text
    assert 'id="titulo-bloco-1"' in pagina.text
    assert 'id="titulo-bloco-14"' in pagina.text


def test_progresso_distingue_respostas_salvas_de_salvamento_vazio(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F18P-SALVAMENTO-VAZIO")
    salvar_bloco_5_form1_integral(
        sessao,
        comando_id="F18P-SALVAMENTO-VAZIO-B5",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        versao_lida=1,
        respostas={},
        complemento_outro="",
    )
    sessao.commit()

    # Act
    _, projecao = carregar_registro(sessao, "CONTA-A1", registro["registro_id"])
    progresso = projecao["form1_integral"]["painel_progresso"]
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}?conta_id=CONTA-A1"
    )

    # Assert
    assert progresso["blocos_salvos"] == [5]
    assert progresso["blocos_com_respostas_salvas"] == [1]
    assert progresso["quantidade_com_respostas_salvas"] == 1
    assert 'data-blocos-salvos="5"' in pagina.text
    assert 'data-blocos-com-respostas="1"' in pagina.text
    assert "salvar um bloco vazio não representa conclusão" in pagina.text


def test_resposta_salva_permanece_e_recebe_estado_proprio_na_regua(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F18P-RESPOSTA-SALVA")
    salvar_bloco_6_form1_integral(
        sessao,
        comando_id="F18P-RESPOSTA-SALVA-B6",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        versao_lida=1,
        respostas={"6.1.1": "Base municipal fictícia"},
    )
    sessao.commit()

    # Act
    _, projecao = carregar_registro(sessao, "CONTA-A1", registro["registro_id"])
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}?conta_id=CONTA-A1#titulo-bloco-6"
    )

    # Assert
    progresso = projecao["form1_integral"]["painel_progresso"]
    assert 6 in progresso["blocos_com_respostas_salvas"]
    assert 'data-blocos-com-respostas="1,6"' in pagina.text
    assert 'class="bloco-com-respostas' in pagina.text
    assert 'value="Base municipal fictícia"' in pagina.text
    assert "Respostas salvas" in pagina.text


def test_pergunta_6_1_1_usa_redacao_orientada_sem_alterar_catalogo(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F18P-ORIGEM")
    pergunta_catalogada = campos_por_id()["6.1.1"].pergunta

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}?conta_id=CONTA-A1#titulo-bloco-6"
    )

    # Assert
    assert "6.1.1 — Qual é a origem dos dados pessoais utilizados neste fluxo?" in pagina.text
    assert (
        "Informe a categoria de quem fornece os dados ou identifique a unidade, órgão, "
        "entidade, sistema ou base de origem. Não registre nomes, CPF ou identificadores "
        "de cidadãos."
    ) in pagina.text
    assert pergunta_catalogada.startswith("Quando necessário")


def test_separacao_nao_anuncia_fim_prematuro_do_form_integral(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F18P-SEPARACAO")

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}?conta_id=CONTA-A1"
    )

    # Assert
    assert "Fim das quatro etapas do FORM 1" not in pagina.text
    assert "Separação entre instrumentos" not in pagina.text
    assert "Outros recursos do ambiente de demonstração" not in pagina.text
    assert "Questionário resumido de demonstração" not in pagina.text
    assert "Questionário sintético legado — recurso exclusivo de demonstração técnica" in pagina.text
