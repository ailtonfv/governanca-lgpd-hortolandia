# Demonstração: grava eventos fictícios na tabela 'evento' e verifica as correntes.
# Dados 100% fictícios. Pode ser rodado mais de uma vez: só grava se a tabela estiver vazia.

from sqlalchemy import select, update, func
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import Evento
from app.eventos import registrar_evento, verificar_cadeia

# --- 1. Gravar (só se a tabela estiver vazia) ----------------------------
with Session(motor) as sessao:
    quantidade = sessao.scalar(select(func.count()).select_from(Evento))

if quantidade == 0:
    # Sessão nova, com transação "tudo ou nada": ou grava os 4 eventos, ou nenhum
    with Session(motor) as sessao, sessao.begin():
        registrar_evento(sessao, "REG-0001", "submeter", "PESSOA-A", {"versao": 1, "instrumento": "FORM 1"})
        registrar_evento(sessao, "REG-0002", "submeter", "PESSOA-C", {"versao": 1, "instrumento": "FORM 1"})
        registrar_evento(sessao, "REG-0001", "analisar", "PESSOA-B", {"versao": 1})
        registrar_evento(sessao, "REG-0001", "validar",  "PESSOA-B", {"versao": 1})
    print("4 eventos gravados.\n")
else:
    print(f"A tabela já tem {quantidade} eventos; nada novo foi gravado.\n")

# --- 2. Mostrar o livro de atos --------------------------------------------
with Session(motor) as sessao:
    print("=== Livro de atos (tabela evento) ===")
    for ev in sessao.scalars(select(Evento).order_by(Evento.id)):
        print(f"id {ev.id}: {ev.cadeia_id} #{ev.sequencia_cadeia} {ev.codigo_evento:<9} "
              f"por {ev.pessoa_id}  anterior {ev.hash_anterior[:8]}…  lacre {ev.hash[:8]}…")

    print("\n=== Verificação das correntes ===")
    for cadeia in ("REG-0001", "REG-0002"):
        ok, mensagem = verificar_cadeia(sessao, cadeia)
        print(f"{cadeia}: {mensagem}")

# --- 3. Simulação de fraude, DESFEITA no final ----------------------------
# Alguém troca 'analisar' por 'devolver' direto no banco. A alteração é desfeita
# (rollback) logo depois: o livro de atos real nunca é modificado.
with Session(motor) as sessao:
    sessao.execute(
        update(Evento)
        .where(Evento.cadeia_id == "REG-0001", Evento.sequencia_cadeia == 2)
        .values(codigo_evento="devolver")
    )
    sessao.expire_all()
    ok, mensagem = verificar_cadeia(sessao, "REG-0001")
    print(f"\nDurante a simulação de fraude -> REG-0001: {mensagem}")
    sessao.rollback()  # desfaz a fraude

with Session(motor) as sessao:
    ok, mensagem = verificar_cadeia(sessao, "REG-0001")
    print(f"Depois de desfeita a simulação -> REG-0001: {mensagem}")
