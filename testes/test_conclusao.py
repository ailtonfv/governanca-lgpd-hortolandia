"""G5: conclusão humana do Registro validado e sem medidas."""

import threading
from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.banco import motor
from app.eventos import verificar_cadeia
from app.modelos import (Ciclo, Comando, Evento, Instrumento, Pendencia,
                         Registro)
from app.workflow import concluir_registro_sem_medidas
from testes.apoio import sem_reexecucao
from testes.test_submissao import (criar_acao_sintetica, criar_form1, i3, i5,
                                   i13, p4, preparar, preparar_resposta)


def g5(registro_id, cmd="CMD-C-G5", conta="CONTA-B1", **extra):
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return concluir_registro_sem_medidas(
            sessao, comando_id=cmd, conta_id=conta, registro_id=registro_id,
            **extra,
        )


def preparar_validado_sem_medidas():
    instrumento_id, registro_id, codigo = criar_form1(cmd="CMD-C-G1")
    preparar(instrumento_id, prefixo="CMD-C")
    submissao = i3(instrumento_id, cmd="CMD-C-I3")
    analise = i13(instrumento_id, submissao["versao_id"], cmd="CMD-C-I13")
    validacao = i5(
        instrumento_id, analise["analise_id"], submissao["versao_id"],
        cmd="CMD-C-I5",
    )
    assert validacao["permitido"] and validacao["estado_registro"] == "em_andamento"
    return instrumento_id, registro_id, codigo, submissao, analise, validacao


def test_g5_conclui_registro_e_ciclo_sem_apagar_a_versao_validada():
    instrumento_id, registro_id, codigo, submissao, _, _ = preparar_validado_sem_medidas()
    momento = datetime(2026, 10, 17, 18, 0, tzinfo=timezone.utc)

    resultado = g5(registro_id, momento=momento)

    assert resultado["permitido"] and resultado["estado_registro"] == "concluido"
    assert resultado["situacao_ciclo"] == "concluido"
    with Session(motor) as sessao:
        registro = sessao.get(Registro, registro_id)
        ciclo = sessao.get(Ciclo, resultado["ciclo_id"])
        instrumento = sessao.get(Instrumento, instrumento_id)
        evento = sessao.scalars(
            select(Evento).where(Evento.codigo_evento == "G5")
        ).one()
        assert registro.estado_atual == "concluido"
        assert ciclo.situacao == "concluido"
        assert instrumento.estado_instrumento == "validado"
        assert instrumento.versao_vigente_id == submissao["versao_id"]
        assert evento.conteudo["concluido_em"] == momento.isoformat()
        assert verificar_cadeia(sessao, codigo)[0]


def test_g5_exige_instrumento_validado_e_competencia_formal():
    instrumento_id, registro_id, _ = criar_form1(cmd="CMD-C-PORTAO-G1")
    sem_validacao = g5(registro_id, cmd="CMD-C-G5-SEM-VALIDACAO")
    assert not sem_validacao["permitido"] and "Instrumentos" in sem_validacao["motivo"]
    assert sem_validacao["instrumentos_invalidos"] == [{
        "instrumento_id": instrumento_id, "tipo": "FORM1", "estado": "nao_iniciado",
    }]

    preparar(instrumento_id, prefixo="CMD-C-PORTAO")
    submissao = i3(instrumento_id, cmd="CMD-C-PORTAO-I3")
    analise = i13(instrumento_id, submissao["versao_id"], cmd="CMD-C-PORTAO-I13")
    validacao = i5(
        instrumento_id, analise["analise_id"], submissao["versao_id"],
        cmd="CMD-C-PORTAO-I5",
    )
    assert validacao["permitido"]
    sem_competencia = g5(
        registro_id, cmd="CMD-C-G5-SEM-COMPETENCIA", conta="CONTA-A1",
    )
    assert not sem_competencia["permitido"] and "competência formal" in sem_competencia["motivo"]


