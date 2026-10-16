"""Atos do Instrumento usados pelo núcleo do M1a.

Este módulo começa pelo menor corte executável do FORM 1 sintético:
I1 abre o preenchimento e I2 salva o rascunho com controle otimista.
I3 e as versões imutáveis ficam para o incremento seguinte.
"""

import json
from datetime import datetime, timezone

from sqlalchemy import select

from app.comandos import abrir_comando, fechar_comando
from app.eventos import lacre, registrar_auditoria, registrar_evento
from app.modelos import Ciclo, Conta, Instrumento, RascunhoInstrumento, Registro
from app.permissoes import tem_papel


def agora_utc():
    return datetime.now(timezone.utc)


def conteudo_canonico(conteudo):
    """Representação estável do rascunho usada pelo lacre e pelos testes posteriores."""
    return json.dumps(conteudo, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def lacre_do_conteudo(conteudo):
    return lacre(conteudo_canonico(conteudo))


def _ator(sessao, conta_id):
    conta = sessao.get(Conta, conta_id)
    pessoa_id = conta.pessoa_id if conta is not None else None
    ator_tipo, ator_id = (("pessoa", pessoa_id) if pessoa_id
                          else ("desconhecido", conta_id))
    return conta, pessoa_id, ator_tipo, ator_id


def _contexto_do_instrumento(sessao, instrumento_id):
    """Trava o Instrumento: todos os atos futuros da mesma cadeia devem usar esta trava."""
    instrumento = sessao.scalars(
        select(Instrumento).where(Instrumento.id == instrumento_id).with_for_update()
    ).one_or_none()
    if instrumento is None:
        return None, None, None
    registro = sessao.get(Registro, instrumento.registro_id)
    ciclo = sessao.scalars(
        select(Ciclo).where(Ciclo.registro_id == registro.id,
                            Ciclo.numero == registro.ciclo_atual)
    ).one()
    return instrumento, registro, ciclo


def _pode_preencher(sessao, conta, pessoa_id, registro):
    if conta is None or not conta.ativa:
        return False, "conta inexistente ou desativada"
    if not tem_papel(sessao, pessoa_id, registro.unidade_principal_atual_id, {"elaborador"}):
        return False, "a pessoa não tem papel de elaborador na unidade responsável"
    return True, "permitido"


def _negar(sessao, comando, ator_tipo, ator_id, acao, conta_id, instrumento_id, motivo,
           **detalhes):
    registrar_auditoria(
        sessao, "tentativa_negada", ator_tipo, ator_id,
        {"acao_tentada": acao, "instrumento_id": instrumento_id,
         "conta_id": conta_id, "motivo": motivo},
        comando_id=None if comando is None else comando.id,
    )
    resultado = dict({"permitido": False, "motivo": motivo}, **detalhes)
    if comando is None:
        return dict(resultado, reexecutado=False)
    resposta = fechar_comando(comando, resultado)
    sessao.flush()
    return resposta


def iniciar_preenchimento(sessao, *, comando_id, conta_id, instrumento_id, momento=None):
    """I1 — cria o rascunho vazio e leva o Instrumento a ``em_preenchimento``."""
    momento = momento or agora_utc()
    parametros = {"conta_id": conta_id, "instrumento_id": instrumento_id}
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(sessao, comando_id, "iniciar_preenchimento", parametros,
                                      ator_tipo, ator_id, conta_id)
    if resposta is not None:
        return resposta

    instrumento, registro, ciclo = _contexto_do_instrumento(sessao, instrumento_id)
    if instrumento is None:
        return _negar(sessao, comando, ator_tipo, ator_id, "iniciar_preenchimento",
                      conta_id, instrumento_id, "Instrumento inexistente")
    permitido, motivo = _pode_preencher(sessao, conta, pessoa_id, registro)
    if not permitido:
        return _negar(sessao, comando, ator_tipo, ator_id, "iniciar_preenchimento",
                      conta_id, instrumento_id, motivo)
    if instrumento.estado_instrumento != "nao_iniciado":
        return _negar(sessao, comando, ator_tipo, ator_id, "iniciar_preenchimento",
                      conta_id, instrumento_id,
                      "I1 exige Instrumento no estado nao_iniciado",
                      estado_atual=instrumento.estado_instrumento)
    if sessao.get(RascunhoInstrumento, instrumento.id) is not None:
        return _negar(sessao, comando, ator_tipo, ator_id, "iniciar_preenchimento",
                      conta_id, instrumento_id,
                      "Instrumento nao_iniciado já possui rascunho; inconsistência detectada")

    conteudo = {}
    rascunho = RascunhoInstrumento(
        instrumento_id=instrumento.id,
        conteudo=conteudo,
        versao_rascunho=1,
        salvo_por=pessoa_id,
        salvo_em=momento,
        lacre_conteudo=lacre_do_conteudo(conteudo),
    )
    sessao.add(rascunho)
    instrumento.estado_instrumento = "em_preenchimento"
    evento = registrar_evento(
        sessao, comando, "instrumento", instrumento.id, "iniciar_preenchimento",
        {"instrumento_id": instrumento.id, "tipo_instrumento": instrumento.tipo_instrumento,
         "versao_rascunho": 1, "lacre_conteudo": rascunho.lacre_conteudo,
         "conta_id": conta_id},
        codigo_evento="I1", registro_id=registro.id, ciclo_id=ciclo.id,
        versao_esquema_evento=2,
    )
    resultado = fechar_comando(
        comando,
        {"permitido": True, "motivo": "preenchimento iniciado",
         "instrumento_id": instrumento.id, "estado_instrumento": "em_preenchimento",
         "versao_rascunho": 1, "lacre_conteudo": rascunho.lacre_conteudo,
         "evento_i1": evento.sequencia_cadeia},
    )
    sessao.flush()
    return resultado


def salvar_rascunho(sessao, *, comando_id, conta_id, instrumento_id, versao_lida,
                    conteudo, momento=None):
    """I2 — substitui o rascunho se ``versao_lida`` ainda for a versão vigente."""
    momento = momento or agora_utc()
    parametros = {"conta_id": conta_id, "instrumento_id": instrumento_id,
                  "versao_lida": versao_lida, "conteudo": conteudo}
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(sessao, comando_id, "salvar_rascunho", parametros,
                                      ator_tipo, ator_id, conta_id)
    if resposta is not None:
        return resposta

    if not isinstance(conteudo, dict):
        return _negar(sessao, comando, ator_tipo, ator_id, "salvar_rascunho",
                      conta_id, instrumento_id, "o conteúdo do rascunho deve ser um objeto JSON")
    if not isinstance(versao_lida, int) or isinstance(versao_lida, bool) or versao_lida < 1:
        return _negar(sessao, comando, ator_tipo, ator_id, "salvar_rascunho",
                      conta_id, instrumento_id, "versao_lida deve ser um inteiro positivo")

    instrumento, registro, ciclo = _contexto_do_instrumento(sessao, instrumento_id)
    if instrumento is None:
        return _negar(sessao, comando, ator_tipo, ator_id, "salvar_rascunho",
                      conta_id, instrumento_id, "Instrumento inexistente")
    permitido, motivo = _pode_preencher(sessao, conta, pessoa_id, registro)
    if not permitido:
        return _negar(sessao, comando, ator_tipo, ator_id, "salvar_rascunho",
                      conta_id, instrumento_id, motivo)
    if instrumento.estado_instrumento != "em_preenchimento":
        return _negar(sessao, comando, ator_tipo, ator_id, "salvar_rascunho",
                      conta_id, instrumento_id,
                      "I2 exige Instrumento no estado em_preenchimento",
                      estado_atual=instrumento.estado_instrumento)

    rascunho = sessao.get(RascunhoInstrumento, instrumento.id)
    if rascunho is None:
        return _negar(sessao, comando, ator_tipo, ator_id, "salvar_rascunho",
                      conta_id, instrumento_id,
                      "Instrumento em_preenchimento não possui rascunho; inconsistência detectada")
    if rascunho.versao_rascunho != versao_lida:
        return _negar(sessao, comando, ator_tipo, ator_id, "salvar_rascunho",
                      conta_id, instrumento_id,
                      "rascunho desatualizado: recarregue antes de salvar",
                      versao_lida=versao_lida, versao_atual=rascunho.versao_rascunho)

    nova_versao = rascunho.versao_rascunho + 1
    novo_lacre = lacre_do_conteudo(conteudo)
    rascunho.conteudo = conteudo
    rascunho.versao_rascunho = nova_versao
    rascunho.salvo_por = pessoa_id
    rascunho.salvo_em = momento
    rascunho.lacre_conteudo = novo_lacre
    evento = registrar_evento(
        sessao, comando, "instrumento", instrumento.id, "salvar_rascunho",
        {"instrumento_id": instrumento.id, "versao_anterior": versao_lida,
         "versao_rascunho": nova_versao, "lacre_conteudo": novo_lacre,
         "conta_id": conta_id},
        codigo_evento="I2", registro_id=registro.id, ciclo_id=ciclo.id,
        versao_esquema_evento=2,
    )
    resultado = fechar_comando(
        comando,
        {"permitido": True, "motivo": "rascunho salvo",
         "instrumento_id": instrumento.id, "estado_instrumento": "em_preenchimento",
         "versao_rascunho": nova_versao, "lacre_conteudo": novo_lacre,
         "evento_i2": evento.sequencia_cadeia},
    )
    sessao.flush()
    return resultado
