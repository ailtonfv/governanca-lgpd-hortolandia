"""Incremento 8H — orientação da próxima providência do FORM 1 integral."""

from fastapi.testclient import TestClient

from app.atribuicao_form1_integral import atribuir_arp_form1_integral
from app.main import app
from testes.test_atribuicao_form1_integral import _registro
from testes.test_bloco5_form1_integral import _rascunho_pronto


cliente = TestClient(app)


def _trecho_proxima_providencia(html):
    inicio = html.index('<section class="proxima-providencia"')
    fim = html.index("</section>", inicio)
    return html[inicio:fim]


def test_arp_autorizado_inicia_form1_e_chega_ao_primeiro_bloco(sessao):
    # Arrange
    registro = _registro("F1-8H-INICIAR-G1")
    atribuir_arp_form1_integral(
        sessao,
        comando_id="F1-8H-INICIAR-ARP",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        modo="proprio",
        versao_lida=0,
    )
    sessao.commit()

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )
    inicio = cliente.post(
        f"/registros/{registro['registro_id']}/form1-integral/iniciar",
        data={"conta_id": "CONTA-A1", "comando_id": "F1-8H-INICIAR-RASCUNHO"},
        follow_redirects=False,
    )

    # Assert
    trecho = _trecho_proxima_providencia(pagina.text)
    assert "Próxima providência" in trecho
    assert "Iniciar FORM 1" in trecho
    assert "Você é o ARP atual" in trecho
    assert 'disabled aria-disabled="true"' in pagina.text
    assert inicio.status_code == 303
    assert "/form1-rev22?conta_id=CONTA-A1" in inicio.headers["location"]
    retomada = cliente.get(inicio.headers["location"])
    assert retomada.status_code == 200
    assert "Preparar o FORM 1" in retomada.text
    assert "Atualizar e continuar" in retomada.text


def test_arp_com_rascunho_recebe_continuacao_para_pendencia_ativa(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F1-8H-CONTINUAR")

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )

    # Assert
    trecho = _trecho_proxima_providencia(pagina.text)
    assert "Preencher FORM 1" in trecho
    assert "/form1-rev22?conta_id=CONTA-A1" in trecho
    assert "Etapas do FORM 1" in pagina.text
    assert "Iniciar FORM 1" not in trecho


def test_apa_com_outro_arp_ve_responsavel_sem_acao_de_preenchimento(sessao):
    # Arrange
    registro = _registro("F1-8H-OUTRO-ARP-G1")
    atribuir_arp_form1_integral(
        sessao,
        comando_id="F1-8H-OUTRO-ARP",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        modo="outro",
        arp_pessoa_id="PESSOA-G",
        versao_lida=0,
    )
    sessao.commit()

    # Act
    pagina_apa = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )
    pagina_arp = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-G1"}
    )

    # Assert
    trecho_apa = _trecho_proxima_providencia(pagina_apa.text)
    assert "matrícula MAT-FICT-0007 · Servidor Épsilon" in trecho_apa
    assert "Somente essa pessoa" in trecho_apa
    assert "Iniciar FORM 1" not in trecho_apa
    assert "Continuar FORM 1" not in trecho_apa
    trecho_arp = _trecho_proxima_providencia(pagina_arp.text)
    assert "Iniciar FORM 1" in trecho_arp


def test_registro_sem_arp_explica_por_que_nao_ha_acao_de_preenchimento(sessao):
    # Arrange
    registro = _registro("F1-8H-SEM-ARP-G1")

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )

    # Assert
    trecho = _trecho_proxima_providencia(pagina.text)
    assert "O APA deverá assumir o preenchimento ou designar um Agente Responsável" in trecho
    assert "antes que o rascunho possa ser iniciado" in trecho
    assert "Iniciar FORM 1" not in trecho
    assert "Continuar FORM 1" not in trecho



def test_entrada_sem_rascunho_orienta_e_preserva_perfil(sessao):
    registro = _registro("ENTRADA-SEM-RASCUNHO-G1")
    rid = registro["registro_id"]
    pagina = cliente.get(f"/registros/{rid}?conta_id=CONTA-A1")
    assert pagina.status_code == 200
    html = pagina.text
    assert html.index('class="proxima-providencia"') < html.index('class="area-designacao-arp"') < html.index('id="instrumentos-registro"')
    assert "O rascunho ainda não foi iniciado" in html
    assert "Abrir edição candidata" not in html
    assert 'href="/registros/'+rid+'/form1-rev22' not in html
    acesso = cliente.get(f"/registros/{rid}/form1-rev22?conta_id=CONTA-A1", follow_redirects=False)
    assert acesso.status_code == 303
    assert acesso.headers['location'] == f"/registros/{rid}?conta_id=CONTA-A1#titulo-proxima-providencia"
    assert "Inicie o rascunho pelo Registro" not in acesso.text
    assert cliente.get(f"/registros/{rid}/form1-rev22?conta_id=CONTA-INEXISTENTE").status_code == 403
