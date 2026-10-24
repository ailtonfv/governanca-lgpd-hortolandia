# Camada de domínio: o ciclo de vida do Registro (SAD 04 e SAD 05).
#
# Regra de ouro (DA-26, item 5): cada ato acontece numa transação só.
# O ato (evento), o pedido (comando) e os resumos (projeções) são gravados juntos, ou nada é gravado.
#
# Etapa 2d (revisão do Encarregado, 14/10/2026): pedido idempotente estrito; papéis explícitos;
# um contexto por Registro (D1); advertência de família com três resoluções e transversalidade (D2);
# numeração anual (D4); todos os conflitos listados; recusas do banco tratadas pelo nome.

import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from app.modelos import (AcaoObrigatoria, Conta, Designacao, Registro, Ciclo, Instrumento,
                         ObjetoCatalogo, ObjetoContextoCatalogo, UnidadeObjetoCatalogo,
                         Pendencia, RegistroObjeto, ContextoAtuacao,
                         FamiliaContexto, ObjetoBase, Transversalidade, ContadorRegistro,
                         PAPEIS_ASSUNTO, PAPEIS_CITADOS)
from app.eventos import registrar_evento, registrar_auditoria
from app.permissoes import tem_papel
from app.comandos import (abrir_comando, fechar_comando, nome_da_restricao,
                          ErroDeIntegridadeInesperado)

FUSO_OFICIAL = ZoneInfo("America/Sao_Paulo")
RESTRICAO_EQUIVALENCIA = "uq_objeto_contexto_assunto_ativo"
RESOLUCOES_DE_FAMILIA = ("tratamento_autonomo",)   # decisão do agente responsável; transversalidade vem da governança

MENSAGEM_FAMILIA = ("Este objeto está associado a mais de um contexto da mesma família. "
                    "Corrija o contexto, justifique a autonomia do tratamento ou consulte a governança.")

# O que pode ser feito com um Registro existente, por estado. Competências ainda não definidas
# nos SADs aparecem como tal, e não como ação possível (Etapa 2d, item A5).
ACOES_DO_ESTADO = {
    "em_andamento": [
        ("concluir sem medidas (G5)", "papel concluidor e portões do G5"),
        ("cancelar (G11)", "competência do G11 (SAD 04, seção 7)"),
    ],
    "em_validacao": [("cancelar (G11)", "competência do G11 (SAD 04, seção 7)")],
    "em_execucao": [
        ("concluir após as medidas (G6)", "papel concluidor e portões do G6"),
        ("cancelar (G11)", "competência do G11 (SAD 04, seção 7)"),
    ],
    "suspenso": [("retomar (G8)", "competência do G8 (SAD 04, seção 7)"),
                 ("cancelar (G11)", "competência do G11 (SAD 04, seção 7)")],
    "concluido": [("reabrir (G10)", "competência do G10 (SAD 04, seção 7)"),
                  ("cancelar (G11)", "competência reforçada (DA-37, item 4) — papel a definir")],
}


# ---------------------------------------------------------------- tempo e numeração (D4)

def agora_utc():
    return datetime.now(timezone.utc)


def ano_administrativo(momento):
    """Ano civil no fuso oficial da Prefeitura (D4). 31/12 às 23h em Hortolândia ainda é o ano velho."""
    return momento.astimezone(FUSO_OFICIAL).year


def proximo_numero_do_ano(sessao, ano):
    """Próximo número do ano, atualizado pelo próprio banco na transação do G1 (D4).
    Dois pedidos simultâneos ficam em fila na linha do ano e nunca recebem o mesmo número."""
    comando_sql = (insert(ContadorRegistro).values(ano=ano, ultimo_numero=1)
                   .on_conflict_do_update(index_elements=["ano"],
                                          set_={"ultimo_numero": ContadorRegistro.ultimo_numero + 1})
                   .returning(ContadorRegistro.ultimo_numero))
    return sessao.execute(comando_sql).scalar_one()


# ---------------------------------------------------------------- consultas

