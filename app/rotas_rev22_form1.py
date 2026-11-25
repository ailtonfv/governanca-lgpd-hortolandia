"""Edição candidata com adoção explícita e histórico preservado."""
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.banco import motor
from app.continuidade_apa import conferente_da_apresentacao, unidades_em_que_e_apa_atual
from app.modelos import ParticipacaoForm2,Registro,RascunhoForm1Integral,Unidade,ConferenciaInternaForm1Integral
from app.consultas_interface import _identidade, _ids_visiveis
from app.rascunho_form1_integral import _contexto_autorizado
from app.rev22_form1 import definicoes, ativa, adotar, salvar
from app.cartilha_local import acesso_local_cartilha, secoes_cartilha_disponiveis
from app.ajudas_cartilha_form1 import VERSAO_CARTILHA_AJUDAS_FORM1

router=APIRouter()
paginas=Jinja2Templates(directory=Path(__file__).parent/'paginas')
from app.identidade_demonstrativa import configurar_identidade
configurar_identidade(paginas)
paginas.env.globals['consulta_cartilha_local'] = acesso_local_cartilha
def sessao_rev22():
    with Session(motor) as s:yield s

@router.get('/registros/{registro_id}/form1-rev22')
def pagina(request:Request,registro_id:str,conta_id:str,bloco:int=1,conjunto:int=1,sessao:Session=Depends(sessao_rev22)):
    identidade=_identidade(sessao,conta_id,vinculos_vigentes=True)
    if not identidade or registro_id not in _ids_visiveis(sessao,identidade):raise HTTPException(403,'Registro fora do seu acesso.')
    if not 1<=bloco<=14 or not 1<=conjunto<=100:raise HTTPException(400,'Bloco ou conjunto inválido.')
    r=sessao.get(RascunhoForm1Integral,registro_id)
    if not r:return RedirectResponse('/registros/'+registro_id+'?'+urlencode({'conta_id':conta_id})+'#titulo-proxima-providencia',status_code=303)
    reg=sessao.get(Registro,registro_id)
    pode=_contexto_autorizado(sessao,conta_id,registro_id)[-1] is None and reg.estado_atual=='em_andamento'
    conferencia=sessao.get(ConferenciaInternaForm1Integral,registro_id)
    conferente = conferente_da_apresentacao(sessao, reg, conferencia)
    pode=pode and conferencia is None
    from app.eventos import registrar_auditoria
    registrar_auditoria(sessao,'consulta_form1_rev22','pessoa',identidade['pessoa_id'],{'registro_id':registro_id,'bloco':bloco})
    sessao.commit()
    conteudo=r.conteudo;adotada='revisao_22' in conteudo
    atualizada=False
    if not adotada and pode:
        tinha_respostas=any(v not in (None,'',[]) for k,v in conteudo.get('respostas',{}).items() if k not in ('1.2','1.3'))
        resultado=adotar(sessao,comando_id=str(uuid4()),conta_id=conta_id,registro_id=registro_id,versao_lida=r.versao_rascunho,confirmar=True)
        if not resultado['permitido']: raise HTTPException(409,resultado['motivo'])
        sessao.commit()
        conteudo=r.conteudo;adotada=True;atualizada=tinha_respostas

    historico=None
    if adotada:
        from app.origem_form2 import ler_origem
        historico=ler_origem(sessao,registro_id,conteudo['revisao_22']['snapshot_anterior_id'])
    rows=conteudo.get('conjuntos_rev22',{}).get(str(bloco),[])
    if conjunto>len(rows)+1:raise HTTPException(400,'Conjunto fora de sequência.')
    valores=conteudo.get('respostas',{})
    row=rows[conjunto-1] if conjunto<=len(rows) else {'respostas':{},'complementos':{}}
    contexto={**valores,**row['respostas']}
    defs=definicoes()
    from app.rev22_form1 import blocos_com_respostas, contagem_blocos, condicoes_tela, orientacao_condicional
    from app.ajudas_cartilha_form1 import ajudas_rev22
    from app.consultas_interface import _devolucao_para_interface
    respondidos = blocos_com_respostas(conteudo)
    campos=[q for q in defs.values() if q['block']==bloco]
    for q in campos:
        q['repetida']=bloco in (3,10) and q['id']!=f'{bloco}.1'
        origem=row if q['repetida'] else conteudo
        q['valor']=origem.get('respostas',{}).get(q['id'])
        q['complemento']=origem.get('complementos',{}).get(q['id'],'')
        q['ativa']=ativa(q['id'],contexto)
        q['orientacao_condicional']=orientacao_condicional(q['id'])
        q.update(ajudas_rev22(q['id'],secoes_cartilha_disponiveis()))
    if historico:
        historico['perguntas']=[p for p in historico['perguntas'] if p['id'] in defs and defs[p['id']]['block']==bloco]
        historico['conteudo']={k:v for k,v in historico.get('conteudo',{}).items() if (k=='participantes' and bloco==3) or (k=='destinatarios_10_2_1' and bloco==10)}
    return paginas.TemplateResponse(request=request,name='form1_rev22.html',context=dict(
        pode_definir_retorno=reg.unidade_principal_atual_id in unidades_em_que_e_apa_atual(sessao,identidade["pessoa_id"]),
        atualizada=atualizada, contagens=contagem_blocos(conteudo), condicoes=condicoes_tela(), contexto_condicoes=contexto,
        retirada_antiga=bool(conteudo.get('revisao_22',{}).get('legado',{}).get('9.2.1')),
        orientacao_levantamento=acesso_local_cartilha(request) and "levantamento" in secoes_cartilha_disponiveis(),
        edicao_cartilha=VERSAO_CARTILHA_AJUDAS_FORM1,
        salvamento_confirmado=request.query_params.get("salvo") == str(r.versao_rascunho),
        e_apa=identidade["pessoa_id"] == conferente, falta_conferente=conferencia and not conferente,
        registro=reg,r=r,identidade=identidade,conta_id=conta_id,bloco=bloco,conjunto=conjunto,
        devolucao=_devolucao_para_interface(sessao, registro_id),
        encaminhado=bool(sessao.scalar(select(ParticipacaoForm2.id).where(ParticipacaoForm2.registro_id==registro_id).limit(1))),
        historico=historico,respondidos=respondidos,conferencia=conferencia,quantidade_conjuntos=len(rows),campos=campos,metadados=[q for q in defs.values() if q['block']==0],pode=pode,adotada=adotada,comando_id=str(uuid4()),
        unidades=sessao.scalars(select(Unidade).where(Unidade.ativa.is_(True),Unidade.id!='UNID-GOV').order_by(Unidade.nome)).all()))

