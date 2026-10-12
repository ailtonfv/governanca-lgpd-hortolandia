# Teste de segregação de funções (O-66) sobre um Registro fictício novo: REG-0003.
# Cada cenário compara o resultado ESPERADO com o OBTIDO.
# Roda uma vez: se o REG-0003 já existir, apenas mostra o que está gravado.

from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import Evento, Conta
from app.permissoes import executar_acao, verificar_acao, autor_da_submissao

REG = "REG-0003"
UNID = "UNID-NORTE"

with Session(motor) as sessao:
    ja_existe = sessao.scalars(select(Evento).where(Evento.cadeia_id == REG)).first() is not None

if not ja_existe:
    cenarios = [
        # (rótulo, conta, ação, esperado)
        ("Preparo: A submete pela conta A1",                         "CONTA-A1", "submeter", True),
        ("(a) A tenta validar pela OUTRA conta (A2)",                "CONTA-A2", "validar",  False),
        ("(b) A tenta validar pela MESMA conta (A1)",                "CONTA-A1", "validar",  False),
        ("(e) A tenta devolver a própria versão",                    "CONTA-A2", "devolver", False),
        ("B analisa a versão de A",                                  "CONTA-B1", "analisar", True),
        ("(c) B valida a versão de A",                               "CONTA-B1", "validar",  True),
    ]
    with Session(motor) as sessao, sessao.begin():
        print(f"=== Cenários de segregação sobre {REG} ===")
        for rotulo, conta, acao, esperado in cenarios:
            obtido, motivo = executar_acao(sessao, conta, REG, UNID, acao, {"versao": 1})
            selo = "✔" if obtido == esperado else "✘ FALHOU"
            print(f"{selo} {rotulo:<45} -> {'PERMITIDO' if obtido else 'NEGADO'} ({motivo})")

    # (f) A conta A1 é desativada depois da submissão: a autoria continua sendo da Pessoa A.
    #     Feito dentro de uma transação desfeita no final, para não alterar os dados de teste.
    with Session(motor) as sessao:
        sessao.execute(update(Conta).where(Conta.id == "CONTA-A1").values(ativa=False))
        autor = autor_da_submissao(sessao, REG)
        permitido, motivo, _ = verificar_acao(sessao, "CONTA-A2", REG, UNID, "validar")
        ok = (autor == "PESSOA-A") and not permitido
        print(f"{'✔' if ok else '✘ FALHOU'} (f) A1 desativada: autor continua {autor}; "
              f"A via A2 continua {'PERMITIDO' if permitido else 'NEGADO'}")
        sessao.rollback()
else:
    print(f"O cenário {REG} já foi executado. Veja o resultado gravado abaixo.")

with Session(motor) as sessao:
    print("\n=== Livro de atos do REG-0003 ===")
    for ev in sessao.scalars(select(Evento).where(Evento.cadeia_id == REG).order_by(Evento.sequencia_cadeia)):
        print(f"#{ev.sequencia_cadeia} {ev.codigo_evento:<9} por {ev.pessoa_id} (conta {ev.conteudo.get('conta_id')})")
    print("\n=== Auditoria: tentativas negadas ===")
    for ev in sessao.scalars(select(Evento).where(Evento.codigo_evento == "acesso_negado").order_by(Evento.id)):
        c = ev.conteudo
        print(f"{ev.cadeia_id} #{ev.sequencia_cadeia}: {ev.pessoa_id} via {c['conta_id']} tentou "
              f"'{c['acao_tentada']}' em {c['objeto']} -> {c['motivo']}")
