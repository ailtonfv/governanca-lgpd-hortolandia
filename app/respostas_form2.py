"""Validação e projeção das respostas estruturadas da Etapa 1 do FORM 2.

Somente controles explicitamente habilitados no contrato privado podem receber
escrita. O módulo não conclui análise, não cria parecer e não encaminha pendência.
"""

from copy import deepcopy
import re
import json
from app.form2_rev212 import (RASCUNHO, montar_bloco, indice_valores, mapa_regras,
                              aplicavel, conjunto_da_chave, catalogo)

from app.catalogo_form2_rev18 import carregar_catalogo
from app.contrato_form2_respostas import (CONTRATO_RESPOSTAS, VERSAO as VERSAO_CONTROLES,
                                           carregar_contrato, referencias_anpd)


ENVELOPE_V2 = "F2-DEMO-PREP-v2"
LIMITE_COMPLEMENTO = 1000
MODOS_IDENTIFICACAO = {"F2-1.2": "unica", "F2-1.2.1": "texto",
                       "F2-1.3": "unica", "F2-1.3.1": "texto"}


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
    if numero == 1:
        for item in itens:
            if item["id"] in MODOS_IDENTIFICACAO:
                item.update(edicao="habilitada", modo=MODOS_IDENTIFICACAO[item["id"]])
    titulo = next((b.get("titulo", "") for b in catalogo["blocos"] if b["numero"] == numero), "")
    return {"numero": numero, "titulo": titulo, "versao": contrato["versao"], "itens": itens}


CADERNO_REV20 = "revisao_blocos_rev20"
CONSULTAS_REV20 = {"F2-13.9", "F2-14.8.1", "F2-14.8.2"}


def estados_regua_form2(conteudo):
    salvos = set()
    pendentes = set()
    for chave, valor in conteudo.get("respostas_etapa1", {}).items():
        if valor:
            salvos.add(chave.split(".")[0].removeprefix("F2-"))
    if conteudo.get("respostas_etapa1", {}).get("F2-1.3.1"):
        pendentes.add("1")
    for sinal in conteudo.get("sinalizadores_etapa1", []):
        pendentes.add(sinal["item_id"].split(".")[0].removeprefix("F2-"))
    for bloco, campos in conteudo.get(RASCUNHO, {}).items():
        for chave, valor in campos.items():
            if chave.startswith(("texto:", "opcao:")) and (valor.strip() if isinstance(valor, str) else valor):
                salvos.add(bloco)
            if chave.startswith("opcao:") and "A_CONFIRMAR" in valor:
                pendentes.add(bloco)
    governanca = conteudo.get("governanca_v9")
    if governanca is not None:
        # A lista formal é independente da visibilidade e do texto da pergunta.
        referenciados = set()
        ativos = set()
        for d in governanca.get("pendencias", {}).values():
            for origem in d.get("origens", []):
                match = re.match(r"F2-(\d+)", origem.get("item", ""))
                if match:
                    referenciados.add(match[1])
                    if d["estado"] in {"aberta", "respondida"}:
                        ativos.add(match[1])
        pendentes.difference_update(referenciados)
        pendentes.update(ativos)
    return {"salvos": salvos, "pendentes": pendentes}


def definicao_revisao(numero):
    return montar_bloco(definicao_bloco(numero))


