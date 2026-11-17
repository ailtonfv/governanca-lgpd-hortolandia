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
