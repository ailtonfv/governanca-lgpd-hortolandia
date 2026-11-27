"""Indicadores puros: números e listas calculados juntos, sem gravação.

Fonte: especificação final de 20/11 e complemento sobre ciências e espera.
Entradas são o retrato autorizado de fontes.carregar, o escopo e filtros.
"""
from datetime import datetime, date, timezone
from zoneinfo import ZoneInfo
from statistics import median
from app.avaliacao_risco34 import pontuar

FAIXAS = ('Pequeno','Moderado','Alto','Crítico')
TIPOS = ('servico','processo','atividade')
F3 = ('Sem consenso','Proposta aguardando confirmação','Aguardando avaliação','Nota confirmada','Avaliação concluída')
F4 = ('Plano em elaboração','Em execução','Aguardando verificação','Concluída e verificada','Cancelada')
METODOLOGIA = 'DEMO-5x5-20261118'
LOCAL = ZoneInfo('America/Sao_Paulo')


def momento(v):
    if not v: return None
    if isinstance(v,str):
        if len(v)==10: return datetime.combine(date.fromisoformat(v),datetime.min.time(),LOCAL)
        v = datetime.fromisoformat(v)
    if isinstance(v,date) and not isinstance(v,datetime): v = datetime.combine(v,datetime.min.time(),LOCAL)
    return v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v


def data_br(v):
    if not v:
        return 'Não disponível'
    if isinstance(v, date) and not isinstance(v, datetime):
        return v.strftime('%d/%m/%Y')
    if isinstance(v, str) and len(v) == 10:
        return date.fromisoformat(v).strftime('%d/%m/%Y')
    return momento(v).astimezone(LOCAL).strftime('%d/%m/%Y às %Hh%M')


def numero_br(v):
    """Somente apresentação; cálculos, URLs e coordenadas mantêm números nativos."""
    return str(v).replace('.', ',') if v is not None else '—'


def conjunta(e):
    return set(e.get('avaliacao_confirmacoes',{})) == {'secretaria','dpo'} and bool(e.get('avaliacao'))


def nota(e, lado='residual'):
    return e.get('avaliacao',{}).get(lado,{}) if conjunta(e) else {}


def situacao_risco(e):
    atual = e.get('reavaliacao') or e
    if atual.get('avaliacao_sem_consenso') or e.get('triagem_sem_consenso'): return F3[0]
    if e.get('reavaliacao') or e.get('avaliacao') and not conjunta(e): return F3[1]
    if not conjunta(e): return F3[2]
    return F3[4] if e.get('conclusao') else F3[3]


def situacao_acao(e):
    if e.get('cancelada'): return F4[4]
    if e.get('verificada') and e.get('verificacao',{}).get('aprovada'): return F4[3]
    if e.get('execucao') and (not e.get('verificacao') or momento(e['execucao']['em']) > momento(e['verificacao']['em'])): return F4[2]
    return F4[1] if e.get('plano_aprovado') else F4[0]


def atrasada(e, hoje):
    return bool(e.get('prazo') and date.fromisoformat(e['prazo']) < hoje and not e.get('verificada') and not e.get('cancelada'))


def marco(item, condicao):
    """Início do intervalo atual da condição, pareando rodadas e sem usar salvamento como início."""
    inicio = None
    for ev in item['eventos']:
        e = ev.conteudo.get('estado')
        if e is None: continue
        if condicao(e):
            if inicio is None: inicio = ev.ocorrido_em
        else: inicio = None
    return inicio


