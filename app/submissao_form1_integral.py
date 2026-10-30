"""Infraestrutura interna da futura submissão do FORM 1 integral.

Não há rota, botão nem transição de estado. O único comando deste incremento
prepara um snapshot técnico imutável do contrato candidato 3 para que os
mecanismos de versão, autoria, idempotência e auditoria possam ser verificados
antes da decisão institucional de liberar a submissão.
"""

from __future__ import annotations

from copy import deepcopy
import json
import uuid

from sqlalchemy import func, select

from app.comandos import abrir_comando, fechar_comando
from app.eventos import registrar_auditoria, registrar_evento, lacre
from app.form1_integral import (
    REVISAO_FONTE_FORM1_INTEGRAL,
    VERSAO_CONTRATO_FORM1_INTEGRAL_CANDIDATA,
)
from app.modelos import (
    ConfirmacaoCanaisRegistro,
    RascunhoForm1Integral,
    RegistroCanal,
    VersaoForm1Integral,
)
from app.rascunho_form1_integral import (
    _agora_utc,
    _ator,
    _ciclo,
    _contexto_autorizado,
    _lacre,
    _negar,
    _rascunho_bloqueado,
    _validar_versao,
)


TIPO_COMANDO = "preparar_snapshot_form1_integral"


def _texto_canonico(conteudo):
    return json.dumps(
        conteudo, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def _data_texto(valor):
    return None if valor is None else valor.isoformat()


def _retrato_canais(sessao, registro_id):
    confirmacao = sessao.get(ConfirmacaoCanaisRegistro, registro_id)
    if confirmacao is None:
        return {
            "estado": "sem_confirmacao_historica",
            "canais": [],
        }
    canais = sessao.scalars(
        select(RegistroCanal)
        .where(RegistroCanal.registro_id == registro_id)
        .order_by(RegistroCanal.canal_id_snapshot)
    ).all()
    return {
        "estado": "ausencia_confirmada" if not canais else "canais_confirmados",
        "objeto_id": confirmacao.objeto_id,
        "confirmado_por_id": confirmacao.confirmado_por_id,
        "confirmado_em": _data_texto(confirmacao.confirmado_em),
        "canais": [
            {
                "objeto_canal_id": item.objeto_canal_id,
                "objeto_id": item.objeto_id_snapshot,
                "canal_id": item.canal_id_snapshot,
                "canal_nome": item.canal_nome_snapshot,
                "classificacao_form1": item.classificacao_form1_snapshot,
            }
            for item in canais
        ],
    }


def _envelope_snapshot(sessao, rascunho):
    return {
        "natureza": "preparacao_tecnica_sem_submissao",
        "submissao_habilitada": False,
        "contrato": {
            "versao": VERSAO_CONTRATO_FORM1_INTEGRAL_CANDIDATA,
            "revisao_fonte": REVISAO_FONTE_FORM1_INTEGRAL,
        },
        "origem": {
            "versao_rascunho": rascunho.versao_rascunho,
            "salvo_por": rascunho.salvo_por,
            "salvo_em": _data_texto(rascunho.salvo_em),
            "lacre_rascunho": rascunho.lacre_conteudo,
        },
        "form1_integral": deepcopy(rascunho.conteudo),
        "retrato_canais": _retrato_canais(sessao, rascunho.registro_id),
    }


def preparar_snapshot_form1_integral(
    sessao, *, comando_id, conta_id, registro_id, versao_lida, momento=None
):
    """Congela a versão lida sem submeter nem alterar estados do workflow."""

    momento = momento or _agora_utc()
    parametros = {
        "conta_id": conta_id,
        "registro_id": registro_id,
        "versao_lida": versao_lida,
    }
    _conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(
        sessao, comando_id, TIPO_COMANDO, parametros,
        ator_tipo, ator_id, conta_id,
    )
    if resposta is not None:
        return resposta
    problema = _validar_versao(versao_lida)
    if problema:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO, problema,
        )
    registro, pessoa_id, ator_tipo, ator_id, problema = _contexto_autorizado(
        sessao, conta_id, registro_id
    )
    if problema:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO, problema,
        )
    rascunho = _rascunho_bloqueado(sessao, registro_id)
    if rascunho is None:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO, "inicie o rascunho integral antes de preparar o snapshot",
        )
    if rascunho.versao_rascunho != versao_lida:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO,
            "rascunho integral desatualizado: recarregue antes de preparar o snapshot",
            versao_lida=versao_lida,
            versao_atual=rascunho.versao_rascunho,
        )
    if _lacre(rascunho.conteudo) != rascunho.lacre_conteudo:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO, "lacre do rascunho integral não confere",
        )
    existente = sessao.scalars(
        select(VersaoForm1Integral).where(
            VersaoForm1Integral.registro_id == registro_id,
            VersaoForm1Integral.versao_rascunho == versao_lida,
        )
    ).one_or_none()
    if existente is not None:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO,
            "esta versão do rascunho já possui snapshot técnico",
            snapshot_id=existente.id,
        )

    conteudo = _envelope_snapshot(sessao, rascunho)
    canonico = _texto_canonico(conteudo)
    lacre_snapshot = lacre(canonico)
    numero = (sessao.scalar(
        select(func.max(VersaoForm1Integral.numero)).where(
            VersaoForm1Integral.registro_id == registro_id
        )
    ) or 0) + 1
    snapshot_id = str(uuid.uuid4())
    evento = registrar_evento(
        sessao, comando, "registro", registro.codigo_lgpd,
        TIPO_COMANDO,
        {
            "registro_id": registro.id,
            "snapshot_id": snapshot_id,
            "numero": numero,
            "versao_rascunho": versao_lida,
            "versao_contrato": VERSAO_CONTRATO_FORM1_INTEGRAL_CANDIDATA,
            "lacre": lacre_snapshot,
            "submissao_habilitada": False,
        },
        registro_id=registro.id,
        ciclo_id=_ciclo(sessao, registro).id,
        versao_esquema_evento=2,
    )
    sessao.add(VersaoForm1Integral(
        id=snapshot_id,
        registro_id=registro.id,
        numero=numero,
        versao_rascunho=versao_lida,
        versao_contrato=VERSAO_CONTRATO_FORM1_INTEGRAL_CANDIDATA,
        revisao_fonte=REVISAO_FONTE_FORM1_INTEGRAL,
        conteudo=conteudo,
        conteudo_canonico=canonico,
        lacre=lacre_snapshot,
        preparado_por=pessoa_id,
        preparado_em=momento,
        evento_preparacao_id=evento.id,
    ))
    registrar_auditoria(
        sessao, "snapshot_form1_integral_preparado", ator_tipo, ator_id,
        {
            "registro_id": registro.id,
            "snapshot_id": snapshot_id,
            "versao_rascunho": versao_lida,
            "submissao_habilitada": False,
        },
        comando_id=comando.id,
    )
    registro.sequencia_atual = evento.sequencia_cadeia
    resultado = fechar_comando(comando, {
        "permitido": True,
        "motivo": "Snapshot técnico do FORM 1 integral preparado",
        "registro_id": registro.id,
        "snapshot_id": snapshot_id,
        "numero": numero,
        "versao_rascunho": versao_lida,
        "versao_contrato": VERSAO_CONTRATO_FORM1_INTEGRAL_CANDIDATA,
        "lacre": lacre_snapshot,
        "evento": evento.sequencia_cadeia,
        "submissao_habilitada": False,
    })
    sessao.flush()
    return resultado
