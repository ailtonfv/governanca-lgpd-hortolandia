"""Atos das pendências usados pelo núcleo do M1a."""

from copy import deepcopy
from datetime import datetime, timezone
import uuid

from sqlalchemy import select

from app.comandos import abrir_comando, fechar_comando
from app.eventos import lacre, registrar_auditoria, registrar_evento
from app.instrumentos import conteudo_canonico
from app.modelos import (Ciclo, Conta, Evento, Instrumento, Pendencia,
                         RascunhoInstrumento, Registro, Unidade, VersaoInstrumento)
from app.permissoes import tem_papel


CAMPOS_RESPOSTA_INTERSECRETARIAL = {
    "etapa_executada", "entrada_recebida", "operacoes_realizadas",
    "saida_produzida", "interfaces_seguinte", "evidencias",
}


def agora_utc():
    return datetime.now(timezone.utc)


def _ator(sessao, conta_id):
    conta = sessao.get(Conta, conta_id)
    pessoa_id = conta.pessoa_id if conta is not None else None
    ator_tipo, ator_id = (("pessoa", pessoa_id) if pessoa_id
                          else ("desconhecido", conta_id))
    return conta, pessoa_id, ator_tipo, ator_id


def _negar(sessao, comando, ator_tipo, ator_id, acao, conta_id, pendencia_id, motivo,
           **detalhes):
    registrar_auditoria(
        sessao, "tentativa_negada", ator_tipo, ator_id,
        {"acao_tentada": acao, "pendencia_id": pendencia_id,
         "conta_id": conta_id, "motivo": motivo},
        comando_id=None if comando is None else comando.id,
    )
    resultado = dict({"permitido": False, "motivo": motivo}, **detalhes)
    if comando is None:
        return dict(resultado, reexecutado=False)
    resposta = fechar_comando(comando, resultado)
    sessao.flush()
    return resposta


def _texto_curto(valor, limite=1000):
    if not isinstance(valor, str):
        return None
    texto = " ".join(valor.split())
    return texto if texto and len(texto) <= limite else None


def _lista_textos(valor, *, obrigatoria, limite_itens=20, limite_texto=500):
    if not isinstance(valor, list) or len(valor) > limite_itens:
        return None
    itens = [_texto_curto(item, limite_texto) for item in valor]
    if any(item is None for item in itens) or (obrigatoria and not itens):
        return None
    return itens


def _normalizar_resposta_intersecretarial(resposta):
    """Contrato mínimo fechado da participação; rejeita campos livres imprevistos."""
    if not isinstance(resposta, dict) or set(resposta) != CAMPOS_RESPOSTA_INTERSECRETARIAL:
        return None
    etapa = _texto_curto(resposta["etapa_executada"])
    entrada = _texto_curto(resposta["entrada_recebida"])
    operacoes = _lista_textos(resposta["operacoes_realizadas"], obrigatoria=True)
    saida = _texto_curto(resposta["saida_produzida"])
    interfaces = _lista_textos(resposta["interfaces_seguinte"], obrigatoria=False)
    evidencias = _lista_textos(resposta["evidencias"], obrigatoria=True)
    if any(item is None for item in (etapa, entrada, operacoes, saida, interfaces, evidencias)):
        return None
    return {
        "etapa_executada": etapa,
        "entrada_recebida": entrada,
        "operacoes_realizadas": operacoes,
        "saida_produzida": saida,
        "interfaces_seguinte": interfaces,
        "evidencias": evidencias,
    }


