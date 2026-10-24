"""Atos do Instrumento usados pelo núcleo do M1a.

I1 abre o preenchimento, I2 salva o rascunho com controle otimista, I3
protocola uma versão imutável e I4 permite retirar a submissão antes da
análise. I5 valida a versão examinada. G2, G3 e G4 recalculam o Registro
na mesma transação dos atos que os causaram. I6 devolve a versão e cria
automaticamente a pendência de correção.
"""

from copy import deepcopy
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select

from app.comandos import abrir_comando, fechar_comando
from app.eventos import lacre, registrar_auditoria, registrar_evento
from app.form1_sintetico import (CAMPOS_DE_CATALOGO, VERSAO_CONTRATO_FORM1,
                                 validar_conteudo)
from app.modelos import (AcaoObrigatoria, AnaliseInstrumento, Ciclo, Conta, Evento,
                         Instrumento, Pendencia, Pessoa, RascunhoInstrumento, Registro,
                         VersaoInstrumento)
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
    """Trava Instrumento e Registro, nessa ordem, antes de acrescentar eventos."""
    instrumento = sessao.scalars(
        select(Instrumento).where(Instrumento.id == instrumento_id).with_for_update()
    ).one_or_none()
    if instrumento is None:
        return None, None, None
    registro = sessao.scalars(
        select(Registro).where(Registro.id == instrumento.registro_id).with_for_update()
    ).one()
    ciclo = sessao.scalars(
        select(Ciclo).where(Ciclo.registro_id == registro.id,
                            Ciclo.numero == registro.ciclo_atual)
    ).one()
    return instrumento, registro, ciclo


def _pode_preencher(sessao, conta, pessoa_id, registro):
    if conta is None or not conta.ativa:
        return False, "conta inexistente ou desativada"
    if not tem_papel(sessao, pessoa_id, registro.unidade_principal_atual_id, {"preenchedor"}):
        return False, "a pessoa não está designada como Servidor responsável pelo preenchimento"
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

    pendencia_congelante = sessao.scalars(
        select(Pendencia).where(
            Pendencia.instrumento_id == instrumento.id,
            Pendencia.tipo_pendencia == "devolucao",
            Pendencia.estado.in_(("respondida", "devolvida_para_complementacao")),
        ).with_for_update()
    ).first()
    if pendencia_congelante is not None:
        return _negar(
            sessao, comando, ator_tipo, ator_id, "salvar_rascunho",
            conta_id, instrumento_id,
            "rascunho congelado enquanto a resposta da pendência aguarda decisão",
            pendencia_id=pendencia_congelante.id,
            estado_pendencia=pendencia_congelante.estado,
        )

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


_CAMPOS_LISTA_FORM1 = tuple(CAMPOS_DE_CATALOGO)


def validar_form1_sintetico(conteudo):
    """Retorna os problemas bloqueantes do contrato mínimo do FORM 1 sintético."""
    return validar_conteudo(conteudo)


def _normalizar_texto(valor):
    return " ".join(valor.casefold().split())


def _campos_materiais(conteudo):
    return {
        "finalidade": {_normalizar_texto(conteudo["finalidade"])},
        **{
            campo: set(conteudo[campo])
            for campo in _CAMPOS_LISTA_FORM1
        },
    }


def _alertas_sobreposicao(sessao, registro_atual, conteudo):
    """Compara com a versão mais recente de cada outro Instrumento, sem bloquear."""
    linhas = sessao.execute(
        select(VersaoInstrumento, Instrumento, Registro)
        .join(Instrumento, Instrumento.id == VersaoInstrumento.instrumento_id)
        .join(Registro, Registro.id == Instrumento.registro_id)
        .where(Registro.id != registro_atual.id)
        .order_by(VersaoInstrumento.instrumento_id, VersaoInstrumento.numero.desc())
    ).all()
    atuais = _campos_materiais(conteudo)
    vistos = set()
    alertas = []
    for versao, instrumento, registro in linhas:
        if instrumento.id in vistos:
            continue
        vistos.add(instrumento.id)
        if validar_form1_sintetico(versao.conteudo):
            continue
        anteriores = _campos_materiais(versao.conteudo)
        coincidencias = {
            campo: sorted(atuais[campo] & anteriores[campo])
            for campo in ("finalidade", *_CAMPOS_LISTA_FORM1)
            if atuais[campo] & anteriores[campo]
        }
        if coincidencias:
            alertas.append({
                "registro_id": registro.id,
                "codigo_lgpd": registro.codigo_lgpd,
                "instrumento_id": instrumento.id,
                "versao": versao.numero,
                "coincidencias": coincidencias,
            })
    return sorted(alertas, key=lambda item: (item["codigo_lgpd"], item["instrumento_id"]))


