# Catálogo operacional FICTÍCIO: serviços, processos e atividades (O-80, DA-36).
# Os canais ficam em catálogo próprio: ver semear_canais.py.
# O identificador (id) é o que define a equivalência; o nome é só para leitura.
# Pode ser rodado mais de uma vez: só acrescenta o que ainda não existe.

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import ObjetoCatalogo

OBJETOS = [
    # (id canônico,   tipo,        nome canônico)
    ("OBJ-SRV-001", "servico",   "2ª via do IPTU (fictício)"),
    ("OBJ-SRV-002", "servico",   "Certidão de débitos (fictício)"),
    ("OBJ-PRC-001", "processo",  "Lançamento do IPTU (fictício)"),
    ("OBJ-ATV-001", "atividade", "Cálculo do valor venal (fictício)"),
    ("OBJ-ATV-002", "atividade", "Emissão dos carnês (fictício)"),
    ("OBJ-SRV-010", "servico",   "Atendimento ao contribuinte (fictício)"),   # mesmo nome,
    ("OBJ-PRC-010", "processo",  "Atendimento ao contribuinte (fictício)"),   # tipo diferente
    ("OBJ-SRV-900", "servico",   "Serviço fictício de demonstração"),
    ("OBJ-SRV-901", "servico",   "Outro serviço fictício de demonstração"),
]

with Session(motor) as sessao, sessao.begin():
    novos = 0
    for oid, tipo, nome in OBJETOS:
        if sessao.get(ObjetoCatalogo, oid) is None:
            sessao.add(ObjetoCatalogo(id=oid, tipo_objeto=tipo, nome_canonico=nome))
            novos += 1
print(f"Catálogo fictício: {novos} objeto(s) novo(s).\n")

with Session(motor) as sessao:
    for o in sessao.scalars(select(ObjetoCatalogo).order_by(ObjetoCatalogo.id)):
        print(f"  {o.id:<12} {o.tipo_objeto:<10} {o.nome_canonico}")
