"""Etapa visual 1 e primeiro recorte da Etapa 2 do FORM 1 integral."""

import threading

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.atribuicao_form1_integral import atribuir_arp_form1_integral
from app.banco import motor
from app.eventos import verificar_cadeia
from app.main import app
from app.modelos import RascunhoForm1Integral
from app.rascunho_form1_integral import (
    adicionar_participante_form1_integral,
    iniciar_rascunho_form1_integral,
    remover_participante_form1_integral,
    salvar_bloco_2_form1_integral,
    salvar_bloco_4_form1_integral,
    salvar_cabecalho_bloco_3_form1_integral,
)
from testes.apoio import CADASTRO, g1


cliente = TestClient(app)


def _rascunho_pronto(sessao, prefixo):
    registro = g1(
        f"{prefixo}-G1", CADASTRO, "CTX-TRIB-01",
        titulo="Atividade tributária fictícia",
    )
    atribuir_arp_form1_integral(
        sessao, comando_id=f"{prefixo}-ARP", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], modo="proprio", versao_lida=0,
    )
    sessao.commit()
    iniciar_rascunho_form1_integral(
        sessao, comando_id=f"{prefixo}-INICIAR", conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
    )
    sessao.commit()
    return registro


def test_bloco_2_salva_fluxo_e_ramificacao_ouvidoria(sessao):
    registro = _rascunho_pronto(sessao, "CMD-F12-OUV")
    respostas = {
        "2.1": "Ouvidoria",
        "2.2": "UNID-NORTE",
        "2.3": "Unidade fictícia de atendimento",
        "2.4": "Sim",
        "2.5": ["Recebe demanda", "Analisa informações"],
        "2.6": "A unidade recebe e analisa a demanda fictícia.",
        "2.8": "11 a 50",
        "2.8.1": "Por mês",
        "OUV.1": ["Solicitação"],
        "OUV.2": ["Mais de uma possibilidade"],
        "OUV.3": "Em alguns casos",
        "OUV.4": "Depende da manifestação",
    }

    resultado = salvar_bloco_2_form1_integral(
        sessao, comando_id="CMD-F12-OUV-SALVAR", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas=respostas,
    )
    sessao.commit()

    rascunho = sessao.get(RascunhoForm1Integral, registro["registro_id"])
    assert resultado["permitido"] and rascunho.versao_rascunho == 2
    assert rascunho.conteudo["respostas"]["OUV.4"] == "Depende da manifestação"
    assert rascunho.conteudo["respostas"]["1.3"] == "Atividade tributária fictícia"
    assert verificar_cadeia(sessao, registro["codigo_lgpd"])[0]


def test_bloco_2_aceita_esic_e_recusa_catalogo_forjado(sessao):
    registro = _rascunho_pronto(sessao, "CMD-F12-ESIC")
    valido = salvar_bloco_2_form1_integral(
        sessao, comando_id="CMD-F12-ESIC-SALVAR", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"2.1": "e-SIC", "ESIC.1": "Sim", "ESIC.2": "Em alguns casos"},
    )
    sessao.commit()
    invalido = salvar_bloco_2_form1_integral(
        sessao, comando_id="CMD-F12-ESIC-FORJADO", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=2,
        respostas={"2.2": "UNID-INEXISTENTE"},
    )
    sessao.commit()

    assert valido["permitido"]
    assert not invalido["permitido"] and "Secretaria fora" in invalido["motivo"]
    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]).versao_rascunho == 2


def test_bloco_2_e_idempotente_e_preserva_outros_blocos(sessao):
    registro = _rascunho_pronto(sessao, "CMD-F12-IDEM")
    parametros = dict(
        comando_id="CMD-F12-IDEM-SALVAR", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"2.1": "Telefone", "2.4": "A confirmar"},
    )
    primeiro = salvar_bloco_2_form1_integral(sessao, **parametros)
    sessao.commit()
    repetido = salvar_bloco_2_form1_integral(sessao, **parametros)
    sessao.commit()

    assert primeiro["permitido"] and repetido["reexecutado"] is True
    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]).versao_rascunho == 2


def test_dois_salvamentos_simultaneos_do_bloco_2_nao_se_sobrescrevem(sessao):
    registro = _rascunho_pronto(sessao, "CMD-F12-CONC")
    barreira = threading.Barrier(2)
    resultados = {}

    def salvar(nome, porta):
        with Session(motor) as outra, outra.begin():
            barreira.wait()
            resultados[nome] = salvar_bloco_2_form1_integral(
                outra, comando_id=f"CMD-F12-CONC-{nome}", conta_id="CONTA-A1",
                registro_id=registro["registro_id"], versao_lida=1,
                respostas={"2.1": porta},
            )

    a = threading.Thread(target=salvar, args=("A", "Telefone"))
    b = threading.Thread(target=salvar, args=("B", "E-mail institucional"))
    a.start(); b.start(); a.join(); b.join()

    assert sum(item["permitido"] for item in resultados.values()) == 1
    assert sum("desatualizado" in item["motivo"] for item in resultados.values()) == 1


