"""Duração do plano; decisão de Ailton de 26/11/2026 (A1).

O prazo começa na aprovação, não no registro nem na espera pela autoridade.
Planos históricos com data fixa permanecem com a data registrada.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.validacao_atos34 import ErrosCampos


def data_municipal(instante):
    if isinstance(instante, str):
        instante = datetime.fromisoformat(instante)
    return instante.astimezone(ZoneInfo('America/Sao_Paulo')).date()


def duracao_validada(estado, valor):
    try:
        if isinstance(valor, bool) or str(valor).strip() != str(int(valor)):
            raise ValueError
        dias = int(valor)
        if dias < 1:
            raise ValueError
    except (ValueError, TypeError, OverflowError):
        raise ErrosCampos({'duracao_dias': 'Informe a duração em dias corridos, como número inteiro positivo.'})
    prioridade = estado.get('respostas', {}).get('F4-4.9')
    if estado.get('faixa_origem') == 'Crítico' or prioridade == 'Imediata':
        if dias > 30:
            raise ErrosCampos({'duracao_dias': 'Para risco Crítico ou prioridade Imediata, o prazo máximo é de 30 dias. Para mais tempo, aprove o plano e peça prorrogação, com justificativa.'})
    return dias


def vencimento_na_aprovacao(estado, instante):
    if estado.get('duracao_dias') is None:
        return estado.get('prazo')  # data histórica, sem reinterpretar o ato
    dias = duracao_validada(estado, estado['duracao_dias'])
    try:
        return (data_municipal(instante) + timedelta(days=dias)).isoformat()
    except OverflowError:
        raise ErrosCampos({'duracao_dias': 'A duração excede o intervalo de datas suportado.'})
