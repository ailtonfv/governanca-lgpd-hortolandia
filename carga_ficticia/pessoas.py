# Carga FICTÍCIA: pessoas, contas, unidades e designações de papéis (SAD 03; O-66; D2).
# Nenhum dado pessoal real, CPF, matrícula ou senha.

from sqlalchemy import select
from app.modelos import Pessoa, Conta, Unidade, Designacao

PESSOAS = [
    # (pessoa,     nome fictício,                 contas)
    ("PESSOA-A", "Servidor Alfa (fictício)",      ["CONTA-A1", "CONTA-A2"]),  # duas contas: teste de segregação
    ("PESSOA-B", "Servidor Beta (fictício)",      ["CONTA-B1"]),
    ("PESSOA-C", "Servidor Gama (fictício)",      ["CONTA-C1"]),
    ("PESSOA-D", "Curador do catálogo (fictício)", ["CONTA-D1"]),
    ("PESSOA-E", "Encarregado de Dados (fictício)", ["CONTA-E1"]),
]

UNIDADES = [
    ("UNID-NORTE", "Unidade Norte (fictícia)"),
    ("UNID-SUL", "Unidade Sul (fictícia)"),
    ("UNID-GOV", "Governança de proteção de dados (fictícia)"),
]

DESIGNACOES = [
    # A acumula elaborador e validador: é ela que tenta validar o próprio trabalho
    ("PESSOA-A", "UNID-NORTE", "elaborador"),
    ("PESSOA-A", "UNID-NORTE", "validador"),
    # B analisa e valida o trabalho dos outros
    ("PESSOA-B", "UNID-NORTE", "analista"),
    ("PESSOA-B", "UNID-NORTE", "validador"),
    # C elabora em outra unidade
    ("PESSOA-C", "UNID-SUL", "elaborador"),
    # D cuida do catálogo; E é a governança de proteção de dados (D2)
    ("PESSOA-D", "UNID-GOV", "curador"),
    ("PESSOA-E", "UNID-GOV", "governanca_protecao_dados"),
]


def semear(sessao):
    """Acrescenta o que ainda não existe. Devolve quantos itens novos foram criados."""
    novos = 0
    for pid, nome, contas in PESSOAS:
        if sessao.get(Pessoa, pid) is None:
            sessao.add(Pessoa(id=pid, nome=nome))
            novos += 1
        sessao.flush()
        for cid in contas:
            if sessao.get(Conta, cid) is None:
                sessao.add(Conta(id=cid, pessoa_id=pid))
                novos += 1
    for uid, nome in UNIDADES:
        if sessao.get(Unidade, uid) is None:
            sessao.add(Unidade(id=uid, nome=nome))
            novos += 1
    sessao.flush()
    for pid, uid, papel in DESIGNACOES:
        existe = sessao.scalars(select(Designacao).where(
            Designacao.pessoa_id == pid, Designacao.unidade_id == uid, Designacao.papel == papel)).first()
        if existe is None:
            sessao.add(Designacao(pessoa_id=pid, unidade_id=uid, papel=papel))
            novos += 1
    sessao.flush()
    return novos
