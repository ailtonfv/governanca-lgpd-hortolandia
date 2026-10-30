"""Pré-validação consultiva do FORM 1 integral (contrato candidato 3).

A matriz versionada em ``docs/planejamento`` é a fonte da classificação de
obrigatoriedade. Este módulo não submete, não altera o rascunho e não converte
pendências de governança em regras de negócio.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.form1_integral import (
    CONDICOES_BLOCO_1, CONDICOES_BLOCO_2, CONDICOES_BLOCO_4,
    CONDICOES_BLOCO_6, CONDICOES_BLOCO_8, CONDICOES_BLOCO_9,
    CONDICOES_BLOCO_10, CONDICOES_BLOCO_11, CONDICOES_BLOCO_12,
    CONDICOES_BLOCO_14, CONDICOES_PARTICIPANTE_BLOCO_3,
    alternativas_outro_por_campo, campos_por_id,
)


CAMINHO_MATRIZ = (Path(__file__).resolve().parents[1] / "docs" / "planejamento"
                  / "MATRIZ_CAMPOS_FORM1_REV13.md")
ID_CANONICO = re.compile(r"(?:\d+(?:\.\d+)*|OUV\.\d+|ESIC\.\d+)")
CLASSE_ESSENCIAL = "Obrigatória essencial"
CLASSE_CONDICIONAL = "Obrigatória condicional"
CLASSE_SOMENTE_LEITURA = "Essencial, somente leitura"
CLASSE_FACULTATIVA_REV13 = "Facultativa (REV13)"
CLASSE_FACULTATIVA_PROPOSTA = "Facultativa nesta proposta"

REGRAS_PENDENTES_GLOBAIS = (
    {"codigo": "F1-D04-DOC", "descricao": "formalizar na próxima Cartilha que o ramo de WhatsApp usa somente a alternativa canônica ‘WhatsApp corporativo’", "campos": ("8.3", "8.7", "8.8", "8.8.1", "8.9")},
    {"codigo": "F1-D06", "descricao": "definir exclusividades ainda não formalizadas em seleções múltiplas", "campos": ()},
    {"codigo": "APROVACAO-MATRIZ", "descricao": "aprovar institucionalmente a matriz e o marco de liberação da submissão", "campos": ()},
)

_CONDICOES = {
    **CONDICOES_BLOCO_1, **CONDICOES_BLOCO_2, **CONDICOES_BLOCO_4,
    **CONDICOES_BLOCO_6, **CONDICOES_BLOCO_8, **CONDICOES_BLOCO_9,
    **CONDICOES_BLOCO_10, **CONDICOES_BLOCO_11, **CONDICOES_BLOCO_12,
    **CONDICOES_BLOCO_14,
}
_CAMPOS_CONDICAO_PENDENTE = frozenset()

_CATEGORIAS_ENTIDADES_10_2 = frozenset({
    "Empresa contratada", "OSC / entidade parceira", "Consórcio",
    "Concessionária ou PPP", "Prestador de serviço",
})
_CATEGORIAS_MUNICIPAIS_10_2 = frozenset({
    "Outra unidade da mesma Secretaria", "Outra Secretaria", "Ouvidoria", "e-SIC",
})


@dataclass(frozen=True, slots=True)
class RegraObrigatoriedade:
    campo_id: str
    etapa: str
    classe: str
    condicao: str
    observacao: str


@lru_cache(maxsize=1)
def carregar_matriz_obrigatoriedade() -> dict[str, RegraObrigatoriedade]:
    """Carrega a única matriz versionada, recusando cobertura incompleta."""

    regras: dict[str, RegraObrigatoriedade] = {}
    for linha in CAMINHO_MATRIZ.read_text(encoding="utf-8").splitlines():
        partes = [parte.strip() for parte in linha.split("|")]
        if len(partes) < 7 or not ID_CANONICO.fullmatch(partes[1]):
            continue
        campo_id = partes[1]
        if campo_id in regras:
            raise ValueError(f"identificador repetido na matriz: {campo_id}")
        regras[campo_id] = RegraObrigatoriedade(
            campo_id, partes[2], partes[3], partes[4], partes[5]
        )
    if len(regras) != 128 or set(regras) != set(campos_por_id()):
        raise ValueError("a matriz de obrigatoriedade não cobre exatamente o catálogo REV13")
    return regras


def metadado_visual_obrigatoriedade(campo_id: str) -> dict:
    """Projeta a matriz canônica em rótulos visuais, sem criar regra funcional."""

    regra = carregar_matriz_obrigatoriedade()[campo_id]
    apresentacoes = {
        CLASSE_ESSENCIAL: ("*", "Obrigatório", "obrigatorio", False),
        CLASSE_SOMENTE_LEITURA: (
            "*", "Obrigatório · somente leitura", "obrigatorio", False
        ),
        CLASSE_CONDICIONAL: (
            "**", "Obrigatório em alguns casos", "condicional", True
        ),
        CLASSE_FACULTATIVA_REV13: (
            "****", "Facultativo (REV13)", "facultativo", False
        ),
        CLASSE_FACULTATIVA_PROPOSTA: (
            "****", "Facultativo (classificação provisória)", "facultativo", False
        ),
    }
    if regra.classe not in apresentacoes:
        raise ValueError(
            f"classe de obrigatoriedade sem apresentação definida: {regra.classe}"
        )
    marcador, rotulo, tom, condicional = apresentacoes[regra.classe]
    return {
        "classe": regra.classe,
        "marcador": marcador,
        "rotulo": rotulo,
        "tom": tom,
        "condicional": condicional,
        "marcador_ativo": "*" if condicional else marcador,
        "rotulo_ativo": "Obrigatório neste caso" if condicional else rotulo,
        "tom_ativo": "obrigatorio" if condicional else tom,
    }


def _bloco(campo_id: str) -> str:
    if campo_id.startswith(("OUV.", "ESIC.")):
        return "2"
    return campo_id.split(".", 1)[0]


def _etapa(bloco: str) -> int | None:
    """Localiza o bloco nas quatro etapas visuais sem criar regra funcional."""

    if not bloco.isdigit():
        return None
    numero = int(bloco)
    if 1 <= numero <= 3:
        return 1
    if 4 <= numero <= 8:
        return 2
    if 9 <= numero <= 11:
        return 3
    if 12 <= numero <= 14:
        return 4
    return None


def _respondido(valor) -> bool:
    if valor is None:
        return False
    if isinstance(valor, str):
        return bool(valor.strip()) and valor != "A confirmar"
    if isinstance(valor, (list, tuple, set)):
        return bool(valor) and "A confirmar" not in valor
    return True


def _corresponde(valor, aceitos) -> bool:
    if isinstance(valor, (list, tuple, set)):
        return bool(set(valor) & set(aceitos))
    return valor in aceitos


def _normalizar_condicoes(condicao):
    if not condicao:
        return ()
    return (condicao,) if isinstance(condicao[0], str) else condicao


def _condicao_ativa(campo_id: str, respostas: dict) -> bool:
    return all(
        _corresponde(respostas.get(dependencia), aceitos)
        for dependencia, aceitos in _normalizar_condicoes(_CONDICOES.get(campo_id))
    )


def _item(campo_id: str, tipo: str, detalhe: str) -> dict:
    campo = campos_por_id()[campo_id]
    bloco = _bloco(campo_id)
    etapa = _etapa(bloco)
    destino_tipo = (
        "secao" if (campo_id.startswith("3.") and campo_id != "3.1")
        or campo_id == "10.2.1"
        else "campo"
    )
    return {
        "campo_id": campo_id,
        "bloco": bloco,
        "etapa": etapa,
        "destino_navegavel": etapa is not None,
        "destino_tipo": destino_tipo if etapa is not None else None,
        "pergunta": campo.pergunta,
        "tipo": tipo,
        "detalhe": detalhe,
    }


def _condicao_participante_ativa(campo_id: str, respostas: dict) -> bool:
    condicao = CONDICOES_PARTICIPANTE_BLOCO_3.get(campo_id)
    return not condicao or _corresponde(respostas.get(condicao[0]), condicao[1])


def _pre_validar_destinatarios_10_2_1(conteudo, respostas, incompletos, regras_pendentes):
    if respostas.get("10.1") not in {"Sim", "Em alguns casos"}:
        return
    categorias = [item for item in respostas.get("10.2", []) if item != "A confirmar"]
    destinatarios = conteudo.get("destinatarios_10_2_1", [])
    destinatarios = destinatarios if isinstance(destinatarios, list) else []
    legado = respostas.get("10.2.1")
    if legado:
        regras_pendentes.append(_item(
            "10.2.1", "compatibilidade_legada",
            "resposta textual legada preservada sem conversão automática; requer revisão humana",
        ))
    for categoria in categorias:
        ocorrencias = [item for item in destinatarios if item.get("categoria") == categoria]
        if not ocorrencias:
            incompletos.append(_item(
                "10.2.1", "incompleto",
                f"categoria ‘{categoria}’: informe ao menos um destinatário ou justificativa controlada",
            ))
        for indice, item in enumerate(ocorrencias, start=1):
            modalidade = item.get("modalidade")
            exigidos = []
            if modalidade == "nao_determinavel":
                exigidos = ["justificativa"]
            elif modalidade == "requisicao_eventual":
                exigidos = ["classe_orgao_requisitante", "hipotese_requisicao"]
            elif modalidade == "identificado":
                if categoria in _CATEGORIAS_MUNICIPAIS_10_2:
                    exigidos = ["unidade_id", "instrumento"]
                elif categoria in _CATEGORIAS_ENTIDADES_10_2:
                    exigidos = ["identificacao", "cnpj", "instrumento"]
                elif categoria == "Outro órgão público":
                    exigidos = ["identificacao", "instrumento"]
                elif categoria == "Público em geral":
                    exigidos = ["meio_publicacao", "instrumento"]
                elif categoria == "Outro":
                    exigidos = ["identificacao", "natureza_destinatario", "instrumento"]
            else:
                exigidos = ["modalidade"]
            for campo in exigidos:
                if not _respondido(item.get(campo)):
                    pendencia = _item(
                        "10.2.1", "incompleto",
                        f"categoria ‘{categoria}’, ocorrência {indice}: falta {campo.replace('_', ' ')}",
                    )
                    pendencia["ocorrencia"] = item.get("id", indice)
                    pendencia["categoria_destinatario"] = categoria
                    incompletos.append(pendencia)
            if modalidade == "nao_determinavel" and _respondido(item.get("justificativa")):
                pendencia = _item(
                    "10.2.1", "validacao_humana",
                    f"categoria ‘{categoria}’, ocorrência {indice}: justificativa requer avaliação humana",
                )
                pendencia["ocorrencia"] = item.get("id", indice)
                regras_pendentes.append(pendencia)


def pre_validar_form1_integral(conteudo: dict, *, nome_institucional: str | None,
                               cargo_funcao: str | None = None,
                               email_institucional: str | None = None,
                               respostas_somente_leitura: dict | None = None) -> dict:
    """Calcula pendências sem escrever estado ou declarar aptidão à submissão."""

    regras = carregar_matriz_obrigatoriedade()
    respostas_originais = conteudo.get("respostas", {}) if isinstance(conteudo, dict) else {}
    respostas_somente_leitura = respostas_somente_leitura or {}
    respostas = {**respostas_originais, **respostas_somente_leitura}
    participantes = conteudo.get("participantes", []) if isinstance(conteudo, dict) else []
    incompletos, nao_aplicaveis, regras_pendentes = [], [], []

    identidade = {"0.1": nome_institucional, "0.2": cargo_funcao, "0.3": email_institucional}
    for campo_id, valor in identidade.items():
        if not _respondido(valor):
            regras_pendentes.append(_item(
                campo_id, "integracao_institucional",
                "metadado obrigatório somente leitura sem fonte institucional autenticada",
            ))

    for campo_id, regra in regras.items():
        if (campo_id.startswith("0.") or campo_id == "10.2.1"
                or (campo_id.startswith("3.") and campo_id != "3.1")):
            continue
        if regra.classe not in {CLASSE_ESSENCIAL, CLASSE_CONDICIONAL}:
            continue
        if campo_id in _CAMPOS_CONDICAO_PENDENTE:
            regras_pendentes.append(_item(
                campo_id, "regra_pendente", "condição reservada à decisão de governança"
            ))
            continue
        ativo = regra.classe == CLASSE_ESSENCIAL or _condicao_ativa(campo_id, respostas)
        if not ativo:
            nao_aplicaveis.append(_item(
                campo_id, "nao_aplicavel", "condição inequívoca não está ativa neste rascunho"
            ))
        elif (campo_id not in respostas_somente_leitura
              and not _respondido(respostas.get(campo_id))):
            incompletos.append(_item(
                campo_id, "incompleto", "campo obrigatório ativo ainda não respondido conclusivamente"
            ))

    # A política F1-D05 passou a abranger todos os 38 contextos catalogados.
    # A consulta antecipa a pendência sem impedir que o rascunho seja salvo.
    complementos = conteudo.get("complementos", {})
    for campo_id, alternativa_outro in alternativas_outro_por_campo().items():
        if campo_id.startswith("3."):
            continue
        valor = respostas.get(campo_id)
        selecionado = (alternativa_outro in valor if isinstance(valor, list)
                       else valor == alternativa_outro)
        if selecionado and not _respondido(complementos.get(campo_id)):
            incompletos.append(_item(
                campo_id, "incompleto",
                f"a alternativa ‘{alternativa_outro}’ requer complemento descritivo",
            ))

    if respostas.get("3.1") == "Sim":
        if not participantes:
            incompletos.append(_item("3.2", "incompleto", "informe ao menos uma unidade participante"))
        for indice, participante in enumerate(participantes, start=1):
            valores = participante.get("respostas", participante)
            complementos_participante = participante.get("complementos", {})
            for campo_id in ("3.2", "3.3", "3.4", "3.4.1", "3.5"):
                if not _respondido(valores.get(campo_id)):
                    item = _item(campo_id, "incompleto", f"participante {indice}: resposta obrigatória ausente")
                    item["ocorrencia"] = indice
                    incompletos.append(item)
            if (_condicao_participante_ativa("3.5.1", valores)
                    and not _respondido(valores.get("3.5.1"))):
                item = _item("3.5.1", "incompleto", f"participante {indice}: resposta condicional ausente")
                item["ocorrencia"] = indice
                incompletos.append(item)
            for campo_id in ("3.2", "3.4", "3.5.1"):
                alternativa_outro = alternativas_outro_por_campo()[campo_id]
                valor = valores.get(campo_id)
                selecionado = (alternativa_outro in valor if isinstance(valor, list)
                               else valor == alternativa_outro)
                if selecionado and not _respondido(complementos_participante.get(campo_id)):
                    item = _item(
                        campo_id, "incompleto",
                        f"participante {indice}: a alternativa ‘{alternativa_outro}’ requer complemento descritivo",
                    )
                    item["ocorrencia"] = indice
                    incompletos.append(item)
    else:
        for campo_id in ("3.2", "3.3", "3.4", "3.4.1", "3.5", "3.5.1"):
            nao_aplicaveis.append(_item(campo_id, "nao_aplicavel", "3.1 não ativa participantes neste rascunho"))

    _pre_validar_destinatarios_10_2_1(
        conteudo, respostas, incompletos, regras_pendentes
    )

    regras_pendentes.extend({**pendencia, "tipo": "governanca"}
                            for pendencia in REGRAS_PENDENTES_GLOBAIS)
    por_bloco: dict[str, list[dict]] = {}
    for item in incompletos:
        por_bloco.setdefault(item["bloco"], []).append(item)

    return {
        "consultiva": True, "submissao_habilitada": False,
        "incompletos": incompletos, "nao_aplicaveis": nao_aplicaveis,
        "regras_pendentes": regras_pendentes,
        "por_bloco": [{"bloco": bloco, "itens": itens} for bloco, itens in
                      sorted(por_bloco.items(), key=lambda parte: int(parte[0]))],
        "quantidades": {"incompletos": len(incompletos),
                        "nao_aplicaveis": len(nao_aplicaveis),
                        "regras_pendentes": len(regras_pendentes)},
    }
