# Cria as pessoas e contas FICTÍCIAS usadas nos testes de segregação (O-66).
# Pessoa A tem duas contas (A1 e A2); Pessoa B e Pessoa C têm uma conta cada.
# Pode ser rodado mais de uma vez: só cria se a tabela 'pessoa' estiver vazia.

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import Pessoa, Conta

with Session(motor) as sessao:
    existentes = sessao.scalar(select(func.count()).select_from(Pessoa))

if existentes == 0:
    with Session(motor) as sessao, sessao.begin():
        a = Pessoa(id="PESSOA-A", nome="Servidor Alfa (fictício)")
        b = Pessoa(id="PESSOA-B", nome="Servidor Beta (fictício)")
        c = Pessoa(id="PESSOA-C", nome="Servidor Gama (fictício)")
        sessao.add_all([a, b, c])
        sessao.add_all([
            Conta(id="CONTA-A1", pessoa=a),
            Conta(id="CONTA-A2", pessoa=a),
            Conta(id="CONTA-B1", pessoa=b),
            Conta(id="CONTA-C1", pessoa=c),
        ])
    print("Pessoas e contas fictícias criadas.\n")
else:
    print(f"Já existem {existentes} pessoas; nada novo foi criado.\n")

with Session(motor) as sessao:
    print("=== Pessoas e suas contas ===")
    for pessoa in sessao.scalars(select(Pessoa).order_by(Pessoa.id)):
        contas = ", ".join(c.id for c in pessoa.contas)
        print(f"{pessoa.id} ({pessoa.nome}): {len(pessoa.contas)} conta(s) -> {contas}")
