# Migração da etapa 2c, parte 2: os vínculos Registro–objeto ganham PAPEL e CONTEXTO DE ATUAÇÃO (DA-38).
#
# Os Registros criados antes (demo e testes, todos fictícios) não tinham essas informações.
# A migração NÃO apaga nem altera eventos: para cada Registro antigo, grava um ATO NOVO no fim
# da sua corrente ("classificar_vinculos"), dizendo qual papel e qual contexto cada objeto recebeu.
# Assim o resumo da tabela continua reconstruível a partir do livro de atos (DA-26, item 5).
#
# Ordem: python criar_tabelas.py -> python semear_contextos.py -> python migrar_vinculos_2c2.py
# Pode ser rodado mais de uma vez: o que já foi migrado não é migrado de novo.

from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import Comando, Registro, RegistroObjeto, ContextoAtuacao
from app.eventos import registrar_evento, verificar_cadeia

# Contexto atribuído aos Registros antigos, pelo objeto principal (todos são fictícios e tributários)
CONTEXTO_POR_PRINCIPAL = {"OBJ-PRC-001": "CTX-TRIB-02"}   # Lançamento -> Lançamento tributário
CONTEXTO_PADRAO = "CTX-TRIB-03"                            # demais -> Arrecadação e cobrança tributária

colunas = {c["name"] for c in inspect(motor).get_columns("registro_objeto")}

with Session(motor) as sessao, sessao.begin():          # tudo ou nada
    if sessao.get(ContextoAtuacao, CONTEXTO_PADRAO) is None:
        raise SystemExit("Rode antes: python semear_contextos.py")

    # 1. novas colunas (ainda sem obrigatoriedade, porque as linhas antigas estão vazias)
    if "papel" not in colunas:
        sessao.execute(text("ALTER TABLE registro_objeto ADD COLUMN papel VARCHAR(20)"))
        sessao.execute(text("ALTER TABLE registro_objeto ADD COLUMN contexto_atuacao_id VARCHAR(20) "
                            "REFERENCES contexto_atuacao(id)"))
        print("Colunas papel e contexto_atuacao_id acrescentadas.")

    # 2. cada Registro antigo: um ato novo na sua corrente, e só então o resumo é preenchido
    pendentes = sessao.scalars(select(RegistroObjeto).where(RegistroObjeto.papel.is_(None))
                               .order_by(RegistroObjeto.registro_id, RegistroObjeto.id)).all()
    por_registro = {}
    for v in pendentes:
        por_registro.setdefault(v.registro_id, []).append(v)

    for registro, vinculos in sorted(((sessao.get(Registro, rid), vs) for rid, vs in por_registro.items()),
                                     key=lambda par: par[0].codigo_lgpd):
        contexto = CONTEXTO_POR_PRINCIPAL.get(vinculos[0].objeto_id, CONTEXTO_PADRAO)
        classificacao = [{"id": v.objeto_id, "papel": "PRINCIPAL" if n == 0 else "ABRANGIDO"}
                         for n, v in enumerate(vinculos)]
        comando = Comando(id=f"CMD-MIG-2C2-{registro.codigo_lgpd}", tipo="classificar_vinculos",
                          ator_tipo="sistema", ator_id="MIGRACAO-2C2")
        sessao.add(comando)
        sessao.flush()
        evento = registrar_evento(
            sessao, comando, "registro", registro.codigo_lgpd, "classificar_vinculos",
            {"objetos": classificacao, "contexto_atuacao": contexto,
             "motivo": "migração da etapa 2c: vínculos anteriores à DA-38 (papel e contexto de atuação)"},
            registro_id=registro.id, versao_esquema_evento=2)
        for v, c in zip(vinculos, classificacao):
            v.papel, v.contexto_atuacao_id = c["papel"], contexto
        registro.sequencia_atual = evento.sequencia_cadeia
        comando.resultado = {"permitido": True, "motivo": "migrado", "registro_id": registro.id}
        sessao.flush()
        print(f"  {registro.codigo_lgpd}: {', '.join(c['id'] + ' ' + c['papel'] for c in classificacao)}"
              f" · {contexto} · ato nº {evento.sequencia_cadeia}")

    # 3. agora as colunas passam a ser obrigatórias, e a trava antiga dá lugar às novas
    sessao.execute(text("ALTER TABLE registro_objeto ALTER COLUMN papel SET NOT NULL"))
    sessao.execute(text("ALTER TABLE registro_objeto ALTER COLUMN contexto_atuacao_id SET NOT NULL"))
    sessao.execute(text("DROP INDEX IF EXISTS uq_objeto_em_um_registro_ativo"))
    for indice in RegistroObjeto.__table__.indexes:
        indice.create(sessao.connection(), checkfirst=True)

print("\nTravas no banco:")
for i in inspect(motor).get_indexes("registro_objeto"):
    print(f"  {i['name']}")

with Session(motor) as sessao:
    print("\nLivros de atos dos Registros:")
    for r in sessao.scalars(select(Registro).order_by(Registro.codigo_lgpd)):
        print(f"  {r.codigo_lgpd}: {verificar_cadeia(sessao, r.codigo_lgpd)[1]}")
