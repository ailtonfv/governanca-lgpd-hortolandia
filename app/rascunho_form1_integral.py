"""Rascunho incremental do FORM 1 integral baseado na REV13.

O módulo mantém o contrato candidato 3 separado do FORM 1 sintético. Os
Blocos 1 a 4 são editáveis; rascunho incompleto é permitido e nenhuma
submissão integral é criada.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.comandos import abrir_comando, fechar_comando
from app.eventos import lacre, registrar_auditoria, registrar_evento
from app.form1_integral import (FAIXAS_VOLUME_REV13, IDS_BLOCO_2, IDS_BLOCO_4,
                                IDS_PARTICIPANTE_BLOCO_3,
                                REVISAO_FONTE_FORM1_INTEGRAL,
                                VERSAO_CONTRATO_FORM1_INTEGRAL_CANDIDATA,
                                campos_por_id)
from app.modelos import (AtribuicaoForm1Integral, Ciclo, Conta, Pessoa,
                          RascunhoForm1Integral, Registro, Unidade)
from app.permissoes import tem_papel


CAMPOS_EDITAVEIS_BLOCO_1 = frozenset({"1.1", "1.1.1", "1.4"})
CAMPOS_REAPROVEITADOS_BLOCO_1 = frozenset({"1.2", "1.3"})
CAMPOS_EDITAVEIS_BLOCO_2 = frozenset(IDS_BLOCO_2)
CAMPOS_EDITAVEIS_CABECALHO_BLOCO_3 = frozenset({"3.1"})
CAMPOS_EDITAVEIS_PARTICIPANTE = frozenset(IDS_PARTICIPANTE_BLOCO_3)
CAMPOS_EDITAVEIS_BLOCO_4 = frozenset(IDS_BLOCO_4)
CAMPOS_SECRETARIA = frozenset({"2.2", "2.4.1"})
CAMPOS_VOLUME = frozenset({"2.8", "2.9", "2.10"})
CONTROLE_MULTIPLO = "seleção múltipla (combo com marcações)"
MAPA_TIPO_OBJETO = {
    "processo": "Processo",
    "atividade": "Atividade",
    "servico": "Serviço",
}


def _agora_utc():
    return datetime.now(timezone.utc)


def _canonico(conteudo):
    return json.dumps(conteudo, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _lacre(conteudo):
    return lacre(_canonico(conteudo))


def _ator(sessao, conta_id):
    conta = sessao.get(Conta, conta_id)
    pessoa_id = conta.pessoa_id if conta is not None else None
    ator_tipo, ator_id = (("pessoa", pessoa_id) if pessoa_id
                          else ("desconhecido", conta_id))
    return conta, pessoa_id, ator_tipo, ator_id


def _negar(sessao, comando, ator_tipo, ator_id, conta_id, registro_id, acao, motivo,
           **detalhes):
    registrar_auditoria(
        sessao,
        "tentativa_negada",
        ator_tipo,
        ator_id,
        {
            "acao_tentada": acao,
            "registro_id": registro_id,
            "conta_id": conta_id,
            "motivo": motivo,
        },
        comando_id=None if comando is None else comando.id,
    )
    resultado = {"permitido": False, "motivo": motivo, **detalhes}
    if comando is None:
        return {**resultado, "reexecutado": False}
    resposta = fechar_comando(comando, resultado)
    sessao.flush()
    return resposta


def _contexto_autorizado(sessao, conta_id, registro_id):
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    registro = sessao.scalars(
        select(Registro).where(Registro.id == registro_id).with_for_update()
    ).one_or_none()
    if conta is None or not conta.ativa:
        return None, None, ator_tipo, ator_id, "conta inexistente ou desativada"
    pessoa = sessao.get(Pessoa, pessoa_id)
    if pessoa is None or not pessoa.ativa:
        return None, None, ator_tipo, ator_id, "pessoa inexistente ou desativada"
    if registro is None:
        return None, None, ator_tipo, ator_id, "Registro inexistente"
    atribuicao = sessao.get(AtribuicaoForm1Integral, registro_id)
    if atribuicao is None:
        return registro, None, ator_tipo, ator_id, "defina o ARP antes de iniciar o FORM 1 integral"
    if atribuicao.arp_atual_id != pessoa_id:
        return registro, pessoa_id, ator_tipo, ator_id, "somente o ARP atual pode alterar este rascunho"
    if not tem_papel(
        sessao, pessoa_id, registro.unidade_principal_atual_id, {"preenchedor"}
    ):
        return registro, pessoa_id, ator_tipo, ator_id, (
            "o ARP não possui designação vigente de preenchedor nesta Secretaria"
        )
    return registro, pessoa_id, ator_tipo, ator_id, None


def _ciclo(sessao, registro):
    return sessao.scalars(
        select(Ciclo).where(
            Ciclo.registro_id == registro.id,
            Ciclo.numero == registro.ciclo_atual,
        )
    ).one()


def _respostas_reaproveitadas(registro):
    return {
        "1.2": MAPA_TIPO_OBJETO[registro.tipo_objeto],
        "1.3": registro.titulo_objeto,
    }


def iniciar_rascunho_form1_integral(
    sessao, *, comando_id, conta_id, registro_id, momento=None
):
    """Cria o envelope parcial REV13 sem tocar no Instrumento nuclear."""

    momento = momento or _agora_utc()
    parametros = {"conta_id": conta_id, "registro_id": registro_id}
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(
        sessao, comando_id, "iniciar_rascunho_form1_integral", parametros,
        ator_tipo, ator_id, conta_id,
    )
    if resposta is not None:
        return resposta

    registro, pessoa_id, ator_tipo, ator_id, problema = _contexto_autorizado(
        sessao, conta_id, registro_id
    )
    if problema:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            "iniciar_rascunho_form1_integral", problema,
        )
    if sessao.get(RascunhoForm1Integral, registro_id) is not None:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            "iniciar_rascunho_form1_integral", "o rascunho integral já foi iniciado",
        )

    conteudo = {
        "revisao_fonte": REVISAO_FONTE_FORM1_INTEGRAL,
        "versao_contrato": VERSAO_CONTRATO_FORM1_INTEGRAL_CANDIDATA,
        "respostas": _respostas_reaproveitadas(registro),
    }
    rascunho = RascunhoForm1Integral(
        registro_id=registro.id,
        conteudo=conteudo,
        versao_rascunho=1,
        salvo_por=pessoa_id,
        salvo_em=momento,
        lacre_conteudo=_lacre(conteudo),
    )
    sessao.add(rascunho)
    evento = registrar_evento(
        sessao, comando, "registro", registro.codigo_lgpd,
        "iniciar_rascunho_form1_integral",
        {
            "registro_id": registro.id,
            "revisao_fonte": REVISAO_FONTE_FORM1_INTEGRAL,
            "versao_contrato": VERSAO_CONTRATO_FORM1_INTEGRAL_CANDIDATA,
            "versao_rascunho": 1,
            "lacre_conteudo": rascunho.lacre_conteudo,
            "campos_reaproveitados": sorted(CAMPOS_REAPROVEITADOS_BLOCO_1),
        },
        registro_id=registro.id,
        ciclo_id=_ciclo(sessao, registro).id,
        versao_esquema_evento=2,
    )
    registro.sequencia_atual = evento.sequencia_cadeia
    resultado = fechar_comando(comando, {
        "permitido": True,
        "motivo": "rascunho do FORM 1 integral iniciado",
        "registro_id": registro.id,
        "versao_rascunho": 1,
        "lacre_conteudo": rascunho.lacre_conteudo,
        "evento": evento.sequencia_cadeia,
    })
    sessao.flush()
    return resultado


def _validar_respostas_bloco_1(respostas):
    if not isinstance(respostas, dict):
        return "as respostas do Bloco 1 devem formar um objeto"
    desconhecidos = set(respostas) - CAMPOS_EDITAVEIS_BLOCO_1
    if desconhecidos:
        return "campo não editável ou desconhecido no Bloco 1: " + ", ".join(sorted(desconhecidos))
    catalogo = campos_por_id()
    for campo_id in ("1.1", "1.4"):
        valor = respostas.get(campo_id)
        if valor is not None and valor not in catalogo[campo_id].alternativas:
            return f"{campo_id}: opção fora do catálogo REV13"
    referencia = respostas.get("1.1.1")
    if referencia is not None and (not isinstance(referencia, str) or len(referencia) > 500):
        return "1.1.1: a referência deve ser um texto de até 500 caracteres"
    return None


def _validar_respostas_catalogadas(sessao, respostas, campos_permitidos):
    """Valida o recorte REV13 sem antecipar as regras de submissão integral."""

    if not isinstance(respostas, dict):
        return "as respostas devem formar um objeto"
    desconhecidos = set(respostas) - set(campos_permitidos)
    if desconhecidos:
        return "campo não editável ou desconhecido: " + ", ".join(sorted(desconhecidos))
    catalogo = campos_por_id()
    for campo_id, valor in respostas.items():
        campo = catalogo[campo_id]
        if campo_id in CAMPOS_SECRETARIA:
            unidade = sessao.get(Unidade, valor) if isinstance(valor, str) else None
            if unidade is None or not unidade.ativa or unidade.id == "UNID-GOV":
                return f"{campo_id}: Secretaria fora do catálogo ativo"
        elif campo_id in CAMPOS_VOLUME:
            if valor not in FAIXAS_VOLUME_REV13:
                return f"{campo_id}: faixa fora do catálogo REV13"
        elif campo.controle == CONTROLE_MULTIPLO or campo_id == "4.2.5.1":
            if not isinstance(valor, list):
                return f"{campo_id}: a resposta deve ser uma lista"
            if len(valor) != len(set(valor)):
                return f"{campo_id}: a seleção contém opção repetida"
            alternativas = (
                catalogo["5.1"].alternativas if campo_id == "4.2.5.1"
                else campo.alternativas
            )
            if any(item not in alternativas for item in valor):
                return f"{campo_id}: opção fora do catálogo REV13"
        elif campo.alternativas:
            if valor not in campo.alternativas:
                return f"{campo_id}: opção fora do catálogo REV13"
        elif not isinstance(valor, str):
            return f"{campo_id}: a resposta deve ser texto"
    return None


def _validar_versao(versao_lida):
    if not isinstance(versao_lida, int) or isinstance(versao_lida, bool) or versao_lida < 1:
        return "versao_lida deve ser um inteiro positivo"
    return None


def _rascunho_bloqueado(sessao, registro_id):
    return sessao.scalars(
        select(RascunhoForm1Integral)
        .where(RascunhoForm1Integral.registro_id == registro_id)
        .with_for_update()
    ).one_or_none()


def _salvar_conteudo(
    sessao, *, comando, registro, rascunho, pessoa_id, versao_lida,
    conteudo, tipo_evento, motivo, detalhes, momento,
):
    nova_versao = versao_lida + 1
    rascunho.conteudo = conteudo
    rascunho.versao_rascunho = nova_versao
    rascunho.salvo_por = pessoa_id
    rascunho.salvo_em = momento
    rascunho.lacre_conteudo = _lacre(conteudo)
    evento = registrar_evento(
        sessao, comando, "registro", registro.codigo_lgpd, tipo_evento,
        {
            "registro_id": registro.id,
            "versao_anterior": versao_lida,
            "versao_rascunho": nova_versao,
            "lacre_conteudo": rascunho.lacre_conteudo,
            **detalhes,
        },
        registro_id=registro.id,
        ciclo_id=_ciclo(sessao, registro).id,
        versao_esquema_evento=2,
    )
    registro.sequencia_atual = evento.sequencia_cadeia
    resultado = fechar_comando(comando, {
        "permitido": True,
        "motivo": motivo,
        "registro_id": registro.id,
        "versao_rascunho": nova_versao,
        "lacre_conteudo": rascunho.lacre_conteudo,
        "evento": evento.sequencia_cadeia,
    })
    sessao.flush()
    return resultado


def _preparar_alteracao(
    sessao, *, comando_id, tipo_comando, conta_id, registro_id,
    versao_lida, parametros, comando=None,
):
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    if comando is None:
        comando, resposta = abrir_comando(
            sessao, comando_id, tipo_comando, parametros, ator_tipo, ator_id, conta_id,
        )
        if resposta is not None:
            return None, None, None, None, resposta
    problema = _validar_versao(versao_lida)
    if problema:
        return None, None, None, comando, _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            tipo_comando, problema,
        )
    registro, pessoa_id, ator_tipo, ator_id, problema = _contexto_autorizado(
        sessao, conta_id, registro_id
    )
    if problema:
        return None, None, None, comando, _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            tipo_comando, problema,
        )
    rascunho = _rascunho_bloqueado(sessao, registro_id)
    if rascunho is None:
        return None, None, None, comando, _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            tipo_comando, "inicie o rascunho integral antes de salvar",
        )
    if rascunho.versao_rascunho != versao_lida:
        return None, None, None, comando, _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            tipo_comando, "rascunho integral desatualizado: recarregue antes de salvar",
            versao_lida=versao_lida, versao_atual=rascunho.versao_rascunho,
        )
    return registro, pessoa_id, rascunho, comando, None


def salvar_bloco_2_form1_integral(
    sessao, *, comando_id, conta_id, registro_id, versao_lida, respostas, momento=None
):
    """Salva o Bloco 2 como rascunho, inclusive ramificações OUV/e-SIC."""

    momento = momento or _agora_utc()
    parametros = {
        "conta_id": conta_id, "registro_id": registro_id,
        "versao_lida": versao_lida, "respostas": respostas,
    }
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(
        sessao, comando_id, "salvar_bloco_2_form1_integral", parametros,
        ator_tipo, ator_id, conta_id,
    )
    if resposta is not None:
        return resposta
    problema = _validar_respostas_catalogadas(sessao, respostas, CAMPOS_EDITAVEIS_BLOCO_2)
    if problema:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            "salvar_bloco_2_form1_integral", problema,
        )
    registro, pessoa_id, rascunho, comando, resposta = _preparar_alteracao(
        sessao, comando_id=comando_id, tipo_comando="salvar_bloco_2_form1_integral",
        conta_id=conta_id, registro_id=registro_id, versao_lida=versao_lida,
        parametros=parametros, comando=comando,
    )
    if resposta is not None:
        return resposta
    atuais = dict(rascunho.conteudo.get("respostas", {}))
    for campo_id in CAMPOS_EDITAVEIS_BLOCO_2:
        atuais.pop(campo_id, None)
    atuais.update({campo_id: valor for campo_id, valor in respostas.items() if valor not in (None, "", [])})
    conteudo = {**rascunho.conteudo, "respostas": atuais}
    return _salvar_conteudo(
        sessao, comando=comando, registro=registro, rascunho=rascunho,
        pessoa_id=pessoa_id, versao_lida=versao_lida, conteudo=conteudo,
        tipo_evento="salvar_bloco_2_form1_integral",
        motivo="Bloco 2 do FORM 1 integral salvo",
        detalhes={"campos_editados": sorted(respostas)}, momento=momento,
    )


def salvar_bloco_4_form1_integral(
    sessao, *, comando_id, conta_id, registro_id, versao_lida, respostas, momento=None
):
    """Primeiro incremento da Etapa visual 2: titulares e representação."""

    momento = momento or _agora_utc()
    parametros = {
        "conta_id": conta_id, "registro_id": registro_id,
        "versao_lida": versao_lida, "respostas": respostas,
    }
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(
        sessao, comando_id, "salvar_bloco_4_form1_integral", parametros,
        ator_tipo, ator_id, conta_id,
    )
    if resposta is not None:
        return resposta
    problema = _validar_respostas_catalogadas(sessao, respostas, CAMPOS_EDITAVEIS_BLOCO_4)
    if problema:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            "salvar_bloco_4_form1_integral", problema,
        )
    registro, pessoa_id, rascunho, comando, resposta = _preparar_alteracao(
        sessao, comando_id=comando_id, tipo_comando="salvar_bloco_4_form1_integral",
        conta_id=conta_id, registro_id=registro_id, versao_lida=versao_lida,
        parametros=parametros, comando=comando,
    )
    if resposta is not None:
        return resposta
    atuais = dict(rascunho.conteudo.get("respostas", {}))
    for campo_id in CAMPOS_EDITAVEIS_BLOCO_4:
        atuais.pop(campo_id, None)
    atuais.update({campo_id: valor for campo_id, valor in respostas.items() if valor not in (None, "", [])})
    conteudo = {**rascunho.conteudo, "respostas": atuais}
    return _salvar_conteudo(
        sessao, comando=comando, registro=registro, rascunho=rascunho,
        pessoa_id=pessoa_id, versao_lida=versao_lida, conteudo=conteudo,
        tipo_evento="salvar_bloco_4_form1_integral",
        motivo="Bloco 4 do FORM 1 integral salvo",
        detalhes={"campos_editados": sorted(respostas)}, momento=momento,
    )


def salvar_cabecalho_bloco_3_form1_integral(
    sessao, *, comando_id, conta_id, registro_id, versao_lida, resposta_3_1, momento=None
):
    """Salva a indicação de existência de outros participantes."""

    momento = momento or _agora_utc()
    respostas = {} if not resposta_3_1 else {"3.1": resposta_3_1}
    problema = _validar_respostas_catalogadas(
        sessao, respostas, CAMPOS_EDITAVEIS_CABECALHO_BLOCO_3
    )
    parametros = {
        "conta_id": conta_id, "registro_id": registro_id,
        "versao_lida": versao_lida, "respostas": respostas,
    }
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(
        sessao, comando_id, "salvar_cabecalho_bloco_3", parametros,
        ator_tipo, ator_id, conta_id,
    )
    if resposta is not None:
        return resposta
    if problema:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            "salvar_cabecalho_bloco_3", problema,
        )
    registro, pessoa_id, rascunho, comando, resposta = _preparar_alteracao(
        sessao, comando_id=comando_id, tipo_comando="salvar_cabecalho_bloco_3",
        conta_id=conta_id, registro_id=registro_id, versao_lida=versao_lida,
        parametros=parametros, comando=comando,
    )
    if resposta is not None:
        return resposta
    atuais = dict(rascunho.conteudo.get("respostas", {}))
    atuais.pop("3.1", None)
    atuais.update(respostas)
    conteudo = {**rascunho.conteudo, "respostas": atuais}
    return _salvar_conteudo(
        sessao, comando=comando, registro=registro, rascunho=rascunho,
        pessoa_id=pessoa_id, versao_lida=versao_lida, conteudo=conteudo,
        tipo_evento="salvar_cabecalho_bloco_3",
        motivo="Bloco 3 do FORM 1 integral salvo",
        detalhes={"campos_editados": sorted(respostas)}, momento=momento,
    )


def adicionar_participante_form1_integral(
    sessao, *, comando_id, conta_id, registro_id, versao_lida, respostas, momento=None
):
    """Acrescenta uma ocorrência individualizada de participante ao Bloco 3."""

    momento = momento or _agora_utc()
    parametros = {
        "conta_id": conta_id, "registro_id": registro_id,
        "versao_lida": versao_lida, "respostas": respostas,
    }
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(
        sessao, comando_id, "adicionar_participante_form1", parametros,
        ator_tipo, ator_id, conta_id,
    )
    if resposta is not None:
        return resposta
    problema = _validar_respostas_catalogadas(sessao, respostas, CAMPOS_EDITAVEIS_PARTICIPANTE)
    if not respostas:
        problema = "informe ao menos um dado do participante"
    if problema:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            "adicionar_participante_form1", problema,
        )
    registro, pessoa_id, rascunho, comando, resposta = _preparar_alteracao(
        sessao, comando_id=comando_id, tipo_comando="adicionar_participante_form1",
        conta_id=conta_id, registro_id=registro_id, versao_lida=versao_lida,
        parametros=parametros, comando=comando,
    )
    if resposta is not None:
        return resposta
    participante_id = str(uuid.uuid4())
    participantes = list(rascunho.conteudo.get("participantes", []))
    participantes.append({"id": participante_id, "respostas": respostas})
    conteudo = {**rascunho.conteudo, "participantes": participantes}
    resultado = _salvar_conteudo(
        sessao, comando=comando, registro=registro, rascunho=rascunho,
        pessoa_id=pessoa_id, versao_lida=versao_lida, conteudo=conteudo,
        tipo_evento="adicionar_participante_form1",
        motivo="Participante do Bloco 3 adicionado",
        detalhes={"participante_id": participante_id, "campos_editados": sorted(respostas)},
        momento=momento,
    )
    resultado["participante_id"] = participante_id
    comando.resultado = {**comando.resultado, "participante_id": participante_id}
    return resultado


def remover_participante_form1_integral(
    sessao, *, comando_id, conta_id, registro_id, versao_lida, participante_id,
    momento=None,
):
    """Remove a ocorrência do rascunho; o evento preserva a trilha da ação."""

    momento = momento or _agora_utc()
    parametros = {
        "conta_id": conta_id, "registro_id": registro_id,
        "versao_lida": versao_lida, "participante_id": participante_id,
    }
    registro, pessoa_id, rascunho, comando, resposta = _preparar_alteracao(
        sessao, comando_id=comando_id, tipo_comando="remover_participante_form1",
        conta_id=conta_id, registro_id=registro_id, versao_lida=versao_lida,
        parametros=parametros,
    )
    if resposta is not None:
        return resposta
    participantes = list(rascunho.conteudo.get("participantes", []))
    filtrados = [item for item in participantes if item.get("id") != participante_id]
    if len(filtrados) == len(participantes):
        _, _, ator_tipo, ator_id = _ator(sessao, conta_id)
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            "remover_participante_form1", "participante inexistente neste rascunho",
        )
    conteudo = {**rascunho.conteudo, "participantes": filtrados}
    return _salvar_conteudo(
        sessao, comando=comando, registro=registro, rascunho=rascunho,
        pessoa_id=pessoa_id, versao_lida=versao_lida, conteudo=conteudo,
        tipo_evento="remover_participante_form1",
        motivo="Participante do Bloco 3 removido",
        detalhes={"participante_id": participante_id}, momento=momento,
    )


def salvar_bloco_1_form1_integral(
    sessao, *, comando_id, conta_id, registro_id, versao_lida, respostas, momento=None
):
    """Substitui os campos editáveis do Bloco 1 com controle otimista."""

    momento = momento or _agora_utc()
    parametros = {
        "conta_id": conta_id,
        "registro_id": registro_id,
        "versao_lida": versao_lida,
        "respostas": respostas,
    }
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(
        sessao, comando_id, "salvar_bloco_1_form1_integral", parametros,
        ator_tipo, ator_id, conta_id,
    )
    if resposta is not None:
        return resposta
    problema = _validar_respostas_bloco_1(respostas)
    if problema:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            "salvar_bloco_1_form1_integral", problema,
        )
    if not isinstance(versao_lida, int) or isinstance(versao_lida, bool) or versao_lida < 1:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            "salvar_bloco_1_form1_integral", "versao_lida deve ser um inteiro positivo",
        )

    registro, pessoa_id, ator_tipo, ator_id, problema = _contexto_autorizado(
        sessao, conta_id, registro_id
    )
    if problema:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            "salvar_bloco_1_form1_integral", problema,
        )
    rascunho = sessao.scalars(
        select(RascunhoForm1Integral)
        .where(RascunhoForm1Integral.registro_id == registro_id)
        .with_for_update()
    ).one_or_none()
    if rascunho is None:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            "salvar_bloco_1_form1_integral", "inicie o rascunho integral antes de salvar",
        )
    if rascunho.versao_rascunho != versao_lida:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            "salvar_bloco_1_form1_integral",
            "rascunho integral desatualizado: recarregue antes de salvar",
            versao_lida=versao_lida,
            versao_atual=rascunho.versao_rascunho,
        )

    atuais = dict(rascunho.conteudo.get("respostas", {}))
    for campo_id in CAMPOS_EDITAVEIS_BLOCO_1:
        atuais.pop(campo_id, None)
    atuais.update({campo_id: valor for campo_id, valor in respostas.items() if valor not in (None, "")})
    atuais.update(_respostas_reaproveitadas(registro))
    conteudo = {
        "revisao_fonte": REVISAO_FONTE_FORM1_INTEGRAL,
        "versao_contrato": VERSAO_CONTRATO_FORM1_INTEGRAL_CANDIDATA,
        "respostas": atuais,
    }
    nova_versao = rascunho.versao_rascunho + 1
    rascunho.conteudo = conteudo
    rascunho.versao_rascunho = nova_versao
    rascunho.salvo_por = pessoa_id
    rascunho.salvo_em = momento
    rascunho.lacre_conteudo = _lacre(conteudo)
    evento = registrar_evento(
        sessao, comando, "registro", registro.codigo_lgpd,
        "salvar_bloco_1_form1_integral",
        {
            "registro_id": registro.id,
            "versao_anterior": versao_lida,
            "versao_rascunho": nova_versao,
            "lacre_conteudo": rascunho.lacre_conteudo,
            "campos_editados": sorted(respostas),
        },
        registro_id=registro.id,
        ciclo_id=_ciclo(sessao, registro).id,
        versao_esquema_evento=2,
    )
    registro.sequencia_atual = evento.sequencia_cadeia
    resultado = fechar_comando(comando, {
        "permitido": True,
        "motivo": "Bloco 1 do FORM 1 integral salvo",
        "registro_id": registro.id,
        "versao_rascunho": nova_versao,
        "lacre_conteudo": rascunho.lacre_conteudo,
        "evento": evento.sequencia_cadeia,
    })
    sessao.flush()
    return resultado
