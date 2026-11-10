"""Rótulos de consulta; não modifica nem reinterpreta a origem histórica."""
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.catalogo_form2_rev18 import VERSAO as VERSAO_CATALOGO, carregar_catalogo
from app.contrato_form2_respostas import referencias_anpd
from app.extensao_guarda_form1 import definicao_guarda
from app.modelos import Pessoa
from app.respostas_form2 import projetar_bloco


ROTULOS = {
    "id": "Identificador preservado", "respostas": "Respostas",
    "resposta": "Resposta histórica", "respostas_inativas": "Respostas anteriores inativas",
    "complementos": "Complementos", "complementos_inativos": "Complementos anteriores inativos",
    "categoria": "Categoria do destinatário", "modalidade": "Modo de identificação",
    "unidade_id": "Código da unidade preservado na origem",
    "identificacao": "Identificação institucional", "cnpj": "CNPJ da entidade",
    "instrumento": "Instrumento pertinente", "classe_orgao_requisitante": "Classe do órgão requisitante",
    "hipotese_requisicao": "Hipótese da requisição", "meio_publicacao": "Meio de publicação",
    "natureza_destinatario": "Natureza do destinatário", "justificativa": "Justificativa",
    "motivo_desativacao": "Motivo da desativação", "motivo_inativacao": "Motivo da inativação",
    "desativada_na_versao": "Desativada na versão",
    "desativado_na_versao": "Desativado na versão", "valor": "Valor preservado", "motivo": "Motivo",
    "versao": "Versão", "versao_estrutura": "Estrutura histórica", "matriz": "Matriz da extensão",
    "adotada_por": "Adoção por", "papel": "Papel exercido", "adotada_em": "Data da adoção",
    "legado": "Respostas anteriores à adoção — não convertidas para os novos campos",
    "campos": "Perguntas anteriores", "campo_id": "Identificador da pergunta",
    "pergunta": "Enunciado histórico", "snapshot_id": "Identificador do snapshot anterior",
    "numero_snapshot": "Número do snapshot anterior", "lacre_snapshot": "Lacre anterior",
    "versao_rascunho": "Versão do rascunho", "rascunho_salvo_por": "Rascunho salvo por",
    "rascunho_salvo_em": "Data de salvamento do rascunho",
}
PAPEIS = {
    "APA_designante": "APA — Agente Público Autorizado (designação)",
    "preparador_demonstrativo": "AAL — Agente de Análise de Legitimidade (preparação)",
    "ARP": "ARP — Agente Responsável pelo Preenchimento",
}
GRUPOS = (
    ("participantes", "Participantes institucionais — ocorrências do Bloco 3"),
    ("participantes_inativos", "Participantes anteriores inativos"),
    ("destinatarios_10_2_1", "10.2.1 — Destinatários registrados"),
    ("destinatarios_10_2_1_inativos", "10.2.1 — Destinatários anteriores inativos"),
    ("complementos", "Complementos das respostas"),
    ("complementos_inativos", "Complementos anteriores inativos"),
    ("respostas_inativas", "Respostas anteriores inativas"),
    ("extensao_medidas", "Extensão MEDIDAS — adoção e legado preservado"),
    ("extensao_guarda", "Extensão GUARDA — adoção e legado preservado"),
)


def apresentar_origem(origem):
    """Usa os enunciados do catálogo efetivo já validado por ler_origem."""
    rotulos = dict(ROTULOS)
    if not origem:
        return {"rotulos": rotulos, "grupos": []}
    rotulos.update({p["id"]: f'{p["id"]} — {p["pergunta"]}' for p in origem["perguntas"]})
    respondidas, vazias = [], []
    for pergunta in origem["perguntas"]:
        destino = respondidas if pergunta.get("valor") not in (None, "", [], {}) else vazias
        destino.append(pergunta)
    fonte = origem["conteudo"]
    return {"respondidas": respondidas, "vazias": vazias, "rotulos": rotulos, "grupos": [
        {"titulo": titulo, "valor": fonte[chave]} for chave, titulo in GRUPOS if chave in fonte
    ]}


