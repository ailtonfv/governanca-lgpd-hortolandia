"""Incremento 8N — próximas providências do ARP no painel inicial."""

from fastapi.testclient import TestClient

from app.atribuicao_form1_integral import atribuir_arp_form1_integral
from app.main import app
from app import consultas_interface
from testes.test_bloco5_form1_integral import _rascunho_pronto


cliente = TestClient(app)


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


def test_arp_com_rascunho_e_pendencias_recebe_proxima_providencia(sessao):
    # Arrange
    registro = _rascunho_do_epsilon(sessao, "F18N-ARP-PENDENTE")

    # Act
    pagina = cliente.get("/?conta_id=CONTA-G1")

    # Assert
    assert pagina.status_code == 200
    assert "Preenchimento do FORM 1" in pagina.text
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
        assert "Preenchimento do FORM 1" not in pagina.text
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
