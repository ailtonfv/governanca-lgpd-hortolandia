"""I1 e I2 do FORM 1 sintético: rascunho, idempotência e concorrência."""

import threading
from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.banco import motor
from app.eventos import verificar_cadeia
from app.instrumentos import iniciar_preenchimento, lacre_do_conteudo, salvar_rascunho
from app.modelos import (AnaliseInstrumento, Comando, Conta, Evento, EventoAuditoria,
                         Instrumento, RascunhoInstrumento, VersaoInstrumento)
from migracoes.analise_instrumento import aplicar as aplicar_migracao_analise
from migracoes.rascunho_versoes import aplicar as aplicar_migracao_rascunho_versoes
from testes.apoio import CADASTRO, g1, sem_reexecucao


def criar_form1(cmd="CMD-R-G1"):
    registro = g1(cmd, CADASTRO, "CTX-TRIB-01")
    with Session(motor) as sessao:
        return sessao.scalars(
            select(Instrumento).where(Instrumento.registro_id == registro["registro_id"])
        ).one().id


def i1(instrumento_id, cmd="CMD-R-I1", conta="CONTA-A1", **extra):
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return iniciar_preenchimento(sessao, comando_id=cmd, conta_id=conta,
                                     instrumento_id=instrumento_id, **extra)


def i2(instrumento_id, versao, conteudo, cmd="CMD-R-I2", conta="CONTA-A1", **extra):
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return salvar_rascunho(sessao, comando_id=cmd, conta_id=conta,
                               instrumento_id=instrumento_id, versao_lida=versao,
                               conteudo=conteudo, **extra)


def test_g1_ainda_cria_form1_nao_iniciado_sem_rascunho():
    instrumento_id = criar_form1()
    with Session(motor) as sessao:
        instrumento = sessao.get(Instrumento, instrumento_id)
        assert instrumento.estado_instrumento == "nao_iniciado"
        assert sessao.get(RascunhoInstrumento, instrumento_id) is None


def test_i1_cria_rascunho_e_evento_na_cadeia_do_instrumento():
    instrumento_id = criar_form1()
    momento = datetime(2026, 10, 16, 12, 30, tzinfo=timezone.utc)
    resultado = i1(instrumento_id, momento=momento)
    assert resultado["permitido"] and resultado["versao_rascunho"] == 1
    assert resultado["evento_i1"] == 1
    assert resultado["lacre_conteudo"] == lacre_do_conteudo({})

    with Session(motor) as sessao:
        instrumento = sessao.get(Instrumento, instrumento_id)
        rascunho = sessao.get(RascunhoInstrumento, instrumento_id)
        evento = sessao.scalars(select(Evento).where(Evento.cadeia_id == instrumento_id)).one()
        assert instrumento.estado_instrumento == "em_preenchimento"
        assert (rascunho.conteudo, rascunho.versao_rascunho) == ({}, 1)
        assert rascunho.salvo_por == "PESSOA-A" and rascunho.salvo_em == momento
        assert evento.codigo_evento == "I1" and evento.cadeia_tipo == "instrumento"
        assert verificar_cadeia(sessao, instrumento_id)[0]


def test_i1_repetido_e_idempotente():
    instrumento_id = criar_form1()
    original = i1(instrumento_id)
    repetido = i1(instrumento_id)
    assert repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(original)
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.cadeia_id == instrumento_id)) == 1


@pytest.mark.parametrize("conta", ["CONTA-B1", "CONTA-C1"])
def test_i1_exige_elaborador_na_unidade_do_registro(conta):
    instrumento_id = criar_form1()
    resultado = i1(instrumento_id, cmd=f"CMD-R-SEM-PAPEL-{conta}", conta=conta)
    assert not resultado["permitido"]
    with Session(motor) as sessao:
        assert sessao.get(Instrumento, instrumento_id).estado_instrumento == "nao_iniciado"
        assert sessao.get(RascunhoInstrumento, instrumento_id) is None
        assert sessao.scalars(select(EventoAuditoria).where(
            EventoAuditoria.comando_id == f"CMD-R-SEM-PAPEL-{conta}")).one()


def test_i1_recusa_conta_desativada_e_estado_inadequado():
    instrumento_id = criar_form1()
    with Session(motor) as sessao, sessao.begin():
        sessao.execute(update(Conta).where(Conta.id == "CONTA-A1").values(ativa=False))
    assert not i1(instrumento_id, cmd="CMD-R-INATIVA")["permitido"]
    with Session(motor) as sessao, sessao.begin():
        sessao.execute(update(Conta).where(Conta.id == "CONTA-A1").values(ativa=True))
    assert i1(instrumento_id, cmd="CMD-R-I1-VALIDO")["permitido"]
    assert not i1(instrumento_id, cmd="CMD-R-I1-DUPLO")["permitido"]


def test_dois_i1_simultaneos_so_um_inicia_o_instrumento():
    instrumento_id = criar_form1()
    barreira = threading.Barrier(2)
    resultados = []

    def iniciar(numero):
        barreira.wait()
        resultados.append(i1(instrumento_id, cmd=f"CMD-R-I1-CONC-{numero}"))

    threads = [threading.Thread(target=iniciar, args=(n,)) for n in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(r["permitido"] for r in resultados) == [False, True]
    with Session(motor) as sessao:
        assert sessao.get(RascunhoInstrumento, instrumento_id).versao_rascunho == 1
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.cadeia_id == instrumento_id)) == 1


