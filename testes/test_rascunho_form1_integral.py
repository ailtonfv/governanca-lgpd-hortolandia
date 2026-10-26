"""Primeiro rascunho executável do FORM 1 integral — Bloco 1."""

import pytest
import threading
from fastapi.testclient import TestClient
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.atribuicao_form1_integral import atribuir_arp_form1_integral
from app.banco import motor
from app.eventos import verificar_cadeia
from app.main import app
from app.modelos import (Evento, EventoAuditoria, RascunhoForm1Integral,
                          Registro)
from app.rascunho_form1_integral import (iniciar_rascunho_form1_integral,
                                         salvar_bloco_1_form1_integral)
from migracoes.rascunho_form1_integral import aplicar as aplicar_migracao
from testes.apoio import CADASTRO, g1


cliente = TestClient(app)


def _registro_e_arp(sessao, prefixo="CMD-F1I"):
    registro = g1(
        f"{prefixo}-G1",
        CADASTRO,
        "CTX-TRIB-01",
        titulo="Cadastro imobiliário fictício",
    )
    resultado = atribuir_arp_form1_integral(
        sessao,
        comando_id=f"{prefixo}-ARP",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        modo="proprio",
        versao_lida=0,
    )
    sessao.commit()
    assert resultado["permitido"]
    return registro


def test_arp_inicia_envelope_e_reaproveita_dados_do_registro(sessao):
    registro = _registro_e_arp(sessao, "CMD-F1I-INICIO")

    resultado = iniciar_rascunho_form1_integral(
        sessao,
        comando_id="CMD-F1I-INICIAR",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
    )
    sessao.commit()

    rascunho = sessao.get(RascunhoForm1Integral, registro["registro_id"])
    assert resultado["permitido"] and rascunho.versao_rascunho == 1
    assert rascunho.conteudo["revisao_fonte"] == "REV13-2026-09-20"
    assert rascunho.conteudo["versao_contrato"] == 3
    assert rascunho.conteudo["respostas"] == {
        "1.2": "Atividade",
        "1.3": "Cadastro imobiliário fictício",
    }
    assert verificar_cadeia(sessao, registro["codigo_lgpd"])[0]


def test_salvar_bloco_1_aceita_rascunho_parcial_e_preserva_reuso(sessao):
    registro = _registro_e_arp(sessao, "CMD-F1I-SALVAR")
    iniciar_rascunho_form1_integral(
        sessao,
        comando_id="CMD-F1I-SALVAR-INICIO",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
    )
    sessao.commit()

    resultado = salvar_bloco_1_form1_integral(
        sessao,
        comando_id="CMD-F1I-SALVAR-B1",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        versao_lida=1,
        respostas={"1.1": "A confirmar", "1.4": "Sim"},
    )
    sessao.commit()

    respostas = sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo["respostas"]
    assert resultado["permitido"] and resultado["versao_rascunho"] == 2
    assert respostas["1.1"] == "A confirmar" and respostas["1.4"] == "Sim"
    assert respostas["1.2"] == "Atividade"
    assert respostas["1.3"] == "Cadastro imobiliário fictício"


def test_bloco_1_inativa_referencia_que_deixou_de_ser_aplicavel(sessao):
    registro = _registro_e_arp(sessao, "CMD-F1I-COND")
    iniciar_rascunho_form1_integral(
        sessao, comando_id="CMD-F1I-COND-INICIO", conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
    )
    sessao.commit()
    salvar_bloco_1_form1_integral(
        sessao, comando_id="CMD-F1I-COND-SIM", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"1.1": "Sim", "1.1.1": "Referência institucional fictícia"},
    )
    sessao.commit()

    resultado = salvar_bloco_1_form1_integral(
        sessao, comando_id="CMD-F1I-COND-NAO", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=2,
        respostas={"1.1": "Não"},
    )
    sessao.commit()

    conteudo = sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo
    assert resultado["permitido"] and "1.1.1" not in conteudo["respostas"]
    assert conteudo["respostas_inativas"]["1.1.1"][-1]["valor"] == (
        "Referência institucional fictícia"
    )

    reativado = salvar_bloco_1_form1_integral(
        sessao, comando_id="CMD-F1I-COND-REATIVADO", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=3,
        respostas={"1.1": "Sim", "1.1.1": "Nova referência institucional fictícia"},
    )
    sessao.commit()

    conteudo = sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo
    assert reativado["permitido"]
    assert conteudo["respostas"]["1.1.1"] == "Nova referência institucional fictícia"
    assert conteudo["respostas_inativas"]["1.1.1"][-1]["valor"] == (
        "Referência institucional fictícia"
    )


