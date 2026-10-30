"""Incremento 8G — retorno perceptível após salvar e indicar o ARP."""

from urllib.parse import unquote

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.banco import motor
from app.main import app
from app.modelos import AtribuicaoForm1Integral, Evento, RascunhoForm1Integral
from testes.test_atribuicao_form1_integral import _registro
from testes.test_bloco5_form1_integral import _rascunho_pronto


cliente = TestClient(app)


def test_salvar_bloco_preserva_etapa_posicao_e_exibe_confirmacao(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F1-8G-SALVAR")

    # Act
    resposta = cliente.post(
        f"/registros/{registro['registro_id']}/form1-integral/bloco-5/salvar",
        data={
            "conta_id": "CONTA-A1",
            "comando_id": "F1-8G-SALVAR-B5",
            "versao_lida": "1",
            "campo__5.1": ["Nome"],
        },
        follow_redirects=False,
    )

    # Assert
    destino = unquote(resposta.headers["location"])
    assert resposta.status_code == 303
    assert destino.endswith("#titulo-bloco-5")
    pagina = cliente.get(resposta.headers["location"])
    assert pagina.status_code == 200
    assert "Bloco 5 do FORM 1 integral salvo com segurança." in pagina.text
    assert 'id="mensagem-registro"' in pagina.text
    assert "var blocoDaUrl" in pagina.text and "scrollIntoView" in pagina.text
    with Session(motor) as verificacao:
        rascunho = verificacao.get(RascunhoForm1Integral, registro["registro_id"])
        assert rascunho.versao_rascunho == 2
        assert rascunho.conteudo["respostas"]["5.1"] == ["Nome"]


def test_indicacao_repetida_confirma_arp_sem_evento_ou_permissao_duplicados(sessao):
    # Arrange
    registro = _registro("F1-8G-ARP-G1")
    rota = f"/registros/{registro['registro_id']}/form1-integral/atribuir-arp"
    dados = {
        "conta_id": "CONTA-A1",
        "modo": "outro",
        "arp_pessoa_id": "PESSOA-G",
    }

    # Act
    primeira = cliente.post(
        rota,
        data={**dados, "comando_id": "F1-8G-ARP-1", "versao_lida": "0"},
        follow_redirects=False,
    )
    repetida = cliente.post(
        rota,
        data={**dados, "comando_id": "F1-8G-ARP-2", "versao_lida": "1"},
        follow_redirects=False,
    )

    # Assert
    assert primeira.status_code == repetida.status_code == 303
    assert primeira.headers["location"].endswith("#titulo-form1-integral")
    pagina_primeira = cliente.get(primeira.headers["location"])
    pagina_repetida = cliente.get(repetida.headers["location"])
    identidade = "Matrícula MAT-FICT-0007 · Servidor Épsilon (fictício)"
    assert "Responsável pelo preenchimento alterado." in pagina_primeira.text
    assert "Nenhuma alteração no responsável pelo preenchimento:" in pagina_repetida.text
    assert identidade in pagina_repetida.text
    with Session(motor) as verificacao:
        atribuicao = verificacao.get(AtribuicaoForm1Integral, registro["registro_id"])
        eventos = verificacao.scalars(select(Evento).where(
            Evento.registro_id == registro["registro_id"],
            Evento.tipo_evento == "atribuir_arp_form1_integral",
        )).all()
        assert atribuicao.arp_atual_id == "PESSOA-G" and atribuicao.versao == 1
        assert len(eventos) == 1