def submeter_instrumento(sessao, *, comando_id, conta_id, instrumento_id, versao_lida,
                         momento=None):
    """I3 + G2 — congela o rascunho e envia o Registro para validação."""
    momento = momento or agora_utc()
    parametros = {"conta_id": conta_id, "instrumento_id": instrumento_id,
                  "versao_lida": versao_lida}
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(sessao, comando_id, "submeter_instrumento", parametros,
                                      ator_tipo, ator_id, conta_id)
    if resposta is not None:
        return resposta

    if not isinstance(versao_lida, int) or isinstance(versao_lida, bool) or versao_lida < 1:
        return _negar(sessao, comando, ator_tipo, ator_id, "submeter_instrumento",
                      conta_id, instrumento_id, "versao_lida deve ser um inteiro positivo")

    instrumento, registro, ciclo = _contexto_do_instrumento(sessao, instrumento_id)
    if instrumento is None:
        return _negar(sessao, comando, ator_tipo, ator_id, "submeter_instrumento",
                      conta_id, instrumento_id, "Instrumento inexistente")
    permitido, motivo = _pode_preencher(sessao, conta, pessoa_id, registro)
    if not permitido:
        return _negar(sessao, comando, ator_tipo, ator_id, "submeter_instrumento",
                      conta_id, instrumento_id, motivo)
    if instrumento.estado_instrumento != "em_preenchimento":
        return _negar(sessao, comando, ator_tipo, ator_id, "submeter_instrumento",
                      conta_id, instrumento_id,
                      "I3 exige Instrumento no estado em_preenchimento",
                      estado_atual=instrumento.estado_instrumento)
    if registro.estado_atual != "em_andamento":
        return _negar(sessao, comando, ator_tipo, ator_id, "submeter_instrumento",
                      conta_id, instrumento_id,
                      "I3 exige Registro no estado em_andamento",
                      estado_registro=registro.estado_atual)

    rascunho = sessao.get(RascunhoInstrumento, instrumento.id)
    if rascunho is None:
        return _negar(sessao, comando, ator_tipo, ator_id, "submeter_instrumento",
                      conta_id, instrumento_id,
                      "Instrumento em_preenchimento não possui rascunho; inconsistência detectada")
    if rascunho.versao_rascunho != versao_lida:
        return _negar(sessao, comando, ator_tipo, ator_id, "submeter_instrumento",
                      conta_id, instrumento_id,
                      "rascunho desatualizado: recarregue antes de submeter",
                      versao_lida=versao_lida, versao_atual=rascunho.versao_rascunho)

    pendencias_devolucao = sessao.scalars(
        select(Pendencia)
        .where(Pendencia.instrumento_id == instrumento.id,
               Pendencia.tipo_pendencia == "devolucao")
        .order_by(Pendencia.criada_em.desc(), Pendencia.id.desc())
        .with_for_update()
    ).all()
    pendencia_ativa = next(
        (item for item in pendencias_devolucao if item.estado != "encerrada"), None
    )
    if pendencia_ativa is not None:
        return _negar(
            sessao, comando, ator_tipo, ator_id, "submeter_instrumento",
            conta_id, instrumento_id,
            "I3 bloqueado até a pendência de devolução ser aceita por P4",
            pendencia_id=pendencia_ativa.id,
            estado_pendencia=pendencia_ativa.estado,
        )
    ultima_aceita = next(
        (item for item in pendencias_devolucao if item.lacre_aceito is not None), None
    )
    if ultima_aceita is not None and rascunho.lacre_conteudo != ultima_aceita.lacre_aceito:
        return _negar(
            sessao, comando, ator_tipo, ator_id, "submeter_instrumento",
            conta_id, instrumento_id,
            "o rascunho atual não coincide com a correção aceita por P4",
            pendencia_id=ultima_aceita.id,
        )

    problemas = validar_form1_sintetico(rascunho.conteudo)
    if problemas:
        return _negar(sessao, comando, ator_tipo, ator_id, "submeter_instrumento",
                      conta_id, instrumento_id,
                      "FORM 1 sintético possui campos obrigatórios inválidos",
                      problemas=problemas)

    canonico = conteudo_canonico(rascunho.conteudo)
    lacre_versao = lacre(canonico)
    if lacre_versao != rascunho.lacre_conteudo:
        return _negar(sessao, comando, ator_tipo, ator_id, "submeter_instrumento",
                      conta_id, instrumento_id,
                      "lacre do rascunho não confere; inconsistência detectada")

    numero = (sessao.scalar(
        select(func.max(VersaoInstrumento.numero))
        .where(VersaoInstrumento.instrumento_id == instrumento.id)
    ) or 0) + 1
    versao_id = str(uuid.uuid4())
    alertas = _alertas_sobreposicao(sessao, registro, rascunho.conteudo)
    evento_i3 = registrar_evento(
        sessao, comando, "instrumento", instrumento.id, "submeter_instrumento",
        {"instrumento_id": instrumento.id, "versao_id": versao_id,
         "numero_versao": numero, "versao_rascunho": rascunho.versao_rascunho,
         "versao_contrato": VERSAO_CONTRATO_FORM1,
         "lacre_conteudo": lacre_versao, "alertas_sobreposicao": alertas,
         "conta_id": conta_id},
        codigo_evento="I3", ordem_no_comando=1, registro_id=registro.id,
        ciclo_id=ciclo.id, versao_esquema_evento=2,
    )
    sessao.add(VersaoInstrumento(
        id=versao_id,
        instrumento_id=instrumento.id,
        numero=numero,
        versao_contrato=VERSAO_CONTRATO_FORM1,
        conteudo=deepcopy(rascunho.conteudo),
        conteudo_canonico=canonico,
        lacre=lacre_versao,
        submetida_por=pessoa_id,
        submetida_em=momento,
        evento_submissao_id=evento_i3.id,
    ))
    estado_anterior = registro.estado_atual
    instrumento.estado_instrumento = "pronto_para_validacao"
    registro.estado_atual = "em_validacao"
    evento_g2 = registrar_evento(
        sessao, comando, "registro", registro.codigo_lgpd, "recalcular_apos_submissao",
        {"registro_id": registro.id, "instrumento_id": instrumento.id,
         "evento_causa_id": evento_i3.id, "estado_anterior": estado_anterior,
         "estado_atual": "em_validacao"},
        codigo_evento="G2", ordem_no_comando=2, registro_id=registro.id,
        ciclo_id=ciclo.id, versao_esquema_evento=2,
    )
    registro.sequencia_atual = evento_g2.sequencia_cadeia
    resultado = fechar_comando(
        comando,
        {"permitido": True, "motivo": "Instrumento submetido",
         "instrumento_id": instrumento.id, "estado_instrumento": "pronto_para_validacao",
         "estado_registro": "em_validacao", "versao_id": versao_id,
         "numero_versao": numero, "versao_contrato": VERSAO_CONTRATO_FORM1,
         "lacre_conteudo": lacre_versao,
         "alertas_sobreposicao": alertas, "evento_i3": evento_i3.sequencia_cadeia,
         "evento_g2": evento_g2.sequencia_cadeia},
    )
    sessao.flush()
    return resultado