def test_bloco_1_recusa_referencia_quando_resposta_controladora_nao_e_sim(sessao):
    registro = _registro_e_arp(sessao, "CMD-F1I-COND-FORJADA")
    iniciar_rascunho_form1_integral(
        sessao, comando_id="CMD-F1I-COND-FORJADA-INICIO", conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
    )
    sessao.commit()

    resultado = salvar_bloco_1_form1_integral(
        sessao, comando_id="CMD-F1I-COND-FORJADA-SALVAR", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"1.1": "Não", "1.1.1": "Referência indevida fictícia"},
    )
    sessao.commit()

    assert not resultado["permitido"] and "campo condicional inativo" in resultado["motivo"]
    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]).versao_rascunho == 1


def test_alternativa_forjada_e_campo_desconhecido_sao_negados(sessao):
    registro = _registro_e_arp(sessao, "CMD-F1I-FORJADO")
    iniciar_rascunho_form1_integral(
        sessao,
        comando_id="CMD-F1I-FORJADO-INICIO",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
    )
    sessao.commit()

    alternativa = salvar_bloco_1_form1_integral(
        sessao,
        comando_id="CMD-F1I-FORJADO-OPCAO",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        versao_lida=1,
        respostas={"1.4": "Talvez"},
    )
    campo = salvar_bloco_1_form1_integral(
        sessao,
        comando_id="CMD-F1I-FORJADO-CAMPO",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        versao_lida=1,
        respostas={"2.1": "Ouvidoria"},
    )
    sessao.commit()

    assert not alternativa["permitido"] and "catálogo REV13" in alternativa["motivo"]
    assert not campo["permitido"] and "não editável" in campo["motivo"]
    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]).versao_rascunho == 1


def test_somente_arp_atual_pode_iniciar_e_salvar(sessao):
    registro = _registro_e_arp(sessao, "CMD-F1I-ARP")

    negado = iniciar_rascunho_form1_integral(
        sessao,
        comando_id="CMD-F1I-ARP-NEGADO",
        conta_id="CONTA-G1",
        registro_id=registro["registro_id"],
    )
    sessao.commit()

    assert not negado["permitido"] and "somente o ARP atual" in negado["motivo"]
    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]) is None
    auditoria = sessao.scalars(
        select(EventoAuditoria).where(
            EventoAuditoria.conteudo["acao_tentada"].as_string()
            == "iniciar_rascunho_form1_integral"
        )
    ).one()
    assert auditoria.ator_id == "PESSOA-G"


def test_salvamento_e_idempotente_e_recusa_versao_desatualizada(sessao):
    registro = _registro_e_arp(sessao, "CMD-F1I-VERSAO")
    iniciar_rascunho_form1_integral(
        sessao,
        comando_id="CMD-F1I-VERSAO-INICIO",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
    )
    sessao.commit()
    parametros = dict(
        comando_id="CMD-F1I-VERSAO-SALVAR",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        versao_lida=1,
        respostas={"1.4": "Sim"},
    )

    primeiro = salvar_bloco_1_form1_integral(sessao, **parametros)
    sessao.commit()
    repetido = salvar_bloco_1_form1_integral(sessao, **parametros)
    desatualizado = salvar_bloco_1_form1_integral(
        sessao,
        comando_id="CMD-F1I-VERSAO-ANTIGA",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        versao_lida=1,
        respostas={"1.4": "A confirmar"},
    )
    sessao.commit()

    assert primeiro["permitido"] and repetido["reexecutado"] is True
    assert not desatualizado["permitido"] and "desatualizado" in desatualizado["motivo"]
    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]).versao_rascunho == 2


