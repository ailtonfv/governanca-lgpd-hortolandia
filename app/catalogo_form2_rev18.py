"""Leitura documental do FORM 2, independente de autorização, rascunhos e banco."""

import hashlib
import json
from pathlib import Path


VERSAO = "F2-REV18-CATALOGO-v1"
ARQUIVO = Path(__file__).with_name("catalogos") / "form2_rev18_v1.json"
# Conteúdo da edição conferida, independente de espaços, quebras de linha e ordem de chaves.
SHA256_CONTEUDO_V1 = "a883ef384937b305f9da9dff67bc7e2ee9ba6014f8279130f9e6e48803a9dcac"


def _validar(catalogo: dict) -> None:
    if catalogo["versao"] != VERSAO:
        raise ValueError("Versão inesperada do catálogo do FORM 2.")

    blocos = catalogo["blocos"]
    numeros = [bloco["numero"] for bloco in blocos]
    percurso = [numero for etapa in catalogo["etapas"] for numero in etapa["blocos"]]
    if numeros != list(range(1, 15)) or sorted(percurso) != numeros:
        raise ValueError("Blocos ausentes, duplicados ou fora da ordem editorial.")

    itens = [item for bloco in blocos for item in bloco["itens"]]
    ids = {item["id"] for item in itens}
    if len(itens) != 250 or len(ids) != len(itens):
        raise ValueError("Quantidade incorreta ou identificador duplicado no FORM 2.")
    paragrafos = [item["paragrafo"] for item in itens]
    if paragrafos != sorted(set(paragrafos)):
        raise ValueError("As perguntas não seguem a ordem editorial do Mestre.")

    representacao = json.dumps(catalogo, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    if hashlib.sha256(representacao.encode("utf-8")).hexdigest() != SHA256_CONTEUDO_V1:
        raise ValueError("O conteúdo diverge da edição conferida do catálogo do FORM 2.")


def carregar_catalogo() -> dict:
    """Retorna uma cópia independente e validada da edição v1, em ordem editorial."""
    catalogo = json.loads(ARQUIVO.read_text(encoding="utf-8"))
    _validar(catalogo)
    return catalogo