def retirar_submissao(sessao, *, comando_id, conta_id, instrumento_id):
    """I4 + G3 — retira a submissão ainda não assumida para análise."""
    parametros = {"conta_id": conta_id, "instrumento_id": instrumento_id}
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(sessao, comando_id, "retirar_submissao", parametros,
                                      ator_tipo, ator_id, conta_id)
    if resposta is not None:
        return resposta

    instrumento, registro, ciclo = _contexto_do_instrumento(sessao, instrumento_id)
    if instrumento is None:
        return _negar(sessao, comando, ator_tipo, ator_id, "retirar_submissao",
                      conta_id, instrumento_id, "Instrumento inexistente")
    permitido, motivo = _pode_preencher(sessao, conta, pessoa_id, registro)
    if not permitido:
        return _negar(sessao, comando, ator_tipo, ator_id, "retirar_submissao",
                      conta_id, instrumento_id, motivo)
    if instrumento.estado_instrumento != "pronto_para_validacao":
        return _negar(sessao, comando, ator_tipo, ator_id, "retirar_submissao",
                      conta_id, instrumento_id,
                      "I4 exige Instrumento no estado pronto_para_validacao",
                      estado_atual=instrumento.estado_instrumento)
    if registro.estado_atual != "em_validacao":
        return _negar(sessao, comando, ator_tipo, ator_id, "retirar_submissao",
                      conta_id, instrumento_id,
                      "I4 exige Registro no estado em_validacao",
                      estado_registro=registro.estado_atual)

    versao = sessao.scalars(
        select(VersaoInstrumento)
        .where(VersaoInstrumento.instrumento_id == instrumento.id)
        .order_by(VersaoInstrumento.numero.desc())
        .limit(1)
    ).one_or_none()
    if versao is None:
        return _negar(sessao, comando, ator_tipo, ator_id, "retirar_submissao",
                      conta_id, instrumento_id,
                      "Instrumento pronto_para_validacao não possui versão; inconsistência detectada")
    evento_submissao = sessao.get(Evento, versao.evento_submissao_id)
    if evento_submissao is None:
        return _negar(sessao, comando, ator_tipo, ator_id, "retirar_submissao",
                      conta_id, instrumento_id,
                      "versão não possui evento de submissão; inconsistência detectada")
    analise_iniciada = sessao.scalar(
        select(Evento.id)
        .where(Evento.cadeia_id == instrumento.id,
               Evento.codigo_evento == "I13",
               Evento.sequencia_cadeia > evento_submissao.sequencia_cadeia)
        .limit(1)
    )
    if analise_iniciada is not None:
        return _negar(sessao, comando, ator_tipo, ator_id, "retirar_submissao",
                      conta_id, instrumento_id,
                      "I4 não é permitido depois do início da análise (I13)")

    evento_i4 = registrar_evento(
        sessao, comando, "instrumento", instrumento.id, "retirar_submissao",
        {"instrumento_id": instrumento.id, "versao_retirada_id": versao.id,
         "numero_versao": versao.numero, "lacre_conteudo": versao.lacre,
         "conta_id": conta_id},
        codigo_evento="I4", ordem_no_comando=1, registro_id=registro.id,
        ciclo_id=ciclo.id, versao_esquema_evento=2,
    )
    estado_anterior = registro.estado_atual
    instrumento.estado_instrumento = "em_preenchimento"
    registro.estado_atual = "em_andamento"
    evento_g3 = registrar_evento(
        sessao, comando, "registro", registro.codigo_lgpd, "recalcular_apos_retirada",
        {"registro_id": registro.id, "instrumento_id": instrumento.id,
         "evento_causa_id": evento_i4.id, "estado_anterior": estado_anterior,
         "estado_atual": "em_andamento"},
        codigo_evento="G3", ordem_no_comando=2, registro_id=registro.id,
        ciclo_id=ciclo.id, versao_esquema_evento=2,
    )
    registro.sequencia_atual = evento_g3.sequencia_cadeia
    resultado = fechar_comando(
        comando,
        {"permitido": True, "motivo": "submissão retirada antes da análise",
         "instrumento_id": instrumento.id, "estado_instrumento": "em_preenchimento",
         "estado_registro": "em_andamento", "versao_preservada_id": versao.id,
         "numero_versao": versao.numero, "evento_i4": evento_i4.sequencia_cadeia,
         "evento_g3": evento_g3.sequencia_cadeia},
    )
    sessao.flush()
    return resultado