def test_falha_no_evento_desfaz_salvamento_do_bloco_2(sessao, monkeypatch):
    registro = _rascunho_pronto(sessao, "CMD-F12-ROLLBACK")

    def falhar(*args, **kwargs):
        raise RuntimeError("falha fictícia controlada")

    monkeypatch.setattr("app.rascunho_form1_integral.registrar_evento", falhar)
    with pytest.raises(RuntimeError, match="falha fictícia"):
        salvar_bloco_2_form1_integral(
            sessao, comando_id="CMD-F12-ROLLBACK-SALVAR", conta_id="CONTA-A1",
            registro_id=registro["registro_id"], versao_lida=1,
            respostas={"2.1": "Telefone"},
        )
        sessao.commit()
    sessao.rollback()

    rascunho = sessao.get(RascunhoForm1Integral, registro["registro_id"])
    assert rascunho.versao_rascunho == 1 and "2.1" not in rascunho.conteudo["respostas"]


def test_bloco_3_mantem_participantes_em_ocorrencias_independentes(sessao):
    registro = _rascunho_pronto(sessao, "CMD-F13-PART")
    cabecalho = salvar_cabecalho_bloco_3_form1_integral(
        sessao, comando_id="CMD-F13-PART-CAB", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1, resposta_3_1="Sim",
    )
    sessao.commit()
    primeiro = adicionar_participante_form1_integral(
        sessao, comando_id="CMD-F13-PART-A", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=2,
        respostas={
            "3.2": ["Outra Secretaria"],
            "3.3": "Secretaria participante fictícia",
            "3.4": ["Recebe encaminhamento"],
            "3.5": "Não",
        },
    )
    sessao.commit()
    segundo = adicionar_participante_form1_integral(
        sessao, comando_id="CMD-F13-PART-B", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=3,
        respostas={
            "3.2": ["Empresa contratada"],
            "3.3": "Empresa fictícia contratada",
            "3.4.1": ["Acessa sistema da Prefeitura"],
            "3.5": "Sim",
            "3.5.1": ["Contrato"],
        },
    )
    sessao.commit()

    participantes = sessao.get(
        RascunhoForm1Integral, registro["registro_id"]
    ).conteudo["participantes"]
    assert cabecalho["permitido"] and primeiro["permitido"] and segundo["permitido"]
    assert primeiro["participante_id"] != segundo["participante_id"]
    assert [item["respostas"]["3.3"] for item in participantes] == [
        "Secretaria participante fictícia", "Empresa fictícia contratada"
    ]


def test_remocao_de_participante_preserva_as_demais_ocorrencias(sessao):
    registro = _rascunho_pronto(sessao, "CMD-F13-REM")
    primeiro = adicionar_participante_form1_integral(
        sessao, comando_id="CMD-F13-REM-A", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"3.3": "Unidade fictícia A"},
    )
    sessao.commit()
    segundo = adicionar_participante_form1_integral(
        sessao, comando_id="CMD-F13-REM-B", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=2,
        respostas={"3.3": "Unidade fictícia B"},
    )
    sessao.commit()
    removido = remover_participante_form1_integral(
        sessao, comando_id="CMD-F13-REMOVER", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=3,
        participante_id=primeiro["participante_id"],
    )
    sessao.commit()

    participantes = sessao.get(
        RascunhoForm1Integral, registro["registro_id"]
    ).conteudo["participantes"]
    assert removido["permitido"]
    assert [item["id"] for item in participantes] == [segundo["participante_id"]]


def test_interface_exibe_e_salva_etapa_visual_1(sessao):
    registro = _rascunho_pronto(sessao, "CMD-F12-HTTP")
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}?conta_id=CONTA-A1"
    )
    salvamento = cliente.post(
        f"/registros/{registro['registro_id']}/form1-integral/bloco-2/salvar",
        data={
            "conta_id": "CONTA-A1", "comando_id": "CMD-F12-HTTP-SALVAR",
            "versao_lida": "1", "campo__2.1": "e-SIC",
            "campo__ESIC.1": "Sim", "campo__ESIC.2": "Sim",
        },
    )

    assert pagina.status_code == 200
    assert "Bloco 2 de 14" in pagina.text and "Bloco 3 de 14" in pagina.text
    assert "Cada participante é uma ocorrência independente" in pagina.text
    assert salvamento.status_code == 200
    assert "Bloco 2 do FORM 1 integral salvo com segurança" in salvamento.text
    assert "Instrumento sintético · contrato 2" in salvamento.text


def test_primeiro_incremento_da_etapa_2_salva_categorias_sem_pessoas(sessao):
    registro = _rascunho_pronto(sessao, "CMD-F13-B4")
    resultado = salvar_bloco_4_form1_integral(
        sessao, comando_id="CMD-F13-B4-SALVAR", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={
            "4.1": ["Munícipe", "Idoso"],
            "4.2": "Sim",
            "4.2.1": ["Responsável legal"],
            "4.2.4": "Sim",
            "4.2.4.1": ["Documento de responsabilidade legal"],
            "4.2.5": "Sim",
            "4.2.5.1": ["Nome", "Telefone"],
        },
    )
    sessao.commit()

    respostas = sessao.get(
        RascunhoForm1Integral, registro["registro_id"]
    ).conteudo["respostas"]
    assert resultado["permitido"]
    assert respostas["4.1"] == ["Munícipe", "Idoso"]
    assert respostas["4.2.5.1"] == ["Nome", "Telefone"]


def test_bloco_4_recusa_categoria_forjada(sessao):
    registro = _rascunho_pronto(sessao, "CMD-F13-B4-FORJADO")
    resultado = salvar_bloco_4_form1_integral(
        sessao, comando_id="CMD-F13-B4-FORJADO-SALVAR", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"4.1": ["Pessoa individual identificada"]},
    )
    sessao.commit()

    assert not resultado["permitido"] and "catálogo REV13" in resultado["motivo"]
    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]).versao_rascunho == 1
