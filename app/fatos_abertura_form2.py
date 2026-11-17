"""Referências factuais da apresentação em análise, sem inferir respostas do AAL."""
ABERTURAS = {f"F2-{n}.1" for n in (4, 5, 6, 7, 8, 9, 11)}


def projetar_fatos_abertura(itens, origem):
    for item in itens:
        if item['id'] not in ABERTURAS:
            continue
        referencias = ['F1-5.1'] if item['id'] == 'F2-4.1' else item['referencias_form1']
        fatos = []
        for referencia in dict.fromkeys(referencias):
            for pergunta in origem['perguntas']:
                if pergunta['id'] == referencia.removeprefix('F1-') and pergunta['respondida']:
                    valor = pergunta['valor']
                    fatos.append({'referencia': referencia, 'conjunto': pergunta.get('conjunto'),
                                  'valor': ', '.join(map(str, valor)) if isinstance(valor, list) else str(valor),
                                  'complemento': pergunta.get('complemento') or
                                      origem['conteudo'].get('complementos', {}).get(pergunta['id'], '')})
        item['fatos_abertura'] = fatos