def iniciar_analise(sessao, *, comando_id, conta_id, instrumento_id, versao_id,
                    momento=None):
    """I13 — atribui a análise da versão a um único responsável vigente."""
    momento = momento or agora_utc()
    parametros = {"conta_id": conta_id, "instrumento_id": instrumento_id,
                  "versao_id": versao_id}
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(sessao, comando_id, "iniciar_analise", parametros,
                                      ator_tipo, ator_id, conta_id)
    if resposta is not None:
        return resposta

    instrumento, registro, ciclo = _contexto_do_instrumento(sessao, instrumento_id)
    if instrumento is None:
        return _negar(sessao, comando, ator_tipo, ator_id, "iniciar_analise",
                      conta_id, instrumento_id, "Instrumento inexistente")
    if conta is None or not conta.ativa:
        return _negar(sessao, comando, ator_tipo, ator_id, "iniciar_analise",
                      conta_id, instrumento_id, "conta inexistente ou desativada")
    if not tem_papel(sessao, pessoa_id, registro.unidade_principal_atual_id, {"analista"}):
        return _negar(sessao, comando, ator_tipo, ator_id, "iniciar_analise",
                      conta_id, instrumento_id,
                      "a pessoa não tem papel de analista na unidade responsável")
    if instrumento.estado_instrumento != "pronto_para_validacao":
        return _negar(sessao, comando, ator_tipo, ator_id, "iniciar_analise",
                      conta_id, instrumento_id,
                      "I13 exige Instrumento no estado pronto_para_validacao",
                      estado_atual=instrumento.estado_instrumento)
    if registro.estado_atual != "em_validacao":
        return _negar(sessao, comando, ator_tipo, ator_id, "iniciar_analise",
                      conta_id, instrumento_id,
                      "I13 exige Registro no estado em_validacao",
                      estado_registro=registro.estado_atual)

    versao = sessao.get(VersaoInstrumento, versao_id)
    if versao is None or versao.instrumento_id != instrumento.id:
        return _negar(sessao, comando, ator_tipo, ator_id, "iniciar_analise",
                      conta_id, instrumento_id,
                      "a versão informada não pertence ao Instrumento")
    ultima_versao = sessao.scalars(
        select(VersaoInstrumento)
        .where(VersaoInstrumento.instrumento_id == instrumento.id)
        .order_by(VersaoInstrumento.numero.desc())
        .limit(1)
    ).one()
    if ultima_versao.id != versao.id:
        return _negar(sessao, comando, ator_tipo, ator_id, "iniciar_analise",
                      conta_id, instrumento_id,
                      "I13 exige a versão submetida mais recente",
                      versao_informada=versao.numero, versao_atual=ultima_versao.numero)
    if versao.submetida_por == pessoa_id:
        return _negar(sessao, comando, ator_tipo, ator_id, "iniciar_analise",
                      conta_id, instrumento_id,
                      "segregação de funções: a pessoa é autora da submissão")

    existente = sessao.scalars(
        select(AnaliseInstrumento).where(AnaliseInstrumento.versao_id == versao.id)
    ).one_or_none()
    if existente is not None:
        return _negar(sessao, comando, ator_tipo, ator_id, "iniciar_analise",
                      conta_id, instrumento_id,
                      "a versão já possui análise iniciada",
                      responsavel_atual_id=existente.responsavel_atual_id)

    analise_id = str(uuid.uuid4())
    evento_i13 = registrar_evento(
        sessao, comando, "instrumento", instrumento.id, "iniciar_analise",
        {"instrumento_id": instrumento.id, "versao_id": versao.id,
         "numero_versao": versao.numero, "analise_id": analise_id,
         "responsavel_atual_id": pessoa_id, "conta_id": conta_id},
        codigo_evento="I13", registro_id=registro.id, ciclo_id=ciclo.id,
        versao_esquema_evento=2,
    )
    sessao.add(AnaliseInstrumento(
        id=analise_id,
        versao_id=versao.id,
        instrumento_id=instrumento.id,
        responsavel_atual_id=pessoa_id,
        iniciada_por=pessoa_id,
        iniciada_em=momento,
        atualizada_em=momento,
        situacao="ativa",
        evento_inicio_id=evento_i13.id,
    ))
    resultado = fechar_comando(
        comando,
        {"permitido": True, "motivo": "análise iniciada",
         "instrumento_id": instrumento.id, "versao_id": versao.id,
         "numero_versao": versao.numero, "analise_id": analise_id,
         "responsavel_atual_id": pessoa_id,
         "estado_instrumento": instrumento.estado_instrumento,
         "estado_registro": registro.estado_atual,
         "evento_i13": evento_i13.sequencia_cadeia},
    )
    sessao.flush()
    return resultado