def aplicar_revisao(conteudo, bloco, campos, ramos=(), *, demonstrativo=False):
    """Guarda o ensaio e os comentários à parte das respostas homologadas."""
    definicao = definicao_revisao(bloco)
    if not definicao["itens"]:
        raise ValueError("Bloco indisponível.")
    itens = {q["id"]: q for q in definicao["itens"]}
    novo = deepcopy(conteudo)
    if demonstrativo:
        novo["regime_respostas"] = {"uso": "demonstracao_ficticia", "homologado": False, "versao": "REV22-DEMO-2"}
    revisao = novo.setdefault(RASCUNHO, {}).setdefault(str(bloco), {})
    regras = mapa_regras(carregar_contrato())
    antes = indice_valores(conteudo)
    for nome, valores in campos.items():
        tipo, _, chave = nome.partition(":")
        item_id, separador, ocorrencia = chave.partition("#")
        q = itens.get(item_id)
        if not q or not isinstance(valores, list) or not all(isinstance(v, str) and "\x00" not in v for v in valores):
            raise ValueError("Campo de revisão inválido.")
        if separador and (not q["repetivel"] or tipo == "comentario"
                          or not re.fullmatch(r"[1-9][0-9]?", ocorrencia)):
            raise ValueError("Ocorrência inválida.")
        if tipo != "comentario" and q["repetivel"] and not separador:
            raise ValueError("Identifique o conjunto da resposta.")
        if tipo == "comentario":
            limite = 2000
        elif q["edicao"] in ("habilitada", "consulta") or bloco == 1 or (not demonstrativo and (bloco in (3, 4, 5, 10) or q["edicao"] == "bloqueada_d11")):
            raise ValueError("Este campo admite somente comentários na revisão.")
        elif tipo == "principal" and item_id == "F2-14.3.1":
            if len(valores) != 1:
                raise ValueError("Selecione um único destino principal.")
            revisao[nome] = valores[0]
            continue
        elif tipo == "opcao" and q["alternativas"]:
            opcoes = [v for v in valores if v]
            permitidas = {a["codigo"] for a in q["alternativas"]}
            multipla = "múltipla" in q["controle"].lower()
            if (not set(opcoes) <= permitidas or len(set(opcoes)) != len(opcoes)
                    or (not multipla and len(opcoes) > 1) or ("A_CONFIRMAR" in opcoes and len(opcoes) > 1)):
                raise ValueError(f"Confira a seleção de {chave}.")
            revisao[nome] = opcoes
            continue
        elif tipo == "texto" and (not q["alternativas"] or "texto" in q["controle"].lower()
                                  or any(a["complemento"].startswith("Texto condicionado") for a in q["alternativas"])):
            limite = limite_texto_revisao(q)
        else:
            raise ValueError("Controle de revisão inválido.")
        if len(valores) != 1 or len(valores[0]) > limite:
            raise ValueError(f"Limite de {limite} caracteres por campo.")
        revisao[nome] = valores[0]
    for nome, valor in revisao.items():
        if nome.startswith("principal:") and valor and valor not in revisao.get(nome.replace("principal:", "opcao:", 1), []):
            raise ValueError("O destino principal deve constar entre os destinos selecionados.")
    depois = indice_valores(novo)
    for nome in campos:
        tipo, chave = nome.split(":", 1)
        if tipo == "comentario":
            continue
        item = chave.partition("#")[0]
        sufixo = conjunto_da_chave(chave)
        if not aplicavel(item, sufixo, depois, ramos, regras):
            if revisao[nome] and revisao[nome] != antes.get(nome):
                raise ValueError(f"{item} depende de resposta anterior. Salve a pergunta de origem.")
            if nome in antes:
                revisao[nome] = antes[nome]
            else:
                revisao.pop(nome, None)
    for nome in list(revisao):
        if nome.startswith("comentario:"):
            continue
        chave = nome.partition(":")[2]
        if not aplicavel(chave.partition("#")[0], conjunto_da_chave(chave), depois, ramos, regras):
            valor = revisao.pop(nome)
            if valor:
                arquivo = novo.setdefault("respostas_inativas_rev212", {}).setdefault(str(bloco), {})
                arquivo[nome] = valor
    return novo, {"edicao": "REV21.2", "bloco": bloco, "campos_revisados": len(campos)}


def limite_texto_revisao(item):
    limite = re.search(r"até ([\d.]+) caracteres", item.get("dominio", ""), re.IGNORECASE)
    return int(limite[1].replace(".", "")) if limite else 2000


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
    if item["modo"] == "texto":
        limite = 200 if item["id"] == "F2-1.3.1" else 1000
        if not isinstance(valor, str) or len(valor) > limite or "\x00" in valor:
            raise ValueError(f"Texto inválido para {item['id']}. Limite de {limite} caracteres.")
        return valor.strip() or None
    if item["modo"] == "unica":
        if not isinstance(valor, str) or valor not in permitidos:
            raise ValueError(f"Valor desconhecido para {item['id']}.")
        return valor
    if item["modo"] == "multipla":
        if not isinstance(valor, list) or len(valor) != len(set(valor)) or any(v not in permitidos for v in valor):
            raise ValueError(f"Seleção múltipla inválida para {item['id']}.")
        if "A_CONFIRMAR" in valor and len(valor) > 1:
            raise ValueError("A confirmar deve ser exclusiva das alternativas substantivas.")
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
                    if a["complemento"].startswith("Texto condicionado") and a["codigo"] in selecionados}
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
            if item_id == "F2-1.3.1" and item_id in inativas and item_id not in respostas:
                # Um campo vazio ao reabrir o ramo não descarta o histórico pendente.
                continue
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
    sinais = [s for s in novo.get("sinalizadores_etapa1", []) if s["item_id"] not in habilitados]
    for item_id, valor in respostas.items():
        if item_id not in habilitados or habilitados[item_id]["modo"] == "texto":
            continue
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
    redacao = catalogo() if numero == 1 else {}
    for item in definicao["itens"]:
        if item["id"] in redacao:
            item["enunciado"] = redacao[item["id"]]["enunciado"]
        item["ativa"] = _ativa(item, respostas) if item["edicao"] == "habilitada" else False
        item["valor"] = deepcopy(respostas.get(item["id"]))
        item["valor_inativo"] = deepcopy(inativas.get(item["id"]))
        item["complementos_ativos"] = deepcopy(complementos.get(item["id"], {}))
        item["complementos_inativos"] = deepcopy(complementos_inativos.get(item["id"], {}))
    definicao["edicao_disponivel"] = any(item["edicao"] == "habilitada" for item in definicao["itens"])
    return definicao
