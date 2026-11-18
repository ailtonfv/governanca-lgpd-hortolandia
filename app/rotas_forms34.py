"""Interface demonstrativa; sem migração no startup ou no GET."""
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlencode
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.banco import motor
from app.modelos import (IdentidadeForms34, ReferenciaParticipacaoForms34, Registro, Pessoa,
                         Conta, Unidade, ParticipacaoForm2, Evento)
from app import fluxo_forms34 as dominio
from app.permissoes_forms34 import contexto
from app.fila_form2 import pessoa_ativa, autorizado, unidades
from app.questionario_forms34 import perguntas, grade, ativa, recolhida
from app.atos_forms34_interface import disponiveis, interpretar
from app.identidade_demonstrativa import configurar_identidade
from app.atos_interface import ato_registrado
from app.eventos import registrar_auditoria
from app.apresentacao_form2 import data_local

MODELO_RIPD=Path(__file__).resolve().parents[1]/'docs/modelos/MODELO_MUNICIPAL_RIPD_PROPOSTA.md'

router=APIRouter()
paginas=Jinja2Templates(directory=Path(__file__).parent/'paginas')
configurar_identidade(paginas)
paginas.env.filters['hora_local']=data_local


def url_objeto(obj,conta,bloco=1,**extra):
    return f'/forms34/{obj}/blocos/{bloco}?'+urlencode(dict(conta_id=conta,**extra))


def erro(request,conta,e,status=409,retorno='/forms34'):
    return paginas.TemplateResponse(request=request,name='forms34_erro.html',status_code=status,
        context={'conta_id':conta,'erro':str(e),'retorno':retorno})


@router.get('/forms34')
def lista(request:Request,conta_id:str):
    with Session(motor) as s:
        pessoa=pessoa_ativa(s,conta_id)
        visiveis=[]
        referencias=[]
        from app.restrito_forms34 import pode_ler
        for obj in s.scalars(select(IdentidadeForms34).order_by(IdentidadeForms34.codigo)):
            try:
                _,ref,e,_,papeis,_=dominio.consultar(s,conta_id,obj.id)
                visiveis.append(dict(obj=obj,estado=e,registro=s.get(Registro,obj.registro_id)))
            except (ValueError,PermissionError):
                try:
                    if pode_ler(s,conta_id,obj.id,dominio.estado(s,obj.id)):
                        referencias.append(dict(id=obj.id,codigo=obj.codigo,registro=s.get(Registro,obj.registro_id).codigo_lgpd))
                except (ValueError,PermissionError):pass
                continue
        contas=s.execute(select(Conta,Pessoa).join(Pessoa,Conta.pessoa_id==Pessoa.id)
            .where(Conta.ativa.is_(True),Pessoa.ativa.is_(True))).all()
        return paginas.TemplateResponse(request=request,name='forms34_lista.html',context={
            'conta_id':conta_id,'pessoa':pessoa,'objetos':visiveis,'referencias':referencias,'contas':contas})


@router.api_route('/form2/participacoes/{pid}/encaminhar34',methods=['GET','POST'])
async def ingresso(request:Request,pid:str,conta_id:str):
    with Session(motor) as s:
        pessoa=pessoa_ativa(s,conta_id)
        p=s.get(ParticipacaoForm2,pid)
        if not p or p.responsavel_id!=pessoa.id or p.tipo!='principal' or not autorizado(s,pessoa,p):
            return erro(request,conta_id,'Somente o AAL responsável encaminha.',403)
        if request.method=='POST':
            d=await request.form()
            try:
                r=dominio.ingressar(s,conta_id=conta_id,comando_id=d.get('comando_id'),participacao_id=pid,
                    versao=int(d.get('versao','0')),form=int(d.get('form','0')),justificativa=d.get('justificativa',''))
                if not r.get('permitido'):raise ValueError(r.get('motivo'))
                s.commit()
                return RedirectResponse(url_objeto(r['identidade_id'],conta_id,registrado=d.get('comando_id')),303)
            except (ValueError,PermissionError) as e:
                s.rollback();return erro(request,conta_id,e,403 if isinstance(e,PermissionError) else 409,
                    f'/form2/participacoes/{pid}/encaminhar34')
        return paginas.TemplateResponse(request=request,name='forms34_ingresso.html',context={
            'p':p,'registro':s.get(Registro,p.registro_id),'pessoa':pessoa,'conta_id':conta_id,'comando_id':str(uuid4())})


