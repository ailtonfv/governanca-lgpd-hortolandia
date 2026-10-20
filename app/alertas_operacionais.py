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
        intersecretarial = pendencia.tipo_pendencia == "participacao"
        papel_destino = {"agente_pendencia"} if intersecretarial else {"elaborador"}
        papel_origem = {"agente_pendencia"} if intersecretarial else {"validador"}
        autorizada_na_unidade = tem_papel(
            sessao, conta.pessoa_id, pendencia.unidade_destino_id, papel_destino
        )
        autorizada_a_decidir = tem_papel(
            sessao, conta.pessoa_id, pendencia.unidade_origem_id, papel_origem
        )
        responsavel = pendencia.responsavel_atual_id == conta.pessoa_id
        if not autorizada_na_unidade and not autorizada_a_decidir and not responsavel:
            continue

        base = {"pendencia_id": pendencia.id, "registro_id": pendencia.registro_id,
                "instrumento_id": pendencia.instrumento_id}
        if pendencia.estado == "aberta" and autorizada_na_unidade:
            alertas.append(dict(
                base,
                codigo=("PROVIDENCIA_INTERSECRETARIAL_RECEBIDA" if intersecretarial
                        else "CORRECAO_SOLICITADA"),
                nivel="atencao",
                proxima_acao="assumir_pendencia",
            ))
        if pendencia.estado == "em_atendimento" and responsavel:
            alertas.append(dict(
                base,
                codigo=("PROVIDENCIA_INTERSECRETARIAL_ATRIBUIDA_A_VOCE"
                        if intersecretarial else "PENDENCIA_ATRIBUIDA_A_VOCE"),
                nivel="proxima_acao",
                proxima_acao=("responder_pendencia_intersecretarial"
                              if intersecretarial else "iniciar_ajuste"),
            ))
        if pendencia.estado == "respondida" and autorizada_a_decidir:
            alertas.append(dict(
                base,
                codigo=("RESPOSTA_INTERSECRETARIAL_AGUARDANDO_DECISAO"
                        if intersecretarial else "RESPOSTA_AGUARDANDO_DECISAO"),
                nivel="proxima_acao",
                proxima_acao=("aceitar_pendencia_intersecretarial"
                              if intersecretarial else "decidir_resposta"),
            ))
        if pendencia.estado == "devolvida_para_complementacao" and responsavel:
            alertas.append(dict(
                base, codigo="COMPLEMENTACAO_SOLICITADA", nivel="proxima_acao",
                proxima_acao="retomar_pendencia",
            ))
        if pendencia.bloqueante and (autorizada_na_unidade or responsavel):
            alertas.append(dict(
                base,
                codigo=("CONCLUSAO_BLOQUEADA" if pendencia.gate_bloqueado == "conclusao"
                        else "SUBMISSAO_BLOQUEADA"),
                nivel="bloqueio",
                proxima_acao="resolver_pendencia",
            ))

    ordem_nivel = {"bloqueio": 0, "atencao": 1, "proxima_acao": 2}
    return sorted(alertas, key=lambda item: (
        ordem_nivel[item["nivel"]], item["codigo"], item["pendencia_id"]
    ))
