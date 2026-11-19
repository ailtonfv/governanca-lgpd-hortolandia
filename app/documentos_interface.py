"""Leitura segura de Markdown interno: apenas texto, títulos e tabelas."""
import re


def blocos_documento(texto):
    blocos=[]
    for linha in texto.splitlines():
        linha=linha.strip()
        if not linha:continue
        if linha.startswith('|'):
            celulas=[c.strip() for c in linha.strip('|').split('|')]
            if all(re.fullmatch(r':?-+:?', c) for c in celulas):continue
            if not blocos or blocos[-1]['tipo']!='tabela':blocos.append(dict(tipo='tabela',linhas=[]))
            blocos[-1]['linhas'].append(celulas)
        else:
            tipo='h2' if linha.startswith('## ') else 'h1' if linha.startswith('# ') else 'p'
            blocos.append(dict(tipo=tipo,texto=linha.lstrip('#> ').strip()))
    return blocos