def reatribuir_analise(sessao, *, comando_id, conta_id, instrumento_id, analise_id,
                       responsavel_lido_id, novo_responsavel_id, momento=None):
    """I14 — troca o responsável vigente sem apagar a autoria anterior."""
    momento = momento or agora_utc()
    parametros = {"conta_id": conta_id, "instrumento_id": instrumento_id,
                  "analise_id": analise_id, "responsavel_lido_id": responsavel_lido_id,
                  "novo_responsavel_id": novo_responsavel_id}
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(sessao, comando_id, "reatribuir_analise", parametros,
                                      ator_tipo, ator_id, conta_id)
    if resposta is not None:
        return resposta

    instrumento, registro, ciclo = _contexto_do_instrumento(sessao, instrumento_id)
    if instrumento is None:
        return _negar(sessao, comando, ator_tipo, ator_id, "reatribuir_analise",
                      conta_id, instrumento_id, "Instrumento inexistente")
    if conta is None or not conta.ativa:
        return _negar(sessao, comando, ator_tipo, ator_id, "reatribuir_analise",
                      conta_id, instrumento_id, "conta inexistente ou desativada")
    if not tem_papel(sessao, pessoa_id, registro.unidade_principal_atual_id, {"validador"}):
        return _negar(sessao, comando, ator_tipo, ator_id, "reatribuir_analise",
                      conta_id, instrumento_id,
                      "a pessoa não tem competência de validador na unidade responsável")
    if instrumento.estado_instrumento != "pronto_para_validacao" or \
            registro.estado_atual != "em_validacao":
        return _negar(sessao, comando, ator_tipo, ator_id, "reatribuir_analise",
                      conta_id, instrumento_id,
                      "I14 exige Instrumento pronto_para_validacao e Registro em_validacao",
                      estado_instrumento=instrumento.estado_instrumento,
                      estado_registro=registro.estado_atual)

    analise = sessao.get(AnaliseInstrumento, analise_id)
    if analise is None or analise.instrumento_id != instrumento.id:
        return _negar(sessao, comando, ator_tipo, ator_id, "reatribuir_analise",
                      conta_id, instrumento_id, "a análise informada não pertence ao Instrumento")
    if analise.situacao != "ativa":
        return _negar(sessao, comando, ator_tipo, ator_id, "reatribuir_analise",
                      conta_id, instrumento_id, "I14 exige análise ativa")
    if analise.responsavel_atual_id != responsavel_lido_id:
        return _negar(sessao, comando, ator_tipo, ator_id, "reatribuir_analise",
                      conta_id, instrumento_id,
                      "responsável desatualizado: recarregue antes de reatribuir",
                      responsavel_lido_id=responsavel_lido_id,
                      responsavel_atual_id=analise.responsavel_atual_id)
    if novo_responsavel_id == analise.responsavel_atual_id:
        return _negar(sessao, comando, ator_tipo, ator_id, "reatribuir_analise",
                      conta_id, instrumento_id,
                      "o novo responsável já é o responsável vigente")

    novo_responsavel = sessao.get(Pessoa, novo_responsavel_id)
    if novo_responsavel is None or not novo_responsavel.ativa:
        return _negar(sessao, comando, ator_tipo, ator_id, "reatribuir_analise",
                      conta_id, instrumento_id,
                      "novo responsável inexistente ou desativado")
    if not tem_papel(sessao, novo_responsavel_id, registro.unidade_principal_atual_id,
                     {"analista"}):
        return _negar(sessao, comando, ator_tipo, ator_id, "reatribuir_analise",
                      conta_id, instrumento_id,
                      "novo responsável não tem papel de analista na unidade responsável")
    versao = sessao.get(VersaoInstrumento, analise.versao_id)
    if versao.submetida_por == novo_responsavel_id:
        return _negar(sessao, comando, ator_tipo, ator_id, "reatribuir_analise",
                      conta_id, instrumento_id,
                      "segregação de funções: o novo responsável é autor da submissão")

    responsavel_anterior = analise.responsavel_atual_id
    evento_i14 = registrar_evento(
        sessao, comando, "instrumento", instrumento.id, "reatribuir_analise",
        {"instrumento_id": instrumento.id, "versao_id": versao.id,
         "numero_versao": versao.numero, "analise_id": analise.id,
         "responsavel_anterior_id": responsavel_anterior,
         "responsavel_atual_id": novo_responsavel_id, "conta_id": conta_id},
        codigo_evento="I14", registro_id=registro.id, ciclo_id=ciclo.id,
        versao_esquema_evento=2,
    )
    analise.responsavel_atual_id = novo_responsavel_id
    analise.atualizada_em = momento
    resultado = fechar_comando(
        comando,
        {"permitido": True, "motivo": "análise reatribuída",
         "instrumento_id": instrumento.id, "versao_id": versao.id,
         "analise_id": analise.id, "responsavel_anterior_id": responsavel_anterior,
         "responsavel_atual_id": novo_responsavel_id,
         "estado_instrumento": instrumento.estado_instrumento,
         "estado_registro": registro.estado_atual,
         "evento_i14": evento_i14.sequencia_cadeia},
    )
    sessao.flush()
    return resultado