def conflitos_de_equivalencia(sessao, objeto_ids, contexto_id):
    """Verificação 1 (DA-38, item 3): TODOS os objetos que já são assunto de Registro não
    cancelado no mesmo contexto — não só o primeiro (Etapa 2d, item A4)."""
    linhas = sessao.execute(
        select(RegistroObjeto, Registro, ObjetoCatalogo)
        .join(Registro, Registro.id == RegistroObjeto.registro_id)
        .join(ObjetoCatalogo, ObjetoCatalogo.id == RegistroObjeto.objeto_id)
        .where(RegistroObjeto.objeto_id.in_(objeto_ids), RegistroObjeto.ativo.is_(True),
               RegistroObjeto.papel.in_(PAPEIS_ASSUNTO),
               RegistroObjeto.contexto_atuacao_id == contexto_id)
        .order_by(RegistroObjeto.objeto_id)
    ).all()
    return [{"objeto": f"{o.id} — {o.nome_canonico}", "registro_existente": r.codigo_lgpd,
             "papel_no_existente": v.papel, "contexto": contexto_id, "estado": r.estado_atual,
             "registro_id": r.id} for v, r, o in linhas]


def ocorrencias_na_familia(sessao, objeto_ids, contexto):
    """Verificação 2 (DA-38, item 6): o objeto já é assunto em OUTRO contexto da MESMA família?"""
    linhas = sessao.execute(
        select(RegistroObjeto, Registro, ContextoAtuacao)
        .join(Registro, Registro.id == RegistroObjeto.registro_id)
        .join(ContextoAtuacao, ContextoAtuacao.id == RegistroObjeto.contexto_atuacao_id)
        .where(RegistroObjeto.objeto_id.in_(objeto_ids), RegistroObjeto.ativo.is_(True),
               RegistroObjeto.papel.in_(PAPEIS_ASSUNTO),
               ContextoAtuacao.familia_id == contexto.familia_id,
               ContextoAtuacao.id != contexto.id)
        .order_by(RegistroObjeto.objeto_id, Registro.codigo_lgpd)
    ).all()
    return [{"objeto": v.objeto_id, "contexto_existente": c.id, "registro_existente": r.codigo_lgpd}
            for v, r, c in linhas]


def transversalidade_vigente(sessao, objeto_id, familia_id):
    """Declaração vigente de transversalidade para objeto + família (D2), ou None."""
    return sessao.scalars(select(Transversalidade).where(
        Transversalidade.objeto_id == objeto_id, Transversalidade.familia_id == familia_id,
        Transversalidade.vigente_ate.is_(None))).first()


def alertas_estruturais(sessao, objeto_ids):
    """Verificação 3, momento 1 — triagem ESTRUTURAL no G1 (Etapa 2d, item A9): outros objetos que
    usam a mesma base de dados e já são assunto de algum Registro. Não bloqueia.
    Um alerta por (objeto relacionado, Registro, contexto, tipo do sinal), com as bases agregadas.
    A semelhança MATERIAL (finalidade, titulares, dados) é verificada na submissão do FORM 1."""
    MinhaBase, OutraBase = ObjetoBase.__table__.alias("minha"), ObjetoBase.__table__.alias("outra")
    linhas = sessao.execute(
        select(OutraBase.c.objeto_id, OutraBase.c.base_id, Registro.codigo_lgpd,
               RegistroObjeto.contexto_atuacao_id)
        .select_from(MinhaBase)
        .join(OutraBase, OutraBase.c.base_id == MinhaBase.c.base_id)
        .join(RegistroObjeto, RegistroObjeto.objeto_id == OutraBase.c.objeto_id)
        .join(Registro, Registro.id == RegistroObjeto.registro_id)
        .where(MinhaBase.c.objeto_id.in_(objeto_ids), MinhaBase.c.vigente_ate.is_(None),
               OutraBase.c.vigente_ate.is_(None), OutraBase.c.objeto_id.not_in(objeto_ids),
               RegistroObjeto.ativo.is_(True), RegistroObjeto.papel.in_(PAPEIS_ASSUNTO))
    ).all()
    agregados = {}
    for objeto, base, codigo, contexto in linhas:
        chave = (objeto, codigo, contexto, "base_comum")
        agregados.setdefault(chave, set()).add(base)
    return [{"tipo_do_sinal": t, "objeto_relacionado": o, "registro": r, "contexto": c,
             "bases": sorted(b)} for (o, r, c, t), b in sorted(agregados.items())]


