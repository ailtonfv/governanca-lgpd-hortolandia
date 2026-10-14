# Carga fictícia completa: python -m carga_ficticia
# Pode ser rodada mais de uma vez: só acrescenta o que ainda não existe.

from sqlalchemy.orm import Session
from app.banco import motor
from carga_ficticia import pessoas, catalogos

with Session(motor) as sessao, sessao.begin():
    n1 = pessoas.semear(sessao)
    n2 = catalogos.semear(sessao)
print(f"Pessoas, contas, unidades e designações: {n1} item(ns) novo(s).")
print(f"Catálogos (operacional, canais, contextos, bases e relações): {n2} item(ns) novo(s).")
