"""Continuidade institucional do Agente Público Autorizado (APA).

O Registro pertence à Secretaria. A pessoa que o abriu permanece em
``Registro.criado_por``; esta camada resolve somente quem exerce atualmente a
responsabilidade institucional e registra substituições autorizadas.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.comandos import abrir_comando, fechar_comando, nome_da_restricao
from app.eventos import registrar_auditoria, registrar_evento
from app.modelos import Conta, Designacao, Pessoa, SubstituicaoApa, Unidade
from app.permissoes import tem_papel


PAPEL_AUTORIDADE_APA = "governanca_protecao_dados"
UNIDADE_GOVERNANCA = "UNID-GOV"
RESTRICAO_SUBSTITUICAO_ATIVA = "uq_substituicao_apa_ativa_unidade"


def _agora_utc():
    return datetime.now(timezone.utc)


def _momento_valido(valor):
    return isinstance(valor, datetime) and valor.tzinfo is not None


def _designacao_vigente(designacao, momento):
    return bool(
        designacao is not None
        and designacao.ativa
        and designacao.papel == "responsavel_registro"
        and designacao.tipo_apa in {"titular", "suplente"}
        and (designacao.vigente_de is None or designacao.vigente_de <= momento)
        and (designacao.vigente_ate is None or momento < designacao.vigente_ate)
    )


def _designacao_apa(sessao, unidade_id, tipo_apa, pessoa_id=None, bloquear=False):
    consulta = select(Designacao).where(
        Designacao.unidade_id == unidade_id,
        Designacao.papel == "responsavel_registro",
        Designacao.tipo_apa == tipo_apa,
        Designacao.ativa.is_(True),
    )
    if pessoa_id is not None:
        consulta = consulta.where(Designacao.pessoa_id == pessoa_id)
    if bloquear:
        consulta = consulta.with_for_update()
    return sessao.scalars(consulta).one_or_none()


def _substituicao_aberta(sessao, unidade_id, bloquear=False):
    consulta = select(SubstituicaoApa).where(
        SubstituicaoApa.unidade_id == unidade_id,
        SubstituicaoApa.encerrada_em.is_(None),
    )
    if bloquear:
        consulta = consulta.with_for_update()
    return sessao.scalars(consulta).one_or_none()


def apa_em_exercicio(sessao, unidade_id, momento=None):
    """Retorna um único APA em exercício ou ``None`` se a unidade não estiver configurada."""

    momento = momento or _agora_utc()
    titular = _designacao_apa(sessao, unidade_id, "titular")
    if not _designacao_vigente(titular, momento):
        return None
    substituicao = _substituicao_aberta(sessao, unidade_id)
    if (
        substituicao is not None
        and substituicao.inicio_em <= momento < substituicao.fim_previsto_em
    ):
        suplente = _designacao_apa(
            sessao, unidade_id, "suplente", substituicao.substituto_id
        )
        if _designacao_vigente(suplente, momento):
            return {
                "pessoa_id": suplente.pessoa_id,
                "titular_id": titular.pessoa_id,
                "modalidade": "substituicao_temporaria",
                "em_nome_de": titular.pessoa_id,
                "substituicao_id": substituicao.id,
                "fim_previsto_em": substituicao.fim_previsto_em,
            }
    return {
        "pessoa_id": titular.pessoa_id,
        "titular_id": titular.pessoa_id,
        "modalidade": "titular",
        "em_nome_de": None,
        "substituicao_id": None,
        "fim_previsto_em": None,
    }


def pessoa_e_apa_em_exercicio(sessao, pessoa_id, unidade_id, momento=None):
    exercicio = apa_em_exercicio(sessao, unidade_id, momento)
    return exercicio if exercicio and exercicio["pessoa_id"] == pessoa_id else None


def unidades_em_que_e_apa_atual(sessao, pessoa_id, momento=None):
    momento = momento or _agora_utc()
    unidades = set(sessao.scalars(select(Unidade.id).where(Unidade.ativa.is_(True))))
    return {
        unidade_id
        for unidade_id in unidades
        if pessoa_e_apa_em_exercicio(sessao, pessoa_id, unidade_id, momento)
    }


def _ator(sessao, conta_id):
    conta = sessao.get(Conta, conta_id)
    pessoa_id = conta.pessoa_id if conta is not None else None
    return conta, pessoa_id, ("pessoa" if pessoa_id else "desconhecido"), (pessoa_id or conta_id)


def _negar(sessao, comando, ator_tipo, ator_id, conta_id, acao, unidade_id, motivo):
    registrar_auditoria(
        sessao,
        "tentativa_negada",
        ator_tipo,
        ator_id,
        {
            "acao_tentada": acao,
            "unidade_id": unidade_id,
            "conta_id": conta_id,
            "motivo": motivo,
        },
        comando_id=None if comando is None else comando.id,
    )
    resultado = {"permitido": False, "motivo": motivo}
    return dict(resultado, reexecutado=False) if comando is None else fechar_comando(comando, resultado)


def _autoridade_valida(sessao, conta, pessoa_id, alvo_id):
    if conta is None or not conta.ativa:
        return "conta inexistente ou desativada"
    pessoa = sessao.get(Pessoa, pessoa_id)
    if pessoa is None or not pessoa.ativa:
        return "pessoa inexistente ou desativada"
    if pessoa_id == alvo_id:
        return "ninguém pode autorizar a própria designação ou substituição como APA"
    if not tem_papel(sessao, pessoa_id, UNIDADE_GOVERNANCA, {PAPEL_AUTORIDADE_APA}):
        return "a pessoa não possui autorização institucional para gerir a continuidade do APA"
    return None


def _validar_fundamento(motivo):
    if not isinstance(motivo, str) or not motivo.strip():
        return None, "informe o motivo ou fundamento administrativo"
    motivo = " ".join(motivo.split())
    if len(motivo) > 250:
        return None, "o motivo ou fundamento administrativo deve ter até 250 caracteres"
    return motivo, None


def iniciar_substituicao_temporaria_apa(
    sessao, *, comando_id, conta_id, unidade_id, suplente_id,
    inicio_em, fim_previsto_em, motivo, momento=None,
):
    """Coloca um suplente formalmente designado em exercício por período definido."""

    momento = momento or _agora_utc()
    parametros = {
        "conta_id": conta_id,
        "unidade_id": unidade_id,
        "suplente_id": suplente_id,
        "inicio_em": inicio_em,
        "fim_previsto_em": fim_previsto_em,
        "motivo": motivo,
    }
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(
        sessao, comando_id, "iniciar_substituicao_temporaria_apa", parametros,
        ator_tipo, ator_id, conta_id,
    )
    if resposta is not None:
        return resposta
    problema = _autoridade_valida(sessao, conta, pessoa_id, suplente_id)
    motivo, problema_motivo = _validar_fundamento(motivo)
    problema = problema or problema_motivo
    if not _momento_valido(inicio_em) or not _momento_valido(fim_previsto_em):
        problema = problema or "o período da substituição deve usar data e hora com fuso"
    elif fim_previsto_em <= inicio_em:
        problema = problema or "o fim previsto deve ser posterior ao início"
    if problema:
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id,
                      "iniciar_substituicao_temporaria_apa", unidade_id, problema)

    unidade = sessao.get(Unidade, unidade_id)
    titular = _designacao_apa(sessao, unidade_id, "titular", bloquear=True)
    suplente = _designacao_apa(sessao, unidade_id, "suplente", suplente_id, bloquear=True)
    existente = _substituicao_aberta(sessao, unidade_id, bloquear=True)
    if unidade is None or not unidade.ativa:
        problema = "Secretaria inexistente ou desativada"
    elif not _designacao_vigente(titular, inicio_em):
        problema = "a Secretaria não possui APA titular vigente"
    elif not _designacao_vigente(suplente, inicio_em):
        problema = "o agente indicado não possui designação vigente de APA suplente"
    elif suplente.vigente_ate is not None and fim_previsto_em > suplente.vigente_ate:
        problema = "o período solicitado ultrapassa a vigência da designação do suplente"
    elif existente is not None:
        problema = "já existe substituição temporária aberta para esta Secretaria"
    if problema:
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id,
                      "iniciar_substituicao_temporaria_apa", unidade_id, problema)

    substituicao = SubstituicaoApa(
        id=str(uuid.uuid4()), unidade_id=unidade_id, titular_id=titular.pessoa_id,
        substituto_id=suplente_id, autorizada_por_id=pessoa_id, motivo=motivo,
        inicio_em=inicio_em, fim_previsto_em=fim_previsto_em,
    )
    try:
        with sessao.begin_nested():
            sessao.add(substituicao)
            sessao.flush()
    except IntegrityError as erro:
        if nome_da_restricao(erro) != RESTRICAO_SUBSTITUICAO_ATIVA:
            raise
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id,
                      "iniciar_substituicao_temporaria_apa", unidade_id,
                      "já existe substituição temporária aberta para esta Secretaria")

    evento = registrar_evento(
        sessao, comando, "unidade_apa", f"APA:{unidade_id}",
        "iniciar_substituicao_temporaria_apa",
        {
            "unidade_id": unidade_id,
            "titular_id": titular.pessoa_id,
            "substituto_id": suplente_id,
            "autorizada_por_id": pessoa_id,
            "motivo": motivo,
            "inicio_em": inicio_em.isoformat(),
            "fim_previsto_em": fim_previsto_em.isoformat(),
        },
        versao_esquema_evento=2,
    )
    substituicao.evento_inicio_id = evento.id
    resultado = fechar_comando(comando, {
        "permitido": True,
        "motivo": "substituição temporária do APA iniciada",
        "unidade_id": unidade_id,
        "titular_id": titular.pessoa_id,
        "apa_em_exercicio_id": suplente_id,
        "substituicao_id": substituicao.id,
        "evento": evento.sequencia_cadeia,
    })
    sessao.flush()
    return resultado


def encerrar_substituicao_temporaria_apa(
    sessao, *, comando_id, conta_id, unidade_id, motivo, momento=None,
):
    """Registra o retorno do titular e encerra a substituição temporária."""

    momento = momento or _agora_utc()
    parametros = {"conta_id": conta_id, "unidade_id": unidade_id, "motivo": motivo}
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(
        sessao, comando_id, "encerrar_substituicao_temporaria_apa", parametros,
        ator_tipo, ator_id, conta_id,
    )
    if resposta is not None:
        return resposta
    problema = _autoridade_valida(sessao, conta, pessoa_id, alvo_id=None)
    motivo, problema_motivo = _validar_fundamento(motivo)
    problema = problema or problema_motivo
    if problema:
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id,
                      "encerrar_substituicao_temporaria_apa", unidade_id, problema)
    substituicao = _substituicao_aberta(sessao, unidade_id, bloquear=True)
    titular = _designacao_apa(sessao, unidade_id, "titular", bloquear=True)
    if substituicao is None:
        problema = "não existe substituição temporária aberta para esta Secretaria"
    elif titular is None or titular.pessoa_id != substituicao.titular_id:
        problema = "a designação titular não corresponde à substituição aberta"
    if problema:
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id,
                      "encerrar_substituicao_temporaria_apa", unidade_id, problema)

    substituicao.encerrada_em = momento
    substituicao.encerrada_por_id = pessoa_id
    evento = registrar_evento(
        sessao, comando, "unidade_apa", f"APA:{unidade_id}",
        "encerrar_substituicao_temporaria_apa",
        {
            "unidade_id": unidade_id,
            "titular_id": titular.pessoa_id,
            "substituto_id": substituicao.substituto_id,
            "encerrada_por_id": pessoa_id,
            "motivo": motivo,
            "substituicao_id": substituicao.id,
        },
        versao_esquema_evento=2,
    )
    substituicao.evento_encerramento_id = evento.id
    resultado = fechar_comando(comando, {
        "permitido": True,
        "motivo": "substituição temporária encerrada; titular retomou o exercício",
        "unidade_id": unidade_id,
        "apa_em_exercicio_id": titular.pessoa_id,
        "substituicao_id": substituicao.id,
        "evento": evento.sequencia_cadeia,
    })
    sessao.flush()
    return resultado


def substituir_apa_definitivamente(
    sessao, *, comando_id, conta_id, unidade_id, sucessor_id, motivo, momento=None,
):
    """Promove um suplente vigente a titular, preservando o titular anterior no evento."""

    momento = momento or _agora_utc()
    parametros = {
        "conta_id": conta_id, "unidade_id": unidade_id,
        "sucessor_id": sucessor_id, "motivo": motivo,
    }
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(
        sessao, comando_id, "substituir_apa_definitivamente", parametros,
        ator_tipo, ator_id, conta_id,
    )
    if resposta is not None:
        return resposta
    problema = _autoridade_valida(sessao, conta, pessoa_id, sucessor_id)
    motivo, problema_motivo = _validar_fundamento(motivo)
    problema = problema or problema_motivo
    if problema:
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id,
                      "substituir_apa_definitivamente", unidade_id, problema)

    titular = _designacao_apa(sessao, unidade_id, "titular", bloquear=True)
    sucessor = _designacao_apa(sessao, unidade_id, "suplente", sucessor_id, bloquear=True)
    substituicao = _substituicao_aberta(sessao, unidade_id, bloquear=True)
    if not _designacao_vigente(titular, momento):
        problema = "a Secretaria não possui APA titular vigente"
    elif not _designacao_vigente(sucessor, momento):
        problema = "o sucessor não possui designação vigente de APA suplente"
    elif substituicao is not None:
        problema = "encerre a substituição temporária aberta antes da sucessão definitiva"
    if problema:
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id,
                      "substituir_apa_definitivamente", unidade_id, problema)

    titular_anterior_id = titular.pessoa_id
    titular.ativa = False
    titular.vigente_ate = momento
    sucessor.tipo_apa = "titular"
    sucessor.vigente_de = momento
    sucessor.vigente_ate = None
    sucessor.fundamento_administrativo = motivo
    sucessor.autorizado_por_id = pessoa_id
    evento = registrar_evento(
        sessao, comando, "unidade_apa", f"APA:{unidade_id}",
        "substituir_apa_definitivamente",
        {
            "unidade_id": unidade_id,
            "titular_anterior_id": titular_anterior_id,
            "titular_atual_id": sucessor_id,
            "autorizada_por_id": pessoa_id,
            "motivo": motivo,
            "vigente_de": momento.isoformat(),
        },
        versao_esquema_evento=2,
    )
    resultado = fechar_comando(comando, {
        "permitido": True,
        "motivo": "sucessão definitiva do APA registrada",
        "unidade_id": unidade_id,
        "titular_anterior_id": titular_anterior_id,
        "apa_em_exercicio_id": sucessor_id,
        "evento": evento.sequencia_cadeia,
    })
    sessao.flush()
    return resultado