def acoes_para(sessao, pessoa_id, registro_id):
    """O que ESTA pessoa pode fazer com um Registro existente (Etapa 2d, item A5)."""
    registro = sessao.get(Registro, registro_id)
    designacoes = sessao.scalars(select(Designacao).where(
        Designacao.unidade_id == registro.unidade_principal_atual_id,
        Designacao.ativa.is_(True)).order_by(Designacao.pessoa_id, Designacao.papel)).all()
    tem_vinculo = any(d.pessoa_id == pessoa_id for d in designacoes)
    return {
        "possiveis": ["abrir"] if tem_vinculo else [],
        "solicitaveis": [] if tem_vinculo else ["solicitar acesso"],
        "dependem_de_competencia": [{"acao": a, "competencia": c}
                                    for a, c in ACOES_DO_ESTADO.get(registro.estado_atual, [])],
        "unidade_principal": registro.unidade_principal_atual_id,
        "designacoes_vigentes": [f"{d.pessoa_id} ({d.papel})" for d in designacoes],
    }


# ---------------------------------------------------------------- G1

def criar_registro(sessao, *, comando_id, conta_id, unidade_id, contexto_id, titulo_objeto,
                   objeto_principal_id, objetos_abrangidos_ids=(), objetos_citados=None,
                   resolucao_familia=None, justificativa=None, momento=None):
    """Ato G1 — Criar Registro (SAD 04, seção 7), com a prevenção de duplicidade (DA-36, DA-38, D1, D2).

    Papéis EXPLÍCITOS (nunca pela ordem de uma lista):
      objeto_principal_id      -> PRINCIPAL
      objetos_abrangidos_ids   -> ABRANGIDO
      objetos_citados          -> {"OBJ-...": "APOIO" | "RELACIONADO"}
    contexto_id: UM contexto de atuação para o Registro (D1).
    resolucao_familia / justificativa: resposta do agente responsável a uma advertência de família (D2).
    momento: relógio injetável (os testes não dependem da data do computador).

    Ordem (DA-38, item 9): barreiras -> 1. equivalência -> 2. família -> 3. alerta estrutural -> resultado.
    Devolve o RESULTADO (dicionário). Numa repetição do pedido, o mesmo resultado com reexecutado = True.
    """
    momento = momento or agora_utc()
    citados = dict(objetos_citados or {})
    abrangidos = list(objetos_abrangidos_ids)
    parametros = {"conta_id": conta_id, "unidade_id": unidade_id, "contexto_id": contexto_id,
                  "titulo_objeto": titulo_objeto, "objeto_principal_id": objeto_principal_id,
                  "objetos_abrangidos_ids": abrangidos, "objetos_citados": citados,
                  "resolucao_familia": resolucao_familia, "justificativa": justificativa}

    conta = sessao.get(Conta, conta_id)
    pessoa_id = conta.pessoa_id if conta is not None else None
    ator_tipo, ator_id = ("pessoa", pessoa_id) if pessoa_id else ("desconhecido", conta_id)

    # 0. o pedido (idempotência estrita)
    comando, resposta = abrir_comando(sessao, comando_id, "criar_registro", parametros,
                                      ator_tipo, ator_id, conta_id)
    if resposta is not None:
        return resposta

    def negar(motivo, **detalhes):
        registrar_auditoria(sessao, "tentativa_negada", ator_tipo, ator_id,
                            {"acao_tentada": "criar_registro", "contexto": contexto_id,
                             "objeto_principal": objeto_principal_id, "conta_id": conta_id,
                             "motivo": motivo}, comando_id=comando.id)
        resultado = fechar_comando(comando, dict({"permitido": False, "motivo": motivo}, **detalhes))
        sessao.flush()
        return resultado

    # 1. barreiras de sempre
    assunto = [objeto_principal_id] + abrangidos
    todos = assunto + list(citados)
    if conta is None or not conta.ativa:
        return negar("conta inexistente ou desativada")
    if not objeto_principal_id:
        return negar("o objeto PRINCIPAL é obrigatório")
    if len(set(todos)) != len(todos):
        return negar("o mesmo objeto foi informado em mais de um papel")
    if any(p not in PAPEIS_CITADOS for p in citados.values()):
        return negar("papel inválido para objeto citado (use APOIO ou RELACIONADO)")
    objetos = {oid: sessao.get(ObjetoCatalogo, oid) for oid in todos}
    if any(o is None or not o.ativo for o in objetos.values()):
        return negar("objeto fora do catálogo ou desativado")
    objetos_da_unidade = set(sessao.scalars(
        select(UnidadeObjetoCatalogo.objeto_id).where(
            UnidadeObjetoCatalogo.unidade_id == unidade_id,
            UnidadeObjetoCatalogo.objeto_id.in_(assunto),
            UnidadeObjetoCatalogo.papel == "RESPONSAVEL",
            UnidadeObjetoCatalogo.vigente_ate.is_(None),
        )
    ))
    if objetos_da_unidade != set(assunto):
        return negar("objeto não vinculado à Secretaria responsável no catálogo")
    contexto = sessao.get(ContextoAtuacao, contexto_id) if contexto_id else None
    if contexto is None or not contexto.ativo:
        return negar("contexto de atuação fora do catálogo ou desativado")
    objetos_do_contexto = set(sessao.scalars(
        select(ObjetoContextoCatalogo.objeto_id).where(
            ObjetoContextoCatalogo.objeto_id.in_(assunto),
            ObjetoContextoCatalogo.contexto_id == contexto.id,
            ObjetoContextoCatalogo.vigente_ate.is_(None),
        )
    ))
    if objetos_do_contexto != set(assunto):
        return negar("contexto de atuação não permitido para o item do catálogo")
    if not tem_papel(sessao, pessoa_id, unidade_id, {"responsavel_registro"}):
        return negar("a pessoa não é Agente Público Autorizado responsável pelo Registro nesta unidade")
    if resolucao_familia is not None and resolucao_familia not in RESOLUCOES_DE_FAMILIA:
        return negar("resolução de advertência inválida")

    # 2. verificação 1 — equivalência bloqueadora (todos os conflitos)
    conflitos = conflitos_de_equivalencia(sessao, assunto, contexto.id)
    if conflitos:
        for c in conflitos:
            c["acoes"] = acoes_para(sessao, pessoa_id, c.pop("registro_id"))
        return negar("já existe Registro para objeto(s) deste pedido neste contexto", conflitos=conflitos)

    # 3. verificação 2 — família de contexto (D2)
    advertencia = None
    ocorrencias = ocorrencias_na_familia(sessao, assunto, contexto)
    if ocorrencias:
        familia = sessao.get(FamiliaContexto, contexto.familia_id)
        decisoes, pendentes = {}, []
        for oc in ocorrencias:
            t = transversalidade_vigente(sessao, oc["objeto"], familia.id)
            if t is not None:
                decisoes[oc["objeto"]] = t.id
            else:
                pendentes.append(oc)
        advertencia = {"familia": familia.id, "ocorrencias": ocorrencias, "mensagem": MENSAGEM_FAMILIA}
        if familia.mutuamente_exclusiva:
            return negar(f"família {familia.id} configurada como mutuamente exclusiva", advertencia=advertencia)
        if pendentes:
            if resolucao_familia != "tratamento_autonomo" or not (justificativa or "").strip():
                return negar("advertência de família: corrija o contexto, ou informe "
                             "resolucao_familia='tratamento_autonomo' com justificativa", advertencia=advertencia)
            advertencia["resolucao"] = "tratamento_autonomo"
            advertencia["justificativa"] = justificativa.strip()
        else:
            advertencia["resolucao"] = "objeto_transversal"
        if decisoes:
            advertencia["decisoes_de_transversalidade"] = decisoes

    # 4. verificação 3 — alerta estrutural (não bloqueia)
    alertas = alertas_estruturais(sessao, assunto)

    # 5. cria, dentro de um ponto de salvamento: só a trava de equivalência é interpretada
    papeis = {objeto_principal_id: "PRINCIPAL", **{o: "ABRANGIDO" for o in abrangidos}, **citados}
    try:
        with sessao.begin_nested():
            registro, evento = _nascer_registro(sessao, comando, conta_id, unidade_id, objetos, papeis,
                                                contexto, titulo_objeto, advertencia, alertas, momento)
    except IntegrityError as erro:
        if nome_da_restricao(erro) != RESTRICAO_EQUIVALENCIA:
            raise                                    # defeito: precisa aparecer, não ser mascarado
        conflitos = conflitos_de_equivalencia(sessao, assunto, contexto.id)
        if not conflitos:
            raise ErroDeIntegridadeInesperado("a trava recusou, mas nenhum ocupante foi encontrado") from erro
        for c in conflitos:
            c["acoes"] = acoes_para(sessao, pessoa_id, c.pop("registro_id"))
        return negar("já existe Registro para objeto(s) deste pedido neste contexto "
                     "(barrado pela trava do banco)", conflitos=conflitos)

    motivo = {None: "criado", "tratamento_autonomo": "criado com justificativa",
              "objeto_transversal": "criado — advertência resolvida por transversalidade vigente"}[
        advertencia and advertencia["resolucao"]]
    resultado = fechar_comando(comando, {"permitido": True, "motivo": motivo,
                                         "registro_id": registro.id, "codigo_lgpd": registro.codigo_lgpd,
                                         "evento_g1": evento.sequencia_cadeia,
                                         "advertencia": advertencia, "alertas": alertas})
    sessao.flush()
    return resultado