def validar_instrumento(sessao, *, comando_id, conta_id, instrumento_id, analise_id,
                        versao_id, momento=None):
    """I5 + G4 — valida a versão analisada e recalcula o estado global do Registro."""
    momento = momento or agora_utc()
    parametros = {"conta_id": conta_id, "instrumento_id": instrumento_id,
                  "analise_id": analise_id, "versao_id": versao_id}
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(sessao, comando_id, "validar_instrumento", parametros,
                                      ator_tipo, ator_id, conta_id)
    if resposta is not None:
        return resposta

    instrumento, registro, ciclo = _contexto_do_instrumento(sessao, instrumento_id)
    if instrumento is None:
        return _negar(sessao, comando, ator_tipo, ator_id, "validar_instrumento",
                      conta_id, instrumento_id, "Instrumento inexistente")
    if conta is None or not conta.ativa:
        return _negar(sessao, comando, ator_tipo, ator_id, "validar_instrumento",
                      conta_id, instrumento_id, "conta inexistente ou desativada")
    if (instrumento.estado_instrumento != "pronto_para_validacao"
            or registro.estado_atual != "em_validacao"):
        return _negar(
            sessao, comando, ator_tipo, ator_id, "validar_instrumento",
            conta_id, instrumento_id,
            "I5 exige Instrumento pronto_para_validacao e Registro em_validacao",
            estado_instrumento=instrumento.estado_instrumento,
            estado_registro=registro.estado_atual,
        )

    analise = sessao.get(AnaliseInstrumento, analise_id)
    if analise is None or analise.instrumento_id != instrumento.id:
        return _negar(sessao, comando, ator_tipo, ator_id, "validar_instrumento",
                      conta_id, instrumento_id, "a análise informada não pertence ao Instrumento")
    if analise.situacao != "ativa":
        return _negar(sessao, comando, ator_tipo, ator_id, "validar_instrumento",
                      conta_id, instrumento_id, "I5 exige análise ativa")
    if analise.responsavel_atual_id != pessoa_id:
        return _negar(
            sessao, comando, ator_tipo, ator_id, "validar_instrumento",
            conta_id, instrumento_id,
            "I5 só pode ser executado pelo responsável vigente da análise",
            responsavel_atual_id=analise.responsavel_atual_id,
        )
    if analise.versao_id != versao_id:
        return _negar(sessao, comando, ator_tipo, ator_id, "validar_instrumento",
                      conta_id, instrumento_id, "a versão informada não é a versão analisada")

    versao = sessao.get(VersaoInstrumento, versao_id)
    if versao is None or versao.instrumento_id != instrumento.id:
        return _negar(sessao, comando, ator_tipo, ator_id, "validar_instrumento",
                      conta_id, instrumento_id, "a versão informada não pertence ao Instrumento")

    evento_i5 = registrar_evento(
        sessao, comando, "instrumento", instrumento.id, "validar_instrumento",
        {"instrumento_id": instrumento.id, "versao_id": versao.id,
         "numero_versao": versao.numero, "analise_id": analise.id,
         "responsavel_analise_id": pessoa_id, "conta_id": conta_id},
        codigo_evento="I5", ordem_no_comando=1, registro_id=registro.id,
        ciclo_id=ciclo.id, versao_esquema_evento=2,
    )

    instrumento.estado_instrumento = "validado"
    instrumento.versao_vigente_id = versao.id
    analise.situacao = "encerrada"
    analise.atualizada_em = momento
    sessao.flush()

    outros_prontos = list(sessao.scalars(
        select(Instrumento.id).where(
            Instrumento.registro_id == registro.id,
            Instrumento.id != instrumento.id,
            Instrumento.estado_instrumento == "pronto_para_validacao",
        ).order_by(Instrumento.id)
    ))
    acoes_abertas = list(sessao.scalars(
        select(AcaoObrigatoria.id).where(
            AcaoObrigatoria.registro_id == registro.id,
            AcaoObrigatoria.ciclo_id == ciclo.id,
            AcaoObrigatoria.estado == "aberta",
        ).order_by(AcaoObrigatoria.id)
    ))
    if outros_prontos:
        novo_estado = "em_validacao"
        criterio = "outro_instrumento_pronto"
    elif acoes_abertas:
        novo_estado = "em_execucao"
        criterio = "acao_obrigatoria_aberta"
    else:
        novo_estado = "em_andamento"
        criterio = "sem_instrumento_pronto_ou_acao_aberta"

    estado_anterior = registro.estado_atual
    registro.estado_atual = novo_estado
    evento_g4 = registrar_evento(
        sessao, comando, "registro", registro.codigo_lgpd, "recalcular_apos_validacao",
        {"registro_id": registro.id, "instrumento_id": instrumento.id,
         "versao_id": versao.id, "evento_causa_id": evento_i5.id,
         "estado_anterior": estado_anterior, "estado_atual": novo_estado,
         "criterio": criterio, "outros_instrumentos_prontos": outros_prontos,
         "acoes_obrigatorias_abertas": acoes_abertas},
        codigo_evento="G4", ordem_no_comando=2, registro_id=registro.id,
        ciclo_id=ciclo.id, versao_esquema_evento=2,
    )
    registro.sequencia_atual = evento_g4.sequencia_cadeia
    resultado = fechar_comando(
        comando,
        {"permitido": True, "motivo": "Instrumento validado",
         "instrumento_id": instrumento.id, "versao_id": versao.id,
         "analise_id": analise.id, "estado_instrumento": "validado",
         "estado_registro": novo_estado, "criterio_g4": criterio,
         "acoes_obrigatorias_abertas": acoes_abertas,
         "evento_i5": evento_i5.sequencia_cadeia,
         "evento_g4": evento_g4.sequencia_cadeia},
    )
    sessao.flush()
    return resultado


