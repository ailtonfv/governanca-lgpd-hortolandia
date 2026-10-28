"""Rascunho incremental do FORM 1 integral baseado na REV13.

O módulo mantém o contrato candidato 3 separado do FORM 1 sintético. Os
Blocos 1 a 4 são editáveis; rascunho incompleto é permitido e nenhuma
submissão integral é criada.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.comandos import abrir_comando, fechar_comando
from app.eventos import lacre, registrar_auditoria, registrar_evento
from app.form1_integral import (CONDICOES_BLOCO_1, CONDICOES_BLOCO_2,
                                CONDICOES_CANAIS_BLOCO_2,
                                CONDICOES_BLOCO_4, CONDICOES_BLOCO_6, CONDICOES_BLOCO_8,
                                CONDICOES_BLOCO_9,
                                CONDICOES_BLOCO_10,
                                CONDICOES_BLOCO_11,
                                CONDICOES_BLOCO_12,
                                CONDICOES_PARTICIPANTE_BLOCO_3,
                                FAIXAS_VOLUME_REV13, IDS_BLOCO_2, IDS_BLOCO_4,
                                IDS_BLOCO_2_SEM_PORTA_ENTRADA, IDS_BLOCO_5,
                                IDS_BLOCO_6, IDS_BLOCO_7, IDS_BLOCO_8, IDS_BLOCO_9,
                                IDS_BLOCO_10,
                                IDS_BLOCO_11,
                                IDS_BLOCO_12,
                                IDS_PARTICIPANTE_BLOCO_3,
                                REVISAO_FONTE_FORM1_INTEGRAL,
                                VERSAO_CONTRATO_FORM1_INTEGRAL_CANDIDATA,
                                campos_por_id)
from app.modelos import (AtribuicaoForm1Integral, Ciclo, ConfirmacaoCanaisRegistro,
                          Conta, Pessoa,
                          RascunhoForm1Integral, Registro, RegistroCanal, Unidade)
from app.permissoes import tem_papel


CAMPOS_EDITAVEIS_BLOCO_1 = frozenset({"1.1", "1.1.1", "1.4"})
CAMPOS_REAPROVEITADOS_BLOCO_1 = frozenset({"1.2", "1.3"})
CAMPOS_EDITAVEIS_BLOCO_2 = frozenset(IDS_BLOCO_2)
CAMPOS_EDITAVEIS_CABECALHO_BLOCO_3 = frozenset({"3.1"})
CAMPOS_EDITAVEIS_PARTICIPANTE = frozenset(IDS_PARTICIPANTE_BLOCO_3)
CAMPOS_EDITAVEIS_BLOCO_4 = frozenset(IDS_BLOCO_4)
CAMPOS_EDITAVEIS_BLOCO_5 = frozenset(IDS_BLOCO_5)
CAMPOS_EDITAVEIS_BLOCO_6 = frozenset(IDS_BLOCO_6)
CAMPOS_EDITAVEIS_BLOCO_7 = frozenset(IDS_BLOCO_7)
CAMPOS_EDITAVEIS_BLOCO_8 = frozenset(IDS_BLOCO_8)
CAMPOS_EDITAVEIS_BLOCO_9 = frozenset(IDS_BLOCO_9)
CAMPOS_EDITAVEIS_BLOCO_10 = frozenset(IDS_BLOCO_10)
CAMPOS_EDITAVEIS_BLOCO_11 = frozenset(IDS_BLOCO_11)
CAMPOS_EDITAVEIS_BLOCO_12 = frozenset(IDS_BLOCO_12)
CAMPOS_SECRETARIA = frozenset({"2.2", "2.4.1"})
CAMPOS_VOLUME = frozenset({"2.8", "2.9", "2.10"})
CONTROLE_MULTIPLO = "seleção múltipla (combo com marcações)"
MAPA_TIPO_OBJETO = {
    "processo": "Processo",
    "atividade": "Atividade",
    "servico": "Serviço",
}
LIMITE_COMPLEMENTO_OUTRO_5_1 = 200
PADRAO_IDENTIFICADOR_CONCRETO = re.compile(
    r"@|\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b|\d{4,}|"
    r"\b(?:cpf|rg|matr[ií]cula|telefone|e-mail|email)\s*[:#-]",
    re.IGNORECASE,
)


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
        elif campo.controle == CONTROLE_MULTIPLO or campo_id in {"4.2.5.1", "6.2.2", "9.2.2", "10.4"}:
            if not isinstance(valor, list):
                return f"{campo_id}: a resposta deve ser uma lista"
            if len(valor) != len(set(valor)):
                return f"{campo_id}: a seleção contém opção repetida"
            alternativas = (
                catalogo["5.1"].alternativas
                if campo_id in {"4.2.5.1", "6.2.2", "9.2.2", "10.4"}
                else campo.alternativas
            )
            if any(item not in alternativas for item in valor):
                return f"{campo_id}: opção fora do catálogo REV13"
        elif campo.alternativas:
            if valor not in campo.alternativas:
                return f"{campo_id}: opção fora do catálogo REV13"
        elif campo_id == "12.1.1":
            if not isinstance(valor, str) or not valor.strip().isdigit():
                return "12.1.1: informe somente o número do prazo"
        elif not isinstance(valor, str):
            return f"{campo_id}: a resposta deve ser texto"
    return None


def _validar_condicionais(respostas, condicoes, ativacao_externa=None):
    """Recusa resposta enviada para ramo que não está ativo no mesmo recorte."""

    ativacao_externa = ativacao_externa or {}
    for campo_id, condicao in condicoes.items():
        clausulas = (
            (condicao,) if condicao and isinstance(condicao[0], str) else condicao
        )
        esta_ativo = all(
            any(item in valores_ativos for item in valor)
            if isinstance((valor := respostas.get(campo_controlador)), list)
            else valor in valores_ativos
            for campo_controlador, valores_ativos in clausulas
        )
        esta_ativo = ativacao_externa.get(campo_id, esta_ativo)
        if campo_id in respostas and not esta_ativo:
            return (
                f"{campo_id}: campo condicional inativo para a resposta de "
                + ", ".join(item[0] for item in clausulas)
            )
    return None


def _conteudo_com_respostas_do_bloco(
    rascunho, *, campos_editaveis, respostas, condicoes, ativacao_externa=None,
):
    """Substitui um bloco e preserva respostas que perderam aplicabilidade."""

    atuais = dict(rascunho.conteudo.get("respostas", {}))
    inativas = dict(rascunho.conteudo.get("respostas_inativas", {}))
    ativacao_externa = ativacao_externa or {}
    proxima_versao = rascunho.versao_rascunho + 1
    for campo_id, condicao in condicoes.items():
        clausulas = (
            (condicao,) if condicao and isinstance(condicao[0], str) else condicao
        )
        valor_anterior = atuais.get(campo_id)
        esta_ativo = all(
            any(item in valores_ativos for item in valor)
            if isinstance((valor := respostas.get(campo_controlador)), list)
            else valor in valores_ativos
            for campo_controlador, valores_ativos in clausulas
        )
        esta_ativo = ativacao_externa.get(campo_id, esta_ativo)
        if not esta_ativo and valor_anterior not in (None, "", []):
            historico = inativas.get(campo_id, [])
            if isinstance(historico, dict):
                historico = [historico]
            historico = list(historico)
            historico.append({
                "valor": valor_anterior,
                "condicoes": [
                    {"campo_controlador": controlador, "valores_ativos": list(valores)}
                    for controlador, valores in clausulas
                ],
                "desativada_na_versao": proxima_versao,
            })
            inativas[campo_id] = historico
    for campo_id in campos_editaveis:
        atuais.pop(campo_id, None)
    atuais.update({
        campo_id: valor for campo_id, valor in respostas.items()
        if valor not in (None, "", [])
    })
    conteudo = {**rascunho.conteudo, "respostas": atuais}
    if inativas:
        conteudo["respostas_inativas"] = inativas
    else:
        conteudo.pop("respostas_inativas", None)
    return conteudo


def _normalizar_complemento_outro_5_1(valor):
    if not isinstance(valor, str):
        return None, "5.1: o complemento de Outro deve ser texto"
    complemento = " ".join(valor.split())
    if len(complemento) > LIMITE_COMPLEMENTO_OUTRO_5_1:
        return None, "5.1: o complemento de Outro deve ter até 200 caracteres"
    if complemento and PADRAO_IDENTIFICADOR_CONCRETO.search(complemento):
        return None, (
            "5.1: descreva somente a categoria, sem dado pessoal, contato, "
            "matrícula ou identificador concreto"
        )
    return complemento, None


def problemas_submissao_bloco_5(conteudo):
    """Prepara as travas da submissão futura sem habilitá-la."""

    respostas = conteudo.get("respostas", {}) if isinstance(conteudo, dict) else {}
    categorias = respostas.get("5.1", [])
    problemas = []
    if not isinstance(categorias, list) or not categorias:
        problemas.append("5.1: informe ao menos uma categoria de dado")
        return problemas
    if "A confirmar" in categorias:
        problemas.append("5.1: A confirmar não satisfaz a submissão integral")
    complemento = conteudo.get("complementos", {}).get("5.1", "")
    if "Outro" in categorias and not complemento:
        problemas.append("5.1: informe o complemento descritivo de Outro")
    return problemas


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
    confirmacao_canais = sessao.get(ConfirmacaoCanaisRegistro, registro_id)
    classificacoes_canais = frozenset()
    ativacao_canais = None
    if confirmacao_canais is not None:
        classificacoes_canais = frozenset(
            item for item in sessao.scalars(
                select(RegistroCanal.classificacao_form1_snapshot).where(
                    RegistroCanal.registro_id == registro_id,
                    RegistroCanal.classificacao_form1_snapshot.is_not(None),
                )
            )
        )
        ativacao_canais = {
            campo_id: classificacao in classificacoes_canais
            for campo_id, classificacao in CONDICOES_CANAIS_BLOCO_2.items()
        }
    campos_editaveis = (
        CAMPOS_EDITAVEIS_BLOCO_2
        if confirmacao_canais is None
        else frozenset(IDS_BLOCO_2_SEM_PORTA_ENTRADA)
    )
    problema = None
    if confirmacao_canais is not None and "2.1" in respostas:
        problema = (
            "2.1: os canais confirmados pelo APA são históricos e somente para consulta"
        )
    problema = problema or _validar_respostas_catalogadas(
        sessao, respostas, campos_editaveis
    )
    problema = problema or _validar_condicionais(
        respostas, CONDICOES_BLOCO_2, ativacao_canais
    )
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
    conteudo = _conteudo_com_respostas_do_bloco(
        rascunho,
        campos_editaveis=campos_editaveis,
        respostas=respostas,
        condicoes=CONDICOES_BLOCO_2,
        ativacao_externa=ativacao_canais,
    )
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
    problema = problema or _validar_condicionais(respostas, CONDICOES_BLOCO_4)
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
    conteudo = _conteudo_com_respostas_do_bloco(
        rascunho,
        campos_editaveis=CAMPOS_EDITAVEIS_BLOCO_4,
        respostas=respostas,
        condicoes=CONDICOES_BLOCO_4,
    )
    return _salvar_conteudo(
        sessao, comando=comando, registro=registro, rascunho=rascunho,
        pessoa_id=pessoa_id, versao_lida=versao_lida, conteudo=conteudo,
        tipo_evento="salvar_bloco_4_form1_integral",
        motivo="Bloco 4 do FORM 1 integral salvo",
        detalhes={"campos_editados": sorted(respostas)}, momento=momento,
    )


def salvar_bloco_5_form1_integral(
    sessao, *, comando_id, conta_id, registro_id, versao_lida, respostas,
    complemento_outro="", momento=None,
):
    """Salva as categorias de dados sem antecipar a submissão integral."""

    momento = momento or _agora_utc()
    complemento, problema_complemento = _normalizar_complemento_outro_5_1(
        complemento_outro
    )
    parametros = {
        "conta_id": conta_id,
        "registro_id": registro_id,
        "versao_lida": versao_lida,
        "respostas": respostas,
        "complemento_outro": complemento,
    }
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(
        sessao, comando_id, "salvar_bloco_5_form1_integral", parametros,
        ator_tipo, ator_id, conta_id,
    )
    if resposta is not None:
        return resposta
    problema = _validar_respostas_catalogadas(
        sessao, respostas, CAMPOS_EDITAVEIS_BLOCO_5
    )
    categorias = respostas.get("5.1", []) if isinstance(respostas, dict) else []
    if not problema and "A confirmar" in categorias and len(categorias) != 1:
        problema = "5.1: A confirmar não pode coexistir com outra alternativa"
    if not problema and complemento and "Outro" not in categorias:
        problema = "5.1: o complemento somente pode ser usado quando Outro estiver marcado"
    problema = problema or problema_complemento
    if problema:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            "salvar_bloco_5_form1_integral", problema,
        )
    registro, pessoa_id, rascunho, comando, resposta = _preparar_alteracao(
        sessao, comando_id=comando_id, tipo_comando="salvar_bloco_5_form1_integral",
        conta_id=conta_id, registro_id=registro_id, versao_lida=versao_lida,
        parametros=parametros, comando=comando,
    )
    if resposta is not None:
        return resposta
    conteudo = _conteudo_com_respostas_do_bloco(
        rascunho,
        campos_editaveis=CAMPOS_EDITAVEIS_BLOCO_5,
        respostas=respostas,
        condicoes={},
    )
    complementos = dict(rascunho.conteudo.get("complementos", {}))
    complemento_anterior = complementos.get("5.1", "")
    if complemento_anterior and complemento_anterior != complemento:
        inativos = dict(rascunho.conteudo.get("complementos_inativos", {}))
        historico = list(inativos.get("5.1", []))
        historico.append({
            "valor": complemento_anterior,
            "motivo": "substituído" if complemento else "removido do rascunho ativo",
            "desativado_na_versao": versao_lida + 1,
        })
        inativos["5.1"] = historico
        conteudo["complementos_inativos"] = inativos
    if "Outro" in categorias and complemento:
        complementos["5.1"] = complemento
    else:
        complementos.pop("5.1", None)
    if complementos:
        conteudo["complementos"] = complementos
    else:
        conteudo.pop("complementos", None)
    return _salvar_conteudo(
        sessao, comando=comando, registro=registro, rascunho=rascunho,
        pessoa_id=pessoa_id, versao_lida=versao_lida, conteudo=conteudo,
        tipo_evento="salvar_bloco_5_form1_integral",
        motivo="Bloco 5 do FORM 1 integral salvo",
        detalhes={
            "campos_editados": sorted(respostas),
            "complemento_outro_informado": bool(complemento),
        },
        momento=momento,
    )


def salvar_bloco_6_form1_integral(
    sessao, *, comando_id, conta_id, registro_id, versao_lida, respostas, momento=None
):
    """Salva origem e eventual relação entre fonte e categorias de dados."""

    momento = momento or _agora_utc()
    tipo_comando = "salvar_bloco_6_form1_integral"
    parametros = {
        "conta_id": conta_id, "registro_id": registro_id,
        "versao_lida": versao_lida, "respostas": respostas,
    }
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(
        sessao, comando_id, tipo_comando, parametros,
        ator_tipo, ator_id, conta_id,
    )
    if resposta is not None:
        return resposta
    problema = _validar_respostas_catalogadas(
        sessao, respostas, CAMPOS_EDITAVEIS_BLOCO_6
    )
    problema = problema or _validar_condicionais(respostas, CONDICOES_BLOCO_6)
    if problema:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            tipo_comando, problema,
        )
    registro, pessoa_id, rascunho, comando, resposta = _preparar_alteracao(
        sessao, comando_id=comando_id, tipo_comando=tipo_comando,
        conta_id=conta_id, registro_id=registro_id, versao_lida=versao_lida,
        parametros=parametros, comando=comando,
    )
    if resposta is not None:
        return resposta
    conteudo = _conteudo_com_respostas_do_bloco(
        rascunho,
        campos_editaveis=CAMPOS_EDITAVEIS_BLOCO_6,
        respostas=respostas,
        condicoes=CONDICOES_BLOCO_6,
    )
    return _salvar_conteudo(
        sessao, comando=comando, registro=registro, rascunho=rascunho,
        pessoa_id=pessoa_id, versao_lida=versao_lida, conteudo=conteudo,
        tipo_evento=tipo_comando,
        motivo="Bloco 6 do FORM 1 integral salvo",
        detalhes={"campos_editados": sorted(respostas)}, momento=momento,
    )


def _salvar_bloco_catalogado_form1_integral(
    sessao, *, numero_bloco, comando_id, conta_id, registro_id, versao_lida,
    respostas, campos_editaveis, condicoes, momento=None,
):
    """Executa o padrão atômico dos blocos catalogados do rascunho REV13."""

    momento = momento or _agora_utc()
    tipo_comando = f"salvar_bloco_{numero_bloco}_form1_integral"
    parametros = {
        "conta_id": conta_id, "registro_id": registro_id,
        "versao_lida": versao_lida, "respostas": respostas,
    }
    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(
        sessao, comando_id, tipo_comando, parametros, ator_tipo, ator_id, conta_id,
    )
    if resposta is not None:
        return resposta
    problema = _validar_respostas_catalogadas(sessao, respostas, campos_editaveis)
    problema = problema or _validar_condicionais(respostas, condicoes)
    if problema:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            tipo_comando, problema,
        )
    registro, pessoa_id, rascunho, comando, resposta = _preparar_alteracao(
        sessao, comando_id=comando_id, tipo_comando=tipo_comando,
        conta_id=conta_id, registro_id=registro_id, versao_lida=versao_lida,
        parametros=parametros, comando=comando,
    )
    if resposta is not None:
        return resposta
    conteudo = _conteudo_com_respostas_do_bloco(
        rascunho, campos_editaveis=campos_editaveis, respostas=respostas,
        condicoes=condicoes,
    )
    return _salvar_conteudo(
        sessao, comando=comando, registro=registro, rascunho=rascunho,
        pessoa_id=pessoa_id, versao_lida=versao_lida, conteudo=conteudo,
        tipo_evento=tipo_comando,
        motivo=f"Bloco {numero_bloco} do FORM 1 integral salvo",
        detalhes={"campos_editados": sorted(respostas)}, momento=momento,
    )


def salvar_bloco_7_form1_integral(
    sessao, *, comando_id, conta_id, registro_id, versao_lida, respostas, momento=None
):
    """Salva as operações de tratamento do Bloco 7."""

    return _salvar_bloco_catalogado_form1_integral(
        sessao, numero_bloco=7, comando_id=comando_id, conta_id=conta_id,
        registro_id=registro_id, versao_lida=versao_lida, respostas=respostas,
        campos_editaveis=CAMPOS_EDITAVEIS_BLOCO_7, condicoes={}, momento=momento,
    )


def salvar_bloco_8_form1_integral(
    sessao, *, comando_id, conta_id, registro_id, versao_lida, respostas, momento=None
):
    """Salva meios, ambientes, suportes e contingências do Bloco 8."""

    return _salvar_bloco_catalogado_form1_integral(
        sessao, numero_bloco=8, comando_id=comando_id, conta_id=conta_id,
        registro_id=registro_id, versao_lida=versao_lida, respostas=respostas,
        campos_editaveis=CAMPOS_EDITAVEIS_BLOCO_8,
        condicoes=CONDICOES_BLOCO_8, momento=momento,
    )


def salvar_bloco_9_form1_integral(
    sessao, *, comando_id, conta_id, registro_id, versao_lida, respostas, momento=None
):
    """Salva perfis e diferenciação de acesso do Bloco 9."""

    return _salvar_bloco_catalogado_form1_integral(
        sessao, numero_bloco=9, comando_id=comando_id, conta_id=conta_id,
        registro_id=registro_id, versao_lida=versao_lida, respostas=respostas,
        campos_editaveis=CAMPOS_EDITAVEIS_BLOCO_9,
        condicoes=CONDICOES_BLOCO_9, momento=momento,
    )


def salvar_bloco_10_form1_integral(
    sessao, *, comando_id, conta_id, registro_id, versao_lida, respostas, momento=None
):
    """Salva envio, disponibilização e saída de dados do Bloco 10."""

    return _salvar_bloco_catalogado_form1_integral(
        sessao, numero_bloco=10, comando_id=comando_id, conta_id=conta_id,
        registro_id=registro_id, versao_lida=versao_lida, respostas=respostas,
        campos_editaveis=CAMPOS_EDITAVEIS_BLOCO_10,
        condicoes=CONDICOES_BLOCO_10, momento=momento,
    )


def salvar_bloco_11_form1_integral(
    sessao, *, comando_id, conta_id, registro_id, versao_lida, respostas, momento=None
):
    """Salva repositórios, infraestrutura e dependência de terceiro."""

    return _salvar_bloco_catalogado_form1_integral(
        sessao, numero_bloco=11, comando_id=comando_id, conta_id=conta_id,
        registro_id=registro_id, versao_lida=versao_lida, respostas=respostas,
        campos_editaveis=CAMPOS_EDITAVEIS_BLOCO_11,
        condicoes=CONDICOES_BLOCO_11, momento=momento,
    )


def salvar_bloco_12_form1_integral(
    sessao, *, comando_id, conta_id, registro_id, versao_lida, respostas, momento=None
):
    """Salva prazo de guarda, destinação e evidências do Bloco 12."""

    return _salvar_bloco_catalogado_form1_integral(
        sessao, numero_bloco=12, comando_id=comando_id, conta_id=conta_id,
        registro_id=registro_id, versao_lida=versao_lida, respostas=respostas,
        campos_editaveis=CAMPOS_EDITAVEIS_BLOCO_12,
        condicoes=CONDICOES_BLOCO_12, momento=momento,
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
    participantes = list(conteudo.get("participantes", []))
    if resposta_3_1 != "Sim" and participantes:
        participantes_inativos = list(conteudo.get("participantes_inativos", []))
        participantes_inativos.extend(participantes)
        conteudo["participantes_inativos"] = participantes_inativos
        conteudo["participantes"] = []
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
    problema = problema or _validar_condicionais(
        respostas, CONDICOES_PARTICIPANTE_BLOCO_3
    )
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
    if rascunho.conteudo.get("respostas", {}).get("3.1") != "Sim":
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            "adicionar_participante_form1",
            "participantes somente podem ser adicionados quando 3.1 = Sim",
        )
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
    problema = problema or _validar_condicionais(respostas, CONDICOES_BLOCO_1)
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

    conteudo = _conteudo_com_respostas_do_bloco(
        rascunho,
        campos_editaveis=CAMPOS_EDITAVEIS_BLOCO_1,
        respostas=respostas,
        condicoes=CONDICOES_BLOCO_1,
    )
    conteudo["respostas"].update(_respostas_reaproveitadas(registro))
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