def filtrar(d, escopo, filtros):
    uid = filtros.get('secretaria')
    if uid and escopo.unidades is not None and uid not in escopo.unidades:
        raise PermissionError('Secretaria fora do seu escopo.')
    if uid and uid not in {u.id for u in d['secretarias']}:
        raise PermissionError('Secretaria fora do seu escopo ou indisponível.')
    if filtros.get('tipo') and filtros['tipo'] not in TIPOS: raise ValueError('Tipo de objeto inválido.')
    if filtros.get('etapa') and filtros['etapa'] not in ('1','2','3','4'): raise ValueError('Etapa inválida.')
    if filtros.get('faixa') and filtros['faixa'] not in FAIXAS: raise ValueError('Faixa inválida.')
    inicio = date.fromisoformat(filtros['inicio']) if filtros.get('inicio') else None
    fim = date.fromisoformat(filtros['fim']) if filtros.get('fim') else None
    if inicio and fim and inicio > fim: raise ValueError('Período invertido.')
    registros = [r for r in d['registros'] if (escopo.unidades is None or r.unidade_principal_atual_id in escopo.unidades)
        and (escopo.registros is None or r.id in escopo.registros)
        and (not uid or r.unidade_principal_atual_id == uid)
        and (not filtros.get('tipo') or r.tipo_objeto == filtros['tipo'])
        and (not inicio or momento(r.criado_em).astimezone(LOCAL).date() >= inicio)
        and (not fim or momento(r.criado_em).astimezone(LOCAL).date() <= fim)]
    pior = {}
    etapas = {}
    for item in d['objetos']:
        rid = item['obj'].registro_id
        etapas.setdefault(rid,set()).add(str(item['estado']['form']))
        n = nota(item['estado'])
        if n.get('nota') is not None and n.get('faixa') in FAIXAS and n['nota'] > pior.get(rid,{}).get('nota',-1): pior[rid] = n
    for p in d['participacoes']:
        if p.tipo == 'principal' and not etapas.get(p.registro_id): etapas[p.registro_id] = {'2'}
    for r in registros: etapas.setdefault(r.id, {'1'})
    registros = [r for r in registros if (not filtros.get('faixa') or pior.get(r.id,{}).get('faixa') == filtros['faixa'])
        and (not filtros.get('etapa') or filtros['etapa'] in etapas[r.id])]
    ids = {r.id for r in registros}
    return {**d, 'registros':registros, 'secretarias':[u for u in d['secretarias'] if not uid or u.id==uid], 'objetos':[i for i in d['objetos'] if i['obj'].registro_id in ids],
            'participacoes':[p for p in d['participacoes'] if p.registro_id in ids],
            'apresentacoes':[a for a in d['apresentacoes'] if a.registro_id in ids], 'pior':pior, 'etapas':etapas}


def linha(d, registro_id, item=None):
    r = next(r for r in d['registros'] if r.id == registro_id)
    u = next((u for u in d['secretarias'] if u.id == r.unidade_principal_atual_id),None)
    from app.identificacao_registro import identificar
    l = dict(id=r.id, registro=identificar(r),servico=r.titulo_objeto,contexto=d.get('contextos',{}).get(getattr(r,'contexto_atuacao_id',None),''), secretaria=u.nome if u else r.unidade_principal_atual_id,
             unidade_id=r.unidade_principal_atual_id,tipo=r.tipo_objeto, item='',situacao='',desde=None,dias=None)
    if item:
        obj,e = item['obj'],item['estado']
        l.update(id=obj.id, item=f"{'Risco' if obj.tipo=='R' else 'Providência'} {obj.numero}",
                 situacao=situacao_risco(e) if obj.tipo=='R' else situacao_acao(e))
    return l


def quadro(chave, titulo, lista, unidade='Registros', fonte='', regra='', papel='Secretaria', **extra):
    return dict(chave=chave,titulo=titulo,numero=len(lista),lista=lista,unidade=unidade,
                tipos={t:len({x['registro'] for x in lista if x.get('tipo')==t}) for t in TIPOS},
                fonte=fonte,regra=regra,papel=papel,disponivel=True,**extra)


def indisponivel(chave,titulo,motivo):
    return dict(chave=chave,titulo=titulo,numero=None,lista=[],unidade='',tipos={},fonte='',regra=motivo,
                papel='',disponivel=False)


def ativos(d):
    return quadro('ativos','Registros ativos',[linha(d,r.id) for r in d['registros'] if r.estado_atual not in ('cancelado','encerrado','concluido')],
                  fonte='Registro LGPD',regra='Registros distintos, não cancelados nem encerrados.')


