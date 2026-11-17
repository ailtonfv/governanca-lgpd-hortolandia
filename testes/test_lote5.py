from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.banco import motor
from app.eventos import registrar_auditoria, verificar_segmento
from app.modelos import EventoAuditoria


def test_auditoria_dez_consultas_simultaneas():
    barreira = Barrier(10)
    def registrar(i):
        with Session(motor) as s, s.begin():
            barreira.wait(timeout=15)
            evento = registrar_auditoria(s, "consulta", "sistema", "ensaio", {"consulta": i})
            return evento.segmento_id
    with ThreadPoolExecutor(10) as pool:
        segmentos = set(pool.map(registrar, range(10)))
    with Session(motor) as s:
        segmento, = segmentos
        eventos = s.scalars(select(EventoAuditoria).where(EventoAuditoria.segmento_id == segmento)).all()
        assert {e.conteudo["consulta"] for e in eventos} == set(range(10))
        assert sorted(e.sequencia_segmento for e in eventos) == list(range(1, 11))
        assert verificar_segmento(s, segmento)[0]


def test_painel_exige_designacao_vigente(sessao):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.fila_form2 import agora
    from app.modelos import DesignacaoEncarregado
    c = TestClient(app)
    for conta in ("CONTA-A1", "CONTA-B1"):
        assert c.get("/form2/painel-dpo", params={"conta_id":conta}).status_code == 403
    assert c.get("/form2/painel-dpo?conta_id=CONTA-E1").status_code == 200
    sessao.scalar(select(DesignacaoEncarregado)).fim = agora()
    sessao.commit()
    assert c.get("/form2/painel-dpo?conta_id=CONTA-E1").status_code == 403


def test_exclusividade_no_dominio():
    import pytest
    from app.respostas_form2 import aplicar_revisao, aplicar_bloco
    chave = "opcao:F2-3.1"
    with pytest.raises(ValueError):
        aplicar_revisao({},3,{chave:["ALT_09","A_CONFIRMAR"]},demonstrativo=True)
    aplicar_revisao({},3,{chave:["ALT_09","ANALISE_JURIDICA"]},demonstrativo=True)
    with pytest.raises(ValueError):
        aplicar_bloco({},bloco=2,alteracoes={"F2-2.9.1":["ALT_01","A_CONFIRMAR"]},proxima_versao=1)
