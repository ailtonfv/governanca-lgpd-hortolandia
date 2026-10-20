"""P1 a P4: participação mínima entre unidades no M1a."""

import threading
from copy import deepcopy
from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.alertas_operacionais import listar_alertas_operacionais
from app.banco import motor
from app.eventos import verificar_cadeia
from app.modelos import (Comando, Designacao, Evento, Instrumento, Pendencia,
                         Registro)
from app.pendencias import (aceitar_pendencia_intersecretarial, assumir_pendencia,
                            criar_pendencia_intersecretarial,
                            responder_pendencia_intersecretarial)
from testes.apoio import CADASTRO, g1, sem_reexecucao
from testes.test_conclusao import g5, preparar_validado_sem_medidas


RESPOSTA = {
    "etapa_executada": "Conferência técnica fictícia",
    "entrada_recebida": "Solicitação sem dados pessoais reais",
    "operacoes_realizadas": ["Conferir o requisito", "Registrar o resultado"],
    "saida_produzida": "Manifestação técnica fictícia concluída",
    "interfaces_seguinte": ["Retorno à Unidade Norte"],
    "evidencias": ["EVIDENCIA-FICTICIA-001"],
}


def criar_registro(cmd="CMD-PI-G1"):
    resultado = g1(cmd, CADASTRO, "CTX-TRIB-01")
    assert resultado["permitido"]
    return resultado


def p1(registro_id, cmd="CMD-PI-P1", conta="CONTA-A1", destino="UNID-SUL", **extra):
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return criar_pendencia_intersecretarial(
            sessao, comando_id=cmd, conta_id=conta, registro_id=registro_id,
            unidade_destino_id=destino,
            solicitacao="Documentar a etapa fictícia executada pela Unidade Sul",
            itens_atribuidos=["Entrada recebida", "Operação", "Saída e interface"],
            **extra,
        )


def p2(pendencia_id, cmd="CMD-PI-P2", conta="CONTA-C1", **extra):
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return assumir_pendencia(
            sessao, comando_id=cmd, conta_id=conta, pendencia_id=pendencia_id,
            **extra,
        )


def p3(pendencia_id, resposta=None, cmd="CMD-PI-P3", conta="CONTA-C1", **extra):
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return responder_pendencia_intersecretarial(
            sessao, comando_id=cmd, conta_id=conta, pendencia_id=pendencia_id,
            resposta=deepcopy(RESPOSTA if resposta is None else resposta), **extra,
        )


def p4(pendencia_id, cmd="CMD-PI-P4", conta="CONTA-A1", **extra):
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return aceitar_pendencia_intersecretarial(
            sessao, comando_id=cmd, conta_id=conta, pendencia_id=pendencia_id,
            **extra,
        )


def preparar_pendencia(prefixo="CMD-PI"):
    registro = criar_registro(cmd=f"{prefixo}-G1")
    criada = p1(registro["registro_id"], cmd=f"{prefixo}-P1")
    assert criada["permitido"]
    return registro, criada


def preparar_resposta(prefixo="CMD-PI"):
    registro, criada = preparar_pendencia(prefixo)
    assumida = p2(criada["pendencia_id"], cmd=f"{prefixo}-P2")
    assert assumida["permitido"]
    respondida = p3(criada["pendencia_id"], cmd=f"{prefixo}-P3")
    assert respondida["permitido"]
    return registro, criada, assumida, respondida


def codigos_alerta(conta):
    with Session(motor) as sessao:
        return {item["codigo"] for item in listar_alertas_operacionais(sessao, conta)}


def test_p1_cria_participacao_na_fila_sem_transferir_o_registro():
    registro = criar_registro()
    momento = datetime(2026, 10, 19, 13, 0, tzinfo=timezone.utc)

    resultado = p1(registro["registro_id"], momento=momento)

    assert resultado["permitido"] and resultado["estado_pendencia"] == "aberta"
    assert resultado["unidade_origem_id"] == "UNID-NORTE"
    assert resultado["unidade_destino_id"] == "UNID-SUL"
    assert resultado["gate_bloqueado"] == "conclusao"
    with Session(motor) as sessao:
        pendencia = sessao.get(Pendencia, resultado["pendencia_id"])
        registro_db = sessao.get(Registro, registro["registro_id"])
        evento = sessao.scalars(select(Evento).where(
            Evento.cadeia_id == pendencia.id, Evento.codigo_evento == "P1"
        )).one()
        assert pendencia.tipo_pendencia == "participacao"
        assert pendencia.instrumento_id is None
        assert pendencia.bloqueante and pendencia.gate_bloqueado == "conclusao"
        assert pendencia.criada_em == momento
        assert pendencia.evento_origem_id == evento.id
        assert registro_db.unidade_principal_atual_id == "UNID-NORTE"
        assert verificar_cadeia(sessao, pendencia.id)[0]