def test_i1_e_atomico_se_a_transacao_falha():
    instrumento_id = criar_form1()
    with pytest.raises(RuntimeError):
        with Session(motor) as sessao, sessao.begin():
            resultado = iniciar_preenchimento(
                sessao, comando_id="CMD-R-I1-ROLLBACK", conta_id="CONTA-A1",
                instrumento_id=instrumento_id,
            )
            assert resultado["permitido"]
            raise RuntimeError("falha simulada depois do ato e antes do commit")
    with Session(motor) as sessao:
        assert sessao.get(Instrumento, instrumento_id).estado_instrumento == "nao_iniciado"
        assert sessao.get(RascunhoInstrumento, instrumento_id) is None
        assert sessao.get(Comando, "CMD-R-I1-ROLLBACK") is None
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.cadeia_id == instrumento_id)) == 0


def test_i2_salva_incrementa_lacre_e_evento():
    instrumento_id = criar_form1()
    i1(instrumento_id)
    conteudo = {"categorias_titulares": ["TIT-CONTRIBUINTE"],
                "finalidade": "Emitir documento tributário fictício"}
    resultado = i2(instrumento_id, 1, conteudo)
    assert resultado["permitido"] and resultado["versao_rascunho"] == 2
    assert resultado["evento_i2"] == 2
    assert resultado["lacre_conteudo"] == lacre_do_conteudo(conteudo)
    with Session(motor) as sessao:
        rascunho = sessao.get(RascunhoInstrumento, instrumento_id)
        assert rascunho.conteudo == conteudo and rascunho.versao_rascunho == 2
        eventos = sessao.scalars(select(Evento).where(
            Evento.cadeia_id == instrumento_id).order_by(Evento.sequencia_cadeia)).all()
        assert [e.codigo_evento for e in eventos] == ["I1", "I2"]
        assert verificar_cadeia(sessao, instrumento_id)[0]


def test_i2_repetido_e_idempotente():
    instrumento_id = criar_form1()
    i1(instrumento_id)
    conteudo = {"finalidade": "Teste fictício"}
    original = i2(instrumento_id, 1, conteudo)
    repetido = i2(instrumento_id, 1, conteudo)
    assert repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(original)
    with Session(motor) as sessao:
        assert sessao.get(RascunhoInstrumento, instrumento_id).versao_rascunho == 2


def test_poc_ts_004_versao_desatualizada_nao_sobrescreve_rascunho():
    instrumento_id = criar_form1()
    i1(instrumento_id)
    vencedor = {"finalidade": "Conteúdo vencedor fictício"}
    assert i2(instrumento_id, 1, vencedor, cmd="CMD-R-VENCE")["permitido"]
    vencido = i2(instrumento_id, 1, {"finalidade": "Conteúdo obsoleto fictício"},
                  cmd="CMD-R-PERDE")
    assert not vencido["permitido"] and "desatualizado" in vencido["motivo"]
    assert (vencido["versao_lida"], vencido["versao_atual"]) == (1, 2)
    with Session(motor) as sessao:
        rascunho = sessao.get(RascunhoInstrumento, instrumento_id)
        assert rascunho.conteudo == vencedor
        assert rascunho.versao_rascunho == 2
        assert rascunho.lacre_conteudo == lacre_do_conteudo(vencedor)
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.cadeia_id == instrumento_id)) == 2
        assert sessao.scalars(select(EventoAuditoria).where(
            EventoAuditoria.comando_id == "CMD-R-PERDE")).one()


def test_dois_i2_simultaneos_com_mesma_versao_so_um_vence():
    instrumento_id = criar_form1()
    i1(instrumento_id)
    barreira = threading.Barrier(2)
    resultados = []

    def salvar(numero):
        barreira.wait()
        resultados.append(i2(instrumento_id, 1, {"tentativa": numero},
                              cmd=f"CMD-R-CONC-{numero}"))

    threads = [threading.Thread(target=salvar, args=(n,)) for n in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(r["permitido"] for r in resultados) == [False, True]
    with Session(motor) as sessao:
        rascunho = sessao.get(RascunhoInstrumento, instrumento_id)
        assert rascunho.versao_rascunho == 2
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.cadeia_id == instrumento_id)) == 2
        assert verificar_cadeia(sessao, instrumento_id)[0]


def test_i2_e_atomico_se_a_transacao_falha():
    instrumento_id = criar_form1()
    i1(instrumento_id)
    with pytest.raises(RuntimeError):
        with Session(motor) as sessao, sessao.begin():
            resultado = salvar_rascunho(
                sessao, comando_id="CMD-R-ROLLBACK", conta_id="CONTA-A1",
                instrumento_id=instrumento_id, versao_lida=1,
                conteudo={"finalidade": "Não pode permanecer"},
            )
            assert resultado["permitido"]
            raise RuntimeError("falha simulada depois do ato e antes do commit")
    with Session(motor) as sessao:
        rascunho = sessao.get(RascunhoInstrumento, instrumento_id)
        assert rascunho.conteudo == {} and rascunho.versao_rascunho == 1
        assert sessao.get(Comando, "CMD-R-ROLLBACK") is None
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.cadeia_id == instrumento_id)) == 1


def test_migracoes_recriam_as_tabelas_do_instrumento_e_da_analise():
    """O banco evoluído e um banco novo terminam com as mesmas tabelas."""
    with motor.begin() as conexao:
        AnaliseInstrumento.__table__.drop(bind=conexao, checkfirst=True)
        VersaoInstrumento.__table__.drop(bind=conexao, checkfirst=True)
        RascunhoInstrumento.__table__.drop(bind=conexao, checkfirst=True)
        with Session(bind=conexao) as sessao:
            aplicar_migracao_rascunho_versoes(sessao)
            aplicar_migracao_analise(sessao)
        nomes = set(conexao.dialect.get_table_names(conexao))
        assert {"rascunho_instrumento", "versao_instrumento", "analise_instrumento"} <= nomes