def risco(d):
    riscos = [i for i in d['objetos'] if i['obj'].tipo=='R']
    linhas=[]; sem_nota={k:[] for k in ('propostas','sem_consenso','nao_avaliados')}; efeito=[]; ripd=[]
    for i in riscos:
        e=i['estado']; l=linha(d,i['obj'].registro_id,i)
        if not conjunta(e):
            k='sem_consenso' if e.get('avaliacao_sem_consenso') or e.get('triagem_sem_consenso') else 'propostas' if e.get('avaliacao') else 'nao_avaliados'
            sem_nota[k].append(l)
            continue
        n=nota(e); inerente=nota(e,'inerente')
        if n.get('nota') is None: sem_nota['nao_avaliados'].append(l); continue
        l.update(residual=n,inerente=inerente,reavaliacao=bool(e.get('reavaliacao')),decisao=decisao(e),
                 ciencia_comite=(e.get('ciencia_comite') or {}).get('em'),
                 ripd='Informada' if e.get('referencia_ripd') else 'Não informada')
        linhas.append(l)
        if n.get('metodologia')==inerente.get('metodologia')==METODOLOGIA and inerente.get('nota') is not None:
            titulo = ' '.join(str(e.get('evento') or 'Título ainda não informado').split())
            efeito.append({**l, 'item':f"Risco {i['obj'].numero}: {titulo}",
                'situacao':f"{inerente['nota']} {inerente['faixa']} → {n['nota']} {n['faixa']}" + (' · nenhuma redução' if n['nota']>=inerente['nota'] else '')})
        if set(e.get('triagem_confirmacoes',{}))=={'secretaria','dpo'} and e.get('triagem',{}).get('resultado') in ('elaborar','revisar','determinado_anpd'):
            ripd.append(l)
    quadros=[quadro('riscos','Riscos com nota conjunta',linhas,'riscos','Eventos de avaliação conjunta','Somente notas confirmadas pelas duas partes.','Secretaria e DPO'),
             quadro('registros_avaliados','Registros com risco avaliado',[linha(d,rid) for rid in sorted({i['obj'].registro_id for i in riscos if conjunta(i['estado']) and nota(i['estado']).get('nota') is not None})]),
             quadro('efeito','Efeito registrado dos controles',efeito,'riscos', 'Notas inerente e residual','Avaliação registrada; não mede redução causal comprovada.'),
             quadro('ripd','Riscos com triagem indicando RIPD',ripd,'riscos', 'Triagem conjunta','Não afirma elaboração ou conclusão do RIPD.','Secretaria e DPO')]
    for chave,titulo in [('propostas','Propostas aguardando confirmação'),('sem_consenso','Sem consenso (ainda sem nota)'),('nao_avaliados','Ainda não avaliado')]:
        quadros.append(quadro(chave,titulo,sem_nota[chave],'riscos','Eventos de ingresso e avaliação','Fora da matriz; ainda não valem como nota.'))
    for f in FAIXAS:
        quadros.append(quadro('riscos_faixa_'+str(FAIXAS.index(f)),f,[l for l in linhas if l['residual']['faixa']==f],'riscos'))
        quadros.append(quadro('faixa_'+str(FAIXAS.index(f)),f,[linha(d,r.id) for r in d['registros'] if d['pior'].get(r.id,{}).get('faixa')==f],
            fonte='Nota residual conjunta',regra='Cada Registro aparece na faixa de seu pior risco vigente.'))
    for k in ('Informada','Não informada'):
        quadros.append(quadro('ripd_'+('sim' if k=='Informada' else 'nao'),'Referência do RIPD '+k.lower(),[l for l in ripd if l['ripd']==k],'riscos'))
    for nf,f in enumerate(FAIXAS):
        for nd,dec in enumerate(('Decidido','Aguardando manifestação','Em instrução (DPO/Comitê)','Aguardando decisão')):
            quadros.append(quadro(f'decisao_{nf}_{nd}',f+' · '+dec,[l for l in linhas if l['residual']['faixa']==f and l['decisao']==dec],'riscos'))
    for lado in ('inerente','residual'):
        for prob in range(1,6):
            for impacto in range(1,6):
                quadros.append(quadro(f'matriz_{lado}_{prob}_{impacto}',f'{lado.title()} · probabilidade {prob}, impacto {impacto}',
                    [l for l in linhas if l[lado].get('probabilidade')==prob and l[lado].get('impacto')==impacto],'riscos',faixa=pontuar(prob,impacto)['faixa']))
    from app.dashboard.regras_a9 import decisao_posterior
    posteriores=[]
    for i in d['objetos']:
        p=decisao_posterior(i['estado']) if i['obj'].tipo=='A' else None
        if p:posteriores.append({**linha(d,i['obj'].registro_id,i),'residual':p['nota'],'situacao':p['decisao']})
    quadros.append(quadro('decisoes_pos_acao','Depois da providência',posteriores,'providências',regra='Somente nota posterior confirmada pela Secretaria e pelo DPO; a decisão anterior não é reaproveitada.'))
    return quadros


