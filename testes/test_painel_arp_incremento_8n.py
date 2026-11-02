"""Incremento 8N — próximas providências do ARP no painel inicial."""

from fastapi.testclient import TestClient

from app.atribuicao_form1_integral import atribuir_arp_form1_integral
from app.main import app
from app import consultas_interface
from testes.apoio import CADASTRO, g1
from testes.test_bloco5_form1_integral import _rascunho_pronto


cliente = TestClient(app)


def test_arp_sem_rascunho_recebe_acao_para_iniciar_form1(sessao):
    # Arrange
    registro = g1(
        "F18AD-ARP-INICIAR",
        CADASTRO,
        "CTX-TRIB-01",
        titulo="Serviço inicial fictício",
    )
    atribuir_arp_form1_integral(
        sessao,
        comando_id="F18AD-ARP-INICIAR-ATRIBUICAO",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        modo="proprio",
        versao_lida=0,
    )
    sessao.commit()

    # Act
    pagina = cliente.get("/?conta_id=CONTA-A1")

    # Assert
    assert pagina.status_code == 200
    assert registro["codigo_lgpd"] in pagina.text
    assert "Situação do FORM 1:</strong> Não iniciado" in pagina.text
    assert "O rascunho do FORM 1 ainda não foi iniciado." in pagina.text
    assert ">Iniciar FORM 1 Integral</a>" in pagina.text
    assert (
        f'/registros/{registro["registro_id"]}?conta_id=CONTA-A1'
        '#titulo-form1-integral'
    ) in pagina.text
    assert (
        'aria-label="1 Registro(s) com providências">1</span>'
        in pagina.text
    )


def test_apa_nao_recebe_inicio_quando_outro_arp_foi_designado(sessao):
    # Arrange
    registro = g1(
        "F18AD-OUTRO-ARP",
        CADASTRO,
        "CTX-TRIB-01",
        titulo="Serviço delegado fictício",
    )
    atribuir_arp_form1_integral(
        sessao,
        comando_id="F18AD-OUTRO-ARP-ATRIBUICAO",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        modo="outro",
        arp_pessoa_id="PESSOA-G",
        versao_lida=0,
    )
    sessao.commit()

    # Act
    pagina_apa = cliente.get("/?conta_id=CONTA-A1")
    pagina_arp = cliente.get("/?conta_id=CONTA-G1")

    # Assert
    assert pagina_apa.status_code == 200
    assert pagina_arp.status_code == 200
    assert registro["codigo_lgpd"] in pagina_apa.text
    assert "Iniciar FORM 1" not in pagina_apa.text
    assert registro["codigo_lgpd"] in pagina_arp.text
    assert ">Iniciar FORM 1 Integral</a>" in pagina_arp.text


def _rascunho_do_epsilon(sessao, prefixo):
    """Arrange comum: rascunho ativo e ARP fictício distinto do APA."""

    registro = _rascunho_pronto(sessao, prefixo)
    atribuir_arp_form1_integral(
        sessao,
        comando_id=f"{prefixo}-ATRIBUIR-EPSILON",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        modo="outro",
        arp_pessoa_id="PESSOA-G",
        versao_lida=1,
    )
    sessao.commit()
    return registro


