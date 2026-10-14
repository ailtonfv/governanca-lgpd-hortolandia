# Camada de domínio: o ciclo de vida do Registro (SAD 04 e SAD 05).
#
# Regra de ouro (DA-26, item 5): cada ato acontece numa transação só.
# O ato (evento), o pedido (comando) e os resumos (projeções) são gravados juntos, ou nada é gravado.

import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.modelos import (Comando, Conta, Registro, Ciclo, Instrumento,
                         ObjetoCatalogo, RegistroObjeto, ContextoAtuacao, FamiliaContexto,
                         ObjetoBase, PAPEIS_ASSUNTO, PAPEIS_CITADOS, seq_codigo_lgpd)
from app.eventos import registrar_evento, registrar_auditoria
from app.permissoes import tem_papel

# O que o sistema oferece a quem tentou criar um Registro que já existe (O-80)
ACOES_POR_ESTADO = {
    "em_andamento": ["abrir", "solicitar acesso"],
    "em_validacao": ["abrir", "solicitar acesso"],
    "em_execucao": ["abrir", "solicitar acesso"],
    "suspenso": ["abrir", "solicitar acesso", "retomar (G8)", "cancelar (G11)"],
    "concluido": ["abrir", "reabrir (G10)"],
}


def proximo_codigo_lgpd(sessao):
    """Próximo código humano, tirado do contador do banco. Ex.: LGPD-2026-00002.
    Formato ainda A VALIDAR (SAD 05, 5.1). Se o número já existir (dados antigos), pula para o seguinte."""
    ano = datetime.now(timezone.utc).year
    while True:
        numero = sessao.execute(seq_codigo_lgpd.next_value()).scalar()
        codigo = f"LGPD-{ano}-{numero:05d}"
        if sessao.scalar(select(Registro.id).where(Registro.codigo_lgpd == codigo)) is None:
            return codigo


def _vinculos_assunto(sessao, objeto_ids):
    """Vínculos ativos em que algum dos objetos é ASSUNTO (PRINCIPAL ou ABRANGIDO) de um Registro."""
    return sessao.scalars(
        select(RegistroObjeto)
        .where(RegistroObjeto.objeto_id.in_(objeto_ids), RegistroObjeto.ativo.is_(True),
               RegistroObjeto.papel.in_(PAPEIS_ASSUNTO))
        .order_by(RegistroObjeto.id)
    ).all()


def registro_que_ocupa(sessao, objeto_ids, contexto_id):
    """Verificação 1 — equivalência bloqueadora (DA-38, item 3): algum objeto já é assunto
    de outro Registro não cancelado NO MESMO contexto? Devolve (objeto, registro) ou (None, None)."""
    for v in _vinculos_assunto(sessao, objeto_ids):
        if v.contexto_atuacao_id == contexto_id:
            return sessao.get(ObjetoCatalogo, v.objeto_id), sessao.get(Registro, v.registro_id)
    return None, None


def mesma_familia(sessao, objeto_ids, contexto):
    """Verificação 2 — família de contexto (DA-38, item 6): o objeto já é assunto de Registro
    em OUTRO contexto da MESMA família? Devolve a lista de ocorrências (vazia se não houver)."""
    ocorrencias = []
    for v in _vinculos_assunto(sessao, objeto_ids):
        outro = sessao.get(ContextoAtuacao, v.contexto_atuacao_id)
        if outro.id != contexto.id and outro.familia_id == contexto.familia_id:
            ocorrencias.append({"objeto": v.objeto_id, "contexto_existente": outro.id,
                                "registro_existente": sessao.get(Registro, v.registro_id).codigo_lgpd})
    return ocorrencias


def alertas_de_sobreposicao(sessao, objeto_ids):
    """Verificação 3 — semelhança material (DA-36, item 7): OUTROS objetos que utilizam a mesma
    base de dados e já são assunto de algum Registro. Gera alerta à governança; não bloqueia.
    (As relações hierárquicas do catálogo entram depois, com a curadoria — O-80.)"""
    bases = sessao.scalars(select(ObjetoBase.base_id).where(
        ObjetoBase.objeto_id.in_(objeto_ids), ObjetoBase.vigente_ate.is_(None))).all()
    if not bases:
        return []
    vizinhos = sessao.scalars(select(ObjetoBase).where(
        ObjetoBase.base_id.in_(bases), ObjetoBase.vigente_ate.is_(None),
        ObjetoBase.objeto_id.not_in(objeto_ids))).all()
    alertas = []
    for viz in vizinhos:
        for v in _vinculos_assunto(sessao, [viz.objeto_id]):
            alertas.append({"motivo": f"utiliza a mesma base {viz.base_id}",
                            "objeto_relacionado": viz.objeto_id,
                            "registro": sessao.get(Registro, v.registro_id).codigo_lgpd,
                            "contexto": v.contexto_atuacao_id})
    return alertas