def residual_comite(e):
    return (e.get('deliberacoes_rodada',{}).get('residual') or e.get('manifestacao_comite',{})).get('finalidade')=='residual'


def decisao(e):
    if e.get('aceitacao'): return 'Decidido'
    faixa=nota(e).get('faixa')
    if faixa=='Crítico' and (not e.get('manifestacao_dpo') or not residual_comite(e)): return 'Em instrução (DPO/Comitê)'
    if faixa=='Alto' and not e.get('manifestacao_dpo'): return 'Aguardando manifestação'
    return 'Aguardando decisão'


def sem_consenso(e):
    atual=e.get('reavaliacao') or e
    return bool(atual.get('avaliacao_sem_consenso') or e.get('triagem_sem_consenso'))


def atencao(d, agora):
    from app.dashboard.regras_a9 import condicoes_abertas, decisao_posterior
    linhas={k:[] for k in ('criticos','ciencias','consenso','instrucao','planos','condicoes','residuais_pos','ripd_pendente')}
    for i in d['objetos']:
        e=i['estado']; l=linha(d,i['obj'].registro_id,i)
        if i['obj'].tipo=='R':
            if condicoes_abertas(d,e):linhas['condicoes'].append(l)
            if set(e.get('triagem_confirmacoes',{}))=={'secretaria','dpo'} and e.get('triagem',{}).get('resultado') in ('elaborar','revisar','determinado_anpd') and not e.get('referencia_ripd'):
                linhas['ripd_pendente'].append(l)
            if conjunta(e) and nota(e).get('faixa')=='Crítico' and not e.get('aceitacao'):
                pronto=bool(e.get('manifestacao_dpo') and residual_comite(e))
                m=marco(i,lambda s: conjunta(s) and nota(s).get('faixa')=='Crítico' and bool(s.get('manifestacao_dpo')) and residual_comite(s) and not s.get('aceitacao')) if pronto else None
                linhas['criticos' if pronto else 'instrucao'].append({**l,'desde':m,'dias':dias(m,agora),'residual':nota(e),
                    'ato':f"/forms34/{i['obj'].id}/blocos/16" if pronto else None})
            if sem_consenso(e):
                m=marco(i,sem_consenso);linhas['consenso'].append({**l,'desde':m,'dias':dias(m,agora)})
        else:
            posterior=decisao_posterior(e)
            if posterior and posterior['pendente'] and posterior['nota']['faixa'] in ('Alto','Crítico'):
                linhas['residuais_pos'].append({**l,'residual':posterior['nota']})
            if e.get('ciencia_prefeito'):
                linhas['ciencias'].append({**l,'situacao':'ciência registrada no sistema','desde':e['ciencia_prefeito']['em'],'prazo':e.get('prazo')})
            if e.get('faixa_origem')=='Crítico' and e.get('plano') and not e.get('plano_aprovado') and not e.get('cancelada'):
                m=marco(i,lambda s: bool(s.get('plano')) and not s.get('plano_aprovado') and not s.get('cancelada'))
                linhas['planos'].append({**l,'desde':m,'dias':dias(m,agora)})
    titulos={'criticos':'Riscos Críticos aguardando decisão do Prefeito','ciencias':'Segundas prorrogações: ciência registrada no sistema',
             'consenso':'Avaliações sem consenso aguardando o Comitê','instrucao':'Em instrução (DPO/Comitê)','planos':'Planos aguardando aprovação',
             'condicoes':'Aceitações condicionadas com condição em aberto','residuais_pos':'Riscos residuais Altos ou Críticos sem decisão após a providência','ripd_pendente':'RIPD indicado e não informado'}
    return [quadro(k,titulos[k],v,'providências' if k in ('ciencias','planos','residuais_pos') else 'riscos','Eventos da rodada atual',
                   'Ciência automática é informação, não pendência nem espera.' if k=='ciencias' else 'Somente fatos registrados.',
                   'Comitê' if k=='consenso' else 'Gabinete') for k,v in linhas.items() if k!='planos' or v]


