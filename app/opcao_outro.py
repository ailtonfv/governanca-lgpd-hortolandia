"""Complemento explícito da alternativa Outro, sem classificar obrigatoriedade geral."""
import re

def eh_outro(rotulo):
    return bool(re.match(r'^outr[oa]s?\b',str(rotulo).strip(),re.I))

def selecionou_outro(valores):
    return any(eh_outro(v) for v in (valores if isinstance(valores,list) else [valores]))

def validar_outro(valores,texto,identificador):
    if selecionou_outro(valores):
        if not isinstance(texto,str) or not texto.strip():
            raise ValueError(f'{identificador}: ao selecionar Outro, informe Qual?')
        if len(texto)>200:raise ValueError(f'{identificador}: Qual? admite até 200 caracteres.')
