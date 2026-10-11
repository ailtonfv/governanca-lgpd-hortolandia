# Cria unidades FICTÍCIAS e as designações de papéis para os testes de segregação (O-66).
# Pode ser rodado mais de uma vez: só cria se a tabela 'unidade' estiver vazia.

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import Unidade, Designacao

with Session(motor) as sessao:
    existentes = sessao.scalar(select(func.count()).select_from(Unidade))

if existentes == 0:
    with Session(motor) as sessao, sessao.begin():
        sessao.add_all([
            Unidade(id="UNID-NORTE", nome="Unidade Norte (fictícia)"),
            Unidade(id="UNID-SUL", nome="Unidade Sul (fictícia)"),
        ])
        sessao.flush()
        sessao.add_all([
            # Pessoa A acumula elaborador e validador: é ela que vai tentar validar o próprio trabalho
            Designacao(pessoa_id="PESSOA-A", unidade_id="UNID-NORTE", papel="elaborador"),
            Designacao(pessoa_id="PESSOA-A", unidade_id="UNID-NORTE", papel="validador"),
            # Pessoa B é quem analisa e valida o trabalho dos outros
            Designacao(pessoa_id="PESSOA-B", unidade_id="UNID-NORTE", papel="analista"),
            Designacao(pessoa_id="PESSOA-B", unidade_id="UNID-NORTE", papel="validador"),
            # Pessoa C elabora em outra unidade
            Designacao(pessoa_id="PESSOA-C", unidade_id="UNID-SUL", papel="elaborador"),
        ])
    print("Unidades e designações fictícias criadas.\n")
else:
    print(f"Já existem {existentes} unidades; nada novo foi criado.\n")

with Session(motor) as sessao:
    print("=== Quem pode fazer o quê, e onde ===")
    designacoes = sessao.scalars(
        select(Designacao).order_by(Designacao.pessoa_id, Designacao.unidade_id, Designacao.papel)
    )
    for d in designacoes:
        print(f"{d.pessoa_id:<9} é {d.papel:<10} na {d.unidade.nome}")
