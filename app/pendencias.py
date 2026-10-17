"""Atos das pendências usados pelo núcleo do M1a."""

from datetime import datetime, timezone

from sqlalchemy import select

from app.comandos import abrir_comando, fechar_comando
from app.eventos import registrar_auditoria, registrar_evento
from app.modelos import Conta, Pendencia
from app.permissoes import tem_papel


def agora_utc():
    return datetime.now(timezone.utc)


def _ator(sessao, conta_id):
    conta = sessao.get(Conta, conta_id)
    pessoa_id = conta.pessoa_id if conta is not None else None
    ator_tipo, ator_id = (("pessoa", pessoa_id) if pessoa_id
                          else ("desconhecido", conta_id))
    return conta, pessoa_id, ator_tipo, ator_id


def _negar(sessao, comando, ator_tipo, ator_id, conta_id, pendencia_id, motivo,
           **detalhes):
    registrar_auditoria(
        sessao, "tentativa_negada", ator_tipo, ator_id,
        {"acao_tentada": "assumir_pendencia", "pendencia_id": pendencia_id,
         "conta_id": conta_id, "motivo": motivo},
        comando_id=None if comando is None else comando.id,
    )
    resultado = dict({"permitido": False, "motivo": motivo}, **detalhes)
    if comando is None:
        return dict(resultado, reexecutado=False)
    resposta = fechar_comando(comando, resultado)
    sessao.flush()
    return resposta


def assumir_pendencia(sessao, *, comando_id, conta_id, pendencia_id, momento=None):
    """P2 — atribui uma pendência aberta a um agente autorizado da unidade de destino."""
    momento = momento or agora_utc()
    parametros = {"conta_id": conta_id, "pendencia_id": pendencia_id}
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(sessao, comando_id, "assumir_pendencia", parametros,
                                      ator_tipo, ator_id, conta_id)
    if resposta is not None:
        return resposta

    pendencia = sessao.scalars(
        select(Pendencia).where(Pendencia.id == pendencia_id).with_for_update()
    ).one_or_none()
    if pendencia is None:
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id, pendencia_id,
                      "Pendência inexistente")
    if conta is None or not conta.ativa:
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id, pendencia_id,
                      "conta inexistente ou desativada")
    if not tem_papel(sessao, pessoa_id, pendencia.unidade_destino_id, {"elaborador"}):
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, pendencia_id,
            "a pessoa não está autorizada a assumir pendências desta unidade",
        )
    if pendencia.estado != "aberta":
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, pendencia_id,
            "P2 exige pendência no estado aberta",
            estado_atual=pendencia.estado,
            responsavel_atual_id=pendencia.responsavel_atual_id,
        )

    estado_anterior = pendencia.estado
    pendencia.estado = "em_atendimento"
    pendencia.responsavel_atual_id = pessoa_id
    pendencia.atualizada_em = momento
    evento_p2 = registrar_evento(
        sessao, comando, "pendencia", pendencia.id, "assumir_pendencia",
        {"pendencia_id": pendencia.id, "estado_anterior": estado_anterior,
         "estado_atual": "em_atendimento", "unidade_destino_id": pendencia.unidade_destino_id,
         "responsavel_atual_id": pessoa_id, "conta_id": conta_id},
        codigo_evento="P2", registro_id=pendencia.registro_id,
        ciclo_id=pendencia.ciclo_contexto_atual_id, versao_esquema_evento=2,
    )
    resultado = fechar_comando(
        comando,
        {"permitido": True, "motivo": "Pendência assumida",
         "pendencia_id": pendencia.id, "estado_pendencia": "em_atendimento",
         "responsavel_atual_id": pessoa_id,
         "evento_p2": evento_p2.sequencia_cadeia},
    )
    sessao.flush()
    return resultado
