"""Critérios de referência e população informada pelo DPO; não homologa risco."""
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

GUARDA = 'Em definição pela Prefeitura (grupo de temporalidade)'
GERAIS = ('Larga escala', 'Possibilidade de afetar significativamente interesses ou direitos fundamentais')
ESPECIFICOS = ('Tecnologia emergente/inovadora', 'Vigilância ou controle de zonas acessíveis ao público',
    'Decisão unicamente automatizada', 'Dados pessoais sensíveis', 'Crianças/adolescentes', 'Idosos')


def alto_risco_referencia(respostas):
    valores = respostas.get('F3-3.10', [])
    return bool(set(valores) & set(GERAIS) and set(valores) & set(ESPECIFICOS))


def volume():
    config = json.loads((Path(__file__).parent/'catalogos/populacao_municipio.json').read_text(encoding='utf8'))
    p = config.get('valor')
    if not p:
        return 'Baixo: menos de 1% da população por ano. Médio: de 1% a 10%. Alto: mais de 10%.'
    def faixa(proporcao):
        n = int((Decimal(str(p))*Decimal(proporcao)).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
        return f'{n:,}'.replace(',','.')
    baixo, alto = faixa('.01'), faixa('.1')
    return (f'Baixo: menos de 1% da população do município por ano (menos de {baixo} pessoas). '
        f'Médio: de 1% a 10% (de {baixo} a {alto}). Alto: mais de 10% (mais de {alto}). '
        f"Referência: {config['fonte']} {config['ano_referencia']}.")


def projetar_guarda(sessao, ref, estado):
    if estado.get('form') != 3 or estado.get('respostas',{}).get('F3-3.35'):
        return estado
    from app.modelos import VersaoForm1Integral
    snapshot = sessao.get(VersaoForm1Integral, ref.snapshot_form1_id)
    respostas = (snapshot.conteudo or {}).get('respostas',{}) if snapshot else {}
    def contem(valor):
        if isinstance(valor, dict):return any(contem(v) for v in valor.values())
        if isinstance(valor, list):return any(contem(v) for v in valor)
        return valor == GUARDA
    if any(contem(v) for k,v in respostas.items() if k.removeprefix('F1-').startswith('12.')):
        estado.setdefault('respostas',{})['F3-3.35'] = GUARDA
    return estado