def escolhas(s,ref,papeis,uid):
    r={'unidade':[(u.id,u.nome) for u in s.scalars(select(Unidade).where(Unidade.ativa.is_(True)))],
       'juridico':[],'executor':[],'autoridade':[]}
    for p in s.scalars(select(Pessoa).where(Pessoa.ativa.is_(True))):
        if unidades(s,p.id,'juridico_form2'):r['juridico'].append((p.id,p.nome))
        if (uid in unidades(s,p.id,'preenchedor')|unidades(s,p.id,'aal_form2')
                and not unidades(s,p.id,'governanca_protecao_dados')):
            r['executor'].append((p.id,p.nome))
        if uid in unidades(s,p.id,'demo34_secretario') or unidades(s,p.id,'demo34_prefeito'):
            r['autoridade'].append((p.id,p.nome))
    return r


@router.api_route('/forms34/{objeto_id}/blocos/{bloco}',methods=['GET','POST'])
async def bloco(request:Request,objeto_id:str,bloco:int,conta_id:str):
    with Session(motor) as s:
        try:obj,ref,e,pessoa,papeis,uid=dominio.consultar(s,conta_id,objeto_id)
        except (PermissionError,ValueError) as exc:return erro(request,conta_id,exc,403)
        if not 1<=bloco<=(16 if ref.form==3 else 9):raise HTTPException(404,'Bloco inexistente.')
        if request.method=='POST':
            d=await request.form();acao=d.get('acao','salvar_bloco')
            try:
                if acao=='salvar_bloco':
                    campos={}
                    for q in perguntas(ref.form):
                        if q['bloco']!=bloco or (q['id'] not in d and 'presente:'+q['id'] not in d):continue
                        campos[q['id']]=d.getlist(q['id']) if q['tipo']=='multi' else d[q['id']]
                    # Também recusar campos editoriais forjados de outro bloco/fora do catálogo.
                    for k in d:
                        if k.startswith(('F3-','F4-')) and k not in campos:campos[k]=d[k]
                    dados=dict(bloco=bloco,campos=campos)
                elif acao=='abrir_detalhes':dados=dict(bloco=bloco,motivo=d.get('motivo',''))
                else:dados=interpretar(acao,d)
                r=dominio.executar(s,conta_id=conta_id,comando_id=d.get('comando_id'),identidade_id=obj.id,
                                  versao=int(d.get('versao','0')),acao=acao,dados=dados)
                if not r.get('permitido'):raise ValueError(r.get('motivo'))
                s.commit()
                return RedirectResponse(url_objeto(r['identidade_id'],conta_id,bloco if r['identidade_id']==obj.id else 1,registrado=d.get('comando_id')),303)
            except (ValueError,PermissionError,KeyError) as exc:
                s.rollback();return erro(request,conta_id,exc,403 if isinstance(exc,PermissionError) else 409,
                                           f'/forms34/{obj.id}/blocos/{bloco}')
        try:itens=[dict(q,ativa=ativa(q,e['respostas'],e),recolhida=recolhida(q,e['respostas'],e))
                   for q in perguntas(ref.form) if q['bloco']==bloco]
        except (FileNotFoundError,ValueError) as exc:return erro(request,conta_id,exc,503)
        origem=s.get(ParticipacaoForm2,e.get('origem_form2_id'))
        atos=disponiveis(ref.form,bloco,papeis)
        for a in atos:a['comando_id']=str(uuid4())
        registro=s.get(Registro,obj.registro_id)
        valores = {'F3-3.1':registro.codigo_lgpd,'F4-4.1':registro.codigo_lgpd,
                   'F4-4.1.1':obj.codigo,'F3-3.2':s.get(Unidade,uid).nome,
                   'F3-3.3':e.get('situacao_form2','Não informado'),
                   'F4-4.15':e['situacao'],'F4-4.10':e.get('prazo') or 'Prazo não definido',
                   'F4-4.23':e.get('faixa_origem','Não avaliado'),
                   'F4-4.24':'Aceitação pendente de autoridade competente',
                   'F3-3.52.5':'Aceitação registrada' if e.get('aceitacao') else 'Pendente de autoridade competente'}
        if e.get('avaliacao'):
            for ident, tipo, chave in [('F3-3.49','inerente','probabilidade'),('F3-3.50','inerente','impacto'),
                    ('F3-3.51','inerente','nota'),('F3-3.52.1','residual','probabilidade'),
                    ('F3-3.52.2','residual','impacto'),('F3-3.52.3','residual','nota')]:
                valores[ident] = e['avaliacao'][tipo][chave] if e['avaliacao'][tipo][chave] is not None else 'Não avaliado'
        from app.atos_forms34_interface import ATOS
        ato=ato_registrado(s,request.query_params.get('registrado'),conta_id,registro_id=registro.id,participacao_id=obj.id)
        from app.restrito_forms34 import pode_ler
        return paginas.TemplateResponse(request=request,name='forms34_bloco.html',context={
            'obj':obj,'ref':ref,'estado':e,'pessoa':pessoa,'papeis':papeis,'registro':registro,
            'conta_id':conta_id,'bloco':bloco,'itens':itens,'grade':grade(ref.form,e['respostas'],e),
            'atos':atos,'escolhas':escolhas(s,ref,papeis,uid),'comando_id':str(uuid4()),'ato':ato,
            'valores':valores,'autores':{p.id:p.nome for p in s.scalars(select(Pessoa))},
            'rotulos_atos':{'f34_'+k:v[3] for k,v in ATOS.items()},
            'atraso':dominio.em_atraso(e),'origem_nova':bool(origem and origem.versao!=ref.fonte_versao),
            'pode_restrito':pode_ler(s,conta_id,obj.id,e),
            'papeis_visiveis':[{'secretaria':'Secretaria — preenchimento','aal':'AAL','dpo':'Encarregado de Dados (DPO)','secretario':'Secretário(a)','prefeito':'Prefeito','verificador':'Verificador do Comitê','relator':'Relator do Comitê'}[p] for p in sorted(papeis)],
            'modelo_ripd_disponivel':MODELO_RIPD.is_file(),
            'historico':s.scalars(select(Evento).where(Evento.cadeia_id==obj.id).order_by(Evento.id.desc())).all()})


