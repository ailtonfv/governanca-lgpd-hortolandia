# Numeração anual do código LGPD (D4): ano no fuso de São Paulo, contador por ano.

import threading
from datetime import datetime
from zoneinfo import ZoneInfo
from testes.apoio import g1

SP = ZoneInfo("America/Sao_Paulo")


def test_virada_do_ano_no_fuso_de_sao_paulo():
    # 31/12/2026 às 23h30 em Hortolândia = 01/01/2027 02h30 em UTC: ainda é 2026
    ultimo_2026 = g1("CMD-N-01", "OBJ-SRV-001", "CTX-TRIB-03", momento=datetime(2026, 12, 31, 23, 30, tzinfo=SP))
    primeiro_2027 = g1("CMD-N-02", "OBJ-SRV-002", "CTX-TRIB-03", momento=datetime(2027, 1, 1, 0, 30, tzinfo=SP))
    segundo_2027 = g1("CMD-N-03", "OBJ-SRV-010", "CTX-TRIB-03", momento=datetime(2027, 1, 1, 9, 0, tzinfo=SP))
    assert ultimo_2026["codigo_lgpd"] == "LGPD-2026-00001"
    assert primeiro_2027["codigo_lgpd"] == "LGPD-2027-00001"
    assert segundo_2027["codigo_lgpd"] == "LGPD-2027-00002"


def test_negacao_nao_consome_numero():
    g1("CMD-N-04", "OBJ-SRV-001", "CTX-TRIB-03")
    g1("CMD-N-05", "OBJ-SRV-001", "CTX-TRIB-03")                 # negado: já existe
    r = g1("CMD-N-06", "OBJ-SRV-002", "CTX-TRIB-03")
    assert r["codigo_lgpd"].endswith("-00002")


def test_pedidos_simultaneos_recebem_numeros_distintos():
    objetos = ["OBJ-SRV-001", "OBJ-SRV-002", "OBJ-SRV-010", "OBJ-PRC-010", "OBJ-ATV-001", "OBJ-ATV-002"]
    resultados = []

    def pedido(n, objeto):
        resultados.append(g1(f"CMD-N-1{n}", objeto, "CTX-TRIB-03"))

    threads = [threading.Thread(target=pedido, args=(n, o)) for n, o in enumerate(objetos)]
    for t in threads: t.start()
    for t in threads: t.join()
    codigos = [r["codigo_lgpd"] for r in resultados]
    assert len(set(codigos)) == len(objetos)