def _nascer_registro(sessao, comando, conta_id, unidade_id, objetos, papeis, contexto,
                     titulo_objeto, advertencia, alertas, momento):
    """Cria o Registro (com o número do ano), o ciclo 1, o FORM 1, os vínculos e o ato G1."""
    ano = ano_administrativo(momento)
    numero = proximo_numero_do_ano(sessao, ano)
    principal = objetos[next(o for o, p in papeis.items() if p == "PRINCIPAL")]
    registro = Registro(id=str(uuid.uuid4()), codigo_lgpd=f"LGPD-{ano}-{numero:05d}",
                        ano_codigo=ano, numero_codigo=numero, contexto_atuacao_id=contexto.id,
                        tipo_objeto=principal.tipo_objeto, titulo_objeto=titulo_objeto,
                        unidade_principal_atual_id=unidade_id, criado_por=comando.ator_id,
                        ciclo_atual=1, estado_atual="em_andamento", sequencia_atual=0)
    sessao.add(registro)
    sessao.flush()
    ciclo = Ciclo(registro_id=registro.id, numero=1, situacao="ativo")
    sessao.add(ciclo)
    sessao.add(Instrumento(id=str(uuid.uuid4()), registro_id=registro.id,
                           tipo_instrumento="FORM1", estado_instrumento="nao_iniciado"))
    for objeto_id, papel in papeis.items():         # a reserva dos objetos: aqui a trava do banco atua
        sessao.add(RegistroObjeto(registro_id=registro.id, objeto_id=objeto_id, papel=papel,
                                  contexto_atuacao_id=contexto.id if papel in PAPEIS_ASSUNTO else None))
    sessao.flush()

    conteudo = {"objetos": [{"id": o, "papel": p} for o, p in papeis.items()],
                "contexto_atuacao": contexto.id, "titulo_objeto": titulo_objeto,
                "unidade_principal": unidade_id, "conta_id": conta_id}
    if advertencia:
        conteudo["advertencia_familia"] = advertencia
    if alertas:
        conteudo["alertas"] = alertas
    evento = registrar_evento(sessao, comando, "registro", registro.codigo_lgpd, "criar_registro",
                              conteudo, codigo_evento="G1", registro_id=registro.id,
                              ciclo_id=ciclo.id, versao_esquema_evento=2)
    ciclo.evento_inicio_id = evento.id
    registro.sequencia_atual = evento.sequencia_cadeia
    sessao.flush()
    return registro, evento