def dias(inicio, agora):
    return max(0,(momento(agora).astimezone(LOCAL).date()-momento(inicio).astimezone(LOCAL).date()).days) if inicio else None


def correcao(d, agora):
    from app.dashboard.regras_a9 import condicoes_abertas
    linhas=[]
    for i in d['objetos']:
        if i['obj'].tipo!='A': continue
        e=i['estado']; l=linha(d,i['obj'].registro_id,i)
        risco_origem=next((r['estado'] for r in d['objetos'] if r['obj'].id==e.get('risco_id')), {})
        tipos=e.get('respostas',{}).get('F4-4.4',[])
        espera=marco(i,lambda s: bool(s.get('plano')) and not s.get('plano_aprovado') and not s.get('cancelada'))
        l.update(tipo_acao=', '.join(tipos) if isinstance(tipos,list) else tipos,
                 faixa_origem=e.get('faixa_origem'),condicao_aberta=bool(condicoes_abertas(d,risco_origem)),
                 espera_aprovacao=dias(espera,agora),desde=espera,dias=dias(espera,agora))
        aprovacao=next((ev for ev in i['eventos'] if ev.tipo_evento=='f34_aprovar_plano'),None)
        prorrogacoes=[]
        for ev in i['eventos']:
            s=ev.conteudo.get('estado',{})
            if ev.tipo_evento=='f34_decidir_prorrogacao' and s.get('prorrogacoes',0)>len(prorrogacoes):
                prorrogacoes.append(dict(numero=s['prorrogacoes'],em=ev.ocorrido_em,prazo=s.get('prazo'),
                    parecer=s.get('manifestacao_comite',{}).get('favoravel'),ciencia=bool(s.get('ciencia_prefeito'))))
        l.update(inicio=aprovacao.ocorrido_em if aprovacao else None,
            prazo_original=aprovacao.conteudo['estado'].get('prazo') if aprovacao else None,
            prazo=e.get('prazo'),prorrogacoes=prorrogacoes,atrasada=atrasada(e,momento(agora).astimezone(LOCAL).date()),
            fim=(e.get('cancelada') or (e.get('verificacao') if e.get('verificada') and e.get('verificacao',{}).get('aprovada') else {}) or {}).get('em'),
            dias_restantes=(date.fromisoformat(e['prazo'])-momento(agora).astimezone(LOCAL).date()).days if e.get('prazo') else None,
            encerrada=bool(e.get('cancelada') or e.get('verificada')),
            origem=next((f"Risco {r['obj'].numero}" for r in d['objetos'] if r['obj'].id==e.get('risco_id')),'FORM 2'),
            verificador='Comitê' if e.get('verificada') else 'Aguardando verificação')
        linhas.append(l)
    return [quadro('acoes','Providências acompanhadas',linhas,'providências','Eventos de plano, execução e verificação','Situações exclusivas; atraso é uma marca.'),
            quadro('atrasadas','Providências atrasadas',[l for l in linhas if l['atrasada']],'providências','Prazo vigente','Prazo anterior a hoje, sem verificação aprovada nem cancelamento.'),
            *[quadro('acao_'+str(n),t,[l for l in linhas if l['situacao']==t],'providências') for n,t in enumerate(F4)],
            indisponivel('incidentes','Incidentes','O painel ainda não recebe os registros de incidentes (previsto para depois de 15/12).')]


