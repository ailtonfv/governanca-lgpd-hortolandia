# Demonstração do ato G1 — Criar Registro (Etapa 2d). Somente dados fictícios.
# Uso: python -m demonstracoes.demo_registro
#   1. PESSOA-A cria um Registro do Cadastro imobiliário em CTX-TRIB-01;
#   2. PESSOA-A repete o MESMO pedido (clique duplo): recebe o resultado original;
#   3. PESSOA-C, de outra unidade, tenta criar o mesmo objeto no mesmo contexto: bloqueada,
#      e vê o que pode fazer;
#   4. PESSOA-A pede o mesmo objeto em CTX-TRIB-03: advertência de família.
# Grava uma vez só: se o pedido CMD-DEMO-01 já existir, apenas mostra o que está gravado.

import json
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import Comando, Registro, RegistroObjeto
from app.workflow import criar_registro
from app.eventos import verificar_cadeia


def pedido(cmd, conta, unidade, contexto, titulo, **extra):
    with Session(motor, expire_on_commit=False) as s, s.begin():
        return criar_registro(s, comando_id=cmd, conta_id=conta, unidade_id=unidade, contexto_id=contexto,
                              titulo_objeto=titulo, objeto_principal_id="OBJ-ATV-020", **extra)


def mostrar(rotulo, r):
    situacao = f"CRIADO {r['codigo_lgpd']}" if r["permitido"] else "NEGADO"
    print(f"\n{rotulo}\n  -> {situacao} · {r['motivo']} · reexecutado: {r['reexecutado']}")
    for c in r.get("conflitos", []):
        a = c["acoes"]
        print(f"     conflito: {c['registro_existente']} ({c['estado']}) · possíveis: {a['possiveis'] or '—'}"
              f" · solicitáveis: {a['solicitaveis'] or '—'}")
        for d in a["dependem_de_competencia"]:
            print(f"     depende de competência: {d['acao']} — {d['competencia']}")
    if r.get("advertencia"):
        print(f"     advertência (família {r['advertencia']['familia']}): {r['advertencia']['mensagem']}")


with Session(motor) as s:
    ja_existe = s.get(Comando, "CMD-DEMO-01") is not None

if not ja_existe:
    mostrar("1. PESSOA-A cria o Registro (CTX-TRIB-01)",
            pedido("CMD-DEMO-01", "CONTA-A1", "UNID-NORTE", "CTX-TRIB-01", "Cadastro imobiliário — gestão tributária"))
    mostrar("2. PESSOA-A repete o mesmo pedido (clique duplo)",
            pedido("CMD-DEMO-01", "CONTA-A1", "UNID-NORTE", "CTX-TRIB-01", "Cadastro imobiliário — gestão tributária"))
    mostrar("3. PESSOA-C (Unidade Sul) tenta o mesmo objeto no mesmo contexto",
            pedido("CMD-DEMO-02", "CONTA-C1", "UNID-SUL", "CTX-TRIB-01", "Cadastro imobiliário"))
    mostrar("4. PESSOA-A pede o mesmo objeto em CTX-TRIB-03, sem justificativa",
            pedido("CMD-DEMO-03", "CONTA-A1", "UNID-NORTE", "CTX-TRIB-03", "Cadastro imobiliário — cobrança"))
else:
    print("A demonstração já foi executada. Veja o que está gravado.")

with Session(motor) as s:
    print("\n=== Registros ===")
    for r in s.scalars(select(Registro).order_by(Registro.ano_codigo, Registro.numero_codigo)):
        objetos = ", ".join(f"{v.objeto_id} ({v.papel})" for v in
                            s.scalars(select(RegistroObjeto).where(RegistroObjeto.registro_id == r.id)))
        print(f"{r.codigo_lgpd} · {r.contexto_atuacao_id} · {r.estado_atual} · {objetos}")
        print(f"   livro de atos: {verificar_cadeia(s, r.codigo_lgpd)[1]}")