def devolver_instrumento(sessao, *, comando_id, conta_id, instrumento_id, analise_id,
                         versao_id, motivo, momento=None):
    """I6 + P1 + G3 — devolve a versão e abre a pendência de correção."""
    momento = momento or agora_utc()
    parametros = {"conta_id": conta_id, "instrumento_id": instrumento_id,
                  "analise_id": analise_id, "versao_id": versao_id, "motivo": motivo}
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(sessao, comando_id, "devolver_instrumento", parametros,
                                      ator_tipo, ator_id, conta_id)
    if resposta is not None:
        return resposta

    if not isinstance(motivo, str) or not motivo.strip():
        return _negar(sessao, comando, ator_tipo, ator_id, "devolver_instrumento",
                      conta_id, instrumento_id, "I6 exige motivo não vazio")
    motivo = motivo.strip()
    if len(motivo) > 1000:
        return _negar(sessao, comando, ator_tipo, ator_id, "devolver_instrumento",
                      conta_id, instrumento_id, "o motivo deve ter no máximo 1000 caracteres")

    instrumento, registro, ciclo = _contexto_do_instrumento(sessao, instrumento_id)
    if instrumento is None:
        return _negar(sessao, comando, ator_tipo, ator_id, "devolver_instrumento",
                      conta_id, instrumento_id, "Instrumento inexistente")
    if conta is None or not conta.ativa:
        return _negar(sessao, comando, ator_tipo, ator_id, "devolver_instrumento",
                      conta_id, instrumento_id, "conta inexistente ou desativada")
    if (instrumento.estado_instrumento != "pronto_para_validacao"
            or registro.estado_atual != "em_validacao"):
        return _negar(
            sessao, comando, ator_tipo, ator_id, "devolver_instrumento",
            conta_id, instrumento_id,
            "I6 exige Instrumento pronto_para_validacao e Registro em_validacao",
            estado_instrumento=instrumento.estado_instrumento,
            estado_registro=registro.estado_atual,
        )

    analise = sessao.get(AnaliseInstrumento, analise_id)
    if analise is None or analise.instrumento_id != instrumento.id:
        return _negar(sessao, comando, ator_tipo, ator_id, "devolver_instrumento",
                      conta_id, instrumento_id, "a análise informada não pertence ao Instrumento")
    if analise.situacao != "ativa":
        return _negar(sessao, comando, ator_tipo, ator_id, "devolver_instrumento",
                      conta_id, instrumento_id, "I6 exige análise ativa")
    if analise.responsavel_atual_id != pessoa_id:
        return _negar(
            sessao, comando, ator_tipo, ator_id, "devolver_instrumento",
            conta_id, instrumento_id,
            "I6 só pode ser executado pelo responsável vigente da análise",
            responsavel_atual_id=analise.responsavel_atual_id,
        )
    if analise.versao_id != versao_id:
        return _negar(sessao, comando, ator_tipo, ator_id, "devolver_instrumento",
                      conta_id, instrumento_id, "a versão informada não é a versão analisada")

    versao = sessao.get(VersaoInstrumento, versao_id)
    if versao is None or versao.instrumento_id != instrumento.id:
        return _negar(sessao, comando, ator_tipo, ator_id, "devolver_instrumento",
                      conta_id, instrumento_id, "a versão informada não pertence ao Instrumento")
    if versao.submetida_por == pessoa_id:
        return _negar(sessao, comando, ator_tipo, ator_id, "devolver_instrumento",
                      conta_id, instrumento_id,
                      "segregação de funções: a pessoa é autora da submissão")

    pendencia_id = str(uuid.uuid4())
    evento_i6 = registrar_evento(
        sessao, comando, "instrumento", instrumento.id, "devolver_instrumento",
        {"instrumento_id": instrumento.id, "versao_id": versao.id,
         "numero_versao": versao.numero, "analise_id": analise.id,
         "pendencia_id": pendencia_id, "motivo": motivo, "conta_id": conta_id},
        codigo_evento="I6", ordem_no_comando=1, registro_id=registro.id,
        ciclo_id=ciclo.id, versao_esquema_evento=2,
    )
    pendencia = Pendencia(
        id=pendencia_id,
        tipo_pendencia="devolucao",
        registro_id=registro.id,
        ciclo_origem_id=ciclo.id,
        ciclo_contexto_atual_id=ciclo.id,
        instrumento_id=instrumento.id,
        evento_origem_id=evento_i6.id,
        unidade_origem_id=registro.unidade_principal_atual_id,
        unidade_destino_id=registro.unidade_principal_atual_id,
        responsavel_atual_id=None,
        estado="aberta",
        bloqueante=True,
        gate_bloqueado="submissao",
        motivo=motivo,
        criada_em=momento,
        atualizada_em=momento,
    )
    sessao.add(pendencia)
    evento_p1 = registrar_evento(
        sessao, comando, "pendencia", pendencia.id, "criar_pendencia",
        {"pendencia_id": pendencia.id, "tipo_pendencia": "devolucao",
         "instrumento_id": instrumento.id, "versao_id": versao.id,
         "evento_causa_id": evento_i6.id,
         "unidade_destino_id": pendencia.unidade_destino_id,
         "bloqueante": True, "gate_bloqueado": "submissao",
         "estado_atual": "aberta"},
        codigo_evento="P1", ordem_no_comando=2, registro_id=registro.id,
        ciclo_id=ciclo.id, versao_esquema_evento=2,
    )

    estado_anterior = registro.estado_atual
    instrumento.estado_instrumento = "devolvido_para_ajuste"
    analise.situacao = "encerrada"
    analise.atualizada_em = momento
    registro.estado_atual = "em_andamento"
    evento_g3 = registrar_evento(
        sessao, comando, "registro", registro.codigo_lgpd, "recalcular_apos_devolucao",
        {"registro_id": registro.id, "instrumento_id": instrumento.id,
         "versao_id": versao.id, "pendencia_id": pendencia.id,
         "evento_causa_id": evento_i6.id, "estado_anterior": estado_anterior,
         "estado_atual": "em_andamento"},
        codigo_evento="G3", ordem_no_comando=3, registro_id=registro.id,
        ciclo_id=ciclo.id, versao_esquema_evento=2,
    )
    registro.sequencia_atual = evento_g3.sequencia_cadeia
    resultado = fechar_comando(
        comando,
        {"permitido": True, "motivo": "Instrumento devolvido para ajuste",
         "instrumento_id": instrumento.id, "versao_id": versao.id,
         "analise_id": analise.id, "pendencia_id": pendencia.id,
         "estado_pendencia": "aberta", "estado_instrumento": "devolvido_para_ajuste",
         "estado_registro": "em_andamento",
         "evento_i6": evento_i6.sequencia_cadeia,
         "evento_p1": evento_p1.sequencia_cadeia,
         "evento_g3": evento_g3.sequencia_cadeia},
    )
    sessao.flush()
    return resultado