def esteira(d, filtros):
    acoes={r.id:[] for r in d['registros']};riscos={r.id:[] for r in d['registros']}
    for i in d['objetos']:(riscos if i['obj'].tipo=='R' else acoes)[i['obj'].registro_id].append(i['estado'])
    principais={p.registro_id:p for p in d['participacoes'] if p.tipo=='principal'}
    hist={a.registro_id:a for a in d['apresentacoes']}
    pendentes={p.registro_id for p in d['participacoes'] if any(c.participacao_id==p.id and c.estado!='resolvida' for c in d['complementos'])}
    grupos={n:[] for n in range(1,5)}
    for r in d['registros']:
        if riscos[r.id] or acoes[r.id]:
            for n,es,func,ordem in [(3,riscos[r.id],situacao_risco,F3),(4,acoes[r.id],situacao_acao,F4)]:
                if es: grupos[n].append({**linha(d,r.id),'situacao':min((func(e) for e in es),key=ordem.index)})
        elif r.id in principais:
            p=principais[r.id]
            grupos[2].append({**linha(d,r.id),'situacao':'Análise concluída' if (p.conteudo or {}).get('conclusao_analise') else 'Em análise'})
        else:
            h=hist.get(r.id)
            s='Aguardando complementação' if r.id in pendentes or h and h.devolvida_em else 'Confirmado' if h and h.confirmada_em else 'Em preenchimento'
            grupos[1].append({**linha(d,r.id),'situacao':s})
    return [indisponivel('form'+str(n),'FORM '+str(n),'Não se aplica: faixa de risco só existe a partir do FORM 3.') if filtros.get('faixa') and n<3
            else quadro('form'+str(n),'FORM '+str(n),v,fonte='Conferência, participação principal e eventos de ingresso',
                        regra='Etapa mais avançada; um Registro pode estar em riscos e providências ao mesmo tempo.') for n,v in grupos.items()]


