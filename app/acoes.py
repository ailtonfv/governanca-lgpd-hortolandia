"""Ação obrigatória sintética mínima do percurso com medidas do M1a."""

from copy import deepcopy
from datetime import datetime, timezone

from sqlalchemy import select

from app.comandos import abrir_comando, fechar_comando
from app.eventos import registrar_auditoria, registrar_evento
from app.modelos import AcaoObrigatoria, Conta, Registro


def agora_utc():
    return datetime.now(timezone.utc)


def finalizar_acao_obrigatoria(sessao, *, comando_id, conta_id, acao_id,
                               resultado, evidencia, motivo=None, momento=None):
    """Conclui a medida ou a encerra formalmente, sempre com evidência."""
    momento = momento or agora_utc()
    motivo = " ".join(motivo.split()) if isinstance(motivo, str) else None
    parametros = {"conta_id": conta_id, "acao_id": acao_id, "resultado": resultado,
                  "evidencia": evidencia, "motivo": motivo}
    conta = sessao.get(Conta, conta_id)
    pessoa_id = conta.pessoa_id if conta is not None else None
    ator_tipo, ator_id = (("pessoa", pessoa_id) if pessoa_id
                          else ("desconhecido", conta_id))
    comando, resposta = abrir_comando(
        sessao, comando_id, "finalizar_acao_obrigatoria", parametros,
        ator_tipo, ator_id, conta_id,
    )
    if resposta is not None:
        return resposta

    def negar(texto, **detalhes):
        registrar_auditoria(
            sessao, "tentativa_negada", ator_tipo, ator_id,
            {"acao_tentada": "finalizar_acao_obrigatoria", "acao_id": acao_id,
             "conta_id": conta_id, "motivo": texto}, comando_id=comando.id,
        )
        retorno = fechar_comando(
            comando, dict({"permitido": False, "motivo": texto}, **detalhes)
        )
        sessao.flush()
        return retorno

    if resultado not in {"concluida", "encerrada"}:
        return negar("resultado deve ser concluida ou encerrada")
    if not isinstance(evidencia, dict) or not evidencia:
        return negar("a evidência estruturada é obrigatória")
    if resultado == "encerrada" and not motivo:
        return negar("o encerramento formal exige motivo")

    referencia = sessao.get(AcaoObrigatoria, acao_id)
    if referencia is None:
        return negar("Ação obrigatória inexistente")
    # A mesma ordem usada pelo G6 (Registro -> Ação) evita interbloqueio se
    # alguém tentar finalizar a medida enquanto outro pedido tenta concluir.
    registro = sessao.scalars(
        select(Registro).where(Registro.id == referencia.registro_id).with_for_update()
    ).one()
    acao = sessao.scalars(
        select(AcaoObrigatoria).where(AcaoObrigatoria.id == acao_id).with_for_update()
    ).one()
    if conta is None or not conta.ativa:
        return negar("conta inexistente ou desativada")
    if registro.estado_atual != "em_execucao":
        return negar(
            "a ação só pode ser finalizada com o Registro em_execucao",
            estado_registro=registro.estado_atual,
        )
    if acao.responsavel_id != pessoa_id:
        return negar(
            "somente o agente responsável pode finalizar a ação",
            responsavel_id=acao.responsavel_id,
        )
    if acao.estado != "aberta":
        return negar("a ação obrigatória não está aberta", estado_acao=acao.estado)

    estado_anterior = acao.estado
    acao.estado = resultado
    acao.evidencia = {
        "conteudo": deepcopy(evidencia),
        "motivo_encerramento": motivo if resultado == "encerrada" else None,
    }
    acao.atualizada_em = momento
    evento = registrar_evento(
        sessao, comando, "acao_obrigatoria", acao.id, "finalizar_acao_obrigatoria",
        {"acao_id": acao.id, "registro_id": acao.registro_id,
         "instrumento_id": acao.instrumento_id, "estado_anterior": estado_anterior,
         "estado_atual": resultado, "evidencia": deepcopy(evidencia),
         "motivo_encerramento": motivo if resultado == "encerrada" else None,
         "conta_id": conta_id},
        codigo_evento="AO1", registro_id=acao.registro_id, ciclo_id=acao.ciclo_id,
        versao_esquema_evento=2,
    )
    retorno = fechar_comando(
        comando,
        {"permitido": True, "motivo": "Ação obrigatória finalizada",
         "acao_id": acao.id, "estado_acao": resultado,
         "evento_acao": evento.sequencia_cadeia},
    )
    sessao.flush()
    return retorno
