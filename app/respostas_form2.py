"""Validação e projeção das respostas estruturadas da Etapa 1 do FORM 2.

Somente controles explicitamente habilitados no contrato privado podem receber
escrita. O módulo não conclui análise, não cria parecer e não encaminha pendência.
"""

from copy import deepcopy

from app.catalogo_form2_rev18 import carregar_catalogo
from app.contrato_form2_respostas import (CONTRATO_RESPOSTAS, VERSAO as VERSAO_CONTROLES,
                                           carregar_contrato, referencias_anpd)


ENVELOPE_V2 = "F2-DEMO-PREP-v2"
LIMITE_COMPLEMENTO = 1000


def _indice_catalogo(catalogo):
    return {item["id"]: item for bloco in catalogo["blocos"] for item in bloco["itens"]}


def definicao_bloco(numero: int) -> dict:
    contrato, catalogo = carregar_contrato(), carregar_catalogo()
    editoriais = _indice_catalogo(catalogo)
    itens_contrato = [item for item in contrato["itens"] if item["bloco"] == numero]
    alternativas = {}
    for alternativa in contrato["alternativas"]:
        alternativas.setdefault(alternativa["id"], []).append(alternativa)
    condicoes = {}
    for condicao in contrato["condicoes"]:
        if condicao["alvo"] in editoriais:
            condicoes.setdefault(condicao["alvo"], []).append(condicao)

    itens = []
    for item in itens_contrato:
        editorial = editoriais[item["id"]]
        escolha = editorial.get("escolha_documental")
        itens.append({
            **deepcopy(item),
            "enunciado": editorial["enunciado"],
            "orientacao": editorial.get("orientacao"),
            "modo": escolha.get("modo") if escolha else None,
            "alternativas": deepcopy(alternativas.get(item["id"], [])),
            "condicoes": deepcopy(condicoes.get(item["id"], [])),
            "fontes_publicas": referencias_anpd(item.get("referencias_anpd")),
        })
    return {"numero": numero, "versao": contrato["versao"], "itens": itens}


def _habilitados(definicao):
    return {item["id"]: item for item in definicao["itens"] if item["edicao"] == "habilitada"}


def _ativa(item, respostas):
    relevantes = [c for c in item["condicoes"] if c["operador"] != "SEMPRE"]
    if not relevantes:
        return True
    resultados = []
    for condicao in relevantes:
        if condicao["operador"] != "IGUAL" or not condicao["origem"].startswith("F2-"):
            raise ValueError("Condição ainda não suportada pelo contrato executável.")
        resultados.append(respostas.get(condicao["origem"]) == condicao["codigo_valor"])
    combinacao = relevantes[0]["combinar"]
    if combinacao in ("SIMPLES", "E"):
        return all(resultados)
    if combinacao == "OU":
        return any(resultados)
    raise ValueError("Combinação lógica ainda não suportada.")


def _validar_valor(item, valor):
    if valor is None:
        return None
    permitidos = {alternativa["codigo"] for alternativa in item["alternativas"]}
    if item["modo"] == "unica":
        if not isinstance(valor, str) or valor not in permitidos:
            raise ValueError(f"Valor desconhecido para {item['id']}.")
        return valor
    if item["modo"] == "multipla":
        if not isinstance(valor, list) or len(valor) != len(set(valor)) or any(v not in permitidos for v in valor):
            raise ValueError(f"Seleção múltipla inválida para {item['id']}.")
        if "A_CONFIRMAR" in valor and len(valor) > 1:
            raise ValueError("A CONFIRMAR deve ser exclusiva das alternativas substantivas.")
        return list(valor)
    raise ValueError(f"O controle de {item['id']} não está habilitado para escrita.")


def _validar_complementos(habilitados, complementos):
    if not isinstance(complementos, dict):
        raise ValueError("Complementos devem ser informados por item e alternativa.")
    resultado = {}
    for item_id, por_codigo in complementos.items():
        item = habilitados.get(item_id)
        if not item or not isinstance(por_codigo, dict):
            raise ValueError("Complemento ligado a item indisponível.")
        permitidos = {a["codigo"] for a in item["alternativas"] if a["complemento"] not in ("", "—")}
        for codigo, valor in por_codigo.items():
            if codigo not in permitidos or not isinstance(valor, str) or len(valor) > LIMITE_COMPLEMENTO or "\x00" in valor:
                raise ValueError("Complemento inválido ou ligado a alternativa sem complemento.")
        resultado[item_id] = deepcopy(por_codigo)
    return resultado


