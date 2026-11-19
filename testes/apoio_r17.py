"""Massa sintética completa para testes de atos; não é carga demonstrativa."""
from copy import deepcopy

def completo2(base=None):
    from app.respostas_form2 import definicao_revisao
    from app.form2_rev212 import RASCUNHO
    c={'respostas_etapa1':{},RASCUNHO:{}}
    for b in range(1,15):
        campos=c[RASCUNHO].setdefault(str(b),{})
        for q in definicao_revisao(b)['itens']:
            if q.get('edicao')=='consulta' or q.get('guardar_concluir')=='Automático em leitura':continue
            sufixo='#1' if q.get('repetivel') else ''
            op=next((a['codigo'] for a in q['alternativas'] if a['rotulo']=='A confirmar'),None)
            op=op or next((a['codigo'] for a in q['alternativas']),None)
            if q['edicao']=='habilitada':c['respostas_etapa1'][q['id']]=op or 'Texto fictício'
            elif op:campos['opcao:'+q['id']+sufixo]=[op]
            else:campos['texto:'+q['id']+sufixo]='Texto fictício'
            if op:campos['texto:'+q['id']+sufixo]='Complemento fictício'
    if base:
        for k,v in deepcopy(base).items():
            if k==RASCUNHO:
                for b,campos in v.items():c[RASCUNHO].setdefault(b,{}).update(campos)
            elif isinstance(v,dict):c.setdefault(k,{}).update(v)
            else:c[k]=v
    return c


def preencher34(sessao,obj):
    from app.fluxo_forms34 import estado,executar
    from app.questionario_forms34 import perguntas,ativa
    from uuid import uuid4
    e=estado(sessao,obj)
    for bloco in range(1,17 if e['form']==3 else 10):
        e=estado(sessao,obj);campos={}
        for q in perguntas(e['form']):
            if q['bloco']!=bloco or q['tipo'] in ('ato','readonly','computed'):continue
            if not ativa(q,{**e.get('respostas',{}),**campos},e):continue
            if q['id'] in e.get('respostas',{}) and e['respostas'][q['id']]:continue
            if q['opcoes']:
                v='A confirmar' if 'A confirmar' in q['opcoes'] else q['opcoes'][0]
                campos[q['id']]=[v] if q['tipo']=='multi' else v
            else:campos[q['id']]='2026-12-15' if q['tipo']=='date' else 'Texto fictício'
        if campos:
            executar(sessao,conta_id='CONTA-B1',comando_id=str(uuid4()),identidade_id=obj,
                     versao=e['versao'],acao='salvar_bloco',dados={'bloco':bloco,'campos':campos})
            sessao.commit()