def criar_pendencia_intersecretarial(
        sessao, *, comando_id, conta_id, registro_id, unidade_destino_id,
        solicitacao, itens_atribuidos, momento=None):
    """P1 humano — encaminha uma participação à fila de outra unidade."""
    momento = momento or agora_utc()
    solicitacao = _texto_curto(solicitacao)
    itens = _lista_textos(itens_atribuidos, obrigatoria=True)
    parametros = {
        "conta_id": conta_id, "registro_id": registro_id,
        "unidade_destino_id": unidade_destino_id, "solicitacao": solicitacao,
        "itens_atribuidos": itens_atribuidos,
    }
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(
        sessao, comando_id, "criar_pendencia_intersecretarial", parametros,
        ator_tipo, ator_id, conta_id,
    )
    if resposta is not None:
        return resposta

    pendencia_id = str(uuid.uuid4())

    def negar(motivo, **detalhes):
        return _negar(
            sessao, comando, ator_tipo, ator_id,
            "criar_pendencia_intersecretarial", conta_id, pendencia_id,
            motivo, **detalhes,
        )

    if solicitacao is None:
        return negar("P1 exige solicitação textual entre 1 e 1000 caracteres")
    if itens is None:
        return negar("P1 exige de 1 a 20 itens atribuídos, com até 500 caracteres cada")

    registro = sessao.scalars(
        select(Registro).where(Registro.id == registro_id).with_for_update()
    ).one_or_none()
    if registro is None:
        return negar("Registro inexistente")
    if conta is None or not conta.ativa:
        return negar("conta inexistente ou desativada")
    if registro.estado_atual not in {"em_andamento", "em_validacao", "em_execucao"}:
        return negar(
            "P1 intersecretarial exige Registro ativo no M1a",
            estado_registro=registro.estado_atual,
        )
    if not tem_papel(
            sessao, pessoa_id, registro.unidade_principal_atual_id,
            {"agente_pendencia"}):
        return negar("a pessoa não está designada para criar pendências pela unidade de origem")

    destino = sessao.get(Unidade, unidade_destino_id)
    if destino is None or not destino.ativa:
        return negar("unidade de destino inexistente ou desativada")
    if destino.id == registro.unidade_principal_atual_id:
        return negar("a pendência intersecretarial exige unidade de destino diferente da origem")

    ciclo = sessao.scalars(
        select(Ciclo).where(
            Ciclo.registro_id == registro.id, Ciclo.numero == registro.ciclo_atual,
        ).with_for_update()
    ).one_or_none()
    if ciclo is None or ciclo.situacao != "ativo":
        return negar("o ciclo atual do Registro não está ativo")

    evento_p1 = registrar_evento(
        sessao, comando, "pendencia", pendencia_id,
        "criar_pendencia_intersecretarial",
        {"pendencia_id": pendencia_id, "tipo_pendencia": "participacao",
         "registro_id": registro.id,
         "unidade_origem_id": registro.unidade_principal_atual_id,
         "unidade_destino_id": destino.id, "solicitacao": solicitacao,
         "itens_atribuidos": itens, "bloqueante": True,
         "gate_bloqueado": "conclusao", "estado_atual": "aberta",
         "conta_id": conta_id},
        codigo_evento="P1", registro_id=registro.id, ciclo_id=ciclo.id,
        versao_esquema_evento=2,
    )
    sessao.add(Pendencia(
        id=pendencia_id, tipo_pendencia="participacao", registro_id=registro.id,
        ciclo_origem_id=ciclo.id, ciclo_contexto_atual_id=ciclo.id,
        instrumento_id=None, evento_origem_id=evento_p1.id,
        unidade_origem_id=registro.unidade_principal_atual_id,
        unidade_destino_id=destino.id, responsavel_atual_id=None,
        estado="aberta", bloqueante=True, gate_bloqueado="conclusao",
        motivo=solicitacao, criada_em=momento, atualizada_em=momento,
    ))
    resultado = fechar_comando(
        comando,
        {"permitido": True, "motivo": "Pendência intersecretarial criada",
         "pendencia_id": pendencia_id, "registro_id": registro.id,
         "unidade_origem_id": registro.unidade_principal_atual_id,
         "unidade_destino_id": destino.id, "estado_pendencia": "aberta",
         "gate_bloqueado": "conclusao",
         "evento_p1": evento_p1.sequencia_cadeia},
    )
    sessao.flush()
    return resultado


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
        return _negar(sessao, comando, ator_tipo, ator_id, "assumir_pendencia",
                      conta_id, pendencia_id,
                      "Pendência inexistente")
    if conta is None or not conta.ativa:
        return _negar(sessao, comando, ator_tipo, ator_id, "assumir_pendencia",
                      conta_id, pendencia_id,
                      "conta inexistente ou desativada")
    papeis_destino = ({"elaborador"} if pendencia.tipo_pendencia == "devolucao"
                      else {"agente_pendencia"})
    if not tem_papel(sessao, pessoa_id, pendencia.unidade_destino_id, papeis_destino):
        return _negar(
            sessao, comando, ator_tipo, ator_id, "assumir_pendencia",
            conta_id, pendencia_id,
            "a pessoa não está autorizada a assumir pendências desta unidade",
        )
    if pendencia.estado != "aberta":
        return _negar(
            sessao, comando, ator_tipo, ator_id, "assumir_pendencia",
            conta_id, pendencia_id,
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


def responder_pendencia_intersecretarial(
        sessao, *, comando_id, conta_id, pendencia_id, resposta, momento=None):
    """P3 — registra a participação e suas evidências, sem editar Instrumento."""
    momento = momento or agora_utc()
    resposta_normalizada = _normalizar_resposta_intersecretarial(resposta)
    parametros = {
        "conta_id": conta_id, "pendencia_id": pendencia_id,
        "resposta": deepcopy(resposta),
    }
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, repeticao = abrir_comando(
        sessao, comando_id, "responder_pendencia_intersecretarial", parametros,
        ator_tipo, ator_id, conta_id,
    )
    if repeticao is not None:
        return repeticao
    if resposta_normalizada is None:
        return _negar(
            sessao, comando, ator_tipo, ator_id,
            "responder_pendencia_intersecretarial", conta_id, pendencia_id,
            "P3 exige resposta estruturada completa, sem campos adicionais",
        )

    pendencia = sessao.scalars(
        select(Pendencia).where(Pendencia.id == pendencia_id).with_for_update()
    ).one_or_none()
    if pendencia is None or pendencia.tipo_pendencia != "participacao":
        return _negar(
            sessao, comando, ator_tipo, ator_id,
            "responder_pendencia_intersecretarial", conta_id, pendencia_id,
            "a pendência informada não é uma participação intersecretarial",
        )
    if conta is None or not conta.ativa:
        return _negar(
            sessao, comando, ator_tipo, ator_id,
            "responder_pendencia_intersecretarial", conta_id, pendencia_id,
            "conta inexistente ou desativada",
        )
    if pendencia.estado != "em_atendimento":
        return _negar(
            sessao, comando, ator_tipo, ator_id,
            "responder_pendencia_intersecretarial", conta_id, pendencia_id,
            "P3 exige pendência em_atendimento",
            estado_pendencia=pendencia.estado,
        )
    if pendencia.responsavel_atual_id != pessoa_id:
        return _negar(
            sessao, comando, ator_tipo, ator_id,
            "responder_pendencia_intersecretarial", conta_id, pendencia_id,
            "P3 só pode ser executado pelo agente que assumiu a pendência",
            responsavel_atual_id=pendencia.responsavel_atual_id,
        )
    if not tem_papel(
            sessao, pessoa_id, pendencia.unidade_destino_id,
            {"agente_pendencia"}):
        return _negar(
            sessao, comando, ator_tipo, ator_id,
            "responder_pendencia_intersecretarial", conta_id, pendencia_id,
            "a pessoa não está designada para responder pela unidade de destino",
        )

    estado_anterior = pendencia.estado
    lacre_resposta = lacre(conteudo_canonico(resposta_normalizada))
    pendencia.estado = "respondida"
    pendencia.lacre_resposta = lacre_resposta
    pendencia.atualizada_em = momento
    evento_p3 = registrar_evento(
        sessao, comando, "pendencia", pendencia.id,
        "responder_pendencia_intersecretarial",
        {"pendencia_id": pendencia.id, "tipo_pendencia": pendencia.tipo_pendencia,
         "estado_anterior": estado_anterior, "estado_atual": "respondida",
         "unidade_destino_id": pendencia.unidade_destino_id,
         "responsavel_atual_id": pessoa_id,
         "resposta": deepcopy(resposta_normalizada),
         "lacre_resposta": lacre_resposta, "conta_id": conta_id},
        codigo_evento="P3", registro_id=pendencia.registro_id,
        ciclo_id=pendencia.ciclo_contexto_atual_id, versao_esquema_evento=2,
    )
    resultado = fechar_comando(
        comando,
        {"permitido": True, "motivo": "Participação intersecretarial respondida",
         "pendencia_id": pendencia.id, "estado_pendencia": "respondida",
         "lacre_resposta": lacre_resposta,
         "evento_p3": evento_p3.sequencia_cadeia},
    )
    sessao.flush()
    return resultado


def aceitar_pendencia_intersecretarial(
        sessao, *, comando_id, conta_id, pendencia_id, momento=None):
    """P4 — a unidade de origem aceita a participação e encerra a pendência."""
    momento = momento or agora_utc()
    parametros = {"conta_id": conta_id, "pendencia_id": pendencia_id}
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, repeticao = abrir_comando(
        sessao, comando_id, "aceitar_pendencia_intersecretarial", parametros,
        ator_tipo, ator_id, conta_id,
    )
    if repeticao is not None:
        return repeticao

    pendencia = sessao.scalars(
        select(Pendencia).where(Pendencia.id == pendencia_id).with_for_update()
    ).one_or_none()
    if pendencia is None or pendencia.tipo_pendencia != "participacao":
        return _negar(
            sessao, comando, ator_tipo, ator_id,
            "aceitar_pendencia_intersecretarial", conta_id, pendencia_id,
            "a pendência informada não é uma participação intersecretarial",
        )
    if conta is None or not conta.ativa:
        return _negar(
            sessao, comando, ator_tipo, ator_id,
            "aceitar_pendencia_intersecretarial", conta_id, pendencia_id,
            "conta inexistente ou desativada",
        )
    if not tem_papel(
            sessao, pessoa_id, pendencia.unidade_origem_id,
            {"agente_pendencia"}):
        return _negar(
            sessao, comando, ator_tipo, ator_id,
            "aceitar_pendencia_intersecretarial", conta_id, pendencia_id,
            "a pessoa não está designada para aceitar pela unidade de origem",
        )
    if pendencia.estado != "respondida":
        return _negar(
            sessao, comando, ator_tipo, ator_id,
            "aceitar_pendencia_intersecretarial", conta_id, pendencia_id,
            "P4 exige pendência respondida",
            estado_pendencia=pendencia.estado,
        )
    if not pendencia.lacre_resposta:
        return _negar(
            sessao, comando, ator_tipo, ator_id,
            "aceitar_pendencia_intersecretarial", conta_id, pendencia_id,
            "pendência respondida não possui lacre da resposta; inconsistência detectada",
        )

    estado_anterior = pendencia.estado
    pendencia.estado = "encerrada"
    pendencia.bloqueante = False
    pendencia.gate_bloqueado = None
    pendencia.lacre_aceito = pendencia.lacre_resposta
    pendencia.atualizada_em = momento
    evento_p4 = registrar_evento(
        sessao, comando, "pendencia", pendencia.id,
        "aceitar_pendencia_intersecretarial",
        {"pendencia_id": pendencia.id, "tipo_pendencia": pendencia.tipo_pendencia,
         "estado_anterior": estado_anterior, "estado_atual": "encerrada",
         "unidade_origem_id": pendencia.unidade_origem_id,
         "lacre_aceito": pendencia.lacre_aceito, "conta_id": conta_id},
        codigo_evento="P4", registro_id=pendencia.registro_id,
        ciclo_id=pendencia.ciclo_contexto_atual_id, versao_esquema_evento=2,
    )
    resultado = fechar_comando(
        comando,
        {"permitido": True, "motivo": "Participação intersecretarial aceita",
         "pendencia_id": pendencia.id, "estado_pendencia": "encerrada",
         "lacre_aceito": pendencia.lacre_aceito,
         "evento_p4": evento_p4.sequencia_cadeia},
    )
    sessao.flush()
    return resultado


def responder_pendencia(sessao, *, comando_id, conta_id, pendencia_id,
                        instrumento_id, versao_lida, momento=None):
    """P3 — registra o lacre do rascunho corrigido e congela novas alterações."""
    momento = momento or agora_utc()
    parametros = {"conta_id": conta_id, "pendencia_id": pendencia_id,
                  "instrumento_id": instrumento_id, "versao_lida": versao_lida}
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(sessao, comando_id, "responder_pendencia", parametros,
                                      ator_tipo, ator_id, conta_id)
    if resposta is not None:
        return resposta

    if not isinstance(versao_lida, int) or isinstance(versao_lida, bool) or versao_lida < 1:
        return _negar(
            sessao, comando, ator_tipo, ator_id, "responder_pendencia",
            conta_id, pendencia_id, "versao_lida deve ser um inteiro positivo",
        )

    # A mesma ordem de trava usada pelo I2 evita que uma resposta e um salvamento
    # concorrentes confirmem silenciosamente conteúdos diferentes.
    instrumento = sessao.scalars(
        select(Instrumento).where(Instrumento.id == instrumento_id).with_for_update()
    ).one_or_none()
    pendencia = sessao.scalars(
        select(Pendencia).where(Pendencia.id == pendencia_id).with_for_update()
    ).one_or_none()
    if instrumento is None:
        return _negar(
            sessao, comando, ator_tipo, ator_id, "responder_pendencia",
            conta_id, pendencia_id, "Instrumento inexistente",
        )
    if (pendencia is None or pendencia.instrumento_id != instrumento.id
            or pendencia.tipo_pendencia != "devolucao"):
        return _negar(
            sessao, comando, ator_tipo, ator_id, "responder_pendencia",
            conta_id, pendencia_id,
            "a pendência informada não é a devolução deste Instrumento",
        )
    if conta is None or not conta.ativa:
        return _negar(
            sessao, comando, ator_tipo, ator_id, "responder_pendencia",
            conta_id, pendencia_id, "conta inexistente ou desativada",
        )
    if pendencia.estado != "em_atendimento":
        return _negar(
            sessao, comando, ator_tipo, ator_id, "responder_pendencia",
            conta_id, pendencia_id, "P3 exige pendência em_atendimento",
            estado_pendencia=pendencia.estado,
        )
    if pendencia.responsavel_atual_id != pessoa_id:
        return _negar(
            sessao, comando, ator_tipo, ator_id, "responder_pendencia",
            conta_id, pendencia_id,
            "P3 só pode ser executado pelo agente que assumiu a pendência",
            responsavel_atual_id=pendencia.responsavel_atual_id,
        )
    if instrumento.estado_instrumento != "em_preenchimento":
        return _negar(
            sessao, comando, ator_tipo, ator_id, "responder_pendencia",
            conta_id, pendencia_id,
            "P3 exige Instrumento no estado em_preenchimento",
            estado_instrumento=instrumento.estado_instrumento,
        )

    rascunho = sessao.scalars(
        select(RascunhoInstrumento)
        .where(RascunhoInstrumento.instrumento_id == instrumento.id)
        .with_for_update()
    ).one_or_none()
    if rascunho is None:
        return _negar(
            sessao, comando, ator_tipo, ator_id, "responder_pendencia",
            conta_id, pendencia_id,
            "Instrumento em_preenchimento não possui rascunho; inconsistência detectada",
        )
    if rascunho.versao_rascunho != versao_lida:
        return _negar(
            sessao, comando, ator_tipo, ator_id, "responder_pendencia",
            conta_id, pendencia_id,
            "rascunho desatualizado: recarregue antes de responder",
            versao_lida=versao_lida, versao_atual=rascunho.versao_rascunho,
        )

    estado_anterior = pendencia.estado
    pendencia.estado = "respondida"
    pendencia.lacre_resposta = rascunho.lacre_conteudo
    pendencia.atualizada_em = momento
    evento_p3 = registrar_evento(
        sessao, comando, "pendencia", pendencia.id, "responder_pendencia",
        {"pendencia_id": pendencia.id, "instrumento_id": instrumento.id,
         "estado_anterior": estado_anterior, "estado_atual": "respondida",
         "versao_rascunho": rascunho.versao_rascunho,
         "lacre_resposta": rascunho.lacre_conteudo, "conta_id": conta_id},
        codigo_evento="P3", registro_id=pendencia.registro_id,
        ciclo_id=pendencia.ciclo_contexto_atual_id, versao_esquema_evento=2,
    )
    resultado = fechar_comando(
        comando,
        {"permitido": True, "motivo": "Correção apresentada",
         "pendencia_id": pendencia.id, "instrumento_id": instrumento.id,
         "estado_pendencia": "respondida",
         "versao_rascunho": rascunho.versao_rascunho,
         "lacre_resposta": rascunho.lacre_conteudo,
         "evento_p3": evento_p3.sequencia_cadeia},
    )
    sessao.flush()
    return resultado


def _versao_devolvida(sessao, pendencia):
    evento_origem = sessao.get(Evento, pendencia.evento_origem_id)
    versao_id = None if evento_origem is None else evento_origem.conteudo.get("versao_id")
    return sessao.get(VersaoInstrumento, versao_id) if versao_id else None


def _validar_decisao(sessao, comando, conta, pessoa_id, ator_tipo, ator_id,
                     acao, conta_id, pendencia_id, instrumento_id):
    instrumento = sessao.scalars(
        select(Instrumento).where(Instrumento.id == instrumento_id).with_for_update()
    ).one_or_none()
    pendencia = sessao.scalars(
        select(Pendencia).where(Pendencia.id == pendencia_id).with_for_update()
    ).one_or_none()
    if instrumento is None:
        return None, None, None, _negar(
            sessao, comando, ator_tipo, ator_id, acao, conta_id, pendencia_id,
            "Instrumento inexistente",
        )
    if (pendencia is None or pendencia.instrumento_id != instrumento.id
            or pendencia.tipo_pendencia != "devolucao"):
        return None, None, None, _negar(
            sessao, comando, ator_tipo, ator_id, acao, conta_id, pendencia_id,
            "a pendência informada não é a devolução deste Instrumento",
        )
    if conta is None or not conta.ativa:
        return None, None, None, _negar(
            sessao, comando, ator_tipo, ator_id, acao, conta_id, pendencia_id,
            "conta inexistente ou desativada",
        )
    if not tem_papel(sessao, pessoa_id, pendencia.unidade_origem_id, {"validador"}):
        return None, None, None, _negar(
            sessao, comando, ator_tipo, ator_id, acao, conta_id, pendencia_id,
            "a pessoa não tem competência de validador na unidade responsável",
        )
    if pendencia.estado != "respondida":
        return None, None, None, _negar(
            sessao, comando, ator_tipo, ator_id, acao, conta_id, pendencia_id,
            f"{acao} exige pendência respondida", estado_pendencia=pendencia.estado,
        )
    if not pendencia.lacre_resposta:
        return None, None, None, _negar(
            sessao, comando, ator_tipo, ator_id, acao, conta_id, pendencia_id,
            "pendência respondida não possui lacre da resposta; inconsistência detectada",
        )

    versao = _versao_devolvida(sessao, pendencia)
    if versao is None or versao.instrumento_id != instrumento.id:
        return None, None, None, _negar(
            sessao, comando, ator_tipo, ator_id, acao, conta_id, pendencia_id,
            "a pendência não aponta para uma versão devolvida válida",
        )
    if versao.submetida_por == pessoa_id:
        return None, None, None, _negar(
            sessao, comando, ator_tipo, ator_id, acao, conta_id, pendencia_id,
            "segregação de funções: a pessoa é autora da submissão",
        )

    rascunho = sessao.scalars(
        select(RascunhoInstrumento)
        .where(RascunhoInstrumento.instrumento_id == instrumento.id)
        .with_for_update()
    ).one_or_none()
    if rascunho is None or rascunho.lacre_conteudo != pendencia.lacre_resposta:
        return None, None, None, _negar(
            sessao, comando, ator_tipo, ator_id, acao, conta_id, pendencia_id,
            "o rascunho não coincide com a resposta apresentada",
        )
    return instrumento, pendencia, rascunho, None


def aceitar_resposta(sessao, *, comando_id, conta_id, pendencia_id,
                     instrumento_id, momento=None):
    """P4 — aceita o lacre apresentado e encerra a pendência de devolução."""
    momento = momento or agora_utc()
    parametros = {"conta_id": conta_id, "pendencia_id": pendencia_id,
                  "instrumento_id": instrumento_id}
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(sessao, comando_id, "aceitar_resposta", parametros,
                                      ator_tipo, ator_id, conta_id)
    if resposta is not None:
        return resposta

    instrumento, pendencia, rascunho, negado = _validar_decisao(
        sessao, comando, conta, pessoa_id, ator_tipo, ator_id, "P4",
        conta_id, pendencia_id, instrumento_id,
    )
    if negado is not None:
        return negado

    estado_anterior = pendencia.estado
    pendencia.estado = "encerrada"
    pendencia.bloqueante = False
    pendencia.gate_bloqueado = None
    pendencia.lacre_aceito = pendencia.lacre_resposta
    pendencia.atualizada_em = momento
    evento_p4 = registrar_evento(
        sessao, comando, "pendencia", pendencia.id, "aceitar_resposta",
        {"pendencia_id": pendencia.id, "instrumento_id": instrumento.id,
         "estado_anterior": estado_anterior, "estado_atual": "encerrada",
         "versao_rascunho": rascunho.versao_rascunho,
         "lacre_aceito": pendencia.lacre_aceito, "conta_id": conta_id},
        codigo_evento="P4", registro_id=pendencia.registro_id,
        ciclo_id=pendencia.ciclo_contexto_atual_id, versao_esquema_evento=2,
    )
    resultado = fechar_comando(
        comando,
        {"permitido": True, "motivo": "Resposta aceita",
         "pendencia_id": pendencia.id, "instrumento_id": instrumento.id,
         "estado_pendencia": "encerrada", "lacre_aceito": pendencia.lacre_aceito,
         "evento_p4": evento_p4.sequencia_cadeia},
    )
    sessao.flush()
    return resultado


def devolver_resposta(sessao, *, comando_id, conta_id, pendencia_id,
                      instrumento_id, motivo, momento=None):
    """P5 — devolve a mesma pendência de I6 para complementação, com motivo."""
    momento = momento or agora_utc()
    motivo = " ".join(motivo.split()) if isinstance(motivo, str) else ""
    parametros = {"conta_id": conta_id, "pendencia_id": pendencia_id,
                  "instrumento_id": instrumento_id, "motivo": motivo}
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(sessao, comando_id, "devolver_resposta", parametros,
                                      ator_tipo, ator_id, conta_id)
    if resposta is not None:
        return resposta
    if not motivo:
        return _negar(
            sessao, comando, ator_tipo, ator_id, "P5", conta_id, pendencia_id,
            "P5 exige motivo obrigatório",
        )

    instrumento, pendencia, rascunho, negado = _validar_decisao(
        sessao, comando, conta, pessoa_id, ator_tipo, ator_id, "P5",
        conta_id, pendencia_id, instrumento_id,
    )
    if negado is not None:
        return negado

    estado_anterior = pendencia.estado
    motivo_anterior = pendencia.motivo
    pendencia.estado = "devolvida_para_complementacao"
    pendencia.motivo = motivo
    pendencia.atualizada_em = momento
    evento_p5 = registrar_evento(
        sessao, comando, "pendencia", pendencia.id, "devolver_resposta",
        {"pendencia_id": pendencia.id, "instrumento_id": instrumento.id,
         "estado_anterior": estado_anterior,
         "estado_atual": "devolvida_para_complementacao",
         "versao_rascunho": rascunho.versao_rascunho,
         "lacre_resposta": pendencia.lacre_resposta,
         "motivo_anterior": motivo_anterior, "motivo": motivo,
         "conta_id": conta_id},
        codigo_evento="P5", registro_id=pendencia.registro_id,
        ciclo_id=pendencia.ciclo_contexto_atual_id, versao_esquema_evento=2,
    )
    resultado = fechar_comando(
        comando,
        {"permitido": True, "motivo": "Resposta devolvida para complementação",
         "pendencia_id": pendencia.id, "instrumento_id": instrumento.id,
         "estado_pendencia": "devolvida_para_complementacao",
         "motivo_complementacao": motivo,
         "evento_p5": evento_p5.sequencia_cadeia},
    )
    sessao.flush()
    return resultado


def retomar_pendencia(sessao, *, comando_id, conta_id, pendencia_id,
                      instrumento_id, momento=None):
    """P6 — retoma a pendência de I6 e libera o rascunho para nova correção."""
    momento = momento or agora_utc()
    parametros = {"conta_id": conta_id, "pendencia_id": pendencia_id,
                  "instrumento_id": instrumento_id}
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(sessao, comando_id, "retomar_pendencia", parametros,
                                      ator_tipo, ator_id, conta_id)
    if resposta is not None:
        return resposta

    instrumento = sessao.scalars(
        select(Instrumento).where(Instrumento.id == instrumento_id).with_for_update()
    ).one_or_none()
    pendencia = sessao.scalars(
        select(Pendencia).where(Pendencia.id == pendencia_id).with_for_update()
    ).one_or_none()
    if instrumento is None:
        return _negar(sessao, comando, ator_tipo, ator_id, "P6", conta_id,
                      pendencia_id, "Instrumento inexistente")
    if (pendencia is None or pendencia.instrumento_id != instrumento.id
            or pendencia.tipo_pendencia != "devolucao"):
        return _negar(
            sessao, comando, ator_tipo, ator_id, "P6", conta_id, pendencia_id,
            "a pendência informada não é a devolução deste Instrumento",
        )
    if conta is None or not conta.ativa:
        return _negar(sessao, comando, ator_tipo, ator_id, "P6", conta_id,
                      pendencia_id, "conta inexistente ou desativada")
    if pendencia.estado != "devolvida_para_complementacao":
        return _negar(
            sessao, comando, ator_tipo, ator_id, "P6", conta_id, pendencia_id,
            "P6 exige pendência devolvida_para_complementacao",
            estado_pendencia=pendencia.estado,
        )
    if pendencia.responsavel_atual_id != pessoa_id:
        return _negar(
            sessao, comando, ator_tipo, ator_id, "P6", conta_id, pendencia_id,
            "P6 só pode ser executado pelo agente responsável pela pendência",
            responsavel_atual_id=pendencia.responsavel_atual_id,
        )
    if not tem_papel(sessao, pessoa_id, pendencia.unidade_destino_id, {"elaborador"}):
        return _negar(
            sessao, comando, ator_tipo, ator_id, "P6", conta_id, pendencia_id,
            "a pessoa não está autorizada a retomar pendências desta unidade",
        )

    estado_anterior = pendencia.estado
    lacre_resposta_anterior = pendencia.lacre_resposta
    pendencia.estado = "em_atendimento"
    pendencia.lacre_resposta = None
    pendencia.atualizada_em = momento
    evento_p6 = registrar_evento(
        sessao, comando, "pendencia", pendencia.id, "retomar_pendencia",
        {"pendencia_id": pendencia.id, "instrumento_id": instrumento.id,
         "estado_anterior": estado_anterior, "estado_atual": "em_atendimento",
         "lacre_resposta_anterior": lacre_resposta_anterior, "conta_id": conta_id},
        codigo_evento="P6", registro_id=pendencia.registro_id,
        ciclo_id=pendencia.ciclo_contexto_atual_id, versao_esquema_evento=2,
    )
    resultado = fechar_comando(
        comando,
        {"permitido": True, "motivo": "Pendência retomada para complementação",
         "pendencia_id": pendencia.id, "instrumento_id": instrumento.id,
         "estado_pendencia": "em_atendimento",
         "evento_p6": evento_p6.sequencia_cadeia},
    )
    sessao.flush()
    return resultado