def aplicar_bloco(conteudo, *, bloco, alteracoes, complementos=None, reativar=None,
                  proxima_versao: int) -> tuple[dict, dict]:
    """Aplica atualização parcial; omissão preserva e ``None`` remove explicitamente."""
    definicao = definicao_bloco(bloco)
    habilitados = _habilitados(definicao)
    if not habilitados:
        raise PermissionError("Bloco sem controles homologados para escrita nesta versão.")
    if not isinstance(alteracoes, dict) or any(item_id not in habilitados for item_id in alteracoes):
        raise ValueError("Alteração contém item desconhecido ou não habilitado.")
    reativar = set(reativar or [])
    if not reativar <= set(habilitados):
        raise ValueError("Pedido de reativação ligado a item indisponível.")
    complementos = _validar_complementos(habilitados, complementos or {})

    novo = deepcopy(conteudo)
    respostas = novo.setdefault("respostas_etapa1", {})
    inativas = novo.setdefault("respostas_inativas_etapa1", {})
    complementos_ativos = novo.setdefault("complementos_etapa1", {})
    complementos_inativos = novo.setdefault("complementos_inativos_etapa1", {})
    normalizadas = {item_id: _validar_valor(habilitados[item_id], valor)
                    for item_id, valor in alteracoes.items()}

    valores_previstos = {**respostas, **normalizadas}
    valores_previstos = {item_id: valor for item_id, valor in valores_previstos.items() if valor is not None}
    for item_id, item in habilitados.items():
        selecionados = valores_previstos.get(item_id, [])
        selecionados = selecionados if isinstance(selecionados, list) else [selecionados]
        informados = complementos.get(item_id, {})
        if any(codigo not in selecionados for codigo in informados):
            raise ValueError("Complemento informado para alternativa não selecionada.")
        exigidos = {a["codigo"] for a in item["alternativas"]
                    if a["complemento"] not in ("", "—") and a["codigo"] in selecionados}
        existentes = complementos_ativos.get(item_id, {})
        if any(not str(informados.get(codigo, existentes.get(codigo, ""))).strip() for codigo in exigidos):
            raise ValueError("A alternativa selecionada exige complemento.")

    for item_id, item in habilitados.items():
        if item_id not in normalizadas:
            continue
        valor = normalizadas[item_id]
        if not _ativa(item, {**respostas, **normalizadas}):
            if valor == respostas.get(item_id):
                continue
            raise ValueError(f"{item_id} está inativo pela resposta de sua origem.")
        if valor is None:
            respostas.pop(item_id, None)
            inativas.pop(item_id, None)
            complementos_ativos.pop(item_id, None)
            complementos_inativos.pop(item_id, None)
        else:
            respostas[item_id] = valor
            inativas.pop(item_id, None)
            complementos_inativos.pop(item_id, None)
            if item_id in complementos:
                complementos_ativos[item_id] = complementos[item_id]
            elif item_id in alteracoes:
                complementos_ativos.pop(item_id, None)

    for item_id, item in habilitados.items():
        ativa = _ativa(item, respostas)
        if not ativa and item_id in respostas:
            inativas[item_id] = {"valor": respostas.pop(item_id), "motivo": "condicao_inativa",
                                 "inativada_na_versao": proxima_versao}
            if item_id in complementos_ativos:
                complementos_inativos[item_id] = complementos_ativos.pop(item_id)
        elif ativa and item_id in reativar and item_id in inativas and item_id not in normalizadas:
            respostas[item_id] = inativas.pop(item_id)["valor"]
            if item_id in complementos_inativos:
                complementos_ativos[item_id] = complementos_inativos.pop(item_id)

    novo["versao_contrato_respostas"] = CONTRATO_RESPOSTAS
    novo["versao_controles_form2"] = VERSAO_CONTROLES
    sinais = []
    for item_id, valor in respostas.items():
        codigos = valor if isinstance(valor, list) else [valor]
        if "A_CONFIRMAR" in codigos:
            sinais.append({"item_id": item_id, "classe": "factual", "efeito": "relacionar_no_bloco_14"})
        item = habilitados.get(item_id)
        tratamentos = {a["codigo"]: a["tratamento"] for a in item["alternativas"]} if item else {}
        if any("Análise especializada" in tratamentos.get(codigo, "") for codigo in codigos):
            sinais.append({"item_id": item_id, "classe": "especializada", "efeito": "aguarda_competencia"})
    novo["sinalizadores_etapa1"] = sinais
    return novo, {"bloco": bloco, "alterados": sorted(alteracoes), "sinalizadores": deepcopy(sinais)}


def projetar_bloco(conteudo, numero: int) -> dict:
    definicao = definicao_bloco(numero)
    respostas = conteudo.get("respostas_etapa1", {})
    inativas = conteudo.get("respostas_inativas_etapa1", {})
    complementos = conteudo.get("complementos_etapa1", {})
    complementos_inativos = conteudo.get("complementos_inativos_etapa1", {})
    for item in definicao["itens"]:
        item["ativa"] = _ativa(item, respostas) if item["edicao"] == "habilitada" else False
        item["valor"] = deepcopy(respostas.get(item["id"]))
        item["valor_inativo"] = deepcopy(inativas.get(item["id"]))
        item["complementos_ativos"] = deepcopy(complementos.get(item["id"], {}))
        item["complementos_inativos"] = deepcopy(complementos_inativos.get(item["id"], {}))
    definicao["edicao_disponivel"] = any(item["edicao"] == "habilitada" for item in definicao["itens"])
    return definicao
