"""Incremento 8O — mapeamentos e providências no painel inicial."""

from fastapi.testclient import TestClient

from app.atribuicao_form1_integral import atribuir_arp_form1_integral
from app.main import app
from app.rascunho_form1_integral import iniciar_rascunho_form1_integral
from testes.apoio import CADASTRO, g1
from testes.test_painel_arp_incremento_8n import _rascunho_do_epsilon
from testes.test_pendencia_intersecretarial import p1


cliente = TestClient(app)


def _rascunho_do_epsilon_em_objeto(
    sessao, prefixo, objeto_id, contexto_id, titulo
):
    registro = g1(
        f"{prefixo}-G1",
        objeto_id,
        contexto_id,
        titulo=titulo,
    )
    atribuir_arp_form1_integral(
        sessao,
        comando_id=f"{prefixo}-ARP-INICIAL",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        modo="proprio",
        versao_lida=0,
    )
    sessao.commit()
    iniciar_rascunho_form1_integral(
        sessao,
        comando_id=f"{prefixo}-INICIAR",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
    )
    sessao.commit()
    atribuir_arp_form1_integral(
        sessao,
        comando_id=f"{prefixo}-ARP-EPSILON",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        modo="outro",
        arp_pessoa_id="PESSOA-G",
        versao_lida=1,
    )
    sessao.commit()
    return registro


def test_painel_reune_consulta_e_providencia_no_mesmo_cartao(sessao):
    # Arrange
    registro = _rascunho_do_epsilon(sessao, "F18O-UM-REGISTRO")

    # Act
    pagina = cliente.get("/?conta_id=CONTA-G1")

    # Assert
    assert pagina.status_code == 200
    assert 'class="grade-painel-inicial"' not in pagina.text
    assert pagina.text.count('class="cartao-mapeamento"') == 1
    assert registro["codigo_lgpd"] in pagina.text
    assert "Situação do Registro:" in pagina.text
    assert "Situação do FORM 1:" in pagina.text
    assert "Responsável pela próxima etapa:" in pagina.text
    assert (
        f'/registros/{registro["registro_id"]}?conta_id=CONTA-G1">'
        "Ver detalhes do Registro"
    ) in pagina.text
    assert (
        f'/registros/{registro["registro_id"]}?conta_id=CONTA-G1#titulo-bloco-'
        in pagina.text
    )


def test_arp_com_quatro_rascunhos_recebe_quatro_providencias_identificadas(sessao):
    # Arrange
    registros = [
        _rascunho_do_epsilon_em_objeto(
            sessao, f"F18O-MULTIPLO-{indice}", objeto, contexto, titulo
        )
        for indice, (objeto, contexto, titulo) in enumerate(
            (
                ("OBJ-ATV-020", "CTX-TRIB-01", "Atividade cadastral fictícia"),
                ("OBJ-PRC-001", "CTX-TRIB-02", "Processo tributário fictício"),
                ("OBJ-SRV-001", "CTX-TRIB-03", "Serviço de guia fictício"),
                ("OBJ-SRV-002", "CTX-TRIB-03", "Serviço de certidão fictício"),
            ),
            start=1,
        )
    ]

    # Act
    pagina = cliente.get("/?conta_id=CONTA-G1")

    # Assert
    assert pagina.status_code == 200
    assert (
        'class="contador contador-providencias" '
        'aria-label="0 providência(s) de conferência">0</span>'
    ) in pagina.text
    assert pagina.text.count(">Continuar FORM 1 Integral</a>") == 4
    for registro in registros:
        assert registro["codigo_lgpd"] in pagina.text
        assert (
            f'/registros/{registro["registro_id"]}?conta_id=CONTA-G1#titulo-bloco-'
            in pagina.text
        )


def test_agente_com_mapeamento_sem_providencia_mantem_consulta(sessao):
    # Arrange
    registro = g1(
        "F18O-SOMENTE-CONSULTA",
        CADASTRO,
        "CTX-TRIB-01",
        titulo="Serviço consultável fictício",
    )

    # Act
    pagina = cliente.get("/?conta_id=CONTA-B1")

    # Assert
    assert pagina.status_code == 200
    assert registro["codigo_lgpd"] in pagina.text
    assert "Serviço consultável fictício" in pagina.text
    assert "Ver detalhes do Registro" in pagina.text
    assert "Nenhuma providência de conferência pendente para seu perfil neste momento." in pagina.text
    assert "Continuar FORM 1" not in pagina.text
    assert 'aria-label="0 providência(s) de conferência">0</span>' in pagina.text


def test_apa_com_outro_arp_visualiza_registro_sem_acao_de_preenchimento(sessao):
    # Arrange
    registro = _rascunho_do_epsilon(sessao, "F18O-APA-CONSULTA")

    # Act
    pagina = cliente.get("/?conta_id=CONTA-A1")

    # Assert
    assert pagina.status_code == 200
    assert registro["codigo_lgpd"] in pagina.text
    assert "Ver detalhes do Registro" in pagina.text
    assert "Continuar FORM 1" not in pagina.text


def test_contador_considera_registro_unico_quando_ha_varios_alertas(sessao):
    # Arrange
    registro = g1("F18O-ALERTAS-G1", CADASTRO, "CTX-TRIB-01")
    p1(registro["registro_id"], cmd="F18O-ALERTAS-P1")

    # Act
    pagina = cliente.get("/?conta_id=CONTA-C1")

    # Assert
    assert pagina.status_code == 200
    assert "Providência de outra unidade recebida" in pagina.text
    assert "Conclusão bloqueada" in pagina.text
    assert 'aria-label="0 providência(s) de conferência">0</span>' in pagina.text
    assert pagina.text.count(">Ver providência no Registro</a>") == 2


def test_layout_unificado_empilha_cartao_em_tela_pequena_sem_biblioteca_externa():
    # Arrange / Act
    estilo = cliente.get("/estaticos/estilo.css")

    # Assert
    assert estilo.status_code == 200
    assert 'painel-registros-unificado' in cliente.get("/?conta_id=CONTA-A1").text
    assert 'grid-template-columns: minmax(0, 3fr) minmax(18rem, 2fr)' not in estilo.text
    assert '.resumo-contadores-painel' in estilo.text
    assert '.providencias-registro' in estilo.text
    assert '.cartao-mapeamento { grid-template-columns: 1fr' in estilo.text
    # A ação de retomar inclui botão, explicação e consulta: não pode
    # consumir a largura do conteúdo por dimensionamento automático.
    assert 'grid-template-columns: minmax(0, 1fr) minmax(11rem, auto)' not in estilo.text
    assert 'grid-template-columns: minmax(0, 1fr) minmax(11rem, 16rem)' in estilo.text
    assert '.acoes-cartao-registro { display: flex; flex-direction: column;' in estilo.text
