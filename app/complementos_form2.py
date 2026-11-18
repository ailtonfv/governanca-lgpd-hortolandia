"""D1: salvamento parcial permitido; complemento conta antes de consolidar."""
ITENS = frozenset(('F2-5.2','F2-5.6.1','F2-6.5.1','F2-7.4.1','F2-8.2','F2-8.6',
    'F2-9W.2','F2-9W.3','F2-9W.5','F2-10.1','F2-11S.2','F2-12.2','F2-12.3',
    'F2-12A.1.1','F2-13.6.1','F2-9.6.1','F2-9.6.2','F2-9.7.2'))


def codigos_com_complemento(q):
    if q['id'] not in ITENS:
        return []
    if q['id'] in ('F2-9.6.1', 'F2-9.6.2'):
        return ['SIM']
    if q['id'] == 'F2-9.7.2':
        return ['ADEQUACAO', 'CLAUSULAS', 'NCG', 'OUTRA']
    return [a['codigo'] for a in q['alternativas'] if a.get('complemento','').startswith('Texto condicionado')]


def falta_complemento(q, opcoes, texto):
    return bool(set(opcoes or []) & set(codigos_com_complemento(q))) and not str(texto or '').strip()


def complementos_pendentes(conteudo, ramos=()):
    from app.respostas_form2 import definicao_revisao
    from app.form2_rev212 import RASCUNHO, indice_valores, aplicavel, mapa_regras, conjunto_da_chave
    from app.contrato_form2_respostas import carregar_contrato
    valores=indice_valores(conteudo); regras=mapa_regras(carregar_contrato()); faltas=[]
    for numero,campos in conteudo.get(RASCUNHO,{}).items():
        itens={q['id']:q for q in definicao_revisao(int(numero))['itens']}
        for chave,valor in campos.items():
            if not chave.startswith('opcao:'): continue
            identificador=chave.partition(':')[2]; item=identificador.partition('#')[0]; q=itens.get(item)
            if (q and aplicavel(item,conjunto_da_chave(chave),valores,ramos,regras)
                    and falta_complemento(q,valor,campos.get('texto:'+identificador))):
                faltas.append({'item':identificador,'bloco':int(numero),'ancora':item})
    return faltas
