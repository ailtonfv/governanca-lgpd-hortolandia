"""Incremento 8AE — estabilização da entrada do FORM 1 Integral (AAA)."""

from fastapi.testclient import TestClient

from app.atribuicao_form1_integral import atribuir_arp_form1_integral
from app.main import app
from app.rascunho_form1_integral import iniciar_rascunho_form1_integral
from testes.test_atribuicao_form1_integral import _registro
from testes.test_conferencia_interna_form1_integral_8ac import _preparar, _solicitar


cliente = TestClient(app)


def _pagina(registro_id, conta_id):
    return cliente.get(f"/registros/{registro_id}", params={"conta_id": conta_id})


def _trecho_proxima_providencia(html):
    inicio = html.index('<section class="proxima-providencia"')
    fim = html.index("</section>", inicio)
    return html[inicio:fim]


def test_sem_arp_mostra_designacao_pendente_sem_conceder_edicao():
    # Arrange
    registro = _registro("8AE-SEM-ARP-G1")

    # Act
    pagina = _pagina(registro["registro_id"], "CONTA-A1")

    # Assert
    trecho = _trecho_proxima_providencia(pagina.text)
    assert "Seu papel neste Registro:</strong> APA" in trecho
    assert "Quem preencherá o FORM 1?" in pagina.text
    assert "Alterar responsável pelo preenchimento" not in pagina.text
    assert "Iniciar FORM 1" not in trecho
    assert '<form class="formulario formulario-integral"' not in pagina.text


def test_apa_que_tambem_e_arp_ve_acao_antes_dos_quadros_e_redesignacao_recolhida(sessao):
    # Arrange
    registro = _registro("8AE-APA-ARP-G1")
    resultado = atribuir_arp_form1_integral(
        sessao, comando_id="8AE-APA-ARP-ATR", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], modo="proprio", versao_lida=0,
    )
    sessao.commit()
    assert resultado["permitido"]

    # Act
    pagina = _pagina(registro["registro_id"], "CONTA-A1")

    # Assert
    trecho = _trecho_proxima_providencia(pagina.text)
    assert "Seu papel neste Registro:</strong> APA e ARP" in trecho
    assert "Iniciar FORM 1" in trecho
    assert pagina.text.index('class="proxima-providencia"') < pagina.text.index(
        'class="informacoes-institucionais-form1"'
    )
    assert "Informações do Registro — somente leitura" in pagina.text
    assert "ARP vigente:</strong> matrícula MAT-FICT-0001 · Servidor Alfa" in pagina.text
    assert '<details class="alteracao-arp">' in pagina.text
    assert '<details class="alteracao-arp" open' not in pagina.text
    assert "Alterar responsável pelo preenchimento" in pagina.text


def test_apa_consulta_e_arp_continua_o_mesmo_rascunho_sem_trocar_permissoes(sessao):
    # Arrange
    registro = _registro("8AE-OUTRO-ARP-G1")
    atribuicao = atribuir_arp_form1_integral(
        sessao, comando_id="8AE-OUTRO-ARP-ATR", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], modo="outro",
        arp_pessoa_id="PESSOA-G", versao_lida=0,
    )
    inicio = iniciar_rascunho_form1_integral(
        sessao, comando_id="8AE-OUTRO-ARP-INI", conta_id="CONTA-G1",
        registro_id=registro["registro_id"],
    )
    sessao.commit()
    assert atribuicao["permitido"] and inicio["permitido"]

    # Act
    pagina_apa = _pagina(registro["registro_id"], "CONTA-A1")
    pagina_arp = _pagina(registro["registro_id"], "CONTA-G1")

    # Assert
    trecho_apa = _trecho_proxima_providencia(pagina_apa.text)
    trecho_arp = _trecho_proxima_providencia(pagina_arp.text)
    assert "Seu papel neste Registro:</strong> APA" in trecho_apa
    assert "Consultar FORM 1 Integral" in trecho_apa
    assert "data-consultar-form1" in trecho_apa
    assert "Você pode consultar o levantamento em modo somente leitura" in trecho_apa
    assert '<form class="formulario formulario-integral"' not in pagina_apa.text
    assert "Seu papel neste Registro:</strong> ARP" in trecho_arp
    assert "Continuar FORM 1" in trecho_arp
    assert '<form class="formulario formulario-integral"' in pagina_arp.text


def test_conferencia_recebida_e_promovida_a_proxima_providencia_do_apa(sessao):
    # Arrange
    registro = _preparar(sessao, "8AE-CONFERENCIA")
    resultado = _solicitar(sessao, registro, comando="8AE-CONFERENCIA-SOL")
    assert resultado["permitido"]

    # Act
    pagina = _pagina(registro["registro_id"], "CONTA-A1")

    # Assert
    trecho = _trecho_proxima_providencia(pagina.text)
    assert "Consultar levantamento recebido" in trecho
    assert "/form1-integral/conferencia-interna?conta_id=CONTA-A1" in trecho
    assert "não conclui nem submete institucionalmente" in trecho
    assert "FORM 1 aguardando conferência interna" in pagina.text


def test_acesso_direto_as_perguntas_preserva_foco_e_navegacao_existentes(sessao):
    # Arrange
    registro = _registro("8AE-FOCO-G1")
    atribuir_arp_form1_integral(
        sessao, comando_id="8AE-FOCO-ATR", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], modo="proprio", versao_lida=0,
    )
    iniciar_rascunho_form1_integral(
        sessao, comando_id="8AE-FOCO-INI", conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
    )
    sessao.commit()

    # Act
    pagina = _pagina(registro["registro_id"], "CONTA-A1")

    # Assert
    assert 'id="titulo-bloco-1"' in pagina.text
    assert "destino.focus({ preventScroll: true });" in pagina.text
    assert "posicionarDestinoForm1(destino);" in pagina.text
    assert "Etapas do FORM 1" in pagina.text
    assert "Fim das quatro etapas do FORM 1" not in pagina.text
