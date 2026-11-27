"""Referências factuais da apresentação em análise, sem inferir respostas do AAL."""
ABERTURAS = {f"F2-{n}.1" for n in (4, 5, 6, 7, 8, 9, 11)}
REFERENCIAS = {'F2-7.1':['F1-5.1','F1-10.8'],
 'F2-12.8':['F1-8.6',*[f'F1-8.6.{n}' for n in range(1,5)]],
 **{q:[f'F1-11.2.{n}' for n in range(1,6)] for q in ('F2-9.7.1','F2-9.8','F2-9.9')}}


def projetar_fatos_abertura(itens, origem, unidades=None):
    for item in itens:
        if item['id'] not in ABERTURAS and item['id'] not in REFERENCIAS:
            continue
        referencias = ['F1-5.1'] if item['id'] == 'F2-4.1' else item['referencias_form1']
        referencias = REFERENCIAS.get(item['id'],referencias)
        item['referencias_exibidas'] = referencias
        fatos = []
        for referencia in dict.fromkeys(referencias):
            for pergunta in origem['perguntas']:
                if pergunta['id'] == referencia.removeprefix('F1-') and pergunta['respondida']:
                    valor = pergunta['valor']
                    codigo = valor if isinstance(valor,str) and valor in (unidades or {}) else ''
                    if codigo:valor=unidades[codigo]
                    fatos.append({'referencia': referencia, 'conjunto': pergunta.get('conjunto'),
                                  'codigo':codigo,
                                  'valor': ', '.join(map(str, valor)) if isinstance(valor, list) else str(valor),
                                  'complemento': pergunta.get('complemento') or
                                      origem['conteudo'].get('complementos', {}).get(pergunta['id'], '')})
        item['fatos_abertura'] = fatos
