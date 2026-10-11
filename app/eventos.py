# Camada de domínio: o livro de atos com a cadeia de hash (DA-26, DA-27).
# É o primeiro_hash.py, agora gravando e lendo do banco de dados.

import hashlib
import json
from sqlalchemy import select
from app.modelos import Evento

HASH_INICIAL = "0" * 64  # o "elo zero": o primeiro evento de cada corrente não tem anterior


def calcular_hash(cadeia_id, sequencia_cadeia, codigo_evento, pessoa_id, conteudo, hash_anterior):
    """Calcula o lacre (SHA-256) de um evento sobre um JSON canônico."""
    pacote = {
        "cadeia_id": cadeia_id,
        "sequencia_cadeia": sequencia_cadeia,
        "codigo_evento": codigo_evento,
        "pessoa_id": pessoa_id,
        "conteudo": conteudo,
        "hash_anterior": hash_anterior,
    }
    # JSON canônico: chaves em ordem fixa e sem espaços -> o mesmo pacote gera sempre o mesmo hash
    texto = json.dumps(pacote, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def registrar_evento(sessao, cadeia_id, codigo_evento, pessoa_id, conteudo):
    """Acrescenta um evento ao fim da corrente do objeto indicado. Nunca altera os anteriores."""
    ultimo = sessao.scalars(
        select(Evento)
        .where(Evento.cadeia_id == cadeia_id)
        .order_by(Evento.sequencia_cadeia.desc())
        .limit(1)
    ).first()

    sequencia = 1 if ultimo is None else ultimo.sequencia_cadeia + 1
    hash_anterior = HASH_INICIAL if ultimo is None else ultimo.hash

    evento = Evento(
        cadeia_id=cadeia_id,
        sequencia_cadeia=sequencia,
        codigo_evento=codigo_evento,
        pessoa_id=pessoa_id,
        conteudo=conteudo,
        hash_anterior=hash_anterior,
        hash=calcular_hash(cadeia_id, sequencia, codigo_evento, pessoa_id, conteudo, hash_anterior),
    )
    sessao.add(evento)
    sessao.flush()  # envia ao banco dentro da transação (ainda pode ser desfeito)
    return evento


def verificar_cadeia(sessao, cadeia_id):
    """Relê a corrente do banco, recalcula cada lacre e diz se está íntegra."""
    eventos = sessao.scalars(
        select(Evento)
        .where(Evento.cadeia_id == cadeia_id)
        .order_by(Evento.sequencia_cadeia)
    ).all()

    anterior = HASH_INICIAL
    for ev in eventos:
        if ev.hash_anterior != anterior:
            return False, f"ELO QUEBRADO antes do evento {ev.sequencia_cadeia}"
        recalculado = calcular_hash(ev.cadeia_id, ev.sequencia_cadeia, ev.codigo_evento,
                                    ev.pessoa_id, ev.conteudo, ev.hash_anterior)
        if recalculado != ev.hash:
            return False, f"ADULTERAÇÃO DETECTADA no evento {ev.sequencia_cadeia}"
        anterior = ev.hash
    return True, f"corrente íntegra ({len(eventos)} eventos)"
