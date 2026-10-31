"""Incremento de identificação do APA e do ARP no FORM 1 integral."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.atribuicao_form1_integral import atribuir_arp_form1_integral
from app.banco import motor
from app.eventos import verificar_cadeia
from app.main import app
from app.modelos import AtribuicaoForm1Integral, Evento, EventoAuditoria, Registro
from migracoes.atribuicao_form1_integral import aplicar as aplicar_migracao_atribuicao
from testes.apoio import CADASTRO, g1


cliente = TestClient(app)


def _registro(prefixo):
    return g1(prefixo, CADASTRO, "CTX-TRIB-01")


def test_apa_pode_assumir_tambem_a_funcao_de_arp(sessao):
    registro = _registro("CMD-ARP-PROPRIO-G1")

    resultado = atribuir_arp_form1_integral(
        sessao,
        comando_id="CMD-ARP-PROPRIO",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        modo="proprio",
        versao_lida=0,
    )
    sessao.commit()

    assert resultado["permitido"] and resultado["arp_pessoa_id"] == "PESSOA-A"
    atribuicao = sessao.get(AtribuicaoForm1Integral, registro["registro_id"])
    assert atribuicao.arp_atual_id == "PESSOA-A"
    assert atribuicao.atribuido_por == "PESSOA-A"
    assert atribuicao.versao == 1


def test_apa_indica_outro_arp_e_evento_preserva_os_papeis(sessao):
    registro = _registro("CMD-ARP-OUTRO-G1")

    resultado = atribuir_arp_form1_integral(
        sessao,
        comando_id="CMD-ARP-OUTRO",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        modo="outro",
        arp_pessoa_id="PESSOA-G",
        versao_lida=0,
    )
    sessao.commit()

    evento = sessao.scalars(
        select(Evento).where(
            Evento.registro_id == registro["registro_id"],
            Evento.tipo_evento == "atribuir_arp_form1_integral",
        )
    ).one()
    assert resultado["permitido"] and evento.ator_id == "PESSOA-A"
    assert evento.conteudo["apa_abertura_id"] == "PESSOA-A"
    assert evento.conteudo["arp_atual_id"] == "PESSOA-G"
    assert verificar_cadeia(sessao, registro["codigo_lgpd"])[0]


def test_indicacao_nao_concede_permissao_automaticamente(sessao):
    registro = _registro("CMD-ARP-SEM-PAPEL-G1")

    resultado = atribuir_arp_form1_integral(
        sessao,
        comando_id="CMD-ARP-SEM-PAPEL",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        modo="outro",
        arp_pessoa_id="PESSOA-B",
        versao_lida=0,
    )
    sessao.commit()

    assert not resultado["permitido"]
    assert "não possui designação vigente" in resultado["motivo"]
    assert sessao.get(AtribuicaoForm1Integral, registro["registro_id"]) is None
    auditoria = sessao.scalars(
        select(EventoAuditoria).where(
            EventoAuditoria.conteudo["acao_tentada"].as_string()
            == "atribuir_arp_form1_integral"
        )
    ).one()
    assert auditoria.ator_id == "PESSOA-A"


def test_opcao_outro_recusa_o_proprio_apa(sessao):
    registro = _registro("CMD-ARP-OUTRO-MESMO-G1")

    resultado = atribuir_arp_form1_integral(
        sessao,
        comando_id="CMD-ARP-OUTRO-MESMO",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        modo="outro",
        arp_pessoa_id="PESSOA-A",
        versao_lida=0,
    )
    sessao.commit()

    assert not resultado["permitido"]
    assert "pessoa diferente" in resultado["motivo"]


def test_somente_apa_da_secretaria_pode_atribuir_arp(sessao):
    registro = _registro("CMD-ARP-NAO-APA-G1")

    resultado = atribuir_arp_form1_integral(
        sessao,
        comando_id="CMD-ARP-NAO-APA",
        conta_id="CONTA-G1",
        registro_id=registro["registro_id"],
        modo="proprio",
        versao_lida=0,
    )
    sessao.commit()

    assert not resultado["permitido"]
    assert "função de APA" in resultado["motivo"]


def test_atribuicao_e_idempotente_e_recusa_tela_desatualizada(sessao):
    registro = _registro("CMD-ARP-VERSAO-G1")
    parametros = dict(
        comando_id="CMD-ARP-VERSAO-1",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        modo="proprio",
        versao_lida=0,
    )

    primeiro = atribuir_arp_form1_integral(sessao, **parametros)
    sessao.commit()
    repetido = atribuir_arp_form1_integral(sessao, **parametros)
    desatualizado = atribuir_arp_form1_integral(
        sessao,
        comando_id="CMD-ARP-VERSAO-2",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        modo="outro",
        arp_pessoa_id="PESSOA-G",
        versao_lida=0,
    )
    sessao.commit()

    assert primeiro["permitido"] and repetido["reexecutado"] is True
    assert not desatualizado["permitido"]
    assert "desatualizada" in desatualizado["motivo"]
    assert sessao.get(AtribuicaoForm1Integral, registro["registro_id"]).arp_atual_id == "PESSOA-A"


def test_falha_no_evento_desfaz_a_projecao(sessao, monkeypatch):
    registro = _registro("CMD-ARP-ROLLBACK-G1")

    def falhar(*args, **kwargs):
        raise RuntimeError("falha fictícia controlada")

    monkeypatch.setattr("app.atribuicao_form1_integral.registrar_evento", falhar)
    with pytest.raises(RuntimeError, match="falha fictícia"):
        atribuir_arp_form1_integral(
            sessao,
            comando_id="CMD-ARP-ROLLBACK",
            conta_id="CONTA-A1",
            registro_id=registro["registro_id"],
            modo="proprio",
            versao_lida=0,
        )
        sessao.commit()
    sessao.rollback()

    assert sessao.get(AtribuicaoForm1Integral, registro["registro_id"]) is None


def test_interface_distingue_form_integral_e_permite_indicar_arp():
    registro = _registro("CMD-ARP-UI-G1")

    antes = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )
    resposta = cliente.post(
        f"/registros/{registro['registro_id']}/form1-integral/atribuir-arp",
        data={
            "conta_id": "CONTA-A1",
            "comando_id": "CMD-ARP-UI",
            "modo": "outro",
            "arp_pessoa_id": "PESSOA-G",
            "versao_lida": "0",
        },
    )

    assert "Ambiente de demonstração · somente dados fictícios" in antes.text
    assert "FORM 1 — Levantamento Inicial do Tratamento de Dados Pessoais" in antes.text
    assert "Quem será responsável pelo preenchimento" in antes.text
    assert "Servidor Épsilon (fictício)" in antes.text
    assert '<option value="PESSOA-A">' not in antes.text
    assert "Etapa 4 de 4" in antes.text
    assert "Instrumento sintético · contrato 2" in antes.text
    assert resposta.status_code == 200
    assert "Responsável pelo preenchimento" in resposta.text
    assert "Servidor Épsilon (fictício)" in resposta.text


def test_interface_nao_oferece_atribuicao_a_quem_nao_e_apa():
    registro = _registro("CMD-ARP-UI-LEITURA-G1")

    resposta = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-G1"}
    )

    assert resposta.status_code == 200
    assert "Confirmar responsável pelo preenchimento" not in resposta.text
    assert "Somente um APA responsável" in resposta.text


def test_migracao_11_recria_tabela_de_atribuicao():
    with motor.begin() as conexao:
        AtribuicaoForm1Integral.__table__.drop(bind=conexao)
    with Session(motor) as sessao, sessao.begin():
        aplicar_migracao_atribuicao(sessao)

    assert inspect(motor).has_table("atribuicao_form1_integral")