def data_local(momento):
    if isinstance(momento, str):
        try:
            momento = datetime.fromisoformat(momento)
        except ValueError:
            return momento
    if not isinstance(momento, datetime) or momento.tzinfo is None:
        return momento
    return momento.astimezone(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y às %H:%M")


def rotulo_demonstrativo(valor):
    return {"Servico": "Serviço", "servico": "serviço",
            "Ensaio ficticio de origens S1 e S2": "Ensaio fictício de origens S1 e S2"}.get(valor, valor)


def unidade_guarda(dados):
    """Projeta a unidade a partir da consulta já autorizada e da origem lacrada."""
    if not dados["pode_editar"]:
        return None
    try:
        catalogo = carregar_catalogo()
        try:
            respostas = projetar_bloco(dados["preparacao"].conteudo, 2) if catalogo["versao"] == VERSAO_CATALOGO else None
        except (FileNotFoundError, OSError, ValueError, KeyError, TypeError):
            respostas = None
    except FileNotFoundError:
        return {"aviso": "O catálogo de guarda documental está indisponível nesta instalação."}
    except (OSError, ValueError, KeyError, TypeError):
        return {"aviso": "Não foi possível validar o catálogo de guarda documental desta instalação."}

    origem = dados["origem"]
    perguntas = {item["id"]: item for item in origem["perguntas"]}
    fatos = []
    ids = ["12.1", "12.1.1", "12.1.2", "12.1.3", "12.2"]
    ids.extend(campo["id"] for campo in definicao_guarda()["campos"])
    for chave in ids:
        fatos.append({"id": chave, "campo": perguntas.get(chave),
                      "complemento": origem["conteudo"].get("complementos", {}).get(chave)})
    bloco = next(b for b in catalogo["blocos"] if b["numero"] == 2)
    if respostas is None:
        questoes = []
        for q in bloco["itens"]:
            if q["id"] not in ("F2-2.9", "F2-2.9.1", "F2-2.9.2", "F2-2.9.3"):
                continue
            condicao = q.get("condicao_documental")
            questoes.append({**q, "modo": q.get("escolha_documental", {}).get("modo"),
                "alternativas": [{"codigo": a, "rotulo": a} for a in q.get("escolha_documental", {}).get("alternativas", [])],
                "condicoes": [] if not condicao else [{"origem": condicao["origem"], "operador": "IGUAL", "codigo_valor": condicao["resposta"]}],
                "edicao": "somente_leitura", "ativa": False, "valor": None,
                "valor_inativo": None, "complementos_ativos": {}})
    else:
        questoes = [q for q in respostas["itens"] if q["edicao"] == "habilitada"]
    return {"versao": catalogo["versao"], "fatos": fatos,
            "sem_prazo": perguntas.get("12.1.1", {}).get("valor") in (None, "", [], {}) and not origem["conteudo"].get("complementos", {}).get("12.1.1"),
            "notas": [nota["texto"] for nota in bloco.get("notas_documentais", [])
                      if "8.159/1991" in nota["texto"]],
            "questoes": questoes,
            "edicao_disponivel": bool(respostas and respostas["edicao_disponivel"]),
            "sinalizadores": dados["preparacao"].conteudo.get("sinalizadores_etapa1", [])}


def reapresentar_tentativa_guarda(guarda, alteracoes, complementos=None):
    """Preserva no HTML uma tentativa rejeitada, sem tratá-la como dado salvo."""
    if not guarda or guarda.get("aviso") or not guarda.get("edicao_disponivel"):
        return guarda
    valores = {q["id"]: q.get("valor") for q in guarda["questoes"]}
    valores.update(alteracoes)
    for questao in guarda["questoes"]:
        item_id = questao["id"]
        if item_id in alteracoes:
            questao["valor"] = alteracoes[item_id]
        if item_id in (complementos or {}):
            questao["complementos_ativos"] = complementos[item_id]
        if item_id == "F2-2.9.1":
            questao["ativa"] = valores.get("F2-2.9") == "SIM"
        elif item_id == "F2-2.9.3":
            questao["ativa"] = valores.get("F2-2.9.2") == "SIM"
    return guarda


def apoio_juridico_etapa1():
    """Referências públicas orientativas; D11 continua impedindo edição jurídica."""
    return [
        {"blocos": "3 e 4", "fontes": referencias_anpd(["ANPD-PP", "ANPD-LI"])},
        {"blocos": "5", "fontes": referencias_anpd(["ANPD-PP"])},
        {"blocos": "10", "fontes": referencias_anpd(["ANPD-AG"])},
    ]


def identificar_agentes(sessao, dados):
    """Resolve somente autores já presentes na consulta autorizada, sem ampliar acesso."""
    ids = {dados["pessoa"].id}
    preparacao, origem = dados.get("preparacao"), dados.get("origem")
    for visivel in dados.get("preparacoes", []):
        ids.update((visivel.designado_por, visivel.salvo_por))
    if preparacao:
        ids.update((preparacao.preparador_id, preparacao.salvo_por))
    if origem:
        ids.add(origem["snapshot"].preparado_por)
        ids.add(origem["canais"].get("confirmado_por_id"))
        for chave in ("extensao_medidas", "extensao_guarda"):
            extensao = origem["conteudo"].get(chave, {})
            ids.add(extensao.get("adotada_por"))
            ids.add(extensao.get("legado", {}).get("rascunho_salvo_por"))
    ids.update(ato.ator_id for ato in dados.get("historico", []))
    pessoas = sessao.scalars(select(Pessoa).where(Pessoa.id.in_(ids - {None})))
    return {p.id: f"{p.matricula} — {p.nome}" for p in pessoas}