# ---------------------------------------------------------------- G5

def concluir_registro_sem_medidas(sessao, *, comando_id, conta_id, registro_id,
                                  momento=None):
    """G5 — conclui um Registro validado, sem medidas ou pendências em aberto."""
    momento = momento or agora_utc()
    parametros = {"conta_id": conta_id, "registro_id": registro_id}
    conta = sessao.get(Conta, conta_id)
    pessoa_id = conta.pessoa_id if conta is not None else None
    ator_tipo, ator_id = (("pessoa", pessoa_id) if pessoa_id
                          else ("desconhecido", conta_id))
    comando, resposta = abrir_comando(
        sessao, comando_id, "concluir_registro_sem_medidas", parametros,
        ator_tipo, ator_id, conta_id,
    )
    if resposta is not None:
        return resposta

    def negar(motivo, **detalhes):
        registrar_auditoria(
            sessao, "tentativa_negada", ator_tipo, ator_id,
            {"acao_tentada": "concluir_registro_sem_medidas",
             "registro_id": registro_id, "conta_id": conta_id, "motivo": motivo},
            comando_id=comando.id,
        )
        resultado = fechar_comando(
            comando, dict({"permitido": False, "motivo": motivo}, **detalhes)
        )
        sessao.flush()
        return resultado

    registro = sessao.scalars(
        select(Registro).where(Registro.id == registro_id).with_for_update()
    ).one_or_none()
    if registro is None:
        return negar("Registro inexistente")
    if conta is None or not conta.ativa:
        return negar("conta inexistente ou desativada")
    if not tem_papel(
            sessao, pessoa_id, registro.unidade_principal_atual_id, {"concluidor"}):
        return negar("a pessoa não possui competência formal para concluir nesta unidade")
    if registro.estado_atual != "em_andamento":
        return negar(
            "G5 exige Registro no estado em_andamento",
            estado_registro=registro.estado_atual,
        )

    ciclo = sessao.scalars(
        select(Ciclo).where(
            Ciclo.registro_id == registro.id,
            Ciclo.numero == registro.ciclo_atual,
        ).with_for_update()
    ).one_or_none()
    if ciclo is None or ciclo.situacao != "ativo":
        return negar(
            "o ciclo atual do Registro não está ativo",
            situacao_ciclo=None if ciclo is None else ciclo.situacao,
        )

    instrumentos = sessao.scalars(
        select(Instrumento).where(Instrumento.registro_id == registro.id)
        .order_by(Instrumento.tipo_instrumento, Instrumento.id)
        .with_for_update()
    ).all()
    instrumentos_invalidos = [
        {"instrumento_id": item.id, "tipo": item.tipo_instrumento,
         "estado": item.estado_instrumento}
        for item in instrumentos
        if item.estado_instrumento != "validado" or item.versao_vigente_id is None
    ]
    if not instrumentos or instrumentos_invalidos:
        return negar(
            "G5 exige todos os Instrumentos obrigatórios validados",
            instrumentos_invalidos=instrumentos_invalidos,
        )

    pendencias_abertas = list(sessao.scalars(
        select(Pendencia.id).where(
            Pendencia.registro_id == registro.id,
            Pendencia.estado.not_in(("encerrada", "cancelada")),
        ).order_by(Pendencia.id).with_for_update()
    ))
    if pendencias_abertas:
        return negar(
            "G5 exige todas as pendências encerradas ou canceladas",
            pendencias_abertas=pendencias_abertas,
        )

    acoes_do_ciclo = list(sessao.scalars(
        select(AcaoObrigatoria.id).where(
            AcaoObrigatoria.registro_id == registro.id,
            AcaoObrigatoria.ciclo_id == ciclo.id,
        ).order_by(AcaoObrigatoria.id).with_for_update()
    ))
    if acoes_do_ciclo:
        return negar(
            "G5 é o percurso sem medidas e não admite ação obrigatória no ciclo",
            acoes_obrigatorias=acoes_do_ciclo,
        )

    estado_anterior = registro.estado_atual
    registro.estado_atual = "concluido"
    ciclo.situacao = "concluido"
    evento_g5 = registrar_evento(
        sessao, comando, "registro", registro.codigo_lgpd, "concluir_sem_medidas",
        {"registro_id": registro.id, "ciclo_id": ciclo.id,
         "numero_ciclo": ciclo.numero, "estado_anterior": estado_anterior,
         "estado_atual": "concluido",
         "instrumentos_validados": [item.id for item in instrumentos],
         "pendencias_abertas": [], "acoes_obrigatorias": [],
         "conta_id": conta_id, "concluido_em": momento.isoformat()},
        codigo_evento="G5", registro_id=registro.id, ciclo_id=ciclo.id,
        versao_esquema_evento=2,
    )
    registro.sequencia_atual = evento_g5.sequencia_cadeia
    resultado = fechar_comando(
        comando,
        {"permitido": True, "motivo": "Registro concluído sem medidas",
         "registro_id": registro.id, "codigo_lgpd": registro.codigo_lgpd,
         "ciclo_id": ciclo.id, "estado_registro": "concluido",
         "situacao_ciclo": "concluido",
         "evento_g5": evento_g5.sequencia_cadeia},
    )
    sessao.flush()
    return resultado


