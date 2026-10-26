"""Catálogo candidato do FORM 1 integral baseado na REV13.

Este módulo prepara o incremento F1-0 sem alterar o contrato 2, o workflow
ou a interface da PoC nuclear. A submissão pelo contrato candidato 3 continua
desabilitada até o fechamento das decisões funcionais documentadas.
"""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


REVISAO_FONTE_FORM1_INTEGRAL = "REV13-2026-09-20"
VERSAO_CONTRATO_FORM1_INTEGRAL_CANDIDATA = 3
QUANTIDADE_CAMPOS_REV13 = 128
SHA256_CATALOGO_REV13 = "37b0c10b0352d1529b73bcfb1a2f57cd95dbcee2c195f4f32b8b028f5d8cc002"

CAMINHO_CATALOGO_REV13 = Path(__file__).resolve().parent / "catalogos" / "form1_rev13.csv"

CONTROLES_REV13 = frozenset({
    "seleção única (combo)",
    "seleção múltipla (combo com marcações)",
    "texto curto / numérico conforme enunciado",
    "texto longo, limitado e orientado",
    "reuso do catálogo de referência (ver campo indicado)",
    "combo de seleção única por faixas",
    "combo de seleção única de catálogo fechado",
    "a confirmar conforme texto da REV13",
})

FAIXAS_VOLUME_REV13 = (
    "Não se aplica", "Até 10", "11 a 50", "51 a 100", "101 a 500",
    "501 a 1.000", "1.001 a 5.000", "5.001 a 10.000", "Mais de 10.000",
    "Não mensurado", "A confirmar",
)

CONDICOES_BLOCO_1 = {
    "1.1.1": ("1.1", ("Sim",)),
}

IDS_BLOCO_2 = (
    "2.1", "2.2", "2.3", "2.4", "2.4.1", "2.4.2", "2.5", "2.6", "2.7",
    "2.8", "2.8.1", "2.9", "2.9.1", "2.10", "2.10.1", "2.11", "2.12",
    "2.12.1", "2.12.2", "2.13", "2.13.1", "OUV.1", "OUV.2", "OUV.3",
    "OUV.4", "ESIC.1", "ESIC.2",
)

IDS_PARTICIPANTE_BLOCO_3 = ("3.2", "3.3", "3.4", "3.4.1", "3.5", "3.5.1")

CONDICOES_BLOCO_2 = {
    "2.4.1": ("2.4", ("Não",)),
    "2.4.2": ("2.4", ("Não",)),
    "2.12.1": ("2.12", ("Sim",)),
    "2.12.2": ("2.12", ("Sim",)),
    "2.13.1": ("2.13", ("Sim", "Em alguns casos")),
    "OUV.1": ("2.1", ("Ouvidoria",)),
    "OUV.2": ("2.1", ("Ouvidoria",)),
    "OUV.3": ("2.1", ("Ouvidoria",)),
    "OUV.4": ("2.1", ("Ouvidoria",)),
    "ESIC.1": ("2.1", ("e-SIC",)),
    "ESIC.2": ("2.1", ("e-SIC",)),
}

IDS_BLOCO_4 = (
    "4.1", "4.2", "4.2.1", "4.2.2", "4.2.3", "4.2.4", "4.2.4.1",
    "4.2.5", "4.2.5.1",
)

CONDICOES_BLOCO_4 = {
    "4.2.1": ("4.2", ("Sim", "Em alguns casos")),
    "4.2.2": ("4.2", ("Sim", "Em alguns casos")),
    "4.2.3": ("4.2", ("Sim", "Em alguns casos")),
    "4.2.4": ("4.2", ("Sim", "Em alguns casos")),
    "4.2.4.1": ("4.2.4", ("Sim", "Em alguns casos")),
    "4.2.5": ("4.2", ("Sim", "Em alguns casos")),
    "4.2.5.1": ("4.2.5", ("Sim",)),
}

CONDICOES_PARTICIPANTE_BLOCO_3 = {
    "3.5.1": ("3.5", ("Sim",)),
}


@dataclass(frozen=True, slots=True)
class CampoForm1Integral:
    """Metadado imutável de uma pergunta inventariada na REV13."""

    id: str
    bloco: str
    pergunta: str
    controle: str
    alternativas: tuple[str, ...]
    instrucao: str


def _alternativas(texto: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in texto.split("|") if item.strip())


def _sha256_catalogo() -> str:
    return hashlib.sha256(CAMINHO_CATALOGO_REV13.read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def carregar_catalogo_form1_integral() -> tuple[CampoForm1Integral, ...]:
    """Lê e confere o inventário sem habilitar seu uso no workflow."""

    if _sha256_catalogo() != SHA256_CATALOGO_REV13:
        raise ValueError("o catálogo REV13 não corresponde ao insumo aprovado para preparação")

    with CAMINHO_CATALOGO_REV13.open("r", encoding="utf-8-sig", newline="") as arquivo:
        linhas = tuple(csv.DictReader(arquivo, delimiter=";"))

    campos = tuple(
        CampoForm1Integral(
            id=linha["id"].strip(),
            bloco=linha["bloco"].strip(),
            pergunta=linha["pergunta"].strip(),
            controle=linha["controle_sugerido"].strip(),
            alternativas=_alternativas(linha["alternativas_original"]),
            instrucao=linha["instrucao_original"].strip(),
        )
        for linha in linhas
    )
    problemas = validar_catalogo_form1_integral(campos)
    if problemas:
        raise ValueError("catálogo REV13 inválido: " + "; ".join(problemas))
    return campos


def validar_catalogo_form1_integral(
    campos: tuple[CampoForm1Integral, ...],
) -> list[str]:
    """Confere somente integridade estrutural; não inventa regras funcionais."""

    problemas = []
    if len(campos) != QUANTIDADE_CAMPOS_REV13:
        problemas.append(
            f"esperados {QUANTIDADE_CAMPOS_REV13} identificadores; encontrados {len(campos)}"
        )

    ids = [campo.id for campo in campos]
    repetidos = sorted({campo_id for campo_id in ids if ids.count(campo_id) > 1})
    if repetidos:
        problemas.append("identificadores repetidos: " + ", ".join(repetidos))

    for campo in campos:
        if not campo.id or not campo.bloco or not campo.pergunta:
            problemas.append(f"campo incompleto: {campo.id or '<sem id>'}")
        if campo.controle not in CONTROLES_REV13:
            problemas.append(f"controle desconhecido em {campo.id}: {campo.controle}")
        if len(campo.alternativas) != len(set(campo.alternativas)):
            problemas.append(f"alternativa repetida em {campo.id}")
    return problemas


def campos_por_id() -> dict[str, CampoForm1Integral]:
    """Índice somente leitura para os incrementos posteriores."""

    return {campo.id: campo for campo in carregar_catalogo_form1_integral()}
