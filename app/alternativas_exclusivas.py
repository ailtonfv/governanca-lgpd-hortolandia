"""D3: alternativas que excluem as demais, sem alterar códigos persistidos."""
import re


def exclusiva(rotulo):
    return bool(re.match(r'^(?:a confirmar$|não se aplica(?:\b|$)|não aplicável(?:\b|$)|nenhum(?:a)?(?:\b|$)|faixa etária não registrada$)', str(rotulo).strip(), re.I))


def combinacao_exclusiva(opcoes, alternativas):
    return len(opcoes) > 1 and any(a['codigo'] in opcoes and exclusiva(a['rotulo']) for a in alternativas)