@router.get('/forms34/{objeto_id}/modelo-ripd')
def modelo_ripd(request:Request,objeto_id:str,conta_id:str):
    with Session(motor) as s:
        try:dominio.consultar(s,conta_id,objeto_id)
        except (PermissionError,ValueError) as exc:return erro(request,conta_id,exc,403)
    if not MODELO_RIPD.is_file():return erro(request,conta_id,'Modelo municipal ainda não instalado.',503)
    trechos=[]
    for linha in MODELO_RIPD.read_text(encoding='utf-8').splitlines():
        if linha.strip():
            tipo='h1' if linha.startswith('# ') else 'h2' if linha.startswith('## ') else 'p'
            trechos.append((tipo,linha.lstrip('# ').strip() if tipo!='p' else linha))
    return paginas.TemplateResponse(request=request,name='forms34_modelo_ripd.html',context={
        'conta_id':conta_id,'objeto_id':objeto_id,'trechos':trechos})


@router.api_route('/forms34/{objeto_id}/referencia-restrita',methods=['GET','POST'])
async def restrita(request:Request,objeto_id:str,conta_id:str):
    from app.restrito_forms34 import ler
    with Session(motor) as s:
        try:
            item=ler(s,conta_id,objeto_id)
            s.commit()  # consulta auditada, inclusive a negativa no caminho abaixo
        except (PermissionError,ValueError) as exc:
            s.commit();return erro(request,conta_id,exc,403)
        if request.method=='POST':
            d=await request.form()
            try:
                r=dominio.registrar_referencia_restrita(s,conta_id=conta_id,comando_id=d.get('comando_id'),
                    identidade_id=objeto_id,versao=int(d.get('versao','0')),
                    dados={k:d.get(k,'') for k in ('referencia','questao','conclusao','localizacao')})
                if not r.get('permitido'):raise ValueError(r.get('motivo'))
                s.commit()
                return RedirectResponse(f'/forms34/{objeto_id}/referencia-restrita?'+urlencode({'conta_id':conta_id}),303)
            except (ValueError,PermissionError) as exc:
                s.rollback();return erro(request,conta_id,exc)
        return paginas.TemplateResponse(request=request,name='forms34_restrita.html',context={
            'conta_id':conta_id,'objeto_id':objeto_id,'item':item,'estado':dominio.estado(s,objeto_id),'comando_id':str(uuid4())})


@router.get('/forms34/{objeto_id}/aprendizagem')
def aprendizagem(request:Request,objeto_id:str,conta_id:str):
    with Session(motor) as s:
        pessoa_ativa(s,conta_id)
        e=dominio.estado(s,objeto_id)
        if not e.get('aprendizagem_autorizada'):
            return erro(request,conta_id,'Versão ainda não autorizada para consulta.',403)
        # Whitelist: nenhuma origem, anexo, referência jurídica ou histórico é enviado.
        return paginas.TemplateResponse(request=request,name='forms34_aprendizagem.html',context={
            'conta_id':conta_id,'aprendizagem':e['aprendizagem']})
