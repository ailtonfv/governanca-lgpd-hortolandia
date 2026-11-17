"""Projeção dos fatos ainda a confirmar, sem classificar impeditivos (D07)."""
import re

from app.contrato_form2_respostas import carregar_contrato
from app.form2_rev212 import indice_valores, mapa_regras, aplicavel, conjunto_da_chave


def itens_a_confirmar(conteudo, ramos=()):
    valores = indice_valores(conteudo)
    regras = mapa_regras(carregar_contrato())
    grupos = {}
    for campo, codigos in valores.items():
        if not campo.startswith("opcao:") or "A_CONFIRMAR" not in codigos:
            continue
        item = campo.removeprefix("opcao:")
        chave = item.partition("#")[0]
        match = re.match(r"F2-(\d+)", chave)
        if not match or not 1 <= int(match[1]) <= 13:
            continue
        if aplicavel(chave, conjunto_da_chave(campo), valores, ramos, regras):
            grupos.setdefault(int(match[1]), []).append({"item": item, "ancora": chave})
    return [{"bloco": bloco, "itens": sorted(itens, key=lambda i: i["item"])}
            for bloco, itens in sorted(grupos.items())]