def test_dois_salvamentos_simultaneos_nao_se_sobrescrevem(sessao):
    registro = _registro_e_arp(sessao, "CMD-F1I-CONCORRENCIA")
    iniciar_rascunho_form1_integral(
        sessao,
        comando_id="CMD-F1I-CONCORRENCIA-INICIO",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
    )
    sessao.commit()
    barreira = threading.Barrier(2)
    resultados = {}

    def salvar(nome, valor):
        with Session(motor) as outra, outra.begin():
            barreira.wait()
            resultados[nome] = salvar_bloco_1_form1_integral(
                outra,
                comando_id=f"CMD-F1I-CONCORRENCIA-{nome}",
                conta_id="CONTA-A1",
                registro_id=registro["registro_id"],
                versao_lida=1,
                respostas={"1.4": valor},
            )

    a = threading.Thread(target=salvar, args=("A", "Sim"))
    b = threading.Thread(target=salvar, args=("B", "A confirmar"))
    a.start(); b.start(); a.join(); b.join()

    assert sum(resultado["permitido"] for resultado in resultados.values()) == 1
    assert sum("desatualizado" in resultado["motivo"] for resultado in resultados.values()) == 1
    sessao.expire_all()
    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]).versao_rascunho == 2


def test_falha_no_evento_desfaz_o_rascunho_integral(sessao, monkeypatch):
    registro = _registro_e_arp(sessao, "CMD-F1I-ROLLBACK")

    def falhar(*args, **kwargs):
        raise RuntimeError("falha fictícia controlada")

    monkeypatch.setattr("app.rascunho_form1_integral.registrar_evento", falhar)
    with pytest.raises(RuntimeError, match="falha fictícia"):
        iniciar_rascunho_form1_integral(
            sessao,
            comando_id="CMD-F1I-ROLLBACK-INICIO",
            conta_id="CONTA-A1",
            registro_id=registro["registro_id"],
        )
        sessao.commit()
    sessao.rollback()

    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]) is None


def test_interface_inicia_e_salva_bloco_1(sessao):
    registro = _registro_e_arp(sessao, "CMD-F1I-HTTP")

    inicio = cliente.post(
        f"/registros/{registro['registro_id']}/form1-integral/iniciar",
        data={"conta_id": "CONTA-A1", "comando_id": "CMD-F1I-HTTP-INICIO"},
    )
    salvamento = cliente.post(
        f"/registros/{registro['registro_id']}/form1-integral/bloco-1/salvar",
        data={
            "conta_id": "CONTA-A1",
            "comando_id": "CMD-F1I-HTTP-SALVAR",
            "versao_lida": "1",
            "referencia_existente": "Não",
            "referencia_institucional": "",
            "fluxo_recorrente": "Sim",
        },
    )

    assert inicio.status_code == 200 and "Bloco 1 de 14" in inicio.text
    assert "Cadastro imobiliário fictício" in inicio.text
    assert salvamento.status_code == 200
    assert "Bloco 1 do FORM 1 integral salvo com segurança" in salvamento.text
    assert "Rascunho 2" in salvamento.text
    assert "Instrumento sintético · contrato 2" in salvamento.text


def test_migracao_12_recria_tabela_do_rascunho_integral():
    with motor.begin() as conexao:
        RascunhoForm1Integral.__table__.drop(bind=conexao)
    with Session(motor) as sessao, sessao.begin():
        aplicar_migracao(sessao)

    assert inspect(motor).has_table("rascunho_form1_integral")