def test_p1_exige_destino_diferente_ativo_e_contexto_minimo():
    registro = criar_registro()
    mesma = p1(registro["registro_id"], cmd="CMD-PI-P1-MESMA", destino="UNID-NORTE")
    assert not mesma["permitido"] and "diferente" in mesma["motivo"]
    inexistente = p1(
        registro["registro_id"], cmd="CMD-PI-P1-INEXISTENTE", destino="UNID-X",
    )
    assert not inexistente["permitido"] and "inexistente" in inexistente["motivo"]

    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        sem_itens = criar_pendencia_intersecretarial(
            sessao, comando_id="CMD-PI-P1-SEM-ITENS", conta_id="CONTA-A1",
            registro_id=registro["registro_id"], unidade_destino_id="UNID-SUL",
            solicitacao="Solicitação fictícia", itens_atribuidos=[],
        )
    assert not sem_itens["permitido"] and "itens atribuídos" in sem_itens["motivo"]


def test_p1_exige_designacao_na_unidade_de_origem_e_registro_ativo():
    registro = criar_registro()
    sem_designacao = p1(
        registro["registro_id"], cmd="CMD-PI-P1-SEM-DESIGNACAO", conta="CONTA-C1",
    )
    assert not sem_designacao["permitido"] and "unidade de origem" in sem_designacao["motivo"]

    with Session(motor) as sessao, sessao.begin():
        sessao.get(Registro, registro["registro_id"]).estado_atual = "concluido"
    terminal = p1(registro["registro_id"], cmd="CMD-PI-P1-TERMINAL")
    assert not terminal["permitido"] and terminal["estado_registro"] == "concluido"


def test_p1_repetido_e_idempotente():
    registro = criar_registro()
    original = p1(registro["registro_id"])
    repetido = p1(registro["registro_id"])

    assert original["permitido"] and repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(original)
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Pendencia)) == 1
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento == "P1")) == 1


def test_p2_entrega_a_pendencia_somente_a_agente_designado_no_destino():
    _, criada = preparar_pendencia(prefixo="CMD-PI-FILA")
    assert codigos_alerta("CONTA-C1") == {
        "CONCLUSAO_BLOQUEADA", "PROVIDENCIA_INTERSECRETARIAL_RECEBIDA",
    }
    origem = p2(criada["pendencia_id"], cmd="CMD-PI-P2-ORIGEM", conta="CONTA-A1")
    assert not origem["permitido"] and "autorizada" in origem["motivo"]

    resultado = p2(criada["pendencia_id"])

    assert resultado["permitido"] and resultado["responsavel_atual_id"] == "PESSOA-C"
    assert codigos_alerta("CONTA-C1") == {
        "CONCLUSAO_BLOQUEADA", "PROVIDENCIA_INTERSECRETARIAL_ATRIBUIDA_A_VOCE",
    }


def test_p3_registra_resposta_e_evidencia_sem_editar_o_form1():
    registro, criada = preparar_pendencia(prefixo="CMD-PI-RESPONDE")
    assert p2(criada["pendencia_id"], cmd="CMD-PI-RESPONDE-P2")["permitido"]
    with Session(motor) as sessao:
        instrumento = sessao.scalars(select(Instrumento).where(
            Instrumento.registro_id == registro["registro_id"]
        )).one()
        estado_anterior = instrumento.estado_instrumento

    resultado = p3(criada["pendencia_id"], cmd="CMD-PI-RESPONDE-P3")

    assert resultado["permitido"] and resultado["lacre_resposta"]
    with Session(motor) as sessao:
        pendencia = sessao.get(Pendencia, criada["pendencia_id"])
        instrumento = sessao.scalars(select(Instrumento).where(
            Instrumento.registro_id == registro["registro_id"]
        )).one()
        evento = sessao.scalars(select(Evento).where(
            Evento.cadeia_id == pendencia.id, Evento.codigo_evento == "P3"
        )).one()
        assert pendencia.estado == "respondida"
        assert evento.conteudo["resposta"] == RESPOSTA
        assert instrumento.estado_instrumento == estado_anterior == "nao_iniciado"
        assert verificar_cadeia(sessao, pendencia.id)[0]
    assert codigos_alerta("CONTA-A1") == {
        "RESPOSTA_INTERSECRETARIAL_AGUARDANDO_DECISAO",
    }


