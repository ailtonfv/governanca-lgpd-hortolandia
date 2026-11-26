"""Projeções do A9: somente fatos e atos existentes, sem texto de evidências."""
from app.encerramento_form4 import nota_confirmada


def condicoes_abertas(d, e):
    estados = {i['obj'].id: i['estado'] for i in d['objetos']}
    return [c for c in e.get('condicoes_aceitacao', [])
            if not estados.get(c['acao_id'], {}).get('encerrada')]


def decisao_posterior(e):
    if not e.get('verificada') or e.get('cancelada'):
        return None
    n = nota_confirmada(e)
    if not n:
        return None
    escolha = e.get('decisao_residual_acao', {}).get('opcao')
    aguarda_autoridade = escolha == 'aceitar' and n['faixa'] in ('Alto','Crítico') and not e.get('aceitacao_residual_acao')
    return dict(nota=n, decisao='Aguardando decisão da autoridade' if aguarda_autoridade else {'aceitar':'Risco aceito', 'reavaliar':'Reavaliação solicitada',
                                'nova_providencia':'Nova providência'}.get(escolha, 'Aguardando decisão'),
                pendente=not escolha or aguarda_autoridade)


def secretaria_pendente(e):
    """Próximo trabalho da Secretaria segundo os atos existentes, sem aprovar por ela."""
    from app.providencias import classificar
    from app.atos_forms34_interface import disponiveis
    if e.get('form') not in (3,4) or e.get('cancelada') or e.get('encerrada'):
        return None
    if e['form']==4 and e.get('verificada'):
        for a in disponiveis(4, 8, {'secretaria'}, e, None):
            if a['acao'] in ('propor_residual_acao','decidir_residual_acao'):
                return a['titulo']
    p = classificar(e['form'], e, {'secretaria','executor_unidade'})
    if p.get('ato') in ('confirmar_avaliacao','confirmar_triagem'):
        campo='avaliacao' if p['ato']=='confirmar_avaliacao' else 'triagem'
        alvo=(e.get('reavaliacao') or e) if campo=='avaliacao' else e
        if 'secretaria' in alvo.get(campo+'_confirmacoes',{}):return None
    return p['pendencia'] if p['pendente'] else None
