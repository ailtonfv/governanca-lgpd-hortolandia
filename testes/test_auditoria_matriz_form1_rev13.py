"""Coerência documental da matriz central de obrigatoriedade REV13."""

import re
from collections import Counter
from pathlib import Path

from app.form1_integral import carregar_catalogo_form1_integral


RAIZ = Path(__file__).resolve().parents[1]
MATRIZ = RAIZ / "docs" / "planejamento" / "MATRIZ_CAMPOS_FORM1_REV13.md"


def _linhas_da_matriz():
    linhas = []
    for linha in MATRIZ.read_text(encoding="utf-8").splitlines():
        partes = [parte.strip() for parte in linha.split("|")]
        if len(partes) >= 7 and re.fullmatch(r"(?:\d+(?:\.\d+)*|OUV\.\d+|ESIC\.\d+)", partes[1]):
            linhas.append({"id": partes[1], "classe": partes[3], "condicao": partes[4], "observacao": partes[5]})
    return linhas


def test_matriz_cobre_exatamente_os_128_identificadores_do_catalogo():
    linhas = _linhas_da_matriz()
    ids_catalogo = {campo.id for campo in carregar_catalogo_form1_integral()}
    ids_matriz = [linha["id"] for linha in linhas]

    assert len(linhas) == 128
    assert len(ids_matriz) == len(set(ids_matriz))
    assert set(ids_matriz) == ids_catalogo


def test_classificacoes_da_matriz_somam_os_128_identificadores():
    contagem = Counter(linha["classe"] for linha in _linhas_da_matriz())

    assert contagem == {
        "Essencial, somente leitura": 3,
        "Obrigatória essencial": 25,
        "Obrigatória condicional": 69,
        "Facultativa (REV13)": 4,
        "Facultativa nesta proposta": 27,
    }


def test_matriz_mantem_decisoes_pendentes_sem_inventar_regras():
    texto = MATRIZ.read_text(encoding="utf-8")

    assert "F1-D04: WhatsApp" in texto
    assert "F1-D05: complemento de Outro" in texto
    assert "F1-D06: excludentes" in texto
    assert "F1-D07: fonte institucional" in texto
