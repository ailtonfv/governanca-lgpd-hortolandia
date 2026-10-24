# Transversalidade de objeto + família (D2): só a governança declara; resolve advertências futuras
# daquela família, sem afastar a trava nem os alertas; justificativa pontual não silencia o futuro.

from sqlalchemy.orm import Session
from app.banco import motor
from app.workflow import declarar_transversalidade
from testes.apoio import g1, evento_g1, CADASTRO


def declarar(conta, cmd, familia="TRIB", fundamento="Cadastro usado por todas as frentes tributárias (fictício)"):
    with Session(motor) as s, s.begin():
        return declarar_transversalidade(s, comando_id=cmd, conta_id=conta, objeto_id=CADASTRO,
                                         familia_id=familia, fundamento=fundamento)


def test_so_a_governanca_declara():
    assert not declarar("CONTA-A1", "CMD-T-01")["permitido"]     # responsável/preenchedor
    assert not declarar("CONTA-D1", "CMD-T-02")["permitido"]     # curador
    assert declarar("CONTA-E1", "CMD-T-03")["permitido"]         # governança


def test_fundamento_obrigatorio_e_uma_vigente_por_par():
    assert not declarar("CONTA-E1", "CMD-T-04", fundamento="   ")["permitido"]
    assert declarar("CONTA-E1", "CMD-T-05")["permitido"]
    assert not declarar("CONTA-E1", "CMD-T-06")["permitido"]


def test_transversalidade_resolve_advertencias_futuras_da_familia():
    g1("CMD-T-07", CADASTRO, "CTX-TRIB-01")
    decisao = declarar("CONTA-E1", "CMD-T-08")["decisao_id"]
    r = g1("CMD-T-09", CADASTRO, "CTX-TRIB-03")                  # sem justificativa
    assert r["permitido"] and "transversalidade" in r["motivo"]
    adv = evento_g1(r["codigo_lgpd"]).conteudo["advertencia_familia"]
    assert adv["resolucao"] == "objeto_transversal"
    assert adv["decisoes_de_transversalidade"] == {CADASTRO: decisao}


def test_transversalidade_nao_afasta_a_trava():
    g1("CMD-T-10", CADASTRO, "CTX-TRIB-01")
    declarar("CONTA-E1", "CMD-T-11")
    assert not g1("CMD-T-12", CADASTRO, "CTX-TRIB-01")["permitido"]


def test_transversalidade_nao_vale_para_outra_familia():
    declarar("CONTA-E1", "CMD-T-13")                             # transversal em TRIB
    g1("CMD-T-14", CADASTRO, "CTX-URB-01")
    assert not g1("CMD-T-15", CADASTRO, "CTX-URB-03")["permitido"]   # URB continua pedindo


def test_justificativa_pontual_nao_silencia_o_futuro():
    g1("CMD-T-16", CADASTRO, "CTX-TRIB-01")
    assert g1("CMD-T-17", CADASTRO, "CTX-TRIB-03", resolucao_familia="tratamento_autonomo",
              justificativa="Caso específico (fictício)")["permitido"]
    assert not g1("CMD-T-18", CADASTRO, "CTX-TRIB-02")["permitido"]
