"""Ação obrigatória e G6: conclusão humana do percurso com medidas."""

import threading
from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.acoes import finalizar_acao_obrigatoria
from app.banco import motor
from app.eventos import verificar_cadeia
from app.modelos import (AcaoObrigatoria, Ciclo, Comando, Evento, Instrumento,
                         Registro)
from app.workflow import concluir_registro_apos_medidas
from testes.apoio import sem_reexecucao
from testes.test_submissao import (criar_acao_sintetica, criar_form1, i3, i5,
                                   i13, preparar)


def finalizar(acao_id, resultado="concluida", evidencia=None,
              motivo=None, cmd="CMD-M-AO1", conta="CONTA-B1", **extra):
    evidencia = ({"comprovacao": "Evidência fictícia da medida"}
                 if evidencia is None else evidencia)
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return finalizar_acao_obrigatoria(
            sessao, comando_id=cmd, conta_id=conta, acao_id=acao_id,
            resultado=resultado, evidencia=evidencia, motivo=motivo, **extra,
        )


def g6(registro_id, cmd="CMD-M-G6", conta="CONTA-B1", **extra):
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return concluir_registro_apos_medidas(
            sessao, comando_id=cmd, conta_id=conta, registro_id=registro_id,
            **extra,
        )


def preparar_com_medida(prefixo="CMD-M", acao_id="ACAO-MEDIDA-1"):
    instrumento_id, registro_id, codigo = criar_form1(cmd=f"{prefixo}-G1")
    preparar(instrumento_id, prefixo=prefixo)
    submissao = i3(instrumento_id, cmd=f"{prefixo}-I3")
    analise = i13(instrumento_id, submissao["versao_id"], cmd=f"{prefixo}-I13")
    criar_acao_sintetica(instrumento_id, registro_id, acao_id=acao_id)
    validacao = i5(
        instrumento_id, analise["analise_id"], submissao["versao_id"],
        cmd=f"{prefixo}-I5",
    )
    assert validacao["permitido"] and validacao["estado_registro"] == "em_execucao"
    return instrumento_id, registro_id, codigo, submissao, acao_id


def test_acao_so_pode_ser_finalizada_durante_execucao_pelo_responsavel():
    instrumento_id, registro_id, _ = criar_form1(cmd="CMD-M-PORTAO-G1")
    acao_id = criar_acao_sintetica(
        instrumento_id, registro_id, acao_id="ACAO-M-PORTAO",
    )
    cedo = finalizar(acao_id, cmd="CMD-M-AO1-CEDO")
    assert not cedo["permitido"] and "em_execucao" in cedo["motivo"]

    preparar(instrumento_id, prefixo="CMD-M-PORTAO")
    submissao = i3(instrumento_id, cmd="CMD-M-PORTAO-I3")
    analise = i13(instrumento_id, submissao["versao_id"], cmd="CMD-M-PORTAO-I13")
    assert i5(instrumento_id, analise["analise_id"], submissao["versao_id"],
              cmd="CMD-M-PORTAO-I5")["permitido"]
    outra_pessoa = finalizar(
        acao_id, cmd="CMD-M-AO1-OUTRA-PESSOA", conta="CONTA-A1",
    )
    assert not outra_pessoa["permitido"] and "responsável" in outra_pessoa["motivo"]


def test_acao_exige_resultado_evidencia_e_motivo_de_encerramento_validos():
    *_, acao_id = preparar_com_medida(prefixo="CMD-M-CAMPOS", acao_id="ACAO-M-CAMPOS")
    resultado = finalizar(acao_id, resultado="ignorada", cmd="CMD-M-AO1-RESULTADO")
    assert not resultado["permitido"] and "resultado" in resultado["motivo"]
    sem_evidencia = finalizar(acao_id, evidencia={}, cmd="CMD-M-AO1-SEM-EVIDENCIA")
    assert not sem_evidencia["permitido"] and "evidência" in sem_evidencia["motivo"]
    sem_motivo = finalizar(
        acao_id, resultado="encerrada", motivo="", cmd="CMD-M-AO1-SEM-MOTIVO",
    )
    assert not sem_motivo["permitido"] and "motivo" in sem_motivo["motivo"]


def test_conclusao_da_acao_guarda_evidencia_evento_e_idempotencia():
    _, registro_id, codigo, _, acao_id = preparar_com_medida(prefixo="CMD-M-CONCLUIR")
    evidencia = {"documento": "REL-FICTICIO-001", "observacao": "Teste sem dados reais"}
    momento = datetime(2026, 10, 17, 19, 0, tzinfo=timezone.utc)

    original = finalizar(acao_id, evidencia=evidencia, momento=momento)
    repetido = finalizar(acao_id, evidencia=evidencia, momento=momento)

    assert original["permitido"] and repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(original)
    with Session(motor) as sessao:
        acao = sessao.get(AcaoObrigatoria, acao_id)
        evento = sessao.scalars(select(Evento).where(Evento.codigo_evento == "AO1")).one()
        assert acao.estado == "concluida"
        assert acao.evidencia == {"conteudo": evidencia, "motivo_encerramento": None}
        assert acao.atualizada_em == momento
        assert evento.conteudo["registro_id"] == registro_id
        assert verificar_cadeia(sessao, codigo)[0]


