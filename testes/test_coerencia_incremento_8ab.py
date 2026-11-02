"""Incremento 8AB — coerência funcional e retorno do salvamento."""

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.atribuicao_form1_integral import atribuir_arp_form1_integral
from app.main import app
from app.modelos import Evento, RascunhoForm1Integral
from app.rascunho_form1_integral import (
    iniciar_rascunho_form1_integral,
    salvar_bloco_5_form1_integral,
)
from testes.test_atribuicao_form1_integral import _registro


cliente = TestClient(app)


def _atribuir_e_iniciar(sessao, prefixo, *, modo="proprio", arp_pessoa_id=None):
    registro = _registro(f"{prefixo}-G1")
    atribuir_arp_form1_integral(
        sessao,
        comando_id=f"{prefixo}-ARP",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        modo=modo,
        arp_pessoa_id=arp_pessoa_id,
        versao_lida=0,
    )
    sessao.commit()
    conta_arp = "CONTA-A1" if modo == "proprio" else "CONTA-G1"
    iniciar_rascunho_form1_integral(
        sessao,
        comando_id=f"{prefixo}-INICIAR",
        conta_id=conta_arp,
        registro_id=registro["registro_id"],
    )
    sessao.commit()
    return registro, conta_arp


def test_interface_unifica_aviso_e_distingue_conclusao_de_envio(sessao):
    # Arrange
    registro, conta_id = _atribuir_e_iniciar(sessao, "F18AB-TEXTO")

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": conta_id}
    )

    # Assert
    assert pagina.status_code == 200
    assert pagina.text.count(
        "Ambiente de demonstração — utilize exclusivamente dados fictícios."
    ) == 1
    assert "A conclusão institucional do FORM 1 ainda não está habilitada" in pagina.text
    assert "a submissão ainda não está disponível neste ambiente" not in pagina.text
    assert "Canais declarados na abertura" in pagina.text
    assert "Nenhum canal foi confirmado como aplicável" not in pagina.text


def test_interface_reconhece_quando_apa_tambem_e_arp(sessao):
    # Arrange
    registro = _registro("F18AB-APA-ARP-G1")
    atribuir_arp_form1_integral(
        sessao,
        comando_id="F18AB-APA-ARP-ATRIBUIR",
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

    # Assert
    assert "Designação vigente · o APA em exercício também é o ARP" in pagina.text
    assert "Servidor Alfa (fictício)" not in pagina.text
    assert "Matrícula MAT-FICT-0001 · Servidor Alfa" in pagina.text


def test_compartilhamento_recebe_ajuda_sem_mudar_opcoes_rev13(sessao):
    # Arrange
    registro, conta_id = _atribuir_e_iniciar(sessao, "F18AB-COMPART")

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": conta_id}
    )

    # Assert
    assert "circulação interna entre unidades ou Secretarias da Prefeitura" in pagina.text
    assert "órgão ou entidade pública externa" in pagina.text
    assert "não torna automaticamente uma entidade Operadora LGPD" in pagina.text
    assert 'value="Outro órgão público"' in pagina.text


def test_feedback_de_salvamento_cobre_andamento_sucesso_falha_e_nova_edicao(sessao):
    # Arrange
    registro, conta_id = _atribuir_e_iniciar(sessao, "F18AB-FEEDBACK")

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": conta_id}
    )

    # Assert
    assert "Alterações não salvas." in pagina.text
    assert "Salvando..." in pagina.text
    assert "Rascunho confirmado no servidor." in pagina.text
    assert "formulario.dataset.enviando" in pagina.text

    falha = cliente.post(
        f"/registros/{registro['registro_id']}/form1-integral/bloco-5/salvar",
        data={
            "conta_id": conta_id,
            "comando_id": "F18AB-FEEDBACK-DESATUALIZADO",
            "versao_lida": "2",
            "campo__5.1": "Nome",
        },
    )
    assert "Não foi possível salvar. Suas alterações ainda não foram confirmadas." in falha.text


def test_repeticao_do_mesmo_pedido_nao_cria_versao_ou_evento_duplicado(sessao):
    # Arrange
    registro, conta_id = _atribuir_e_iniciar(sessao, "F18AB-SEM-MUDANCA")
    rascunho = sessao.get(RascunhoForm1Integral, registro["registro_id"])
    parametros = {
        "sessao": sessao,
        "comando_id": "F18AB-MESMO-PEDIDO-SALVAR",
        "conta_id": conta_id,
        "registro_id": registro["registro_id"],
        "versao_lida": rascunho.versao_rascunho,
        "respostas": {},
    }
    quantidade_antes = sessao.scalar(
        select(func.count()).select_from(Evento).where(
            Evento.registro_id == registro["registro_id"]
        )
    )
    # Act
    primeiro = salvar_bloco_5_form1_integral(**parametros)
    sessao.commit()
    repetido = salvar_bloco_5_form1_integral(**parametros)
    sessao.commit()

    # Assert
    sessao.refresh(rascunho)
    quantidade_depois = sessao.scalar(
        select(func.count()).select_from(Evento).where(
            Evento.registro_id == registro["registro_id"]
        )
    )
    assert primeiro["permitido"] and repetido["reexecutado"] is True
    assert rascunho.versao_rascunho == 2
    assert quantidade_depois == quantidade_antes + 1