def test_g5_bloqueia_pendencia_ainda_aberta():
    instrumento_id, registro_id, _, _, _, _ = preparar_validado_sem_medidas()
    with Session(motor) as sessao, sessao.begin():
        registro = sessao.get(Registro, registro_id)
        ciclo = sessao.scalars(select(Ciclo).where(Ciclo.registro_id == registro_id)).one()
        origem = sessao.scalars(
            select(Evento).where(Evento.registro_id == registro_id)
            .order_by(Evento.id.desc()).limit(1)
        ).one()
        sessao.add(Pendencia(
            id="PEND-G5-ABERTA", tipo_pendencia="providencia",
            registro_id=registro_id, ciclo_origem_id=ciclo.id,
            ciclo_contexto_atual_id=ciclo.id, instrumento_id=instrumento_id,
            evento_origem_id=origem.id, unidade_origem_id=registro.unidade_principal_atual_id,
            unidade_destino_id=registro.unidade_principal_atual_id,
            estado="aberta", bloqueante=False, gate_bloqueado=None,
            motivo="Providência fictícia ainda aberta",
            criada_em=datetime(2026, 10, 17, 17, 0, tzinfo=timezone.utc),
            atualizada_em=datetime(2026, 10, 17, 17, 0, tzinfo=timezone.utc),
        ))

    resultado = g5(registro_id)
    assert not resultado["permitido"] and resultado["pendencias_abertas"] == ["PEND-G5-ABERTA"]


def test_g5_recusa_ciclo_que_possui_medida_mesmo_ja_encerrada():
    instrumento_id, registro_id, _, _, _, _ = preparar_validado_sem_medidas()
    criar_acao_sintetica(
        instrumento_id, registro_id, estado="concluida", acao_id="ACAO-G5-CONCLUIDA",
    )

    resultado = g5(registro_id)
    assert not resultado["permitido"]
    assert resultado["acoes_obrigatorias"] == ["ACAO-G5-CONCLUIDA"]
    assert "sem medidas" in resultado["motivo"]


def test_g5_repetido_e_idempotente():
    _, registro_id, _, _, _, _ = preparar_validado_sem_medidas()
    original = g5(registro_id)
    repetido = g5(registro_id)
    assert original["permitido"] and repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(original)
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento == "G5")) == 1


def test_dois_g5_simultaneos_concluem_uma_unica_vez():
    _, registro_id, _, _, _, _ = preparar_validado_sem_medidas()
    barreira = threading.Barrier(2)
    resultados = []

    def concluir(numero):
        barreira.wait()
        resultados.append(g5(registro_id, cmd=f"CMD-C-G5-CONC-{numero}"))

    threads = [threading.Thread(target=concluir, args=(numero,)) for numero in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(resultado["permitido"] for resultado in resultados) == [False, True]
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento == "G5")) == 1


def test_g5_e_desfeito_no_rollback():
    _, registro_id, _, _, _, _ = preparar_validado_sem_medidas()
    with pytest.raises(RuntimeError):
        with Session(motor) as sessao, sessao.begin():
            resultado = concluir_registro_sem_medidas(
                sessao, comando_id="CMD-C-G5-ROLLBACK", conta_id="CONTA-B1",
                registro_id=registro_id,
            )
            assert resultado["permitido"]
            raise RuntimeError("falha simulada antes do commit")

    with Session(motor) as sessao:
        registro = sessao.get(Registro, registro_id)
        ciclo = sessao.scalars(select(Ciclo).where(Ciclo.registro_id == registro_id)).one()
        assert registro.estado_atual == "em_andamento" and ciclo.situacao == "ativo"
        assert sessao.get(Comando, "CMD-C-G5-ROLLBACK") is None
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento == "G5")) == 0


def test_g5_conclui_depois_da_correcao_aceita_e_da_versao_2_validada():
    dados = preparar_resposta()
    instrumento_id, registro_id, _, _, _, devolucao, _, _ = dados
    assert p4(instrumento_id, devolucao["pendencia_id"])["permitido"]
    submissao_2 = i3(instrumento_id, versao=4, cmd="CMD-C-A2-I3-2")
    analise_2 = i13(
        instrumento_id, submissao_2["versao_id"], cmd="CMD-C-A2-I13-2",
    )
    validacao_2 = i5(
        instrumento_id, analise_2["analise_id"], submissao_2["versao_id"],
        cmd="CMD-C-A2-I5-2",
    )
    assert validacao_2["permitido"] and validacao_2["estado_registro"] == "em_andamento"

    resultado = g5(registro_id, cmd="CMD-C-A2-G5")
    assert resultado["permitido"] and resultado["estado_registro"] == "concluido"
