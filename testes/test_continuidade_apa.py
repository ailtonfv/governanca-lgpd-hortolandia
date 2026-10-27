"""Continuidade institucional do APA com massa exclusivamente fictícia."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from app.atribuicao_form1_integral import atribuir_arp_form1_integral
from app.banco import motor
from app.continuidade_apa import (
    apa_em_exercicio,
    encerrar_substituicao_temporaria_apa,
    iniciar_substituicao_temporaria_apa,
    substituir_apa_definitivamente,
)
from app.eventos import verificar_cadeia
from app.modelos import (
    AtribuicaoForm1Integral,
    Designacao,
    Evento,
    EventoAuditoria,
    RascunhoForm1Integral,
    Registro,
    SubstituicaoApa,
)
from app.rascunho_form1_integral import iniciar_rascunho_form1_integral
from app.workflow import criar_registro
from migracoes.continuidade_apa import aplicar as aplicar_migracao_continuidade
from testes.apoio import CADASTRO, g1, sem_reexecucao


AGORA = datetime(2026, 10, 26, 15, 0, tzinfo=timezone.utc)


def _iniciar(sessao, comando="CMD-APA-TEMP", **ajustes):
    parametros = {
        "comando_id": comando,
        "conta_id": "CONTA-E1",
        "unidade_id": "UNID-NORTE",
        "suplente_id": "PESSOA-F",
        "inicio_em": AGORA - timedelta(hours=1),
        "fim_previsto_em": AGORA + timedelta(days=1),
        "motivo": "afastamento fictício para teste",
        "momento": AGORA,
    }
    parametros.update(ajustes)
    return iniciar_substituicao_temporaria_apa(sessao, **parametros)


def test_titular_e_suplente_formalmente_designados(sessao):
    titular = apa_em_exercicio(sessao, "UNID-NORTE", AGORA)
    suplente = sessao.scalars(select(Designacao).where(
        Designacao.pessoa_id == "PESSOA-F",
        Designacao.unidade_id == "UNID-NORTE",
        Designacao.papel == "responsavel_registro",
    )).one()

    assert titular == {
        "pessoa_id": "PESSOA-A", "titular_id": "PESSOA-A",
        "modalidade": "titular", "em_nome_de": None,
        "substituicao_id": None, "fim_previsto_em": None,
    }
    assert suplente.tipo_apa == "suplente"
    assert suplente.autorizado_por_id == "PESSOA-E"
    assert suplente.fundamento_administrativo


def test_substituicao_temporaria_transfere_exercicio_e_preserva_autoria(sessao):
    resultado = _iniciar(sessao)
    sessao.commit()
    exercicio = apa_em_exercicio(sessao, "UNID-NORTE", AGORA)

    criado = criar_registro(
        sessao, comando_id="CMD-APA-TEMP-G1", conta_id="CONTA-F1",
        unidade_id="UNID-NORTE", contexto_id="CTX-TRIB-01",
        titulo_objeto="Registro temporário fictício", objeto_principal_id=CADASTRO,
        momento=AGORA,
    )
    sessao.commit()

    registro = sessao.get(Registro, criado["registro_id"])
    evento = sessao.scalars(select(Evento).where(
        Evento.registro_id == registro.id, Evento.codigo_evento == "G1"
    )).one()
    assert resultado["permitido"]
    assert exercicio["pessoa_id"] == "PESSOA-F"
    assert registro.criado_por == "PESSOA-F"
    assert evento.ator_id == "PESSOA-F"
    assert evento.em_nome_de == "PESSOA-A"
    assert evento.conteudo["apa_titular_id"] == "PESSOA-A"
    assert verificar_cadeia(sessao, registro.codigo_lgpd)[0]
    assert verificar_cadeia(sessao, "APA:UNID-NORTE")[0]


def test_fora_do_periodo_o_titular_permanece_em_exercicio(sessao):
    _iniciar(
        sessao, comando="CMD-APA-FUTURA",
        inicio_em=AGORA + timedelta(days=1),
        fim_previsto_em=AGORA + timedelta(days=2),
    )
    sessao.commit()

    assert apa_em_exercicio(sessao, "UNID-NORTE", AGORA)["pessoa_id"] == "PESSOA-A"
    negado = criar_registro(
        sessao, comando_id="CMD-APA-FUTURA-G1", conta_id="CONTA-F1",
        unidade_id="UNID-NORTE", contexto_id="CTX-TRIB-01",
        titulo_objeto="Tentativa fictícia", objeto_principal_id=CADASTRO,
        momento=AGORA,
    )
    sessao.commit()
    assert not negado["permitido"]
    assert "em exercício" in negado["motivo"]


def test_retorno_formal_do_titular(sessao):
    _iniciar(sessao)
    sessao.commit()

    retorno = encerrar_substituicao_temporaria_apa(
        sessao, comando_id="CMD-APA-RETORNO", conta_id="CONTA-E1",
        unidade_id="UNID-NORTE", motivo="retorno fictício do titular", momento=AGORA,
    )
    sessao.commit()

    substituicao = sessao.scalars(select(SubstituicaoApa)).one()
    assert retorno["permitido"]
    assert substituicao.encerrada_em == AGORA
    assert substituicao.encerrada_por_id == "PESSOA-E"
    assert apa_em_exercicio(sessao, "UNID-NORTE", AGORA)["pessoa_id"] == "PESSOA-A"
    assert verificar_cadeia(sessao, "APA:UNID-NORTE")[0]


def test_sucessao_definitiva_preserva_registro_arp_e_rascunho(sessao):
    registro = g1("CMD-APA-PRESERVA-G1", CADASTRO, "CTX-TRIB-01", momento=AGORA)
    atribuicao = atribuir_arp_form1_integral(
        sessao, comando_id="CMD-APA-PRESERVA-ARP", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], modo="outro", arp_pessoa_id="PESSOA-G",
        versao_lida=0, momento=AGORA,
    )
    sessao.commit()
    rascunho = iniciar_rascunho_form1_integral(
        sessao, comando_id="CMD-APA-PRESERVA-RASC", conta_id="CONTA-G1",
        registro_id=registro["registro_id"], momento=AGORA,
    )
    sessao.commit()
    conteudo_anterior = dict(sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo)

    sucessao = substituir_apa_definitivamente(
        sessao, comando_id="CMD-APA-SUCESSAO", conta_id="CONTA-E1",
        unidade_id="UNID-NORTE", sucessor_id="PESSOA-F",
        motivo="sucessão institucional fictícia", momento=AGORA + timedelta(minutes=1),
    )
    sessao.commit()

    registro_db = sessao.get(Registro, registro["registro_id"])
    atribuicao_db = sessao.get(AtribuicaoForm1Integral, registro["registro_id"])
    rascunho_db = sessao.get(RascunhoForm1Integral, registro["registro_id"])
    assert atribuicao["permitido"] and rascunho["permitido"] and sucessao["permitido"]
    assert registro_db.criado_por == "PESSOA-A"
    assert atribuicao_db.arp_atual_id == "PESSOA-G"
    assert rascunho_db.conteudo == conteudo_anterior
    assert apa_em_exercicio(sessao, "UNID-NORTE", AGORA + timedelta(minutes=2))["pessoa_id"] == "PESSOA-F"
    assert verificar_cadeia(sessao, registro["codigo_lgpd"])[0]
    assert verificar_cadeia(sessao, "APA:UNID-NORTE")[0]


def test_ator_sem_autorizacao_e_secretaria_errada_sao_recusados(sessao):
    sem_autorizacao = _iniciar(sessao, comando="CMD-APA-SEM-AUT", conta_id="CONTA-A1")
    unidade_errada = _iniciar(
        sessao, comando="CMD-APA-UNIDADE-ERRADA", unidade_id="UNID-SUL",
        suplente_id="PESSOA-F",
    )
    sessao.commit()

    assert not sem_autorizacao["permitido"]
    assert "autorização institucional" in sem_autorizacao["motivo"]
    assert not unidade_errada["permitido"]
    assert "suplente" in unidade_errada["motivo"]
    assert sessao.scalar(select(SubstituicaoApa).where(
        SubstituicaoApa.unidade_id.in_(["UNID-NORTE", "UNID-SUL"])
    )) is None
    auditorias = sessao.scalars(select(EventoAuditoria).where(
        EventoAuditoria.conteudo["acao_tentada"].as_string()
        == "iniciar_substituicao_temporaria_apa"
    )).all()
    assert len(auditorias) == 2


def test_ninguem_concede_a_si_proprio_poder_de_apa(sessao):
    resultado = _iniciar(
        sessao, comando="CMD-APA-AUTO", suplente_id="PESSOA-E"
    )
    sessao.commit()

    assert not resultado["permitido"]
    assert "própria designação" in resultado["motivo"]


def test_substituicao_e_idempotente_e_nao_admite_duas_abertas(sessao):
    primeiro = _iniciar(sessao, comando="CMD-APA-IDEM")
    sessao.commit()
    repetido = _iniciar(sessao, comando="CMD-APA-IDEM")
    segundo = _iniciar(sessao, comando="CMD-APA-SEGUNDA")
    sessao.commit()

    assert sem_reexecucao(repetido) == sem_reexecucao(primeiro)
    assert repetido["reexecutado"] is True
    assert not segundo["permitido"]
    assert len(sessao.scalars(select(SubstituicaoApa)).all()) == 1


def test_concorrencia_resulta_em_uma_unica_substituicao_aberta():
    def tentar(numero):
        with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
            return _iniciar(sessao, comando=f"CMD-APA-CONC-{numero}")

    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados = list(executor.map(tentar, (1, 2)))

    with Session(motor) as sessao:
        abertas = sessao.scalars(select(SubstituicaoApa).where(
            SubstituicaoApa.encerrada_em.is_(None)
        )).all()
    assert sum(resultado["permitido"] for resultado in resultados) == 1
    assert len(abertas) == 1


def test_falha_de_evento_desfaz_substituicao(sessao, monkeypatch):
    def falhar(*args, **kwargs):
        raise RuntimeError("falha fictícia controlada")

    monkeypatch.setattr("app.continuidade_apa.registrar_evento", falhar)
    with pytest.raises(RuntimeError, match="falha fictícia"):
        _iniciar(sessao, comando="CMD-APA-ROLLBACK")
        sessao.commit()
    sessao.rollback()

    assert sessao.scalar(select(SubstituicaoApa)) is None


def test_migracao_13_recria_estrutura_sem_apagar_designacoes():
    with motor.begin() as conexao:
        conexao.execute(text("DROP TABLE substituicao_apa"))
        conexao.execute(text("ALTER TABLE designacao DROP COLUMN tipo_apa CASCADE"))
        conexao.execute(text("ALTER TABLE designacao DROP COLUMN vigente_de CASCADE"))
        conexao.execute(text("ALTER TABLE designacao DROP COLUMN vigente_ate CASCADE"))
        conexao.execute(text("ALTER TABLE designacao DROP COLUMN fundamento_administrativo CASCADE"))
        conexao.execute(text("ALTER TABLE designacao DROP COLUMN autorizado_por_id CASCADE"))
    with Session(motor) as sessao, sessao.begin():
        aplicar_migracao_continuidade(sessao)

    inspetor = inspect(motor)
    colunas = {coluna["name"] for coluna in inspetor.get_columns("designacao")}
    assert inspetor.has_table("substituicao_apa")
    assert {"tipo_apa", "vigente_de", "vigente_ate", "fundamento_administrativo", "autorizado_por_id"} <= colunas
    with Session(motor) as sessao:
        assert len(sessao.scalars(select(Designacao)).all()) > 0
