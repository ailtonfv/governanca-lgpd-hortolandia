# Catálogo FICTÍCIO de canais e a relação "atendido por" (DA-36, item 6).
# Pode ser rodado mais de uma vez: só acrescenta o que ainda não existe.

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import Canal, ServicoCanal, ObjetoCatalogo

CANAIS = [
    ("CNL-001", "Balcão de atendimento (fictício)"),
    ("CNL-002", "Portal da Prefeitura (fictício)"),
    ("CNL-003", "Telefone (fictício)"),
]

# (serviço, canal): o serviço é atendido pelo canal
ATENDIMENTOS = [
    ("OBJ-SRV-001", "CNL-001"),   # 2ª via do IPTU — balcão
    ("OBJ-SRV-001", "CNL-002"),   # 2ª via do IPTU — portal
    ("OBJ-SRV-002", "CNL-001"),   # Certidão de débitos — balcão
]

with Session(motor) as sessao, sessao.begin():
    novos_canais = 0
    for cid, nome in CANAIS:
        if sessao.get(Canal, cid) is None:
            sessao.add(Canal(id=cid, nome_canonico=nome))
            novos_canais += 1
    sessao.flush()

    novas_ligacoes = 0
    for servico_id, canal_id in ATENDIMENTOS:
        servico = sessao.get(ObjetoCatalogo, servico_id)
        if servico is None or servico.tipo_objeto != "servico":
            print(f"  aviso: {servico_id} não é um serviço do catálogo operacional; ligação ignorada")
            continue
        existe = sessao.scalars(select(ServicoCanal).where(
            ServicoCanal.servico_id == servico_id, ServicoCanal.canal_id == canal_id,
            ServicoCanal.vigente_ate.is_(None))).first()
        if existe is None:
            sessao.add(ServicoCanal(servico_id=servico_id, canal_id=canal_id))
            novas_ligacoes += 1

    # o balcão, se tiver sido cadastrado antes como objeto do catálogo operacional, é desativado (nunca apagado)
    antigo = sessao.get(ObjetoCatalogo, "OBJ-CNL-001")
    if antigo is not None and antigo.ativo:
        antigo.ativo = False
        print("  OBJ-CNL-001 (balcão no catálogo operacional) desativado: agora é o canal CNL-001.")

print(f"Canais novos: {novos_canais}. Ligações novas: {novas_ligacoes}.\n")

with Session(motor) as sessao:
    for canal in sessao.scalars(select(Canal).order_by(Canal.id)):
        servicos = sessao.scalars(
            select(ObjetoCatalogo.nome_canonico)
            .join(ServicoCanal, ServicoCanal.servico_id == ObjetoCatalogo.id)
            .where(ServicoCanal.canal_id == canal.id, ServicoCanal.vigente_ate.is_(None))
            .order_by(ObjetoCatalogo.nome_canonico)).all()
        lista = "; ".join(servicos) if servicos else "(nenhum serviço ainda)"
        print(f"  🚪 {canal.id} {canal.nome_canonico}\n       atende: {lista}")
