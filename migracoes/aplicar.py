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
from migracoes.rascunho_versoes import aplicar as migracao_0002

MIGRACOES = [
    # (número, nome, função que recebe a sessão)
    (2, "rascunho e versões do Instrumento (M1a: I1 a I3)", migracao_0002),
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