def iniciar_ajuste(sessao, *, comando_id, conta_id, instrumento_id, pendencia_id,
                   momento=None):
    """I7 — inicia o ajuste com novo rascunho derivado da versão devolvida."""
    momento = momento or agora_utc()
    parametros = {"conta_id": conta_id, "instrumento_id": instrumento_id,
                  "pendencia_id": pendencia_id}
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(sessao, comando_id, "iniciar_ajuste", parametros,
                                      ator_tipo, ator_id, conta_id)
    if resposta is not None:
        return resposta

    instrumento, registro, ciclo = _contexto_do_instrumento(sessao, instrumento_id)
    if instrumento is None:
        return _negar(sessao, comando, ator_tipo, ator_id, "iniciar_ajuste",
                      conta_id, instrumento_id, "Instrumento inexistente")
    if conta is None or not conta.ativa:
        return _negar(sessao, comando, ator_tipo, ator_id, "iniciar_ajuste",
                      conta_id, instrumento_id, "conta inexistente ou desativada")
    if not tem_papel(sessao, pessoa_id, registro.unidade_principal_atual_id, {"preenchedor"}):
        return _negar(sessao, comando, ator_tipo, ator_id, "iniciar_ajuste",
                      conta_id, instrumento_id,
                      "a pessoa não está designada como Servidor responsável pelo preenchimento")
    if (instrumento.estado_instrumento != "devolvido_para_ajuste"
            or registro.estado_atual != "em_andamento"):
        return _negar(
            sessao, comando, ator_tipo, ator_id, "iniciar_ajuste",
            conta_id, instrumento_id,
            "I7 exige Instrumento devolvido_para_ajuste e Registro em_andamento",
            estado_instrumento=instrumento.estado_instrumento,
            estado_registro=registro.estado_atual,
        )

    pendencia = sessao.scalars(
        select(Pendencia).where(Pendencia.id == pendencia_id).with_for_update()
    ).one_or_none()
    if (pendencia is None or pendencia.instrumento_id != instrumento.id
            or pendencia.tipo_pendencia != "devolucao"):
        return _negar(sessao, comando, ator_tipo, ator_id, "iniciar_ajuste",
                      conta_id, instrumento_id,
                      "a pendência informada não é a devolução deste Instrumento")
    if pendencia.estado != "em_atendimento":
        return _negar(sessao, comando, ator_tipo, ator_id, "iniciar_ajuste",
                      conta_id, instrumento_id,
                      "I7 exige pendência assumida e em_atendimento",
                      estado_pendencia=pendencia.estado)
    if pendencia.responsavel_atual_id != pessoa_id:
        return _negar(sessao, comando, ator_tipo, ator_id, "iniciar_ajuste",
                      conta_id, instrumento_id,
                      "I7 só pode ser executado pelo agente que assumiu a pendência",
                      responsavel_atual_id=pendencia.responsavel_atual_id)

    evento_origem = sessao.get(Evento, pendencia.evento_origem_id)
    versao_id = None if evento_origem is None else evento_origem.conteudo.get("versao_id")
    versao = sessao.get(VersaoInstrumento, versao_id) if versao_id else None
    if versao is None or versao.instrumento_id != instrumento.id:
        return _negar(sessao, comando, ator_tipo, ator_id, "iniciar_ajuste",
                      conta_id, instrumento_id,
                      "a pendência não aponta para uma versão devolvida válida")

    rascunho = sessao.get(RascunhoInstrumento, instrumento.id)
    if rascunho is None:
        return _negar(sessao, comando, ator_tipo, ator_id, "iniciar_ajuste",
                      conta_id, instrumento_id,
                      "Instrumento devolvido não possui rascunho; inconsistência detectada")
    versao_anterior_rascunho = rascunho.versao_rascunho
    rascunho.conteudo = deepcopy(versao.conteudo)
    rascunho.versao_rascunho += 1
    rascunho.salvo_por = pessoa_id
    rascunho.salvo_em = momento
    rascunho.lacre_conteudo = versao.lacre
    instrumento.estado_instrumento = "em_preenchimento"
    evento_i7 = registrar_evento(
        sessao, comando, "instrumento", instrumento.id, "iniciar_ajuste",
        {"instrumento_id": instrumento.id, "versao_devolvida_id": versao.id,
         "numero_versao_devolvida": versao.numero, "pendencia_id": pendencia.id,
         "versao_rascunho_anterior": versao_anterior_rascunho,
         "versao_rascunho": rascunho.versao_rascunho,
         "lacre_conteudo": rascunho.lacre_conteudo, "conta_id": conta_id},
        codigo_evento="I7", registro_id=registro.id, ciclo_id=ciclo.id,
        versao_esquema_evento=2,
    )
    resultado = fechar_comando(
        comando,
        {"permitido": True, "motivo": "Ajuste iniciado",
         "instrumento_id": instrumento.id, "pendencia_id": pendencia.id,
         "versao_devolvida_id": versao.id,
         "versao_rascunho": rascunho.versao_rascunho,
         "estado_instrumento": "em_preenchimento",
         "estado_pendencia": pendencia.estado,
         "evento_i7": evento_i7.sequencia_cadeia},
    )
    sessao.flush()
    return resultado
