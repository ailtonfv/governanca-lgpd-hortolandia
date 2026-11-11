"""Rascunho candidato versionado. Catálogo fornecido pela instalação privada."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from uuid import uuid4
import json

VERSAO = 'F1-C3-REV22-CANDIDATA-v1'
LACRE = '064216ae5a32bb189caea3f125ad8405314cbca12eac72a3679995f00b48a9c3'
NOVOS = ('2.1.1', '3.4.2', '4.1.1', '4.1.2', '12.1.4')
EQUIVALENCIA = dict(zip(('8.7','8.8','8.8.1','8.9'), ('WPP.1','WPP.2','WPP.3','WPP.4')))

def pre_validar(conteudo):
    """Consulta candidata; não presume uma nova matriz de obrigatoriedade."""
    avisos=[];respostas=conteudo.get('respostas',{})
    for k,q in definicoes().items():
        if q['block']==0:continue
        if ativa(k,respostas) and not respostas.get(k) and q['block'] not in (3,10):
            avisos.append({'campo_id':k,'bloco':str(q['block']),'tipo':'aviso','pergunta':q['question'],
                'detalhe':'Sem resposta no rascunho candidato. Não equivale a Não ou Não se aplica.'})
    pendentes=[{'tipo':'governanca','detalhe':'Matriz de obrigatoriedade REV22 e conclusão institucional pendentes de deliberação.'}]
    return dict(consultiva=True,submissao_habilitada=False,versao_politica='REV22-CANDIDATA',
        matriz_base='REV22-PENDENTE',versao_estrutura=VERSAO,matriz_extensao=None,matriz_guarda=None,
        incompletos=[],nao_aplicaveis=[],regras_pendentes=pendentes,avisos=avisos,por_bloco=[],
        quantidades={'avisos':len(avisos),'incompletos':0,'nao_aplicaveis':0,'regras_pendentes':1})

def definicoes():
    raw=(Path(__file__).parent/'catalogos/form1_rev22_privado.json').read_bytes()
    if sha256(raw).hexdigest()!=LACRE: raise ValueError('Catálogo privado REV22 divergente.')
    return {q['id']:q for q in json.loads(raw)['items']}

def catalogo():
    from app.form1_integral import CampoForm1Integral
    tipos={'multi':'seleção múltipla (combo com marcações)', 'single':'seleção única (combo)', 'unit':'seleção única (combo)', 'text':'texto curto'}
    return {k:CampoForm1Integral(k, f"BLOCO {q['block']} — {q['title']}", q['question'],tipos[q['kind']],tuple(q['options']),q['help']) for k,q in definicoes().items()}

def respostas_conjuntos(conteudo):
    defs=definicoes();itens=[]
    for bloco,rows in conteudo.get('conjuntos_rev22',{}).items():
        for indice,row in enumerate(rows,1):
            for k,v in row.get('respostas',{}).items():
                if k in defs:
                    itens.append({'id':k,'pergunta':defs[k]['question'], 'valor':deepcopy(v),
                        'respondida':True,'conjunto':indice,'conjunto_id':row['id']})
    return itens

def ativa(key, respostas):
    q=definicoes()[key]
    def tem(k, choices):
        v=respostas.get(k,[]); v=v if isinstance(v,list) else [v]
        return any(x in choices for x in v)
    canais=[]
    for k in ('2.1','2.1.1','8.3'):
        v=respostas.get(k,[]);canais.extend(v if isinstance(v,list) else [v])
    if key.startswith('WPP.') and not any('WhatsApp' in x for x in canais if isinstance(x,str)):return False
    if key.startswith('OUV.') and 'Ouvidoria' not in canais:return False
    if key.startswith('ESIC.') and 'e-SIC' not in canais:return False
    if key.startswith('3.') and key!='3.1' and not tem('3.1',('Sim',)):return False
    if key.startswith('10.') and key!='10.1' and not tem('10.1',('Sim','Em alguns casos')):return False
    if key in ('13.3','13.4') and not any(x not in ('A confirmar','Não se aplica','Nenhuma das situações acima') for x in respostas.get('13.1',[])):return False
    conditions=q['conditions']
    if key.startswith(('OUV.','ESIC.')):
        conditions=[c for c in conditions if isinstance(c,(list,tuple)) and c[0]!='2.1'] if conditions and not isinstance(conditions[0],str) else []
    if conditions and isinstance(conditions[0],str):conditions=[conditions]
    return all(tem(k,choices) and (k==key or ativa(k,respostas)) for k,choices in conditions)

def validar(q,v):
    if v in (None,'',[]):return None
    if q['kind']=='multi':
        if not isinstance(v,list) or not all(isinstance(x,str) for x in v):raise ValueError('Seleção múltipla inválida.')
        if len(set(v))!=len(v) or not set(v)<=set(q['options']):raise ValueError('Alternativa desconhecida ou repetida.')
        especiais={'A confirmar','Não se aplica','Nenhum outro canal','Nenhuma identificada','Nenhuma das situações acima','Faixa etária não registrada'}
        if len(v)>1 and especiais.intersection(v):raise ValueError('Alternativa exclusiva combinada com outra.')
    elif not isinstance(v,str) or '\x00' in v or len(v)>2000:raise ValueError('Texto inválido ou maior que 2.000 caracteres.')
    elif q['kind']=='single' and v not in q['options']:raise ValueError('Alternativa desconhecida.')
    if q['id']=='12.1.1' and not v.isdigit():raise ValueError('Informe apenas o número do prazo.')
    return v.strip() if isinstance(v,str) else v

def migrar(conteudo, catalogo_anterior):
    """Copia somente valores semanticamente compatíveis; nunca altera snapshot."""
    novo=deepcopy(conteudo); old=deepcopy(conteudo.get('respostas',{}));dest={};legado={};defs=definicoes()
    for key,value in old.items():
        target=EQUIVALENCIA.get(key,key)
        # 4.1 mudou de categorias compostas para papel. Bloco 10 agora é por destinatário.
        if target not in defs or key=='4.1' or (key.startswith('10.') and key!='10.1'):
            legado[key]=value;continue
        q=defs[target]
        anterior=catalogo_anterior.get(key)
        if anterior and q['kind'] in ('single','multi') and not set(anterior.alternativas)<=set(q['options']):
            legado[key]=value;continue
        try:dest[target]=validar(q,value)
        except (ValueError,TypeError):legado[key]=value
    for key in NOVOS:dest.pop(key,None)
    novo['respostas']={k:v for k,v in dest.items() if v is not None}
    novo['revisao_22']={'versao':VERSAO,'catalogo_sha256':LACRE,'legado':legado,
        'complementos_anteriores':deepcopy(conteudo.get('complementos',{})),
        'participantes_anteriores':deepcopy(conteudo.get('participantes',[])),
        'destinatarios_anteriores':deepcopy(conteudo.get('destinatarios_10_2_1',[])),
        'novos_sem_resposta':list(NOVOS),'equivalencia':EQUIVALENCIA}
    # Conjuntos antigos continuam no retrato anterior e no histórico da adoção.
    novo['participantes']=[];novo['destinatarios_10_2_1']=[];novo['complementos']={}
    novo['conjuntos_rev22']={'3':[],'10':[]}
    return novo

def _preparar(sessao, parametros, tipo):
    from app.rascunho_form1_integral import _preparar_alteracao,_negar,_lacre
    from app.modelos import ConferenciaInternaForm1Integral
    registro,pessoa,rascunho,cmd,resposta=_preparar_alteracao(sessao,comando_id=parametros['comando_id'],tipo_comando=tipo,conta_id=parametros['conta_id'],registro_id=parametros['registro_id'],versao_lida=parametros['versao_lida'],parametros=parametros)
    if resposta is not None:return registro,pessoa,rascunho,cmd,resposta
    if registro.estado_atual!='em_andamento' or sessao.get(ConferenciaInternaForm1Integral,registro.id) or _lacre(rascunho.conteudo)!=rascunho.lacre_conteudo:
        return registro,pessoa,rascunho,cmd,_negar(sessao,cmd,cmd.ator_tipo,cmd.ator_id,parametros['conta_id'],registro.id,tipo,'Rascunho indisponível, em conferência ou com integridade divergente.')
    return registro,pessoa,rascunho,cmd,None

def _gravar(sessao,registro,pessoa,r,cmd,params,novo,tipo,detalhes,ordem=1):
    from app.rascunho_form1_integral import _salvar_conteudo,_agora_utc
    from app.eventos import registrar_auditoria
    result=_salvar_conteudo(sessao,comando=cmd,registro=registro,rascunho=r,pessoa_id=pessoa,versao_lida=params['versao_lida'],conteudo=novo,tipo_evento=tipo,motivo='Rascunho candidato REV22 salvo.',detalhes={**detalhes,'conteudo_rev22':deepcopy(novo)},momento=_agora_utc(),ordem_no_comando=ordem)
    registrar_auditoria(sessao,tipo,cmd.ator_tipo,cmd.ator_id,{'registro_id':registro.id,**detalhes},comando_id=cmd.id)
    return result

def adotar(sessao, *, comando_id,conta_id,registro_id,versao_lida,confirmar):
    params=dict(comando_id=comando_id,conta_id=conta_id,registro_id=registro_id,versao_lida=versao_lida,confirmar=confirmar)
    reg,pessoa,r,cmd,res=_preparar(sessao,params,'adotar_rev22_form1')
    if res is not None:return res
    if confirmar is not True or 'revisao_22' in r.conteudo:raise ValueError('Confirme a adoção em um rascunho anterior à REV22.')
    from app.submissao_form1_integral import preparar_snapshot_na_transacao
    from app.extensao_medidas_form1 import catalogo_efetivo
    from app.rascunho_form1_integral import _agora_utc
    snap,ev=preparar_snapshot_na_transacao(sessao,comando=cmd,registro=reg,rascunho=r,pessoa_id=pessoa,momento=_agora_utc(),reusar_existente=True)
    novo=migrar(r.conteudo,catalogo_efetivo(r.conteudo))
    novo['revisao_22'].update(snapshot_anterior_id=snap.id,lacre_anterior=snap.lacre,adotada_por=pessoa)
    return _gravar(sessao,reg,pessoa,r,cmd,params,novo,'adotar_rev22_form1',{'snapshot_anterior_id':snap.id},2 if ev else 1)

def salvar(sessao, *, comando_id,conta_id,registro_id,versao_lida,bloco,respostas,conjunto=None,complementos=None):
    params=dict(comando_id=comando_id,conta_id=conta_id,registro_id=registro_id,versao_lida=versao_lida,bloco=bloco,respostas=respostas,conjunto=conjunto,complementos=complementos)
    reg,pessoa,r,cmd,res=_preparar(sessao,params,'salvar_bloco_rev22_form1')
    if res is not None:return res
    if 'revisao_22' not in r.conteudo or not 1<=bloco<=14:raise ValueError('Estrutura ou bloco incompatível.')
    defs=definicoes();novo=deepcopy(r.conteudo);valores=novo.setdefault('respostas',{})
    fields={k:q for k,q in defs.items() if q['block']==bloco}
    repetidos=bloco in (3,10) and conjunto is not None
    if repetidos:
        if not isinstance(conjunto,int) or not 1<=conjunto<=100:raise ValueError('Conjunto inválido.')
        rows=novo.setdefault('conjuntos_rev22',{}).setdefault(str(bloco),[])
        if conjunto>len(rows)+1:raise ValueError('Conjunto fora de sequência.')
        if conjunto==len(rows)+1:rows.append({'id':str(uuid4()),'respostas':{},'complementos':{}})
        target=rows[conjunto-1];values=target['respostas'];fields.pop(f'{bloco}.1',None)
    else:
        if bloco in (3,10):fields={f'{bloco}.1':fields[f'{bloco}.1']}
        target=novo;values=valores
    if not isinstance(respostas,dict) or not set(respostas)<=set(fields):raise ValueError('Campo fora do bloco.')
    validated={k:validar(fields[k],v) for k,v in respostas.items()}
    merged={**valores,**values,**validated}
    for key,v in validated.items():
        if v is not None and not ativa(key,merged):raise ValueError(f'F1-{key}: salve a pergunta de origem antes de responder este campo.')
        if fields[key]['kind']=='unit' and v:
            from app.modelos import Unidade
            unit=sessao.get(Unidade,v)
            if not unit or not unit.ativa or unit.id=='UNID-GOV':raise ValueError('Unidade fora da tabela-mestre ativa.')
        if v is None:values.pop(key,None)
        else:values[key]=v
    if valores.get('2.1') in valores.get('2.1.1',[]):raise ValueError('O canal principal não deve se repetir nos adicionais.')
    if valores.get('8.1') in ('Físico','Digital'):
        fisicos={'Processo administrativo físico','Arquivo físico da unidade'}
        chosen=valores.get('8.2',[])
        if any(v!='A confirmar' and ((v in fisicos)!=(valores['8.1']=='Físico')) for v in chosen):raise ValueError('Ambientes incompatíveis com o meio informado em F1-8.1.')
    extras=target.setdefault('complementos',{})
    for key,value in (complementos or {}).items():
        if key not in fields or not isinstance(value,str) or len(value)>1000 or '\x00' in value:raise ValueError('Complemento inválido.')
        if value.strip():extras[key]=value.strip()
        else:extras.pop(key,None)
    # Respostas que saem de aplicabilidade ficam no histórico, sem reativação implícita.
    archive=novo.setdefault('inativas_rev22',[])
    groups=[(valores,novo.get('complementos',{}),None)]
    for b,rows in novo.get('conjuntos_rev22',{}).items():groups += [(row['respostas'],row.get('complementos',{}),row['id']) for row in rows]
    for answers,extras,cid in groups:
        context={**valores,**answers}
        for key in list(answers):
            if key in defs and not ativa(key,context):archive.append({'id':key,'valor':answers.pop(key),'complemento':extras.pop(key,None),'conjunto':cid,'versao':versao_lida+1})
    return _gravar(sessao,reg,pessoa,r,cmd,params,novo,'salvar_bloco_rev22_form1',{'bloco':bloco,'conjunto':conjunto})
