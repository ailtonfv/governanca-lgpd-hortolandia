"""Projeções visuais; pontuação gravada continua no domínio."""
from app.avaliacao_risco34 import pontuar
from app.apresentacao_form2 import data_local
PROBABILIDADE=['Muito baixa: não se espera que ocorra','Baixa: pode ocorrer em situação excepcional','Média: pode ocorrer algumas vezes','Alta: provável; já ocorreu ou há falha conhecida','Muito alta: esperado ou recorrente']
IMPACTO=['Muito baixo: incômodo mínimo','Baixo: transtorno pequeno','Médio: transtorno relevante (tempo, custo, constrangimento)','Alto: consequência séria e de difícil reversão (discriminação, prejuízo financeiro, exposição de dado sensível)','Muito alto: consequência grave ou irreversível (integridade física, retaliação, perda de acesso a serviço essencial)']
EXIGENCIAS={'Pequeno':'Pequeno: acompanhar controles; aceitação pela autoridade da Secretaria.',
 'Moderado':'Moderado: planejar controles e acompanhamento; aceitação pela autoridade da Secretaria.',
 'Alto':'Alto: controles e triagem de RIPD; manifestação do DPO, ciência do Comitê e aceitação pela autoridade da Secretaria.',
 'Crítico':'Crítico: controles imediatos, triagem de RIPD, manifestação do DPO e do Comitê, aceitação pelo Prefeito.'}

def situacao_avaliacao(e):
    if e.get('avaliacao_sem_consenso'):return 'Sem consenso — encaminhado ao Comitê'
    c=e.get('avaliacao_confirmacoes',{})
    if set(c)=={'secretaria','dpo'}:return 'Nota conjunta confirmada pela Secretaria e pelo DPO em '+str(data_local(max(v.get('em','') for v in c.values())))
    if not e.get('avaliacao'):return 'Ainda não avaliado — registre a proposta para o outro lado conferir.'
    proponente=e.get('avaliacao_proponente') or next((dict(v,lado=k) for k,v in c.items()),{})
    if not proponente:return 'Deliberação registrada — revisar e confirmar a proposta em conjunto.'
    dpo=proponente.get('lado')=='dpo'
    return ('Proposta pelo DPO' if dpo else 'Proposta pela Secretaria')+' em '+str(data_local(proponente.get('em')))+' · aguardando confirmação '+('da Secretaria' if dpo else 'do DPO')

def valores_proposta(e):
    a=e.get('avaliacao') or {}; c=(a.get('controles') or [{}])[0]
    return dict(evento=e.get('evento',''),causa=e.get('causa',''),consequencia=e.get('consequencia',''),
        p=a.get('inerente',{}).get('probabilidade',''),i=a.get('inerente',{}).get('impacto',''),
        pr=a.get('residual',{}).get('probabilidade',''),ir=a.get('residual',{}).get('impacto',''),
        controle=c.get('descricao',''),implementado='sim' if c.get('implementado') else 'nao',
        evidencia=c.get('evidencia',''),justificativa=a.get('justificativa',''))

def matriz():
    return [[dict(p=p,i=i,**pontuar(p,i)) for i in range(1,6)] for p in range(5,0,-1)]

def titulo_bloco(texto):
    import re
    titulo=texto[:1].upper()+texto[1:].lower()
    return re.sub(r'\b(ripd|lgpd|dpo|anpd|form|ppps)\b',lambda m:'PPPs' if m[0].lower()=='ppps' else m[0].upper(),titulo,flags=re.I)

def grade_visual(grade,obj,conta,bloco,estado=None):
    from urllib.parse import urlencode
    from app.leitura_atos34 import situacao_bloco
    saida=[]
    for g in grade:
        ato=situacao_bloco(estado.get('form'),g['numero'],estado) if estado else ''
        texto=g['texto'] if g['m'] else ''
        if g['n'] and g['n']==g['m']:
            texto='✓ Todas respondidas · '+str(g['a_confirmar'])+' a confirmar' if g.get('a_confirmar') else '✓ Todas as perguntas ativas respondidas'
        saida.append(dict(numero=g['numero'],titulo=titulo_bloco(g['titulo']),
            texto=texto,situacao_ato=ato,respondidas=g['n'],ativas=g['m'],percentual=g['percentual'],
            href=f'/forms34/{obj}/blocos/{g["numero"]}?'+urlencode({'conta_id':conta}),atual=g['numero']==bloco))
    return saida



def descricao_nota34(valor, eixo):
    """Mesmo vocabulário das listas, sem recalcular a pontuação histórica."""
    textos = PROBABILIDADE if eixo == 'probabilidade' else IMPACTO
    if valor is None or valor == '':
        return 'Ainda não avaliado'
    numero = int(valor)
    return f'{numero} — {textos[numero-1]}' if 1 <= numero <= 5 else str(valor)