def test_g6_permanece_bloqueado_enquanto_houver_acao_aberta():
    _, registro_id, _, _, acao_id = preparar_com_medida(prefixo="CMD-M-ABERTA")

    resultado = g6(registro_id)

    assert not resultado["permitido"]
    assert resultado["acoes_pendentes"] == [acao_id]
    with Session(motor) as sessao:
        assert sessao.get(Registro, registro_id).estado_atual == "em_execucao"


def test_g6_conclui_registro_e_ciclo_sem_apagar_versao_ou_evidencia():
    instrumento_id, registro_id, codigo, submissao, acao_id = preparar_com_medida(
        prefixo="CMD-M-SUCESSO",
    )
    evidencia = {"protocolo": "PROTOCOLO-FICTICIO-01"}
    assert finalizar(acao_id, evidencia=evidencia)["permitido"]
    momento = datetime(2026, 10, 17, 20, 0, tzinfo=timezone.utc)

    resultado = g6(registro_id, momento=momento)

    assert resultado["permitido"] and resultado["estado_registro"] == "concluido"
    assert resultado["situacao_ciclo"] == "concluido"
    with Session(motor) as sessao:
        registro = sessao.get(Registro, registro_id)
        ciclo = sessao.get(Ciclo, resultado["ciclo_id"])
        instrumento = sessao.get(Instrumento, instrumento_id)
        acao = sessao.get(AcaoObrigatoria, acao_id)
        evento = sessao.scalars(select(Evento).where(Evento.codigo_evento == "G6")).one()
        assert registro.estado_atual == "concluido" and ciclo.situacao == "concluido"
        assert instrumento.versao_vigente_id == submissao["versao_id"]
        assert acao.evidencia["conteudo"] == evidencia
        assert evento.conteudo["concluido_em"] == momento.isoformat()
        assert verificar_cadeia(sessao, codigo)[0]


def test_g6_aceita_encerramento_formal_com_motivo_e_evidencia():
    _, registro_id, _, _, acao_id = preparar_com_medida(prefixo="CMD-M-ENCERRADA")
    motivo = "Medida substituída por controle fictício equivalente"
    assert finalizar(
        acao_id, resultado="encerrada", motivo=motivo,
        evidencia={"decisao": "ATO-FICTICIO-01"}, cmd="CMD-M-AO1-ENCERRADA",
    )["permitido"]

    resultado = g6(registro_id, cmd="CMD-M-G6-ENCERRADA")

    assert resultado["permitido"]
    with Session(motor) as sessao:
        acao = sessao.get(AcaoObrigatoria, acao_id)
        assert acao.estado == "encerrada"
        assert acao.evidencia["motivo_encerramento"] == motivo


def test_g6_exige_competencia_formal_para_concluir():
    _, registro_id, _, _, acao_id = preparar_com_medida(prefixo="CMD-M-COMPETENCIA")
    assert finalizar(acao_id)["permitido"]

    resultado = g6(registro_id, cmd="CMD-M-G6-SEM-PAPEL", conta="CONTA-A1")

    assert not resultado["permitido"] and "competência formal" in resultado["motivo"]


def test_g6_repetido_e_idempotente():
    _, registro_id, _, _, acao_id = preparar_com_medida(prefixo="CMD-M-IDEMP")
    assert finalizar(acao_id)["permitido"]
    original = g6(registro_id)
    repetido = g6(registro_id)

    assert original["permitido"] and repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(original)
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento == "G6")) == 1


def test_dois_g6_simultaneos_concluem_uma_unica_vez():
    _, registro_id, _, _, acao_id = preparar_com_medida(prefixo="CMD-M-CONCORRENCIA")
    assert finalizar(acao_id)["permitido"]
    barreira = threading.Barrier(2)
    resultados = []

    def concluir(numero):
        barreira.wait()
        resultados.append(g6(registro_id, cmd=f"CMD-M-G6-CONC-{numero}"))

    threads = [threading.Thread(target=concluir, args=(numero,)) for numero in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(resultado["permitido"] for resultado in resultados) == [False, True]
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento == "G6")) == 1


def test_g6_e_desfeito_no_rollback():
    _, registro_id, _, _, acao_id = preparar_com_medida(prefixo="CMD-M-ROLLBACK")
    assert finalizar(acao_id)["permitido"]
    with pytest.raises(RuntimeError):
        with Session(motor) as sessao, sessao.begin():
            resultado = concluir_registro_apos_medidas(
                sessao, comando_id="CMD-M-G6-ROLLBACK", conta_id="CONTA-B1",
                registro_id=registro_id,
            )
            assert resultado["permitido"]
            raise RuntimeError("falha simulada antes do commit")

    with Session(motor) as sessao:
        registro = sessao.get(Registro, registro_id)
        ciclo = sessao.scalars(select(Ciclo).where(Ciclo.registro_id == registro_id)).one()
        assert registro.estado_atual == "em_execucao" and ciclo.situacao == "ativo"
        assert sessao.get(Comando, "CMD-M-G6-ROLLBACK") is None
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento == "G6")) == 0
