"""D9: classificação explícita. Critério aprovado pelo DPO em 18/11/2026."""
JURIDICAS = frozenset(('F2-3.1','F2-3.2.2','F2-3.3','F2-3.5','F2-3.6','F2-3.7','F2-3.8','F2-3.9',
 'F2-4.3','F2-5.3','F2-5.4','F2-5.7','F2-6.2','F2-6.4','F2-7.1.2','F2-7.5','F2-7.11.4',
 'F2-8.6','F2-9.7.2','F2-10.1','F2-10.4','F2-10.5','F2-10.7.8','F2-11.8','F2-14.1'))
TECNICAS = frozenset(('F2-2.1','F2-4.6','F2-5.5','F2-11.7.3','F2-13.6'))


# D9, 18/11/2026: norma/fundamento = jurídica; processo/dados/sistemas = técnica.
DELIBERADAS_1811 = {
    **dict.fromkeys(('F2-2.5', 'F2-2.6', 'F2-2.8', 'F2-2.9', 'F2-2.9.3',
                     'F2-8.4', 'F2-8.5', 'F2-11S.8', 'F2-14.5'), 'tecnica'),
    **dict.fromkeys(('F2-4.5', 'F2-6.6', 'F2-7.4.2.1', 'F2-11.7'), 'juridica'),
}


def classificar(q):
    tipo = 'juridica' if q['id'] in JURIDICAS else 'tecnica' if q['id'] in TECNICAS else 'a_deliberar'
    tipo = DELIBERADAS_1811.get(q['id'], tipo)
    codigos=[]
    for a in q.get('alternativas',[]):
        if a['rotulo'].startswith('Requer análise'):
            codigos.append(a['codigo'])
            if tipo != 'a_deliberar':
                a['rotulo'] = 'Requer análise jurídica' if tipo == 'juridica' else 'Requer análise técnica'
    q['analise_especializada'] = {'classificacao':tipo,'codigos':codigos}
    if q['id'] in DELIBERADAS_1811:
        q['analise_especializada']['destinos'] = [
            ('dpo', 'Consultar o DPO'),
            ('juridico', 'Consultar o Jurídico') if tipo == 'juridica' else ('tematica', 'Consultar a área'),
        ]
    return q
