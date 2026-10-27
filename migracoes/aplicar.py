# Aplicador de migrações versionadas (Etapa 2d): python -m migracoes.aplicar
#
# Cada migração tem um número, um nome e uma função. A tabela versao_esquema guarda
# as que já foram aplicadas a ESTE banco; o aplicador roda só as pendentes, em ordem,
# cada uma na sua transação. Rodar de novo não faz nada.
#
# A migração 1 é o esquema inicial (instalacao.criar_tabelas). As seguintes entram nesta lista.
# Histórico: migracoes/historico/ guarda migrações aplicadas a bancos anteriores (ex.: 2c2, na lgpd_poc).

import getpass
from sqlalchemy import select, inspect
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import VersaoEsquema
from migracoes.atribuicao_form1_integral import aplicar as migracao_0011
from migracoes.acao_obrigatoria import aplicar as migracao_0006
from migracoes.analise_instrumento import aplicar as migracao_0004
from migracoes.contrato_form1 import aplicar as migracao_0005
from migracoes.imutabilidade_versao import aplicar as migracao_0003
from migracoes.identidade_agente import aplicar as migracao_0008
from migracoes.catalogo_por_secretaria import aplicar as migracao_0009
from migracoes.contextos_por_objeto import aplicar as migracao_0010
from migracoes.pendencia import aplicar as migracao_0007
from migracoes.rascunho_versoes import aplicar as migracao_0002
from migracoes.rascunho_form1_integral import aplicar as migracao_0012
from migracoes.continuidade_apa import aplicar as migracao_0013
from migracoes.objeto_canal import aplicar as migracao_0014
from migracoes.canais_registro import aplicar as migracao_0015
from migracoes.classificacao_canais_form1 import aplicar as migracao_0016

MIGRACOES = [
    # (número, nome, função que recebe a sessão)
    (2, "rascunho e versões do Instrumento (M1a: I1 a I3)", migracao_0002),
    (3, "imutabilidade das versões do Instrumento (M1a: I3)", migracao_0003),
    (4, "análise vigente da versão do Instrumento (M1a: I13 e I14)", migracao_0004),
    (5, "contrato fechado do FORM 1 sintético", migracao_0005),
    (6, "ação obrigatória sintética mínima (M1a: G4 e G6)", migracao_0006),
    (7, "pendência mínima da devolução (M1a: I6 e P1)", migracao_0007),
    (8, "matrícula funcional única do agente da plataforma", migracao_0008),
    (9, "vínculo entre Secretarias e itens do catálogo operacional", migracao_0009),
    (10, "vínculo entre itens do catálogo e contextos de atuação", migracao_0010),
    (11, "atribuição do ARP na preparação do FORM 1 integral", migracao_0011),
    (12, "rascunho do FORM 1 integral — Bloco 1", migracao_0012),
    (13, "continuidade institucional do APA titular e suplentes", migracao_0013),
    (14, "vínculo de canais com serviços, processos e atividades", migracao_0014),
    (15, "retrato dos canais confirmados na abertura do Registro", migracao_0015),
    (16, "classificação dos canais condicionais do FORM 1", migracao_0016),
]


def pendentes(sessao):
    aplicadas = set(sessao.scalars(select(VersaoEsquema.numero)))
    return [m for m in MIGRACOES if m[0] not in aplicadas]


def aplicar():
    if "versao_esquema" not in inspect(motor).get_table_names():
        raise SystemExit("Banco sem controle de versão: rode antes  python -m instalacao.criar_tabelas")
    with Session(motor) as sessao:
        lista = pendentes(sessao)
    if not lista:
        print("Nenhuma migração pendente.")
    for numero, nome, funcao in lista:
        with Session(motor) as sessao, sessao.begin():          # cada migração: tudo ou nada
            funcao(sessao)
            sessao.add(VersaoEsquema(numero=numero, nome=nome, aplicada_por=getpass.getuser()))
        print(f"Migração {numero} aplicada: {nome}")
    with Session(motor) as sessao:
        for v in sessao.scalars(select(VersaoEsquema).order_by(VersaoEsquema.numero)):
            print(f"  versão {v.numero}: {v.nome} (aplicada em {v.aplicada_em:%d/%m/%Y %H:%M}, por {v.aplicada_por})")


if __name__ == "__main__":
    aplicar()