def test_p3_exige_resposta_fechada_e_o_mesmo_responsavel():
    _, criada = preparar_pendencia(prefixo="CMD-PI-P3-PORTAO")
    assert p2(criada["pendencia_id"], cmd="CMD-PI-P3-PORTAO-P2")["permitido"]
    incompleta = deepcopy(RESPOSTA)
    incompleta.pop("evidencias")
    sem_evidencia = p3(
        criada["pendencia_id"], resposta=incompleta, cmd="CMD-PI-P3-INCOMPLETA",
    )
    assert not sem_evidencia["permitido"] and "estruturada completa" in sem_evidencia["motivo"]
    outra_pessoa = p3(
        criada["pendencia_id"], cmd="CMD-PI-P3-OUTRA", conta="CONTA-A1",
    )
    assert not outra_pessoa["permitido"] and "assumiu" in outra_pessoa["motivo"]


def test_p4_so_origem_aceita_e_preserva_a_unidade_principal():
    registro, criada, _, respondida = preparar_resposta(prefixo="CMD-PI-ACEITE")
    destino = p4(criada["pendencia_id"], cmd="CMD-PI-P4-DESTINO", conta="CONTA-C1")
    assert not destino["permitido"] and "unidade de origem" in destino["motivo"]

    resultado = p4(criada["pendencia_id"], cmd="CMD-PI-ACEITE-P4")

    assert resultado["permitido"] and resultado["estado_pendencia"] == "encerrada"
    assert resultado["lacre_aceito"] == respondida["lacre_resposta"]
    with Session(motor) as sessao:
        pendencia = sessao.get(Pendencia, criada["pendencia_id"])
        registro_db = sessao.get(Registro, registro["registro_id"])
        eventos = sessao.scalars(select(Evento).where(
            Evento.cadeia_id == pendencia.id
        ).order_by(Evento.sequencia_cadeia)).all()
        assert not pendencia.bloqueante and pendencia.gate_bloqueado is None
        assert registro_db.unidade_principal_atual_id == "UNID-NORTE"
        assert [evento.codigo_evento for evento in eventos] == ["P1", "P2", "P3", "P4"]
        assert verificar_cadeia(sessao, pendencia.id)[0]
    assert codigos_alerta("CONTA-A1") == set()
    assert codigos_alerta("CONTA-C1") == set()


def test_p2_concorrente_mantem_um_unico_responsavel():
    _, criada = preparar_pendencia(prefixo="CMD-PI-CONCORRENCIA")
    with Session(motor) as sessao, sessao.begin():
        sessao.add(Designacao(
            pessoa_id="PESSOA-F", unidade_id="UNID-SUL", papel="agente_pendencia",
        ))
    barreira = threading.Barrier(2)
    resultados = []

    def assumir(numero, conta):
        barreira.wait()
        resultados.append(p2(
            criada["pendencia_id"], cmd=f"CMD-PI-P2-CONC-{numero}", conta=conta,
        ))

    threads = [
        threading.Thread(target=assumir, args=(1, "CONTA-C1")),
        threading.Thread(target=assumir, args=(2, "CONTA-F1")),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(resultado["permitido"] for resultado in resultados) == [False, True]
    with Session(motor) as sessao:
        pendencia = sessao.get(Pendencia, criada["pendencia_id"])
        assert pendencia.responsavel_atual_id in {"PESSOA-C", "PESSOA-F"}
        assert sessao.scalar(select(func.count()).select_from(Evento).where(
            Evento.cadeia_id == pendencia.id, Evento.codigo_evento == "P2"
        )) == 1


def test_p4_repetido_e_idempotente():
    _, criada, _, _ = preparar_resposta(prefixo="CMD-PI-IDEMP")
    original = p4(criada["pendencia_id"])
    repetido = p4(criada["pendencia_id"])

    assert original["permitido"] and repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(original)
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Evento).where(
            Evento.cadeia_id == criada["pendencia_id"], Evento.codigo_evento == "P4"
        )) == 1