def operacao(d, agora):
    filas={k:[] for k in ('Origem (ARP/APA)','AAL','Jurídico','DPO','Secretaria (FORMs 3 e 4)','Secretário','Comitê','Verificação (Comitê)','Gabinete')}
    abertas=[]
    def incluir(papel,l,inicio,motivo):
        filas[papel].append({**l,'desde':inicio,'dias':dias(inicio,agora),'situacao':motivo})
    from app.consultas_dpo import aguardando_dpo
    from app.dashboard.regras_a9 import secretaria_pendente
    for o in d.get('esperas_origem',[]):
        if o['registro_id'] in {r.id for r in d['registros']}:
            incluir('Origem (ARP/APA)',{**linha(d,o['registro_id']),'etapa':'FORM 1'},o['desde'],o['situacao'])
    for p in d['participacoes']:
        if p.tipo == 'dpo' and not aguardando_dpo(p): continue
        if p.concluida_em or p.estado=='concluida': continue
        papel={'principal':'AAL','tematica':'AAL','juridico':'Jurídico','dpo':'DPO'}[p.tipo]
        l={**linha(d,p.registro_id),'id':p.id,'item':'Participação '+('principal' if p.tipo=='principal' else p.tipo),'etapa':'FORM 2'}
        incluir(papel,l,p.entrada_em,'Análise em aberto');abertas.append(l)
    for i in d['objetos']:
        e=i['estado']; l={**linha(d,i['obj'].registro_id,i),'etapa':'FORM '+str(e['form'])}
        trabalho=secretaria_pendente(e)
        if trabalho:incluir('Secretaria (FORMs 3 e 4)',l,marco(i,lambda s: secretaria_pendente(s)==trabalho),trabalho)
        regras=[]
        if e['form']==3:
            regras=[('DPO','Confirmar proposta',lambda s: any(x.get(c) and 'dpo' not in x.get(c+'_confirmacoes',{}) and not x.get(c+'_sem_consenso')
                for x,c in [(s.get('reavaliacao') or s,'avaliacao'),(s,'triagem')])),
                ('DPO','Manifestação sobre risco',lambda s: conjunta(s) and nota(s).get('faixa') in ('Alto','Crítico') and not s.get('manifestacao_dpo')),
                ('Comitê','Deliberar sem consenso',sem_consenso),
                ('Comitê','Deliberar sobre o residual',lambda s: conjunta(s) and nota(s).get('faixa')=='Crítico' and not residual_comite(s) and not s.get('aceitacao')),
                ('Secretário','Decidir sobre o residual',lambda s: conjunta(s) and nota(s).get('faixa') in ('Pequeno','Moderado','Alto') and decisao(s)=='Aguardando decisão'),
                ('Gabinete','Registrar decisão sobre o residual',lambda s: conjunta(s) and nota(s).get('faixa')=='Crítico' and decisao(s)=='Aguardando decisão')]
        else:
            def cancelamento_exige_dpo(s):
                pedido=s.get('decisoes_pendentes',{}).get('cancelamento')
                return bool(pedido and s.get('faixa_origem') in ('Alto','Crítico') and
                    (not s.get('manifestacao_dpo') or momento(s['manifestacao_dpo']['em']) < momento(pedido['em'])))
            regras=[('Gabinete' if e.get('faixa_origem')=='Crítico' else 'Secretário','Aprovar plano',lambda s: bool(s.get('plano')) and not s.get('plano_aprovado') and not s.get('cancelada')),
                ('Verificação (Comitê)','Verificar execução',lambda s:situacao_acao(s)==F4[2]),
                ('Comitê','Manifestar-se sobre segunda prorrogação',lambda s:bool(s.get('decisoes_pendentes',{}).get('prorrogacao')) and s.get('prorrogacoes')==1 and s.get('manifestacao_comite',{}).get('finalidade')!='prorrogacao'),
                ('Secretário','Decidir prorrogação',lambda s:bool(s.get('decisoes_pendentes',{}).get('prorrogacao')) and (s.get('prorrogacoes',0)!=1 or s.get('manifestacao_comite',{}).get('finalidade')=='prorrogacao')),
                ('DPO','Manifestação sobre cancelamento',cancelamento_exige_dpo),
                ('Secretário','Decidir cancelamento',lambda s:bool(s.get('decisoes_pendentes',{}).get('cancelamento')) and not cancelamento_exige_dpo(s))]
        for papel,motivo,cond in regras:
            if cond(e): incluir(papel,l,marco(i,cond),motivo)
    quadros=[];todos={}
    for papel,linhas in filas.items():
        unicos={}
        for l in linhas:
            chave=l['registro'];todos.setdefault(chave,l)
            if chave not in unicos or (l['dias'] or 0)>(unicos[chave]['dias'] or 0):unicos[chave]=l
        esperas=[l['dias'] for l in unicos.values() if l['dias'] is not None]
        quadros.append(quadro('fila_'+papel,papel,list(unicos.values()),fonte='Participações e eventos que abrem/fecham a espera',
            regra='Registros distintos nesta fila; usa a espera mais antiga de cada Registro. Ciências automáticas não entram. Espera não é atraso.',papel=papel,
            detalhes=linhas,mediana=median(esperas) if esperas else None,maior=max(esperas) if esperas else None))
    return [quadro('esperando','Registros aguardando alguém',list(todos.values())),
            quadro('participacoes','Participações abertas',abertas,'participações'),*quadros]


def cobertura(d):
    linhas=[]; confirmados={a.registro_id for a in d['apresentacoes'] if a.confirmada_em}
    concluidos={p.registro_id for p in d['participacoes'] if p.tipo=='principal' and (p.conteudo or {}).get('conclusao_analise')}
    analise={p.registro_id for p in d['participacoes'] if p.tipo=='principal'}
    for u in d['secretarias']:
        rs=[r for r in d['registros'] if r.unidade_principal_atual_id==u.id]
        externos={p.registro_id for p in d['participacoes'] if p.unidade_id==u.id and p.registro_id not in {r.id for r in rs}}
        linhas.append(dict(id=u.id,registro='',secretaria=u.nome,tipo='',item='',situacao='',total=len(rs),
            servicos=sum(r.tipo_objeto=='servico' for r in rs),processos=sum(r.tipo_objeto=='processo' for r in rs),atividades=sum(r.tipo_objeto=='atividade' for r in rs),
            confirmados=[linha(d,r.id) for r in rs if r.id in confirmados],concluidos=[linha(d,r.id) for r in rs if r.id in concluidos],
            form1=[linha(d,r.id) for r in rs if r.id not in analise],em_analise=[linha(d,r.id) for r in rs if r.id in analise and r.id not in concluidos],
            registros=[linha(d,r.id) for r in rs],externos=[linha(d,rid) for rid in sorted(externos)]))
    linhas.sort(key=lambda l:(-l['total'],l['secretaria']))
    return [quadro('secretarias','Secretarias com pelo menos um Registro',[l for l in linhas if l['total']],'Secretarias',
                   'De onde vem: Secretarias ativas da tabela-mestre com pelo menos um Registro no seu escopo.','Quantidades; percentual depende de inventário de referência aprovado.',total_ativas=len(linhas)),
            quadro('cobertura','Secretarias ativas',linhas,'Secretarias')]


