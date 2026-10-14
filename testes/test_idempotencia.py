# Pedido idempotente estrito (Etapa 2d, item A1).

import threading
import time
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import Registro, EventoAuditoria
from app.workflow import criar_registro
from app.permissoes import executar_acao
from testes.apoio import g1, sem_reexecucao, CADASTRO


def test_repeticao_devolve_o_resultado_original_identico():
    original = g1("CMD-I-01", CADASTRO, "CTX-TRIB-01")
    repetido = g1("CMD-I-01", CADASTRO, "CTX-TRIB-01")
    assert original["permitido"] and original["reexecutado"] is False
    assert repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(original)


def test_repeticao_de_uma_negacao_devolve_a_mesma_negacao():
    g1("CMD-I-02", CADASTRO, "CTX-TRIB-01")
    negado = g1("CMD-I-03", CADASTRO, "CTX-TRIB-01")
    repetido = g1("CMD-I-03", CADASTRO, "CTX-TRIB-01")
    assert not negado["permitido"] and repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(negado)


def test_mesma_chave_com_conteudo_diferente_e_recusada():
    g1("CMD-I-04", CADASTRO, "CTX-TRIB-01")
    r = g1("CMD-I-04", CADASTRO, "CTX-URB-01")           # outro contexto, mesma chave
    assert not r["permitido"] and "reutilização indevida" in r["motivo"]
    with Session(motor) as s:
        assert s.scalar(select(func.count()).select_from(Registro)) == 1
        assert s.scalars(select(EventoAuditoria).where(EventoAuditoria.comando_id == "CMD-I-04")).first()


def test_pedido_sem_chave_e_recusado():
    r = g1(None, CADASTRO, "CTX-TRIB-01")
    assert not r["permitido"] and "comando_id" in r["motivo"]
    r = g1("   ", CADASTRO, "CTX-TRIB-01")
    assert not r["permitido"]


def test_dois_pedidos_simultaneos_com_a_mesma_chave():
    """A grava o comando e segura a transação; B chega com a mesma chave, espera o banco,
    é recusado pela chave primária e responde como reexecução do resultado de A."""
    resultados, a_gravou = {}, threading.Event()

    def pedido_a():
        with Session(motor, expire_on_commit=False) as s, s.begin():
            resultados["A"] = criar_registro(s, comando_id="CMD-I-05", conta_id="CONTA-A1",
                                             unidade_id="UNID-NORTE", contexto_id="CTX-TRIB-01",
                                             titulo_objeto="Simultâneo", objeto_principal_id=CADASTRO)
            a_gravou.set()
            time.sleep(1.5)

    def pedido_b():
        a_gravou.wait()
        resultados["B"] = g1("CMD-I-05", CADASTRO, "CTX-TRIB-01", titulo="Simultâneo")

    ta, tb = threading.Thread(target=pedido_a), threading.Thread(target=pedido_b)
    ta.start(); tb.start(); ta.join(); tb.join()
    assert resultados["A"]["permitido"] and resultados["B"]["reexecutado"] is True
    assert resultados["B"]["codigo_lgpd"] == resultados["A"]["codigo_lgpd"]
    with Session(motor) as s:
        assert s.scalar(select(func.count()).select_from(Registro)) == 1


def test_executar_acao_tambem_e_estrito():
    with Session(motor) as s, s.begin():
        assert executar_acao(s, "CONTA-A1", "REG-T", "UNID-NORTE", "submeter", {"versao": 1}, "CMD-I-06") \
            == (True, "permitido", False)
        assert executar_acao(s, "CONTA-A1", "REG-T", "UNID-NORTE", "submeter", {"versao": 1}, "CMD-I-06") \
            == (True, "permitido", True)
        permitido, motivo, _ = executar_acao(s, "CONTA-A1", "REG-T", "UNID-NORTE", "submeter",
                                             {"versao": 2}, "CMD-I-06")
        assert not permitido and "reutilização indevida" in motivo
        permitido, motivo, _ = executar_acao(s, "CONTA-A1", "REG-T", "UNID-NORTE", "submeter", {"versao": 1}, None)
        assert not permitido and "comando_id" in motivo
