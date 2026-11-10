"""Contrato local das respostas do FORM 2, separado do catálogo editorial privado.

O código público conhece apenas o formato e as referências públicas. A instalação
autorizada fornece o arquivo privado derivado da matriz técnica candidata.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from app.catalogo_form2_rev18 import carregar_catalogo


VERSAO = "F2-REV18-CONTROLES-CANDIDATA-v2"
CONTRATO_RESPOSTAS = "F2-ETAPA1-RESPOSTAS-v1"
MATRIZ_SHA256 = "9aa05457b637a7842908d469e17646383aa77dd45fb64f4b8b20a59818194577"
ARQUIVO = Path(__file__).with_name("catalogos") / "form2_controles_rev18_candidata_v2.json"

REFERENCIAS_ANPD = {
    "ANPD-PP": {
        "titulo": "Guia Orientativo: Tratamento de Dados Pessoais pelo Poder Público",
        "versao": "2.0 (2023)",
        "url": "https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/guia-poder-publico-anpd-versao-final.pdf",
    },
    "ANPD-LI": {
        "titulo": "Guia Orientativo: Hipóteses Legais de Tratamento — Legítimo Interesse",
        "versao": "1.0 (2024)",
        "url": "https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/guia_legitimo_interesse.pdf",
    },
    "ANPD-AG": {
        "titulo": "Guia Orientativo para Definições dos Agentes de Tratamento e do Encarregado",
        "versao": "2.0 (2022)",
        "url": "https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/anonimizado___guia_de_agente_de_tratamento_e_encarregado_da_anpd_novo.pdf",
    },
}


def _sha256_conteudo(dados: dict) -> str:
    canonico = json.dumps(dados, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()


def _validar(contrato: dict) -> None:
    if contrato.get("versao") != VERSAO or contrato.get("contrato_respostas") != CONTRATO_RESPOSTAS:
        raise ValueError("Versão inesperada do contrato de respostas do FORM 2.")
    if contrato.get("origem", {}).get("matriz_sha256", "").lower() != MATRIZ_SHA256:
        raise ValueError("O contrato não corresponde à matriz técnica candidata v2 conferida.")

    itens = contrato.get("itens")
    if not isinstance(itens, list) or len(itens) != 250:
        raise ValueError("O contrato deve conter os 250 identificadores do FORM 2.")
    ids = [item.get("id") for item in itens]
    if len(set(ids)) != 250:
        raise ValueError("Há identificador ausente ou duplicado no contrato do FORM 2.")

    catalogo = carregar_catalogo()
    ids_catalogo = [item["id"] for bloco in catalogo["blocos"] for item in bloco["itens"]]
    if ids != ids_catalogo:
        raise ValueError("A ordem dos controles diverge do catálogo editorial instalado.")

    alternativas = contrato.get("alternativas")
    condicoes = contrato.get("condicoes")
    if not isinstance(alternativas, list) or len(alternativas) != 718:
        raise ValueError("Quantidade inesperada de alternativas no contrato candidato.")
    if not isinstance(condicoes, list) or len(condicoes) != 259:
        raise ValueError("Quantidade inesperada de condições no contrato candidato.")

    por_item = {item_id: set() for item_id in ids}
    for alternativa in alternativas:
        item_id, codigo = alternativa.get("id"), alternativa.get("codigo")
        if item_id not in por_item or not isinstance(codigo, str) or codigo in por_item[item_id]:
            raise ValueError("Alternativa inválida, duplicada ou ligada a item desconhecido.")
        por_item[item_id].add(codigo)
    for condicao in condicoes:
        if condicao.get("alvo") not in por_item:
            raise ValueError("Condição ligada a item desconhecido.")
        origem = condicao.get("origem")
        if isinstance(origem, str) and origem.startswith("F2-") and origem not in por_item:
            raise ValueError("Condição possui origem desconhecida.")

    habilitados = {item["id"] for item in itens if item.get("edicao") == "habilitada"}
    if habilitados != {"F2-2.9", "F2-2.9.1", "F2-2.9.2", "F2-2.9.3"}:
        raise ValueError("Somente a unidade documental de guarda pode estar habilitada.")
    if any(item.get("edicao") != "bloqueada_d11" for item in itens
           if item.get("bloco") in (3, 4, 5, 10)):
        raise ValueError("Os blocos jurídicos devem permanecer bloqueados por D11.")

    esperado = contrato.get("sha256_conteudo")
    sem_lacre = {k: v for k, v in contrato.items() if k != "sha256_conteudo"}
    if not isinstance(esperado, str) or esperado != _sha256_conteudo(sem_lacre):
        raise ValueError("Integridade do contrato privado de respostas não confere.")


def carregar_contrato() -> dict:
    """Carrega uma cópia validada; ausência do arquivo mantém a unidade indisponível."""
    contrato = json.loads(ARQUIVO.read_text(encoding="utf-8"))
    _validar(contrato)
    return deepcopy(contrato)


def referencias_anpd(chaves) -> list[dict]:
    """Resolve somente fontes públicas conhecidas, sem expor o catálogo privado."""
    resultado = []
    for chave in chaves or []:
        if chave not in REFERENCIAS_ANPD:
            raise ValueError("Referência pública da ANPD desconhecida.")
        resultado.append({"chave": chave, **REFERENCIAS_ANPD[chave]})
    return resultado
