# Carga da PoC: pessoas, contas e designações FICTÍCIAS; nomes institucionais públicos das
# 18 Secretarias da Administração Direta de Hortolândia, conferidos no portal municipal em
# 19/10/2026. O Hortoprev não integra o recorte. Nenhum dado pessoal real, CPF ou senha.

from datetime import datetime, timezone

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
    ("PESSOA-G", "MAT-FICT-0007", "Servidor Épsilon (fictício)",     ["CONTA-G1", "CONTA-G2"]),
    ("PESSOA-H", "MAT-FICT-0008", "Servidor Zeta (fictício)",        ["CONTA-H1"]),
]

# Cargos de demonstração, sem efeito sobre as permissões.
CARGOS_FICTICIOS = {pid: "Agente administrativo (fictício)" for pid, _, _, _ in PESSOAS}
CARGOS_FICTICIOS.update({"PESSOA-B": "Analista de gestão (fictício)",
                         "PESSOA-E": "Encarregado de dados (fictício)"})

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
    # A é o ponto focal: abre o Registro e também pode preencher o FORM 1
    ("PESSOA-A", "UNID-NORTE", "responsavel_registro"),
    ("PESSOA-A", "UNID-NORTE", "preenchedor"),
    ("PESSOA-A", "UNID-NORTE", "validador"),
    ("PESSOA-A", "UNID-NORTE", "agente_pendencia"),
    # B analisa e valida o trabalho dos outros
    ("PESSOA-B", "UNID-NORTE", "analista"),
    ("PESSOA-B", "UNID-NORTE", "validador"),
    ("PESSOA-B", "UNID-NORTE", "concluidor"),
    ("PESSOA-F", "UNID-NORTE", "analista"),
    ("PESSOA-F", "UNID-NORTE", "responsavel_registro"),
    # G preenche na unidade Norte; a segunda conta prova segregação por pessoa
    ("PESSOA-G", "UNID-NORTE", "preenchedor"),
    ("PESSOA-G", "UNID-NORTE", "validador"),
    # C demonstra a acumulação abertura + preenchimento; H é outro preenchedor
    ("PESSOA-C", "UNID-SUL", "responsavel_registro"),
    ("PESSOA-C", "UNID-SUL", "preenchedor"),
    ("PESSOA-C", "UNID-SUL", "agente_pendencia"),
    ("PESSOA-H", "UNID-SUL", "preenchedor"),
    ("PESSOA-H", "UNID-SUL", "responsavel_registro"),
    # D cuida do catálogo; E é a governança de proteção de dados (D2)
    ("PESSOA-D", "UNID-GOV", "curador"),
    ("PESSOA-E", "UNID-GOV", "governanca_protecao_dados"),
]

CONFIGURACAO_APA = [
    # pessoa, unidade, condição institucional inicial da massa fictícia
    ("PESSOA-A", "UNID-NORTE", "titular"),
    ("PESSOA-F", "UNID-NORTE", "suplente"),
    ("PESSOA-C", "UNID-SUL", "titular"),
    ("PESSOA-H", "UNID-SUL", "suplente"),
]
INICIO_DESIGNACOES_APA = datetime(2026, 1, 1, tzinfo=timezone.utc)


def semear(sessao):
    """Acrescenta o que ainda não existe. Devolve quantos itens novos foram criados."""
    # A validação acontece antes do primeiro INSERT. Uma carga suspeita não deixa
    # nem mesmo um fragmento no banco e a mensagem nunca repete o valor encontrado.
    validar_identidades(PESSOAS)
    validar_ausencia_de_identificadores(
        "estrutura institucional",
        {
            "secretarias": SECRETARIAS,
            "unidades": UNIDADES,
            "designacoes": DESIGNACOES,
            "configuracao_apa": CONFIGURACAO_APA,
        },
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
    for pid, uid, tipo_apa in CONFIGURACAO_APA:
        designacao = sessao.scalars(select(Designacao).where(
            Designacao.pessoa_id == pid,
            Designacao.unidade_id == uid,
            Designacao.papel == "responsavel_registro",
        )).one()
        if designacao.tipo_apa is None:
            designacao.tipo_apa = tipo_apa
            designacao.vigente_de = INICIO_DESIGNACOES_APA
            designacao.fundamento_administrativo = "designação fictícia inicial da PoC"
            designacao.autorizado_por_id = "PESSOA-E"
    sessao.flush()
    semear_designacao_dpo(sessao)
    return novos


def semear_eta(sessao):
    """Carga adicional do ensaio de reatribuição, somente em banco de teste ou cópia."""
    import re
    banco = sessao.get_bind().url.database or ""
    if not (banco.endswith("_teste") or re.fullmatch(r"lgpd_lote1_[0-9a-f]{12}", banco)):
        raise ValueError("A carga de Eta exige a cópia da vistoria ou o banco de testes.")
    pid = "PESSOA-I"
    if sessao.get(Pessoa, pid) is None:
        sessao.add(Pessoa(id=pid, matricula="MAT-FICT-0009", nome="Servidor Eta (fictício)"))
        sessao.flush()
    if sessao.get(Conta, "CONTA-I1") is None:
        sessao.add(Conta(id="CONTA-I1", pessoa_id=pid))
    habilitacao = select(Designacao).where(Designacao.pessoa_id == pid,
        Designacao.unidade_id == "UNID-NORTE", Designacao.papel == "aal_form2")
    if sessao.scalar(habilitacao) is None:
        sessao.add(Designacao(pessoa_id=pid, unidade_id="UNID-NORTE", papel="aal_form2", ativa=True))
    sessao.flush()


def semear_designacao_dpo(sessao):
    from app.modelos import DesignacaoEncarregado
    if sessao.scalar(select(DesignacaoEncarregado.id).limit(1)) is None:
        sessao.add(DesignacaoEncarregado(pessoa_id="PESSOA-E", ato_tipo="Portaria fictícia",
            ato_numero="DEMO-DPO-01", ato_data=INICIO_DESIGNACOES_APA,
            inicio=INICIO_DESIGNACOES_APA, email_institucional="dpo@example.invalid"))
        sessao.flush()
