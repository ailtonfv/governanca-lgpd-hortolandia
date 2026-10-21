# Carga da PoC: pessoas, contas e designações FICTÍCIAS; nomes institucionais públicos das
# 18 Secretarias da Administração Direta de Hortolândia, conferidos no portal municipal em
# 19/10/2026. O Hortoprev não integra o recorte. Nenhum dado pessoal real, CPF ou senha.

from sqlalchemy import select
from app.modelos import Pessoa, Conta, Unidade, Designacao
from carga_ficticia.seguranca import (validar_ausencia_de_identificadores,
                                      validar_identidades)

PESSOAS = [
    # (pessoa,     matrícula fictícia, nome fictício,                   contas técnicas)
    ("PESSOA-A", "MAT-FICT-0001", "Servidor Alfa (fictício)",        ["CONTA-A1", "CONTA-A2"]),  # conta extra: teste de segregação
    ("PESSOA-B", "MAT-FICT-0002", "Servidor Beta (fictício)",        ["CONTA-B1"]),
    ("PESSOA-C", "MAT-FICT-0003", "Servidor Gama (fictício)",        ["CONTA-C1"]),
    ("PESSOA-D", "MAT-FICT-0004", "Curador do catálogo (fictício)",  ["CONTA-D1"]),
    ("PESSOA-E", "MAT-FICT-0005", "Encarregado de Dados (fictício)", ["CONTA-E1"]),
    ("PESSOA-F", "MAT-FICT-0006", "Servidor Delta (fictício)",       ["CONTA-F1"]),
]

SECRETARIAS = [
    ("SEC-ADM-GP", "Administração e Gestão de Pessoal"),
    ("SEC-AJ", "Assuntos Jurídicos"),
    ("SEC-CULT", "Cultura"),
    ("SEC-DETTI", "Desenvolvimento Econômico, Trabalho, Turismo e Inovação"),
    ("SEC-EDUC", "Educação, Ciência e Tecnologia"),
    ("SEC-ESP", "Esporte e Lazer"),
    ("UNID-SUL", "Finanças"),  # id legado preservado para não alterar Registros e eventos
    ("SEC-GOV", "Governo"),
    ("SEC-HAB", "Habitação"),
    ("SEC-IDS", "Inclusão e Desenvolvimento Social"),
    ("SEC-MA", "Meio Ambiente, Desenvolvimento Sustentável e Assuntos Climáticos"),
    ("SEC-MOB", "Mobilidade Urbana"),
    ("SEC-OBRAS", "Obras"),
    ("UNID-NORTE", "Planejamento Urbano e Gestão Estratégica"),  # id legado preservado
    ("SEC-SAUDE", "Saúde"),
    ("SEC-SEG", "Segurança Pública"),
    ("SEC-SU", "Serviços Urbanos"),
    ("SEC-TI", "Tecnologia e Inovação"),
]

UNIDADES = SECRETARIAS + [
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
    # A validação acontece antes do primeiro INSERT. Uma carga suspeita não deixa
    # nem mesmo um fragmento no banco e a mensagem nunca repete o valor encontrado.
    validar_identidades(PESSOAS)
    validar_ausencia_de_identificadores(
        "estrutura institucional",
        {"secretarias": SECRETARIAS, "unidades": UNIDADES, "designacoes": DESIGNACOES},
    )
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
        unidade = sessao.get(Unidade, uid)
        if unidade is None:
            sessao.add(Unidade(id=uid, nome=nome))
            novos += 1
        elif unidade.nome != nome:
            # Sincroniza somente metadado institucional público; ids e vínculos permanecem.
            unidade.nome = nome
    sessao.flush()
    for pid, uid, papel in DESIGNACOES:
        existe = sessao.scalars(select(Designacao).where(
            Designacao.pessoa_id == pid, Designacao.unidade_id == uid, Designacao.papel == papel)).first()
        if existe is None:
            sessao.add(Designacao(pessoa_id=pid, unidade_id=uid, papel=papel))
            novos += 1
    sessao.flush()
    return novos