def concluir_registro_apos_medidas(sessao, *, comando_id, conta_id, registro_id,
                                   momento=None):
    """G6 — conclui um Registro em execução depois de todas as medidas finalizadas."""
    momento = momento or agora_utc()
    parametros = {"conta_id": conta_id, "registro_id": registro_id}
    conta = sessao.get(Conta, conta_id)
    pessoa_id = conta.pessoa_id if conta is not None else None
    ator_tipo, ator_id = (("pessoa", pessoa_id) if pessoa_id
                          else ("desconhecido", conta_id))
    comando, resposta = abrir_comando(
        sessao, comando_id, "concluir_registro_apos_medidas", parametros,
        ator_tipo, ator_id, conta_id,
    )
    if resposta is not None:
        return resposta

    def negar(motivo, **detalhes):
        registrar_auditoria(
            sessao, "tentativa_negada", ator_tipo, ator_id,
            {"acao_tentada": "concluir_registro_apos_medidas",
             "registro_id": registro_id, "conta_id": conta_id, "motivo": motivo},
            comando_id=comando.id,
        )
        retorno = fechar_comando(
            comando, dict({"permitido": False, "motivo": motivo}, **detalhes)
        )
        sessao.flush()
        return retorno

    registro = sessao.scalars(
        select(Registro).where(Registro.id == registro_id).with_for_update()
    ).one_or_none()
    if registro is None:
        return negar("Registro inexistente")
    if conta is None or not conta.ativa:
        return negar("conta inexistente ou desativada")
    if not tem_papel(
            sessao, pessoa_id, registro.unidade_principal_atual_id, {"concluidor"}):
        return negar("a pessoa não possui competência formal para concluir nesta unidade")
    if registro.estado_atual != "em_execucao":
        return negar(
            "G6 exige Registro no estado em_execucao",
            estado_registro=registro.estado_atual,
        )

    ciclo = sessao.scalars(
        select(Ciclo).where(Ciclo.registro_id == registro.id,
                            Ciclo.numero == registro.ciclo_atual).with_for_update()
    ).one_or_none()
    if ciclo is None or ciclo.situacao != "ativo":
        return negar("o ciclo atual do Registro não está ativo")

    instrumentos = sessao.scalars(
        select(Instrumento).where(Instrumento.registro_id == registro.id)
        .order_by(Instrumento.tipo_instrumento, Instrumento.id).with_for_update()
    ).all()
    if (not instrumentos or any(item.estado_instrumento != "validado"
                                or item.versao_vigente_id is None
                                for item in instrumentos)):
        return negar("G6 exige todos os Instrumentos obrigatórios validados")

    pendencias_abertas = list(sessao.scalars(
        select(Pendencia.id).where(
            Pendencia.registro_id == registro.id,
            Pendencia.estado.not_in(("encerrada", "cancelada")),
        ).order_by(Pendencia.id).with_for_update()
    ))
    if pendencias_abertas:
        return negar("G6 exige todas as pendências encerradas ou canceladas",
                     pendencias_abertas=pendencias_abertas)

    acoes = sessao.scalars(
        select(AcaoObrigatoria).where(
            AcaoObrigatoria.registro_id == registro.id,
            AcaoObrigatoria.ciclo_id == ciclo.id,
        ).order_by(AcaoObrigatoria.id).with_for_update()
    ).all()
    if not acoes:
        return negar("G6 exige ao menos uma ação obrigatória no ciclo")
    acoes_pendentes = [item.id for item in acoes if item.estado == "aberta"]
    acoes_sem_evidencia = [item.id for item in acoes if not item.evidencia]
    if acoes_pendentes or acoes_sem_evidencia:
        return negar(
            "G6 exige todas as ações finalizadas com evidência",
            acoes_pendentes=acoes_pendentes,
            acoes_sem_evidencia=acoes_sem_evidencia,
        )

    registro.estado_atual = "concluido"
    ciclo.situacao = "concluido"
    evento = registrar_evento(
        sessao, comando, "registro", registro.codigo_lgpd, "concluir_apos_medidas",
        {"registro_id": registro.id, "ciclo_id": ciclo.id,
         "numero_ciclo": ciclo.numero, "estado_anterior": "em_execucao",
         "estado_atual": "concluido",
         "instrumentos_validados": [item.id for item in instrumentos],
         "acoes_finalizadas": [{"id": item.id, "estado": item.estado} for item in acoes],
         "conta_id": conta_id, "concluido_em": momento.isoformat()},
        codigo_evento="G6", registro_id=registro.id, ciclo_id=ciclo.id,
        versao_esquema_evento=2,
    )
    registro.sequencia_atual = evento.sequencia_cadeia
    retorno = fechar_comando(
        comando,
        {"permitido": True, "motivo": "Registro concluído após as medidas",
         "registro_id": registro.id, "codigo_lgpd": registro.codigo_lgpd,
         "ciclo_id": ciclo.id, "estado_registro": "concluido",
         "situacao_ciclo": "concluido", "evento_g6": evento.sequencia_cadeia},
    )
    sessao.flush()
    return retorno


