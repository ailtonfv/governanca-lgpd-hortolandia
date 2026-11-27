"""A11: a conclusão usa o resultado salvo no bloco 14."""
def resultado_salvo(conteudo):
    from app.respostas_form2 import definicao_revisao
    from app.form2_rev212 import RASCUNHO
    q=next(q for q in definicao_revisao(14)['itens'] if q['id']=='F2-14.1')
    campos=conteudo.get(RASCUNHO,{}).get('14',{})
    codigos=campos.get('opcao:F2-14.1',[])
    rotulos={a['codigo']:a['rotulo'] for a in q['alternativas']}
    if not codigos or any(c not in rotulos for c in codigos):
        raise ValueError('Registre o resultado da análise na F2-14.1 antes de concluir.')
    partes=[rotulos[c] for c in codigos]
    if campos.get('texto:F2-14.1','').strip():partes.append(campos['texto:F2-14.1'].strip())
    return ' · '.join(partes)
