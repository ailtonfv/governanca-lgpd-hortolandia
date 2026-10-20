# Carga FICTÍCIA: pessoas, contas, unidades e designações de papéis (SAD 03; O-66; D2).
# Nenhum dado pessoal real, CPF, matrícula ou senha.

from sqlalchemy import select
from app.modelos import Pessoa, Conta, Unidade, Designacao

PESSOAS = [
    # (pessoa,     matrícula fictícia, nome fictício,                   contas técnicas)
    ("PESSOA-A", "MAT-FICT-0001", "Servidor Alfa (fictício)",        ["CONTA-A1", "CONTA-A2"]),  # conta extra: teste de segregação
    ("PESSOA-B", "MAT-FICT-0002", "Servidor Beta (fictício)",        ["CONTA-B1"]),
    ("PESSOA-C", "MAT-FICT-0003", "Servidor Gama (fictício)",        ["CONTA-C1"]),
    ("PESSOA-D", "MAT-FICT-0004", "Curador do catálogo (fictício)",  ["CONTA-D1"]),
    ("PESSOA-E", "MAT-FICT-0005", "Encarregado de Dados (fictício)", ["CONTA-E1"]),
    ("PESSOA-F", "MAT-FICT-0006", "Servidor Delta (fictício)",       ["CONTA-F1"]),
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
    ("PESSOA-A", "UNID-NORTE", "agente_pendencia"),
    # B analisa e valida o trabalho dos outros
    ("PESSOA-B", "UNID-NORTE", "analista"),
    ("PESSOA-B", "UNID-NORTE", "validador"),
    ("PESSOA-B", "UNID-NORTE", "concluidor"),
    ("PESSOA-F", "UNID-NORTE", "analista"),
    # C elabora em outra unidade
    ("PESSOA-C", "UNID-SUL", "elaborador"),
    ("PESSOA-C", "UNID-SUL", "agente_pendencia"),
    # D cuida do catálogo; E é a governança de proteção de dados (D2)
    ("PESSOA-D", "UNID-GOV", "curador"),
    ("PESSOA-E", "UNID-GOV", "governanca_protecao_dados"),
]


def semear(sessao):
    """Acrescenta o que ainda não existe. Devolve quantos itens novos foram criados."""
    novos = 0
    for pid, matricula, nome, contas in PESSOAS:
        if sessao.get(Pessoa, pid) is None:
            sessao.add(Pessoa(id=pid, matricula=matricula, nome=nome))
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