def test_p3_repetido_e_idempotente():
    _, criada = preparar_pendencia(prefixo="CMD-PI-P3-IDEMP")
    assert p2(criada["pendencia_id"], cmd="CMD-PI-P3-IDEMP-P2")["permitido"]
    original = p3(criada["pendencia_id"])
    repetido = p3(criada["pendencia_id"])

    assert original["permitido"] and repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(original)
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Evento).where(
            Evento.cadeia_id == criada["pendencia_id"], Evento.codigo_evento == "P3"
        )) == 1


def test_p1_e_desfeito_no_rollback():
    registro = criar_registro()
    with pytest.raises(RuntimeError):
        with Session(motor) as sessao, sessao.begin():
            resultado = criar_pendencia_intersecretarial(
                sessao, comando_id="CMD-PI-P1-ROLLBACK", conta_id="CONTA-A1",
                registro_id=registro["registro_id"], unidade_destino_id="UNID-SUL",
                solicitacao="Solicitação fictícia para rollback",
                itens_atribuidos=["Item fictício"],
            )
            assert resultado["permitido"]
            raise RuntimeError("falha simulada antes do commit")

    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Pendencia)) == 0
        assert sessao.get(Comando, "CMD-PI-P1-ROLLBACK") is None
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento == "P1")) == 0


def test_p3_e_desfeito_no_rollback():
    _, criada = preparar_pendencia(prefixo="CMD-PI-P3-ROLLBACK")
    assert p2(criada["pendencia_id"], cmd="CMD-PI-P3-ROLLBACK-P2")["permitido"]
    with pytest.raises(RuntimeError):
        with Session(motor) as sessao, sessao.begin():
            resultado = responder_pendencia_intersecretarial(
                sessao, comando_id="CMD-PI-P3-ROLLBACK", conta_id="CONTA-C1",
                pendencia_id=criada["pendencia_id"], resposta=deepcopy(RESPOSTA),
            )
            assert resultado["permitido"]
            raise RuntimeError("falha simulada antes do commit")

    with Session(motor) as sessao:
        pendencia = sessao.get(Pendencia, criada["pendencia_id"])
        assert pendencia.estado == "em_atendimento" and pendencia.lacre_resposta is None
        assert sessao.get(Comando, "CMD-PI-P3-ROLLBACK") is None
        assert sessao.scalar(select(func.count()).select_from(Evento).where(
            Evento.cadeia_id == pendencia.id, Evento.codigo_evento == "P3"
        )) == 0


def test_p4_e_desfeito_no_rollback():
    _, criada, _, respondida = preparar_resposta(prefixo="CMD-PI-P4-ROLLBACK")
    with pytest.raises(RuntimeError):
        with Session(motor) as sessao, sessao.begin():
            resultado = aceitar_pendencia_intersecretarial(
                sessao, comando_id="CMD-PI-P4-ROLLBACK", conta_id="CONTA-A1",
                pendencia_id=criada["pendencia_id"],
            )
            assert resultado["permitido"]
            raise RuntimeError("falha simulada antes do commit")

    with Session(motor) as sessao:
        pendencia = sessao.get(Pendencia, criada["pendencia_id"])
        assert pendencia.estado == "respondida" and pendencia.bloqueante
        assert pendencia.lacre_resposta == respondida["lacre_resposta"]
        assert pendencia.lacre_aceito is None and pendencia.gate_bloqueado == "conclusao"
        assert sessao.get(Comando, "CMD-PI-P4-ROLLBACK") is None
        assert sessao.scalar(select(func.count()).select_from(Evento).where(
            Evento.cadeia_id == pendencia.id, Evento.codigo_evento == "P4"
        )) == 0


def test_g5_fica_bloqueado_ate_o_aceite_intersecretarial():
    _, registro_id, _, _, _, _ = preparar_validado_sem_medidas()
    criada = p1(registro_id, cmd="CMD-PI-GATE-P1")
    bloqueado = g5(registro_id, cmd="CMD-PI-GATE-G5-BLOQUEADO")
    assert not bloqueado["permitido"]
    assert bloqueado["pendencias_abertas"] == [criada["pendencia_id"]]

    assert p2(criada["pendencia_id"], cmd="CMD-PI-GATE-P2")["permitido"]
    assert p3(criada["pendencia_id"], cmd="CMD-PI-GATE-P3")["permitido"]
    assert p4(criada["pendencia_id"], cmd="CMD-PI-GATE-P4")["permitido"]

    concluido = g5(registro_id, cmd="CMD-PI-GATE-G5-CONCLUIDO")
    assert concluido["permitido"] and concluido["estado_registro"] == "concluido"
