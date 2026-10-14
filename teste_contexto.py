# Teste da equivalência por OBJETO + CONTEXTO DE ATUAÇÃO, com papéis, advertência de família
# e alerta de sobreposição (DA-36 e DA-38). Somente dados fictícios.
# Requer: semear_catalogo.py, semear_contextos.py, semear_bases.py e migrar_vinculos_2c2.py.
# Cada cenário compara o resultado ESPERADO com o OBTIDO.
# Roda uma vez: se o pedido CMD-CTX-01 já existir, apenas mostra o que está gravado.

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import Comando, Registro, RegistroObjeto, FamiliaContexto
from app.workflow import criar_registro

CADASTRO = "OBJ-ATV-020"          # Gerir e manter o Cadastro imobiliário (fictício)


def mostrar(selo_ok, rotulo, registro, motivo, detalhes):
    selo = "✔" if selo_ok else "✘ FALHOU"
    resultado = f"CRIADO {registro.codigo_lgpd} ({motivo})" if registro else f"NEGADO ({motivo})"
    print(f"{selo} {rotulo:<52} -> {resultado}")
    d = detalhes or {}
    if d.get("registro_existente"):
        print(f"      ↳ existente: {d['registro_existente']} · {d['objeto']} · {d['contexto']} · "
              f"estado {d['estado']} · ações: {', '.join(d['acoes_possiveis'])}")
    adv = d.get("advertencia") or (d if d.get("familia") else None)
    if adv:
        onde = "; ".join(f"{o['registro_existente']} em {o['contexto_existente']}" for o in adv["ocorrencias"])
        print(f"      ↳ ⚠️ advertência (família {adv['familia']}): já é assunto de {onde}")
        if adv.get("justificativa"):
            print(f"      ↳ justificativa: {adv['justificativa']}")
    for a in d.get("alertas") or []:
        print(f"      ↳ 🔔 alerta: {a['objeto_relacionado']} ({a['registro']}, {a['contexto']}) {a['motivo']}")


def pedido(objetos, titulo, contexto, cmd, **extra):
    """Um pedido numa transação própria (expire_on_commit=False: o resultado continua legível depois)."""
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return criar_registro(sessao, "CONTA-A1", "UNID-NORTE", objetos, titulo, contexto,
                              comando_id=cmd, **extra)


with Session(motor) as sessao:
    ja_existe = sessao.get(Comando, "CMD-CTX-01") is not None

if not ja_existe:
    print("=== Objeto + contexto de atuação (DA-38) ===")

    r, m, d = pedido([CADASTRO], "Cadastro imobiliário — gestão tributária", "CTX-TRIB-01", "CMD-CTX-01")
    mostrar(r is not None and d["alertas"], "(1) Cadastro em TRIB-01 (com alerta: mesma base)", r, m, d)

    r, m, d = pedido([CADASTRO], "Cadastro imobiliário (outro título)", "CTX-TRIB-01", "CMD-CTX-02")
    mostrar(r is None and "neste contexto" in m, "(2) de novo em TRIB-01 -> bloqueado", r, m, d)

    r, m, d = pedido([CADASTRO], "Cadastro imobiliário — planejamento", "CTX-URB-01", "CMD-CTX-03")
    mostrar(r is not None and d["advertencia"] is None, "(3) em URB-01: outra família, sem advertência", r, m, d)

    r, m, d = pedido([CADASTRO], "Cadastro imobiliário — cobrança", "CTX-TRIB-03", "CMD-CTX-04")
    mostrar(r is None and "justificativa" in m, "(4) em TRIB-03 sem justificativa -> pede", r, m, d)

    r, m, d = pedido([CADASTRO], "Cadastro imobiliário — cobrança", "CTX-TRIB-03", "CMD-CTX-05",
                     justificativa="Tratamento próprio da cobrança, com operador e base de envio distintos (fictício)")
    mostrar(r is not None and m == "criado com justificativa", "(5) em TRIB-03 com justificativa", r, m, d)

    r, m, d = pedido(["OBJ-SRV-901"], "Serviço com citação", "CTX-ATD-01", "CMD-CTX-06",
                     citados={"OBJ-SRV-001": "RELACIONADO"})
    mostrar(r is not None, "(6) citar objeto já ocupado (RELACIONADO) não trava", r, m, d)

    r, m, d = pedido(["OBJ-ATV-001"], "Contexto inventado", "CTX-INVENTADO", "CMD-CTX-07")
    mostrar(r is None and "contexto" in m, "(7) contexto fora do catálogo -> negado", r, m, d)

    r, m, d = pedido([CADASTRO], "Cadastro imobiliário — gestão tributária", "CTX-TRIB-01", "CMD-CTX-01")
    mostrar(r is not None and m == "pedido repetido", "(8) repetição do pedido CMD-CTX-01", r, m, d)

    # (9) família mutuamente exclusiva — configuração experimental, DESFEITA ao final (rollback)
    with Session(motor) as sessao:
        sessao.begin()
        sessao.get(FamiliaContexto, "URB").mutuamente_exclusiva = True
        sessao.flush()
        r, m, d = criar_registro(sessao, "CONTA-A1", "UNID-NORTE", [CADASTRO], "Regularização",
                                 "CTX-URB-03", comando_id="CMD-CTX-09-TESTE")
        mostrar(r is None and "exclusiva" in m, "(9) família exclusiva -> bloqueia (desfeito)", r, m, d)
        sessao.rollback()

    # (10) a trava do PRÓPRIO BANCO, sem passar pelas barreiras do código (desfeito ao final)
    with Session(motor) as sessao:
        sessao.begin()
        existente = sessao.scalars(select(RegistroObjeto).where(
            RegistroObjeto.objeto_id == CADASTRO, RegistroObjeto.contexto_atuacao_id == "CTX-TRIB-01",
            RegistroObjeto.ativo.is_(True))).first()
        outro = sessao.scalars(select(Registro).where(Registro.id != existente.registro_id)).first()
        for rotulo, vinculo in [
            ("(10a) banco recusa mesmo objeto+contexto", RegistroObjeto(registro_id=outro.id,
                objeto_id=CADASTRO, papel="ABRANGIDO", contexto_atuacao_id="CTX-TRIB-01")),
            ("(10b) banco recusa segundo PRINCIPAL", RegistroObjeto(registro_id=existente.registro_id,
                objeto_id="OBJ-ATV-002", papel="PRINCIPAL", contexto_atuacao_id="CTX-TRIB-01")),
        ]:
            try:
                with sessao.begin_nested():
                    sessao.add(vinculo)
                    sessao.flush()
                print(f"✘ FALHOU {rotulo}: o banco aceitou")
            except IntegrityError:
                print(f"✔ {rotulo:<52} -> recusado pelo índice único")
        sessao.rollback()
else:
    print("Os cenários de contexto já foram executados. Veja o que está gravado.")

with Session(motor) as sessao:
    print("\n=== Vínculos ativos: objeto · papel · contexto -> Registro ===")
    for v in sessao.scalars(select(RegistroObjeto).where(RegistroObjeto.ativo.is_(True))
                            .order_by(RegistroObjeto.objeto_id, RegistroObjeto.contexto_atuacao_id)):
        trava = "🔒" if v.papel in ("PRINCIPAL", "ABRANGIDO") else "🔓"
        print(f"  {trava} {v.objeto_id:<12} {v.papel:<11} {v.contexto_atuacao_id:<12} "
              f"-> {sessao.get(Registro, v.registro_id).codigo_lgpd}")