def aprendizados(d):
    linhas=[]
    for i in d['objetos']:
        if i['obj'].tipo!='A':continue
        # A versão mais recente autorizada permanece consultável durante nova proposta.
        ultimo=None
        for ev in i['eventos']:
            e=ev.conteudo.get('estado',{})
            a=e.get('aprendizagem');c=e.get('aprendizagem_conferida');p=e.get('aprendizagem_autorizada')
            if a and c and p and e.get('verificada') and e.get('verificacao',{}).get('aprovada'):
                ultimo=e
        if ultimo:
            a=ultimo['aprendizagem'];p=ultimo['aprendizagem_autorizada']
            linhas.append({**linha(d,i['obj'].registro_id,i),'contexto':a.get('contexto') or 'Contexto não informado',
                'diretriz':a['diretriz'],'limites':a['escopo'],'autorizado':p['em'],'verificado':ultimo['verificacao']['em']})
    return [quadro('aprendizados','Aprendizados autorizados para consulta',linhas,'aprendizados',
        'Verificação, conferência do DPO e autorização da Secretaria','Última versão autorizada; não exibe evidências.','Secretaria e DPO')]


def circulacao(d, categorias):
    if categorias is None:
        return [indisponivel('circulacao','Circulação de dados','Não disponível: fonte categórica não carregada ou íntegra.')]
    resultado=[]; categorias_ordenadas=sorted({c for v in categorias.values() for c in v['categorias']})
    for nu,u in enumerate(d['secretarias']):
        for nc,categoria in enumerate(categorias_ordenadas):
            lista=[linha(d,r.id) for r in d['registros'] if r.unidade_principal_atual_id==u.id and categoria in categorias.get(r.id,{}).get('categorias',set())]
            resultado.append(quadro(f'circulacao_{nu}_{nc}',u.nome+' · '+categoria,lista,
                fonte='F1-10.2 e F2-8.1/8.2',regra='Registros que declaram o tipo; não conta relações, empresas ou contratos distintos.',secretaria=u.nome,categoria=categoria))
    for k,rotulo in enumerate(('Sim','Não','A confirmar','Sem resposta','Ainda não chegou a esta pergunta')):
        def corresponde(r):
            v=categorias.get(r.id,{})
            if not v.get('pergunta_ativa',True):return False
            if rotulo=='Ainda não chegou a esta pergunta':return not v.get('bloco8_salvo',bool(v.get('instrumentos')))
            if rotulo=='Sem resposta':return v.get('bloco8_salvo',False) and not v.get('instrumentos')
            return rotulo in v.get('instrumentos',set())
        lista=[linha(d,r.id) for r in d['registros'] if corresponde(r)]
        resultado.append(quadro('instrumento_'+str(k),'Instrumento formal: '+rotulo,lista,fonte='F2-8.7',
            regra='Sem salvamento do bloco 8: Ainda não chegou a esta pergunta. Bloco 8 salvo com pergunta ativa e vazia: Sem resposta. Condicional fechada fica fora dessas contagens. Fornecedores e operadores do bloco 9 não entram nesta conta. Declaração estruturada, sem avaliação de cláusulas.'))
    resultado.insert(0,quadro('circulacao','Registros com destinatários declarados',[linha(d,r.id) for r in d['registros'] if categorias.get(r.id,{}).get('categorias')],
        fonte='Categorias estruturadas do FORM 1 e FORM 2',regra='Não contamos relações, empresas ou contratos distintos, nem avaliamos cláusulas.'))
    return resultado
