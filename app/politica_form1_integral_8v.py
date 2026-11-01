"""Recorte P0 aprovado no Incremento 8V para o FORM 1 Integral.

Esta camada identifica explicitamente a política restrita aplicada sobre a
matriz vigente. Ela não substitui a candidata v2-8U nem reinterpreta versões
históricas do contrato 3.
"""

from __future__ import annotations


VERSAO_POLITICA_FORM1_8V = "POLITICA-F1-REV13-P0-8V-v1"
VERSAO_MATRIZ_BASE_FORM1_8V = "MATRIZ-F1-REV13-OBR-v1"
METADADOS_INSTITUCIONAIS_NAO_BLOQUEANTES = frozenset({"0.2", "0.3"})


def problema_exclusividade_multisselecao(
    campo_id: str, valores: list[str], alternativas: tuple[str, ...]
) -> str | None:
    """Recusa apenas as exclusividades aprovadas e previstas no catálogo.

    A validação é aplicada na escrita de uma nova versão do rascunho. Conteúdo
    histórico não é normalizado nem alterado silenciosamente.
    """

    if campo_id == "13.1":
        excludentes = {"Nenhuma das situações acima", "A confirmar", "Não se aplica"}
        if excludentes.intersection(valores) and len(valores) != 1:
            return "13.1: a alternativa excludente deve ser selecionada isoladamente"

    if "A confirmar" in alternativas and "A confirmar" in valores and len(valores) != 1:
        return f"{campo_id}: A confirmar não pode coexistir com outra alternativa"

    if "Não se aplica" in alternativas and "Não se aplica" in valores and len(valores) != 1:
        return f"{campo_id}: Não se aplica não pode coexistir com outra alternativa"

    return None