def informacao_do_existente(objeto, registro, contexto_id):
    """A resposta útil para quem tentou duplicar: o que existe e o que pode fazer (DA-36, item 7)."""
    return {
        "registro_existente": registro.codigo_lgpd,
        "titulo": registro.titulo_objeto,
        "objeto": f"{objeto.id} — {objeto.nome_canonico}",
        "contexto": contexto_id,
        "estado": registro.estado_atual,
        "unidade": registro.unidade_principal_atual_id,
        "responsavel": registro.criado_por,
        "acoes_possiveis": ACOES_POR_ESTADO.get(registro.estado_atual, ["abrir"]),
    }


def criar_registro(sessao, conta_id, unidade_id, objeto_ids, titulo_objeto, contexto_id,
                   comando_id=None, citados=None, justificativa=None):
    """Ato G1 — Criar Registro (SAD 04, seção 7), com a prevenção de duplicidade (DA-36 e DA-38).

    objeto_ids: os objetos que são ASSUNTO do Registro; o primeiro é o PRINCIPAL, os demais ABRANGIDOS.
    contexto_id: o contexto de atuação (escolhido do catálogo, nunca digitado).
    citados: objetos apenas citados, ex.: {"OBJ-SRV-001": "RELACIONADO"} (APOIO ou RELACIONADO).
    justificativa: exigida quando houver advertência de família.

    Ordem das verificações (DA-38, item 9): 1. equivalência bloqueadora; 2. família de contexto;
    3. objetos relacionados; 4. resultado: bloquear, criar com justificativa ou criar.
    Devolve (registro ou None, motivo, detalhes): se negado, detalhes = o Registro existente ou a
    advertência; se criado, detalhes = {"advertencia": ..., "alertas": [...]}.
    """
    citados = citados or {}

    # 1. pedido repetido? devolve o mesmo resultado
    if comando_id is not None:
        anterior = sessao.get(Comando, comando_id)
        if anterior is not None:
            r = anterior.resultado
            rid = r.get("registro_id")
            registro = sessao.get(Registro, rid) if rid else None
            return registro, "pedido repetido", r.get("detalhes", r.get("existente"))

    # 2. barreiras de sempre
    conta = sessao.get(Conta, conta_id)
    contexto = sessao.get(ContextoAtuacao, contexto_id) if contexto_id else None
    todos_ids = list(objeto_ids) + list(citados)
    objetos = [sessao.get(ObjetoCatalogo, oid) for oid in todos_ids]
    motivo, detalhes, advertencia, alertas = None, None, None, []
    if conta is None or not conta.ativa:
        motivo = "conta inexistente ou desativada"
    elif not objeto_ids or any(o is None or not o.ativo for o in objetos):
        motivo = "objeto fora do catálogo ou inativo"
    elif len(set(todos_ids)) != len(todos_ids):
        motivo = "o mesmo objeto foi informado mais de uma vez"
    elif any(p not in PAPEIS_CITADOS for p in citados.values()):
        motivo = "papel inválido para objeto citado (use APOIO ou RELACIONADO)"
    elif contexto is None or not contexto.ativo:
        motivo = "contexto de atuação fora do catálogo ou inativo"
    elif not tem_papel(sessao, conta.pessoa_id, unidade_id, {"elaborador"}):
        motivo = "a pessoa não tem papel de elaborador nesta unidade"
    else:
        # 3. verificação 1 — equivalência bloqueadora (pesquisa prévia; a trava do banco confirma)
        objeto, registro = registro_que_ocupa(sessao, objeto_ids, contexto.id)
        if registro is not None:
            motivo = f"já existe Registro para este objeto neste contexto: {registro.codigo_lgpd}"
            detalhes = informacao_do_existente(objeto, registro, contexto.id)
        else:
            # 4. verificação 2 — família de contexto
            ocorrencias = mesma_familia(sessao, objeto_ids, contexto)
            if ocorrencias:
                familia = sessao.get(FamiliaContexto, contexto.familia_id)
                advertencia = {"familia": familia.id, "ocorrencias": ocorrencias,
                               "mensagem": MENSAGEM_FAMILIA}
                if familia.mutuamente_exclusiva:
                    motivo = f"família {familia.id} configurada como mutuamente exclusiva"
                    detalhes = advertencia
                elif not (justificativa and justificativa.strip()):
                    motivo = "advertência de família: informe a justificativa para prosseguir"
                    detalhes = advertencia
                else:
                    advertencia["justificativa"] = justificativa.strip()
            # 5. verificação 3 — objetos relacionados (só alerta)
            if motivo is None:
                alertas = alertas_de_sobreposicao(sessao, objeto_ids)

    pessoa_id = conta.pessoa_id if conta is not None else None
    comando = Comando(id=comando_id or str(uuid.uuid4()), tipo="criar_registro",
                      ator_tipo="pessoa" if pessoa_id else "desconhecido",
                      ator_id=pessoa_id or conta_id, conta_id=conta_id)
    sessao.add(comando)
    sessao.flush()

    # 6. tenta criar, dentro de um "ponto de salvamento": se a trava do banco recusar,
    #    só esta parte é desfeita; o pedido e a auditoria continuam valendo
    if motivo is None:
        papeis = {oid: ("PRINCIPAL" if n == 0 else "ABRANGIDO") for n, oid in enumerate(objeto_ids)}
        papeis.update(citados)
        try:
            with sessao.begin_nested():
                registro = _nascer_registro(sessao, comando, conta_id, unidade_id, objetos, papeis,
                                            contexto, titulo_objeto, advertencia, alertas)
        except IntegrityError:
            # outro pedido, no mesmo instante, ocupou o objeto primeiro: a trava do banco funcionou
            objeto, ocupante = registro_que_ocupa(sessao, objeto_ids, contexto.id)
            motivo = (f"já existe Registro para este objeto neste contexto: {ocupante.codigo_lgpd} "
                      "(barrado pela trava do banco)")
            detalhes = informacao_do_existente(objeto, ocupante, contexto.id)

    # 7. negado: vai para a auditoria (nunca para o livro de atos do domínio)
    if motivo is not None:
        registrar_auditoria(sessao, "tentativa_negada", comando.ator_tipo, comando.ator_id,
                            {"acao_tentada": "criar_registro", "objetos": list(objeto_ids),
                             "contexto": contexto_id, "conta_id": conta_id, "motivo": motivo,
                             "registro_existente": (detalhes or {}).get("registro_existente")},
                            comando_id=comando.id)
        comando.resultado = {"permitido": False, "motivo": motivo, "detalhes": detalhes}
        sessao.flush()
        return None, motivo, detalhes

    detalhes = {"advertencia": advertencia, "alertas": alertas}
    resultado = "criado com justificativa" if advertencia else "permitido"
    comando.resultado = {"permitido": True, "motivo": resultado, "registro_id": registro.id,
                         "detalhes": detalhes}
    sessao.flush()
    return registro, resultado, detalhes