# ---------------------------------------------------------------- transversalidade (D2)

def declarar_transversalidade(sessao, *, comando_id, conta_id, objeto_id, familia_id, fundamento):
    """Declara que o objeto é transversal DENTRO da família (D2). Só a governança de proteção de
    dados (papel 'governanca_protecao_dados'; na PoC, o Encarregado). Corrente própria de eventos."""
    conta = sessao.get(Conta, conta_id)
    pessoa_id = conta.pessoa_id if conta is not None else None
    ator_tipo, ator_id = ("pessoa", pessoa_id) if pessoa_id else ("desconhecido", conta_id)
    parametros = {"conta_id": conta_id, "objeto_id": objeto_id, "familia_id": familia_id,
                  "fundamento": fundamento}
    comando, resposta = abrir_comando(sessao, comando_id, "declarar_transversalidade", parametros,
                                      ator_tipo, ator_id, conta_id)
    if resposta is not None:
        return resposta

    def negar(motivo):
        registrar_auditoria(sessao, "tentativa_negada", ator_tipo, ator_id,
                            {"acao_tentada": "declarar_transversalidade", "objeto": objeto_id,
                             "familia": familia_id, "motivo": motivo}, comando_id=comando.id)
        resultado = fechar_comando(comando, {"permitido": False, "motivo": motivo})
        sessao.flush()
        return resultado

    if conta is None or not conta.ativa:
        return negar("conta inexistente ou desativada")
    if not sessao.scalars(select(Designacao).where(
            Designacao.pessoa_id == pessoa_id, Designacao.papel == "governanca_protecao_dados",
            Designacao.ativa.is_(True))).first():
        return negar("somente a governança de proteção de dados declara transversalidade (D2)")
    if sessao.get(ObjetoCatalogo, objeto_id) is None or sessao.get(FamiliaContexto, familia_id) is None:
        return negar("objeto ou família fora do catálogo")
    if not (fundamento or "").strip():
        return negar("o fundamento é obrigatório")
    if transversalidade_vigente(sessao, objeto_id, familia_id) is not None:
        return negar("já existe declaração vigente para este objeto nesta família")

    decisao = Transversalidade(objeto_id=objeto_id, familia_id=familia_id, fundamento=fundamento.strip(),
                               decidido_por=pessoa_id, comando_id=comando.id)
    sessao.add(decisao)
    sessao.flush()
    evento = registrar_evento(sessao, comando, "transversalidade", f"TRV-{objeto_id}-{familia_id}",
                              "declarar_transversalidade",
                              {"decisao_id": decisao.id, "objeto": objeto_id, "familia": familia_id,
                               "fundamento": decisao.fundamento}, versao_esquema_evento=2)
    resultado = fechar_comando(comando, {"permitido": True, "motivo": "declarada",
                                         "decisao_id": decisao.id, "evento": evento.sequencia_cadeia})
    sessao.flush()
    return resultado
