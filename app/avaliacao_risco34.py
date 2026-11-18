"""Decisão 4/A1, 18/11/2026: metodologia demonstrativa, sem homologação."""
from copy import deepcopy

METODOLOGIA = 'DEMO-5x5-20261118'


def pontuar(probabilidade, impacto):
    for valor in (probabilidade, impacto):
        if valor is not None and (type(valor) is not int or not 1 <= valor <= 5):
            raise ValueError('Probabilidade e impacto devem estar entre 1 e 5.')
    nota = probabilidade * impacto if None not in (probabilidade, impacto) else None
    faixa = ('Não avaliado' if nota is None else 'Pequeno' if nota <= 3 else
             'Moderado' if nota <= 6 else 'Alto' if nota <= 12 else 'Crítico')
    return dict(probabilidade=probabilidade, impacto=impacto, nota=nota,
                faixa=faixa, metodologia=METODOLOGIA, d11=True)


def propor_avaliacao(dados):
    inerente = pontuar(dados.get('p'), dados.get('i'))
    residual = pontuar(dados.get('pr'), dados.get('ir'))
    if inerente['nota'] is None and residual['nota'] is not None:
        raise ValueError('Registre a avaliação inerente antes da residual.')
    controles = deepcopy(dados.get('controles', []))
    if not isinstance(controles, list) or any(not isinstance(c, dict) for c in controles):
        raise ValueError('Controles inválidos.')
    if (residual['nota'] is not None and residual['nota'] < inerente['nota']
            and not any(c.get('implementado') is True and isinstance(c.get('evidencia'), str)
                        and c['evidencia'].strip() for c in controles)):
        raise ValueError('Redução residual exige controle implementado e evidência.')
    justificativa = dados.get('justificativa', '')
    if not isinstance(justificativa, str) or not 1 <= len(justificativa.strip()) <= 1000:
        raise ValueError('Justifique a avaliação em até 1000 caracteres.')
    return dict(inerente=inerente, residual=residual, controles=controles,
                justificativa=justificativa)


def exige_triagem(avaliacao, sinais):
    return bool(sinais) or any(avaliacao.get(k, {}).get('faixa') in ('Alto', 'Crítico')
                              for k in ('inerente', 'residual'))
