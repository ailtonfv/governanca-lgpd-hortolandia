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
    """Fila institucional por fatos de cada etapa, independente da Central pessoal."""
    from app.avaliacao_risco34 import exige_triagem
    from app.encerramento_form4 import pode_encerrar, reducao_total
    if e.get('form') not in (3,4) or e.get('cancelada'):
        return None
    if e['form']==3:
        if e.get('conclusao') and not e.get('reavaliacao'):return None
        alvo=e.get('reavaliacao') or e
        if alvo.get('avaliacao_sem_consenso'):return None
        if not alvo.get('avaliacao'):return 'Propor avaliação conjunta'
        if set(alvo.get('avaliacao_confirmacoes',{}))!={'secretaria','dpo'}:
            return None if 'secretaria' in alvo.get('avaliacao_confirmacoes',{}) else 'Confirmar avaliação conjunta'
        if exige_triagem(e['avaliacao'],e.get('sinais')) and set(e.get('triagem_confirmacoes',{}))!={'secretaria','dpo'}:
            if e.get('triagem_sem_consenso'):return None
            if not e.get('triagem'):return 'Propor triagem de RIPD'
            return None if 'secretaria' in e.get('triagem_confirmacoes',{}) else 'Confirmar triagem de RIPD'
        if not e.get('aceitacao'):return None
        r=e.get('respostas',{})
        if r.get('F3-3.59')=='Sim' and 'Providência no FORM 4' in r.get('F3-3.61',[]) and not e.get('acoes_rodada',e.get('acoes')):
            return 'Encaminhar providência'
        return 'Concluir a avaliação do risco'
    if e.get('decisoes_pendentes'):return None
    if not e.get('plano'):return 'Registrar plano'
    if not e.get('plano_aprovado'):return None
    if not e.get('execucao'):return 'Registrar execução'
    if not e.get('verificada'):return None
    if not e.get('encerrada') and not reducao_total(e):
        if not e.get('residual_acao'):return 'Propor nota residual após a ação'
        if not nota_confirmada(e):return None
        if not e.get('decisao_residual_acao'):return 'Decidir sobre o risco residual após a ação'
    if not pode_encerrar(e) or e.get('condicoes_abertas'):return None
    if not e.get('aprendizagem') or e.get('aprendizagem_devolvida'):return 'Registrar aprendizagem'
    if e.get('aprendizagem_conferida') and not e.get('aprendizagem_autorizada'):return 'Autorizar versão para consulta'
    return None