MENSAGEM_FAMILIA = ("Este objeto está associado a mais de um contexto da mesma família. "
                    "Confirme se ele é transversal ou escolha um contexto principal.")


def _nascer_registro(sessao, comando, conta_id, unidade_id, objetos, papeis, contexto,
                     titulo_objeto, advertencia, alertas):
    """Cria o Registro, o ciclo 1, o FORM 1, os vínculos com o catálogo e o ato G1."""
    principal = objetos[0]
    registro = Registro(id=str(uuid.uuid4()), codigo_lgpd=proximo_codigo_lgpd(sessao),
                        tipo_objeto=principal.tipo_objeto, titulo_objeto=titulo_objeto,
                        unidade_principal_atual_id=unidade_id, criado_por=comando.ator_id,
                        ciclo_atual=1, estado_atual="em_andamento", sequencia_atual=0)
    sessao.add(registro)
    sessao.flush()
    ciclo = Ciclo(registro_id=registro.id, numero=1, situacao="ativo")
    sessao.add(ciclo)
    sessao.add(Instrumento(id=str(uuid.uuid4()), registro_id=registro.id,
                           tipo_instrumento="FORM1", estado_instrumento="nao_iniciado"))
    for objeto in objetos:                       # a reserva dos objetos: aqui a trava do banco atua
        sessao.add(RegistroObjeto(registro_id=registro.id, objeto_id=objeto.id,
                                  papel=papeis[objeto.id], contexto_atuacao_id=contexto.id))
    sessao.flush()

    conteudo = {"objetos": [{"id": o.id, "papel": papeis[o.id]} for o in objetos],
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
    return registro
