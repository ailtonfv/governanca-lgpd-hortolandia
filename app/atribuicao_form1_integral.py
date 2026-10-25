"""Atribuição do Agente Responsável pelo Preenchimento (ARP).

Este incremento prepara a abertura do FORM 1 integral. Ele não cria rascunho,
não habilita o contrato 3 e não altera o Instrumento sintético vigente.
"""

from datetime import datetime, timezone

from sqlalchemy import select

from app.comandos import abrir_comando, fechar_comando
from app.eventos import registrar_auditoria, registrar_evento
from app.modelos import AtribuicaoForm1Integral, Ciclo, Conta, Pessoa, Registro
from app.permissoes import tem_papel


def _agora_utc():
    return datetime.now(timezone.utc)


def _negar(sessao, comando, ator_tipo, ator_id, conta_id, registro_id, motivo):
    registrar_auditoria(
        sessao,
        "tentativa_negada",
        ator_tipo,
        ator_id,
        {
            "acao_tentada": "atribuir_arp_form1_integral",
            "registro_id": registro_id,
            "conta_id": conta_id,
            "motivo": motivo,
        },
        comando_id=None if comando is None else comando.id,
    )
    resultado = {"permitido": False, "motivo": motivo}
    if comando is None:
        return dict(resultado, reexecutado=False)
    return fechar_comando(comando, resultado)


def atribuir_arp_form1_integral(
    sessao,
    *,
    comando_id,
    conta_id,
    registro_id,
    modo,
    arp_pessoa_id=None,
    versao_lida=0,
    momento=None,
):
    """Atribui o ARP atual sem conceder designação ou acesso automaticamente."""

    momento = momento or _agora_utc()
    parametros = {
        "conta_id": conta_id,
        "registro_id": registro_id,
        "modo": modo,
        "arp_pessoa_id": arp_pessoa_id,
        "versao_lida": versao_lida,
    }
    conta = sessao.get(Conta, conta_id)
    pessoa_id = conta.pessoa_id if conta is not None else None
    ator_tipo, ator_id = (("pessoa", pessoa_id) if pessoa_id
                          else ("desconhecido", conta_id))
    comando, resposta = abrir_comando(
        sessao, comando_id, "atribuir_arp_form1_integral", parametros,
        ator_tipo, ator_id, conta_id,
    )
    if resposta is not None:
        return resposta

    if conta is None or not conta.ativa:
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
                      "conta inexistente ou desativada")
    pessoa = sessao.get(Pessoa, pessoa_id)
    if pessoa is None or not pessoa.ativa:
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
                      "pessoa inexistente ou desativada")
    if modo not in {"proprio", "outro"}:
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
                      "modo de atribuição inválido")
    if not isinstance(versao_lida, int) or isinstance(versao_lida, bool) or versao_lida < 0:
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
                      "versao_lida deve ser um inteiro maior ou igual a zero")

    registro = sessao.scalars(
        select(Registro).where(Registro.id == registro_id).with_for_update()
    ).one_or_none()
    if registro is None:
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
                      "Registro inexistente")
    if not tem_papel(
        sessao, pessoa_id, registro.unidade_principal_atual_id, {"responsavel_registro"}
    ):
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
                      "a pessoa não possui função de APA responsável pelo Registro nesta Secretaria")

    alvo_id = pessoa_id if modo == "proprio" else arp_pessoa_id
    if not alvo_id:
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
                      "selecione o agente que será o ARP")
    if modo == "outro" and alvo_id == pessoa_id:
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
                      "para indicar outro agente, selecione uma pessoa diferente do APA atual")
    alvo = sessao.get(Pessoa, alvo_id)
    if alvo is None or not alvo.ativa:
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
                      "o agente indicado não existe ou está desativado")
    if not tem_papel(
        sessao, alvo_id, registro.unidade_principal_atual_id, {"preenchedor"}
    ):
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
                      "a indicação não possui designação vigente de preenchedor nesta Secretaria")
    conta_ativa = sessao.scalars(
        select(Conta).where(Conta.pessoa_id == alvo_id, Conta.ativa.is_(True))
    ).first()
    if conta_ativa is None:
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
                      "o agente indicado não possui conta ativa")

    atribuicao = sessao.scalars(
        select(AtribuicaoForm1Integral)
        .where(AtribuicaoForm1Integral.registro_id == registro.id)
        .with_for_update()
    ).one_or_none()
    versao_atual = 0 if atribuicao is None else atribuicao.versao
    if versao_lida != versao_atual:
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
                      "atribuição desatualizada: recarregue antes de confirmar")
    if atribuicao is not None and atribuicao.arp_atual_id == alvo_id:
        return fechar_comando(comando, {
            "permitido": True,
            "motivo": "o agente indicado já é o ARP atual",
            "registro_id": registro.id,
            "arp_pessoa_id": alvo_id,
            "versao": atribuicao.versao,
            "alterado": False,
        })

    arp_anterior_id = None if atribuicao is None else atribuicao.arp_atual_id
    nova_versao = versao_atual + 1
    if atribuicao is None:
        atribuicao = AtribuicaoForm1Integral(registro_id=registro.id)
        sessao.add(atribuicao)
    atribuicao.arp_atual_id = alvo_id
    atribuicao.atribuido_por = pessoa_id
    atribuicao.atribuido_em = momento
    atribuicao.versao = nova_versao

    ciclo = sessao.scalars(
        select(Ciclo).where(
            Ciclo.registro_id == registro.id,
            Ciclo.numero == registro.ciclo_atual,
        )
    ).one()
    evento = registrar_evento(
        sessao,
        comando,
        "registro",
        registro.codigo_lgpd,
        "atribuir_arp_form1_integral",
        {
            "registro_id": registro.id,
            "apa_abertura_id": registro.criado_por,
            "arp_anterior_id": arp_anterior_id,
            "arp_atual_id": alvo_id,
            "atribuido_por": pessoa_id,
            "modo": modo,
            "versao_atribuicao": nova_versao,
        },
        registro_id=registro.id,
        ciclo_id=ciclo.id,
        versao_esquema_evento=2,
    )
    registro.sequencia_atual = evento.sequencia_cadeia
    resultado = fechar_comando(comando, {
        "permitido": True,
        "motivo": "ARP atribuído ao FORM 1 integral",
        "registro_id": registro.id,
        "arp_pessoa_id": alvo_id,
        "versao": nova_versao,
        "alterado": True,
        "evento": evento.sequencia_cadeia,
    })
    sessao.flush()
    return resultado