@router.post('/registros/{registro_id}/form1-rev22')
async def gravar(request:Request,registro_id:str,sessao:Session=Depends(sessao_rev22)):
    d=await request.form();conta=d.get('conta_id','');conjunto=d.get('conjunto')
    try:
        bloco=int(d.get('bloco','1'))
        args=dict(conta_id=conta,registro_id=registro_id,comando_id=d.get('comando_id'),versao_lida=int(d.get('versao','0')))
    except (ValueError,TypeError):
        raise HTTPException(400,'Bloco ou versão inválidos.')
    try:
        if d.get('acao')=='adotar':resultado=adotar(sessao,**args,confirmar=d.get('confirmar')=='sim')
        elif d.get('acao')=='conferir':
            from app.conferencia_interna_form1_integral import solicitar_conferencia_interna_form1_integral
            resultado=solicitar_conferencia_interna_form1_integral(sessao,**args)
        else:
            defs=definicoes();respostas={};complementos={}
            for key in d:
                if key.startswith('r:'):
                    id=key[2:]
                    if id not in defs:raise ValueError('Campo desconhecido.')
                    vs=[v for v in d.getlist(key) if v]
                    respostas[id]=vs if defs[id]['kind']=='multi' else (vs[0] if len(vs)==1 else None)
                    if defs[id]['kind']!='multi' and len(vs)>1:raise ValueError('Resposta única repetida.')
                elif key.startswith('c:'):complementos[key[2:]]=d[key]
            resultado=salvar(sessao,**args,bloco=bloco,respostas=respostas,complementos=complementos,conjunto=int(conjunto) if conjunto else None)
        if not resultado['permitido']:raise ValueError(resultado['motivo'])
        sessao.commit()
    except (ValueError,PermissionError) as e:
        sessao.rollback();raise HTTPException(409,str(e))
    destino=dict(conta_id=conta,bloco=bloco,conjunto=conjunto or 1)
    if d.get('acao') not in ('adotar','conferir'):
        destino['salvo']=sessao.get(RascunhoForm1Integral,registro_id).versao_rascunho
    return RedirectResponse('/registros/'+registro_id+'/form1-rev22?'+urlencode(destino),status_code=303)
