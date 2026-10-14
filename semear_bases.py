# Catálogo FICTÍCIO de bases e conjuntos de dados e a relação "utiliza" (DA-38, item 7).
# A base, enquanto ativo informacional, NÃO é assunto de Registro: as atividades e os
# processos que a criam, mantêm ou utilizam é que podem ser.
# Requer o catálogo operacional (python semear_catalogo.py).
# Pode ser rodado mais de uma vez: só acrescenta o que ainda não existe.

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import BaseDados, ObjetoBase, ObjetoCatalogo

BASES = [
    # (id,       nome,                                         suporte)
    ("BAS-001", "Cadastro imobiliário (fictício)",            "sistema"),
    ("BAS-002", "Cadastro funcional de servidores (fictício)", "banco de dados"),
]

# (objeto, base): o objeto UTILIZA a base
USOS = [
    ("OBJ-ATV-020", "BAS-001"),   # Gerir e manter o Cadastro imobiliário
    ("OBJ-PRC-001", "BAS-001"),   # Lançamento do IPTU
]

with Session(motor) as sessao, sessao.begin():
    novas = novos = 0
    for bid, nome, suporte in BASES:
        if sessao.get(BaseDados, bid) is None:
            sessao.add(BaseDados(id=bid, nome_canonico=nome, suporte=suporte))
            novas += 1
    sessao.flush()
    for oid, bid in USOS:
        objeto = sessao.get(ObjetoCatalogo, oid)
        if objeto is None or objeto.tipo_objeto not in ("atividade", "processo"):
            print(f"  aviso: {oid} não é atividade nem processo do catálogo; ligação ignorada")
            continue
        existe = sessao.scalars(select(ObjetoBase).where(
            ObjetoBase.objeto_id == oid, ObjetoBase.base_id == bid,
            ObjetoBase.vigente_ate.is_(None))).first()
        if existe is None:
            sessao.add(ObjetoBase(objeto_id=oid, base_id=bid))
            novos += 1
print(f"Bases novas: {novas}. Ligações \"utiliza\" novas: {novos}.\n")

with Session(motor) as sessao:
    for b in sessao.scalars(select(BaseDados).order_by(BaseDados.id)):
        usuarios = sessao.scalars(
            select(ObjetoCatalogo.nome_canonico)
            .join(ObjetoBase, ObjetoBase.objeto_id == ObjetoCatalogo.id)
            .where(ObjetoBase.base_id == b.id, ObjetoBase.vigente_ate.is_(None))
            .order_by(ObjetoCatalogo.nome_canonico)).all()
        lista = "; ".join(usuarios) if usuarios else "(nenhum ainda)"
        print(f"  🗄️ {b.id} {b.nome_canonico} [{b.suporte}]\n       utilizada por: {lista}")
