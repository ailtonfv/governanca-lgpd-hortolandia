# Demonstração do livro de atos — versão alinhada à DA-26 e à DA-27. Somente dados fictícios.
#
#   1. um pedido (comando) da PESSOA-C gera 2 atos na corrente REG-DEMO-01;
#   2. uma consulta vira evento no livro de auditoria do mês;
#   3. as duas correntes são conferidas;
#   4. três fraudes são simuladas e desfeitas (rollback): nada fica alterado no banco.
# Grava uma vez só: se a REG-DEMO-01 já existir, apenas mostra e confere.
# Uso: python -m demonstracoes.demo_eventos

import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import Comando, Evento, EventoAuditoria
from app.eventos import (registrar_evento, registrar_auditoria, verificar_cadeia,
                         verificar_segmento, lacre)

CADEIA = "REG-DEMO-01"

# ---- 1 e 2. gravar (uma vez só)
with Session(motor) as sessao:
    ja_existe = sessao.scalars(select(Evento).where(Evento.cadeia_id == CADEIA)).first() is not None

if not ja_existe:
    with Session(motor) as sessao, sessao.begin():   # tudo ou nada
        pedido = Comando(id=str(uuid.uuid4()), tipo="criar_e_preencher",
                         ator_tipo="pessoa", ator_id="PESSOA-C", conta_id="CONTA-C1")
        sessao.add(pedido)
        sessao.flush()
        registrar_evento(sessao, pedido, "registro", CADEIA, "criar_registro",
                         {"titulo": "Registro de demonstração (fictício)"},
                         codigo_evento="G1", ordem_no_comando=1)
        registrar_evento(sessao, pedido, "registro", CADEIA, "iniciar_preenchimento",
                         {"instrumento": "FORM 1"},
                         codigo_evento="I1", ordem_no_comando=2)
        registrar_auditoria(sessao, "consultar_registro", "pessoa", "PESSOA-C",
                            {"objeto": CADEIA, "conta_id": "CONTA-C1"})
    print("Gravado: 1 pedido com 2 atos e 1 consulta na auditoria.\n")

# ---- 3. mostrar e conferir
with Session(motor) as sessao:
    print(f"Livro de atos — {CADEIA}")
    for ev in sessao.scalars(select(Evento).where(Evento.cadeia_id == CADEIA)
                             .order_by(Evento.sequencia_cadeia)):
        print(f"  #{ev.sequencia_cadeia} {ev.tipo_evento:<22} ({ev.codigo_evento})  "
              f"por {ev.ator_tipo} {ev.ator_id}  pedido {ev.comando_id[:8]}…, ato {ev.ordem_no_comando}  "
              f"lacre {ev.hash[:12]}…")
    print("  Conferência:", verificar_cadeia(sessao, CADEIA)[1])

    segmento = sessao.scalars(select(EventoAuditoria.segmento_id)
                              .order_by(EventoAuditoria.id.desc()).limit(1)).first()
    print(f"\nLivro de auditoria — {segmento}")
    for ev in sessao.scalars(select(EventoAuditoria).where(EventoAuditoria.segmento_id == segmento)
                             .order_by(EventoAuditoria.sequencia_segmento)):
        print(f"  #{ev.sequencia_segmento} {ev.tipo_evento:<22} por {ev.ator_tipo} {ev.ator_id}  "
              f"lacre {ev.hash[:12]}…")
    print("  Conferência:", verificar_segmento(sessao, segmento)[1])

# ---- 4. três fraudes, cada uma desfeita em seguida
print("\nSimulação de fraudes (desfeitas por rollback):")
with Session(motor) as sessao:
    def primeiro_ato():
        return sessao.scalars(select(Evento).where(Evento.cadeia_id == CADEIA,
                                                   Evento.sequencia_cadeia == 1)).one()

    # Fraude 1: troca o autor do ato, direto no banco
    ev = primeiro_ato()
    ev.ator_id = "PESSOA-B"
    print("  Fraude 1 — troca o autor:                      ", verificar_cadeia(sessao, CADEIA)[1])
    sessao.rollback()

    # Fraude 2: troca o autor e reescreve o texto lacrado para combinar
    ev = primeiro_ato()
    ev.ator_id = "PESSOA-B"
    ev.payload_canonico = ev.payload_canonico.replace('"PESSOA-C"', '"PESSOA-B"')
    print("  Fraude 2 — troca autor e texto lacrado:        ", verificar_cadeia(sessao, CADEIA)[1])
    sessao.rollback()

    # Fraude 3: troca autor, texto E recalcula o lacre -> quebra o elo com o ato seguinte
    ev = primeiro_ato()
    ev.ator_id = "PESSOA-B"
    ev.payload_canonico = ev.payload_canonico.replace('"PESSOA-C"', '"PESSOA-B"')
    ev.hash = lacre(ev.payload_canonico)
    print("  Fraude 3 — troca autor, texto e refaz o lacre: ", verificar_cadeia(sessao, CADEIA)[1])
    sessao.rollback()

print("\nNada foi alterado no banco.")
