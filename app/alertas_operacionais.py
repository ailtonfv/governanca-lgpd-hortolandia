"""Flags calculadas para a futura tela inicial; não duplicam o estado do workflow."""

from sqlalchemy import select

from app.modelos import Conta, Pendencia
from app.permissoes import tem_papel


ESTADOS_ATIVOS_PENDENCIA = {
    "aberta", "em_atendimento", "respondida", "devolvida_para_complementacao",
}


def listar_alertas_operacionais(sessao, conta_id):
    """Lista alertas pertinentes à pessoa autenticada, derivados dos dados atuais."""
    conta = sessao.get(Conta, conta_id)
    if conta is None or not conta.ativa:
        return []

    alertas = []
    pendencias = sessao.scalars(
        select(Pendencia)
        .where(Pendencia.estado.in_(ESTADOS_ATIVOS_PENDENCIA))
        .order_by(Pendencia.criada_em, Pendencia.id)
    ).all()
    for pendencia in pendencias:
        autorizada_na_unidade = tem_papel(
            sessao, conta.pessoa_id, pendencia.unidade_destino_id, {"elaborador"}
        )
        if not autorizada_na_unidade and pendencia.responsavel_atual_id != conta.pessoa_id:
            continue

        base = {"pendencia_id": pendencia.id, "registro_id": pendencia.registro_id,
                "instrumento_id": pendencia.instrumento_id}
        if pendencia.estado == "aberta" and autorizada_na_unidade:
            alertas.append(dict(
                base, codigo="CORRECAO_SOLICITADA", nivel="atencao",
                proxima_acao="assumir_pendencia",
            ))
        if (pendencia.estado == "em_atendimento"
                and pendencia.responsavel_atual_id == conta.pessoa_id):
            alertas.append(dict(
                base, codigo="PENDENCIA_ATRIBUIDA_A_VOCE", nivel="proxima_acao",
                proxima_acao="iniciar_ajuste",
            ))
        if pendencia.bloqueante:
            alertas.append(dict(
                base, codigo="SUBMISSAO_BLOQUEADA", nivel="bloqueio",
                proxima_acao="resolver_pendencia",
            ))

    ordem_nivel = {"bloqueio": 0, "atencao": 1, "proxima_acao": 2}
    return sorted(alertas, key=lambda item: (
        ordem_nivel[item["nivel"]], item["codigo"], item["pendencia_id"]
    ))
