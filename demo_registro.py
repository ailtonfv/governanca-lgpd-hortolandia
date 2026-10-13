# Demonstração do ato G1 — Criar Registro. Somente dados fictícios.
#   1. PESSOA-A (elaboradora na Unidade Norte) cria um Registro: nasce com ciclo 1 e FORM 1;
#   2. PESSOA-B (sem papel de elaborador) tenta criar outro: negado e registrado na auditoria;
#   3. clique duplo: o pedido 1 é repetido e nada novo é gravado.
# Grava uma vez só: se o pedido CMD-G1-01 já existir, apenas mostra.

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import Comando, Registro, Ciclo, Instrumento
from app.workflow import criar_registro
from app.eventos import verificar_cadeia

with Session(motor) as sessao:
    ja_existe = sessao.get(Comando, "CMD-G1-01") is not None

if not ja_existe:
    with Session(motor) as sessao, sessao.begin():   # tudo ou nada
        reg, motivo = criar_registro(sessao, "CONTA-A1", "UNID-NORTE", "servico",
                                     "Serviço fictício de demonstração", "CMD-G1-01")
        print(f"{'✔' if reg else '✘ FALHOU'} PESSOA-A cria Registro       -> {motivo}: {reg.codigo_lgpd if reg else '-'}")

        reg2, motivo2 = criar_registro(sessao, "CONTA-B1", "UNID-NORTE", "servico",
                                       "Tentativa sem papel", "CMD-G1-02")
        print(f"{'✔' if reg2 is None else '✘ FALHOU'} PESSOA-B tenta criar (sem papel) -> NEGADO ({motivo2})")

        reg3, motivo3 = criar_registro(sessao, "CONTA-A1", "UNID-NORTE", "servico",
                                       "Serviço fictício de demonstração", "CMD-G1-01")
        ok = reg3 is not None and reg3.id == reg.id
        print(f"{'✔' if ok else '✘ FALHOU'} Clique duplo no pedido 1     -> {motivo3}: mesmo Registro {reg3.codigo_lgpd}")
else:
    print("A demonstração já foi executada. Veja o que está gravado.")

with Session(motor) as sessao:
    for reg in sessao.scalars(select(Registro).order_by(Registro.codigo_lgpd)):
        print(f"\nRegistro {reg.codigo_lgpd} — {reg.titulo_objeto}")
        print(f"  tipo: {reg.tipo_objeto} · unidade: {reg.unidade_principal_atual_id} · "
              f"criado por: {reg.criado_por} · estado: {reg.estado_atual} · ciclo atual: {reg.ciclo_atual}")
        for c in sessao.scalars(select(Ciclo).where(Ciclo.registro_id == reg.id)):
            print(f"  ciclo {c.numero}: {c.situacao} (aberto pelo evento nº {c.evento_inicio_id})")
        for i in sessao.scalars(select(Instrumento).where(Instrumento.registro_id == reg.id)):
            print(f"  {i.tipo_instrumento}: {i.estado_instrumento}")
        print("  Livro de atos:", verificar_cadeia(sessao, reg.codigo_lgpd)[1])
