# Teste de segregação de funções (O-66) no livro de atos novo (DA-26, DA-27). Dados fictícios.
# Registro de teste: REG-0003, na Unidade Norte (fictícia).
# Cada cenário compara o resultado ESPERADO com o OBTIDO.
# Roda uma vez: se o REG-0003 já existir no livro novo, apenas mostra o que está gravado.

from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import Conta, Evento, EventoAuditoria
from app.permissoes import executar_acao, verificar_acao, autor_da_submissao
from app.eventos import verificar_cadeia, verificar_segmento

REG = "REG-0003"
UNID = "UNID-NORTE"

with Session(motor) as sessao:
    ja_existe = sessao.scalars(select(Evento).where(Evento.cadeia_id == REG)).first() is not None

if not ja_existe:
    cenarios = [
        # (rótulo, conta, ação, esperado, comando_id)
        ("Preparo: A submete pela conta A1",            "CONTA-A1", "submeter", True,  "CMD-REG3-01"),
        ("(a) A tenta validar pela OUTRA conta (A2)",   "CONTA-A2", "validar",  False, "CMD-REG3-02"),
        ("(b) A tenta validar pela MESMA conta (A1)",   "CONTA-A1", "validar",  False, "CMD-REG3-03"),
        ("(e) A tenta devolver a própria versão",       "CONTA-A2", "devolver", False, "CMD-REG3-04"),
        ("B analisa a versão de A",                     "CONTA-B1", "analisar", True,  "CMD-REG3-05"),
        ("(c) B valida a versão de A",                  "CONTA-B1", "validar",  True,  "CMD-REG3-06"),
        ("Clique duplo: B repete o mesmo pedido",       "CONTA-B1", "validar",  True,  "CMD-REG3-06"),
    ]
    with Session(motor) as sessao, sessao.begin():   # tudo ou nada
        print(f"=== Cenários de segregação sobre {REG} ===")
        for rotulo, conta, acao, esperado, cmd in cenarios:
            obtido, motivo, repetido = executar_acao(sessao, conta, REG, UNID, acao, {"versao": 1}, cmd)
            selo = "✔" if obtido == esperado else "✘ FALHOU"
            extra = "  [pedido repetido: nada gravado]" if repetido else ""
            print(f"{selo} {rotulo:<44} -> {'PERMITIDO' if obtido else 'NEGADO'} ({motivo}){extra}")

    # (f) A conta A1 é desativada depois da submissão: a autoria continua sendo da Pessoa A.
    #     Feito numa transação desfeita no final, para não alterar os dados de teste.
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
    print(f"\n=== Livro de atos do {REG} ===")
    for ev in sessao.scalars(select(Evento).where(Evento.cadeia_id == REG)
                             .order_by(Evento.sequencia_cadeia)):
        print(f"#{ev.sequencia_cadeia} {ev.tipo_evento:<16} ({ev.codigo_evento:<3}) por {ev.ator_id} "
              f"(conta {ev.conteudo.get('conta_id')}), pedido {ev.comando_id}")
    print("Conferência:", verificar_cadeia(sessao, REG)[1])

    print("\n=== Livro de auditoria: tentativas negadas ===")
    for ev in sessao.scalars(select(EventoAuditoria)
                             .where(EventoAuditoria.tipo_evento == "tentativa_negada")
                             .order_by(EventoAuditoria.id)):
        c = ev.conteudo
        print(f"{ev.segmento_id} #{ev.sequencia_segmento}: {ev.ator_id} via {c['conta_id']} tentou "
              f"'{c['acao_tentada']}' em {c['objeto']} -> {c['motivo']}")
        segmento = ev.segmento_id
    print("Conferência:", verificar_segmento(sessao, segmento)[1])