def test_cartoes_atribuem_acoes_corretas_a_alfa_e_epsilon(sessao):
    # Arrange
    registro_epsilon = _rascunho_do_epsilon(sessao, "F18AD-CARTAO-EPSILON")
    registro_alfa = g1(
        "F18AD-CARTAO-ALFA",
        "OBJ-SRV-001",
        "CTX-TRIB-03",
        titulo="Serviço inicial de Alfa fictício",
    )
    atribuir_arp_form1_integral(
        sessao,
        comando_id="F18AD-CARTAO-ALFA-ATRIBUICAO",
        conta_id="CONTA-A1",
        registro_id=registro_alfa["registro_id"],
        modo="proprio",
        versao_lida=0,
    )
    sessao.commit()

    # Act
    pagina_alfa = cliente.get("/?conta_id=CONTA-A1")
    pagina_epsilon = cliente.get("/?conta_id=CONTA-G1")

    # Assert
    for pagina in (pagina_alfa, pagina_epsilon):
        assert pagina.status_code == 200
        assert pagina.text.count('class="cartao-mapeamento"') == 2
        assert 'aria-label="1 Registro(s) com providências">1</span>' in pagina.text
        assert registro_alfa["codigo_lgpd"] in pagina.text
        assert registro_epsilon["codigo_lgpd"] in pagina.text

    assert ">Iniciar FORM 1 Integral</a>" in pagina_alfa.text
    assert ">Continuar FORM 1 Integral</a>" not in pagina_alfa.text
    assert "MAT-FICT-0007" in pagina_alfa.text
    assert "(ARP)" in pagina_alfa.text

    assert ">Continuar FORM 1 Integral</a>" in pagina_epsilon.text
    assert ">Iniciar FORM 1 Integral</a>" not in pagina_epsilon.text
    assert "MAT-FICT-0001" in pagina_epsilon.text
    assert "(ARP)" in pagina_epsilon.text


def test_arp_com_rascunho_e_pendencias_recebe_proxima_providencia(sessao):
    # Arrange
    registro = _rascunho_do_epsilon(sessao, "F18N-ARP-PENDENTE")

    # Act
    pagina = cliente.get("/?conta_id=CONTA-G1")

    # Assert
    assert pagina.status_code == 200
    assert "Responsável pela próxima etapa:" in pagina.text
    assert registro["codigo_lgpd"] in pagina.text
    assert "Atividade tributária fictícia" in pagina.text
    assert "Situação do FORM 1:</strong> Em preenchimento" in pagina.text
    assert "campo(s) obrigatório(s) ativo(s) incompleto(s)" in pagina.text
    assert "Continuar FORM 1" in pagina.text
    assert (
        f'/registros/{registro["registro_id"]}?conta_id=CONTA-G1#titulo-bloco-'
        in pagina.text
    )
    assert "Nenhuma pendência ou próxima ação para este agente." not in pagina.text


def test_apa_e_agente_sem_permissao_nao_recebem_acao_do_arp(sessao):
    # Arrange
    registro = _rascunho_do_epsilon(sessao, "F18N-SEGREGACAO")

    # Act
    pagina_apa = cliente.get("/?conta_id=CONTA-A1")
    pagina_sem_permissao = cliente.get("/?conta_id=CONTA-B1")

    # Assert
    for pagina in (pagina_apa, pagina_sem_permissao):
        assert pagina.status_code == 200
        assert registro["codigo_lgpd"] in pagina.text
        assert "Continuar FORM 1" not in pagina.text


def test_arp_sem_resposta_obrigatoria_pendente_e_encaminhado_a_pre_validacao(
    sessao, monkeypatch
):
    # Arrange
    registro = _rascunho_do_epsilon(sessao, "F18N-SEM-INCOMPLETOS")

    def pre_validacao_sem_incompletos(*args, **kwargs):
        return {
            "consultiva": True,
            "submissao_habilitada": False,
            "incompletos": [],
            "nao_aplicaveis": [],
            "regras_pendentes": [
                {"tipo": "governanca", "mensagem": "Dependência institucional fictícia"}
            ],
            "por_bloco": [],
            "quantidades": {
                "incompletos": 0,
                "nao_aplicaveis": 0,
                "regras_pendentes": 1,
            },
        }

    monkeypatch.setattr(
        consultas_interface,
        "_pre_validar_rascunho_integral",
        pre_validacao_sem_incompletos,
    )

    # Act
    pagina = cliente.get("/?conta_id=CONTA-G1")

    # Assert
    assert pagina.status_code == 200
    assert registro["codigo_lgpd"] in pagina.text
    assert "Nenhum campo obrigatório ativo incompleto" in pagina.text
    assert (
        f'/registros/{registro["registro_id"]}?conta_id=CONTA-G1'
        "#titulo-pre-validacao-form1"
    ) in pagina.text
    assert "Continuar FORM 1" in pagina.text
