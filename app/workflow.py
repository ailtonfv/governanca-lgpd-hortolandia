# Camada de domínio: o ciclo de vida do Registro (SAD 04 e SAD 05).
#
# Regra de ouro (DA-26, item 5): cada ato acontece numa transação só.
# O ato (evento), o pedido (comando) e os resumos (projeções) são gravados juntos, ou nada é gravado.

import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.modelos import (Comando, Conta, Registro, Ciclo, Instrumento,
                         ObjetoCatalogo, RegistroObjeto, seq_codigo_lgpd)
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


def registro_que_ocupa(sessao, objeto_ids):
    """Se algum dos objetos já estiver ligado a um Registro não cancelado, devolve (objeto, registro)."""
    vinculo = sessao.scalars(
        select(RegistroObjeto)
        .where(RegistroObjeto.objeto_id.in_(objeto_ids), RegistroObjeto.ativo.is_(True))
        .limit(1)
    ).first()
    if vinculo is None:
        return None, None
    return sessao.get(ObjetoCatalogo, vinculo.objeto_id), sessao.get(Registro, vinculo.registro_id)


def informacao_do_existente(objeto, registro):
    """A resposta útil para quem tentou duplicar: o que existe e o que pode fazer (O-80, item 4)."""
    return {
        "registro_existente": registro.codigo_lgpd,
        "titulo": registro.titulo_objeto,
        "objeto": f"{objeto.id} — {objeto.nome_canonico}",
        "estado": registro.estado_atual,
        "unidade": registro.unidade_principal_atual_id,
        "responsavel": registro.criado_por,
        "acoes_possiveis": ACOES_POR_ESTADO.get(registro.estado_atual, ["abrir"]),
    }


def criar_registro(sessao, conta_id, unidade_id, objeto_ids, titulo_objeto, comando_id=None):
    """Ato G1 — Criar Registro (SAD 04, seção 7), com a trava contra duplicidade (O-80).

    objeto_ids: um ou mais objetos do catálogo (RF-PRC-13); o primeiro é o objeto principal.
    Devolve (registro ou None, motivo, informação do Registro existente ou None).
    """
    # 1. pedido repetido? devolve o mesmo resultado
    if comando_id is not None:
        anterior = sessao.get(Comando, comando_id)
        if anterior is not None:
            r = anterior.resultado
            rid = r.get("registro_id")
            registro = sessao.get(Registro, rid) if rid else None
            return registro, "pedido repetido", r.get("existente")

    # 2. barreiras de sempre
    conta = sessao.get(Conta, conta_id)
    objetos = [sessao.get(ObjetoCatalogo, oid) for oid in objeto_ids]
    motivo, existente = None, None
    if conta is None or not conta.ativa:
        motivo = "conta inexistente ou desativada"
    elif not objeto_ids or any(o is None or not o.ativo for o in objetos):
        motivo = "objeto fora do catálogo ou inativo"
    elif not tem_papel(sessao, conta.pessoa_id, unidade_id, {"elaborador"}):
        motivo = "a pessoa não tem papel de elaborador nesta unidade"
    else:
        # 3. barreira da duplicidade — pesquisa prévia (rápida, mas não suficiente sozinha)
        objeto, registro = registro_que_ocupa(sessao, objeto_ids)
        if registro is not None:
            motivo = f"já existe Registro para este objeto: {registro.codigo_lgpd}"
            existente = informacao_do_existente(objeto, registro)

    pessoa_id = conta.pessoa_id if conta is not None else None
    comando = Comando(id=comando_id or str(uuid.uuid4()), tipo="criar_registro",
                      ator_tipo="pessoa" if pessoa_id else "desconhecido",
                      ator_id=pessoa_id or conta_id, conta_id=conta_id)
    sessao.add(comando)
    sessao.flush()

    # 4. tenta criar, dentro de um "ponto de salvamento": se a trava do banco recusar,
    #    só esta parte é desfeita; o pedido e a auditoria continuam valendo
    if motivo is None:
        try:
            with sessao.begin_nested():
                registro = _nascer_registro(sessao, comando, conta_id, unidade_id, objetos, titulo_objeto)
        except IntegrityError:
            # outro pedido, no mesmo instante, ocupou o objeto primeiro: a trava do banco funcionou
            objeto, ocupante = registro_que_ocupa(sessao, objeto_ids)
            motivo = f"já existe Registro para este objeto: {ocupante.codigo_lgpd} (barrado pela trava do banco)"
            existente = informacao_do_existente(objeto, ocupante)

    # 5. negado: vai para a auditoria (nunca para o livro de atos do domínio)
    if motivo is not None:
        registrar_auditoria(sessao, "tentativa_negada", comando.ator_tipo, comando.ator_id,
                            {"acao_tentada": "criar_registro", "objetos": list(objeto_ids),
                             "conta_id": conta_id, "motivo": motivo,
                             "registro_existente": existente and existente["registro_existente"]},
                            comando_id=comando.id)
        comando.resultado = {"permitido": False, "motivo": motivo, "existente": existente}
        sessao.flush()
        return None, motivo, existente

    comando.resultado = {"permitido": True, "motivo": "permitido", "registro_id": registro.id}
    sessao.flush()
    return registro, "permitido", None


def _nascer_registro(sessao, comando, conta_id, unidade_id, objetos, titulo_objeto):
    """Cria o Registro, o ciclo 1, o FORM 1, os vínculos com o catálogo e o ato G1."""
    registro = Registro(id=str(uuid.uuid4()), codigo_lgpd=proximo_codigo_lgpd(sessao),
                        tipo_objeto=objetos[0].tipo_objeto, titulo_objeto=titulo_objeto,
                        unidade_principal_atual_id=unidade_id, criado_por=comando.ator_id,
                        ciclo_atual=1, estado_atual="em_andamento", sequencia_atual=0)
    sessao.add(registro)
    sessao.flush()
    ciclo = Ciclo(registro_id=registro.id, numero=1, situacao="ativo")
    sessao.add(ciclo)
    sessao.add(Instrumento(id=str(uuid.uuid4()), registro_id=registro.id,
                           tipo_instrumento="FORM1", estado_instrumento="nao_iniciado"))
    for objeto in objetos:                       # a reserva dos objetos: aqui a trava do banco atua
        sessao.add(RegistroObjeto(registro_id=registro.id, objeto_id=objeto.id))
    sessao.flush()

    evento = registrar_evento(sessao, comando, "registro", registro.codigo_lgpd, "criar_registro",
                              {"objetos": [o.id for o in objetos], "titulo_objeto": titulo_objeto,
                               "unidade_principal": unidade_id, "conta_id": conta_id},
                              codigo_evento="G1", registro_id=registro.id, ciclo_id=ciclo.id)
    ciclo.evento_inicio_id = evento.id
    registro.sequencia_atual = evento.sequencia_cadeia
    sessao.flush()
    return registro
