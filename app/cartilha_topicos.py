"""Catálogo editorial local e resolução de tópicos da Cartilha integrada."""
from functools import lru_cache
import json
from pathlib import Path

from app.cartilha_local import EDICAO_INTEGRADA, secoes_cartilha_integrada

CAMINHO_TOPICOS = Path(__file__).with_name("catalogos") / "topicos_cartilha.json"
CHAVES_CARTILHA = frozenset(f"CART-{numero:02d}" for numero in range(1, 55))


@lru_cache(maxsize=4)
def _ler_catalogo(caminho, mtime_ns, tamanho):
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    topicos = dados["topicos"]
    if dados["edicao"] != EDICAO_INTEGRADA or set(topicos) != CHAVES_CARTILHA:
        raise ValueError("Edição ou conjunto de chaves da Cartilha divergente.")
    if any(not isinstance(t["nome"], str) or not t["nome"].strip() or
           (not t.get("retirado") and (not isinstance(t["ancora"], str) or not t["ancora"].strip()))
           for t in topicos.values()):
        raise ValueError("Tópico ou marcador inválido no catálogo da Cartilha.")
    ancoras = [t["ancora"] for t in topicos.values() if not t.get("retirado")]
    if len(ancoras) != len(set(ancoras)):
        raise ValueError("Marcador repetido no catálogo da Cartilha.")
    return topicos


def catalogo_topicos():
    try:
        arquivo = CAMINHO_TOPICOS.stat()
        return _ler_catalogo(CAMINHO_TOPICOS, arquivo.st_mtime_ns, arquivo.st_size)
    except (OSError, KeyError, TypeError, ValueError, AttributeError):
        return {}


def destinos_integrados(topicos):
    ancoras = {t["ancora"]: chave for chave, t in topicos.items() if not t.get("retirado")}
    return secoes_cartilha_integrada(ancoras) if ancoras else {}
