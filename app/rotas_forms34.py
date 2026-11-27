"""Interface demonstrativa; sem migração no startup ou no GET."""
from app.obrigatoriedade_forms import conferencia_para_tela, conferencia34, FormularioIncompleto
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlencode
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.banco import motor
from app.modelos import (IdentidadeForms34, ReferenciaParticipacaoForms34, Registro, Pessoa,
                         Conta, Unidade, ParticipacaoForm2, Evento, ContextoAtuacao)
from app import fluxo_forms34 as dominio
from app.permissoes_forms34 import contexto
from app.fila_form2 import pessoa_ativa, autorizado, unidades
from app.questionario_forms34 import perguntas, grade, ativa, recolhida
from app.atos_forms34_interface import disponiveis, interpretar
from app.validacao_atos34 import ErrosCampos
from app.apresentacao_forms34 import descricao_nota34, matriz, grade_visual, situacao_avaliacao, valores_proposta, PROBABILIDADE, IMPACTO
from app.identidade_demonstrativa import configurar_identidade
from app.atos_interface import ato_registrado
from app.eventos import registrar_auditoria
from app.apresentacao_form2 import data_local
from app.leitura_atos34 import proposta as quadro_proposta, historico_visual, NOMES, RESULTADOS, situacao_atual
from app.apresentacao_forms34 import titulo_bloco

MODELO_RIPD=Path(__file__).resolve().parents[1]/'docs/modelos/MODELO_MUNICIPAL_RIPD_PROPOSTA.md'

router=APIRouter()
paginas=Jinja2Templates(directory=Path(__file__).parent/'paginas')
configurar_identidade(paginas)
paginas.env.globals['descricao_nota34'] = descricao_nota34
paginas.env.filters['hora_local']=data_local


def url_objeto(obj,conta,bloco=1,**extra):
    return f'/forms34/{obj}/blocos/{bloco}?'+urlencode(dict(conta_id=conta,**extra))


@router.get('/temas/pedidos')
def pedidos_tema(request:Request,conta_id:str):
    from app.pedidos_tema import consultar
    with Session(motor) as s:
        try:pedidos=consultar(s,conta_id)
        except PermissionError as exc:raise HTTPException(403,str(exc)) from exc
        return paginas.TemplateResponse(request=request,name='pedidos_tema.html',context=dict(conta_id=conta_id,pedidos=pedidos))


def erro(request,conta,e,status=409,retorno='/forms34'):
    return paginas.TemplateResponse(request=request,name='forms34_erro.html',status_code=status,
        context={'conta_id':conta,'erro':str(e),'retorno':retorno,'conferencia_r17':getattr(e,'conferencia',None),'base_r17':getattr(e,'base','')})


@router.get('/forms34')
def lista(request:Request,conta_id:str,form:int|None=Query(default=None,ge=3,le=4),tema:str=''):
    with Session(motor) as s:
        pessoa=pessoa_ativa(s,conta_id)
        visiveis=[]
        referencias=[]
        from app.temas_form4 import corresponde, nomes, catalogo
        from app.restrito_forms34 import pode_ler
        for obj in s.scalars(select(IdentidadeForms34).order_by(IdentidadeForms34.codigo)):
            try:
                _,ref,e,_,papeis,_=dominio.consultar(s,conta_id,obj.id)
                if (form is None or ref.form == form) and corresponde(e.get('temas'),tema):
                    from app.acompanhamento_forms34 import resumo
                    visiveis.append(dict(obj=obj,estado=e,temas=nomes(s,e.get('temas')),**resumo(s,obj,e,papeis,pessoa.id),registro=s.get(Registro,obj.registro_id)))
            except (ValueError,PermissionError):
                try:
                    if pode_ler(s,conta_id,obj.id,dominio.estado(s,obj.id)):
                        referencias.append(dict(id=obj.id,codigo=obj.codigo,registro=s.get(Registro,obj.registro_id).codigo_lgpd))
                except (ValueError,PermissionError):pass
                continue
        contas=s.execute(select(Conta,Pessoa).join(Pessoa,Conta.pessoa_id==Pessoa.id)
            .where(Conta.ativa.is_(True),Pessoa.ativa.is_(True))).all()
        return paginas.TemplateResponse(request=request,name='forms34_lista.html',context={
            'contextos':{c.id:c.nome for c in s.scalars(select(ContextoAtuacao))},'temas':catalogo(s),'tema':tema,
            'pode_encaminhar':bool(unidades(s,pessoa.id,'aal_form2')),'filtro_form':form,'conta_id':conta_id,'pessoa':pessoa,'objetos':sorted(visiveis,key=lambda i:not i['pendente']),'referencias':referencias,'contas':contas,
            'gabinete':bool(unidades(s,pessoa.id,'demo34_gabinete'))})


@router.api_route('/form2/participacoes/{pid}/encaminhar34',methods=['GET','POST'])
async def ingresso(request:Request,pid:str,conta_id:str):
    with Session(motor) as s:
        pessoa=pessoa_ativa(s,conta_id)
        p=s.get(ParticipacaoForm2,pid)
        if not p or p.responsavel_id!=pessoa.id or p.tipo!='principal' or not autorizado(s,pessoa,p):
            return erro(request,conta_id,'Somente o AAL responsável encaminha.',403)
        if request.method=='POST':return erro(request,conta_id,'O encaminhamento ocorre ao concluir a análise do FORM 2.',409,f'/form2/participacoes/{pid}')
        return RedirectResponse(f'/form2/participacoes/{pid}/blocos/14?conta_id={conta_id}',303)


def escolhas(s,ref,papeis,uid):
    r={'unidade':[(u.id,u.nome) for u in s.scalars(select(Unidade).where(Unidade.ativa.is_(True)))],
       'juridico':[],'executor':[],'autoridade':[]}
    for p in s.scalars(select(Pessoa).where(Pessoa.ativa.is_(True))):
        if unidades(s,p.id,'juridico_form2'):r['juridico'].append((p.id,p.nome))
        if (uid in unidades(s,p.id,'preenchedor')|unidades(s,p.id,'aal_form2')
                and not unidades(s,p.id,'governanca_protecao_dados')):
            r['executor'].append((p.id,p.nome))
        if uid in unidades(s,p.id,'demo34_secretario') or unidades(s,p.id,'demo34_gabinete'):
            r['autoridade'].append((p.id,p.nome))
    return r


@router.api_route('/forms34/{objeto_id}/blocos/{bloco}',methods=['GET','POST'])
async def bloco(request:Request,objeto_id:str,bloco:int,conta_id:str):
    with Session(motor) as s:
        try:obj,ref,e,pessoa,papeis,uid=dominio.consultar(s,conta_id,objeto_id)
        except (PermissionError,ValueError) as exc:return erro(request,conta_id,exc,403)
        if not 1<=bloco<=(16 if ref.form==3 else 9):raise HTTPException(404,'Bloco inexistente.')
        erros_campos={}; valores_enviados={}; acao_erro=None; status=200; falhas_r17=False
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
                    dados=dict(bloco=bloco,campos=campos,complementos={k.partition(':')[2]:d[k] for k in d if k.startswith('complemento:')})
                    if ref.form==4:dados['clausulas_contrato']={k.partition(':')[2]:d[k] for k in d if k.startswith('clausula:')}
                    if ref.form == 3 and bloco == 13:
                        selecionados=campos.get('F3-3.47',[])
                        dados['controles_bloco13']={nome:dict(implementado=d.get('implementado:'+nome,''),evidencia=d.get('evidencia:'+nome,''))
                            for nome in selecionados if nome not in ('A confirmar','Nenhum controle identificado')}
                        dados['observacoes_controles']=d.get('observacoes_controles','')
                elif acao=='abrir_detalhes':dados=dict(bloco=bloco,motivo=d.get('motivo',''))
                else:dados=interpretar(acao,d)
                r=dominio.executar(s,conta_id=conta_id,comando_id=d.get('comando_id'),identidade_id=obj.id,
                                  versao=int(d.get('versao','0')),acao=acao,dados=dados)
                if not r.get('permitido'):raise ValueError(r.get('motivo'))
                s.commit()
                return RedirectResponse(url_objeto(r['identidade_id'],conta_id,bloco if r['identidade_id']==obj.id else 1,registrado=d.get('comando_id')),303)
            except FormularioIncompleto as exc:
                s.rollback(); falhas_r17=True; valores_enviados=dict(d,condicoes=[dict(texto=t,tipo=p) for t,p in zip(d.getlist('condicao_texto'),d.getlist('condicao_tipo'))]); acao_erro=acao; status=409
            except ErrosCampos as exc:
                s.rollback(); erros_campos=exc.erros; valores_enviados=dict(d,condicoes=[dict(texto=t,tipo=p) for t,p in zip(d.getlist('condicao_texto'),d.getlist('condicao_tipo'))]); acao_erro=acao; status=409
            except (ValueError,PermissionError,KeyError) as exc:
                s.rollback();return erro(request,conta_id,exc,403 if isinstance(exc,PermissionError) else 409,
                                           f'/forms34/{obj.id}/blocos/{bloco}')
        try:itens=[dict(q,ativa=ativa(q,e['respostas'],e),recolhida=recolhida(q,e['respostas'],e))
                   for q in perguntas(ref.form) if q['bloco']==bloco]
        except (FileNotFoundError,ValueError) as exc:return erro(request,conta_id,exc,503)
        from app.referencias_leitura_form3 import referencias
        anteriores=referencias(s,ref,itens)
        for q in itens:q['referencias_anteriores']=anteriores.get(q['id'],[])
        from app.opcao_outro import eh_outro
        from app.criterios_form3 import volume, alto_risco_referencia, GERAIS, ESPECIFICOS
        for q in itens:
            q['opcoes_outro']=[v for v in q['opcoes'] if eh_outro(v)]
            q['ocultar_condicional']=q['id']=='F3-3.38' or q['id'] in ('F3-3.33','F3-3.41','F3-3.42') or q['id'].startswith('F3-3.43.')
            if q['id']=='F3-3.6':q['ajuda']=volume()
            if q['id']=='F3-3.53':q['ajuda']='Calculado a partir do bloco 3.'
            if q['id']=='F3-3.10':
                q['grupos']=[('Critérios gerais (ANPD)',GERAIS),('Critérios específicos (ANPD)',ESPECIFICOS),
                    ('Outros fatores (Prefeitura)',[v for v in q['opcoes'] if v not in GERAIS+ESPECIFICOS])]
        origem=s.get(ParticipacaoForm2,e['origem_form2_id']) if e.get('origem_form2_id') else None
        revisar=request.query_params.get('revisar')=='1' or acao_erro=='revisar_avaliacao'
        atos=disponiveis(ref.form,bloco,papeis,e,pessoa.id,revisar)
        from app.temas_form4 import configurar_campos, nomes as nomes_temas
        if ref.form==4:
            configurar_campos(s,atos,e)
        listas=escolhas(s,ref,papeis,uid)
        eventos=s.scalars(select(Evento).where(Evento.cadeia_id==obj.id).order_by(Evento.id.desc())).all()
        autores={p.id:p.nome for p in s.scalars(select(Pessoa))}
        unidades_nomes={u.id:u.nome for u in s.scalars(select(Unidade))}
        proposta_av=quadro_proposta(e,'avaliacao',autores,unidades_nomes,eventos)
        proposta_reavaliacao=quadro_proposta(e['reavaliacao'],'avaliacao',autores,unidades_nomes) if e.get('reavaliacao') else None
        proposta_tr=quadro_proposta(e,'triagem',autores,unidades_nomes,eventos)
        hist=historico_visual(eventos,autores,unidades_nomes,{q['id']:q['bloco'] for q in perguntas(ref.form)},obj,ref)
        for item in hist:
            item['bloco']=__import__('app.atos_forms34_interface',fromlist=['ATOS']).ATOS.get(item['acao'],(0,0))[1]
            if item['acao']=='ingresso' and e.get('risco_id'):
                risco_origem = s.get(IdentidadeForms34,e['risco_id'])
                if risco_origem:item['nome'] += f' (Risco {risco_origem.numero})'
        codigo_risco=obj.codigo.split('-')[-1]

        for a in atos:
            a['reavaliacao']=a['acao']=='revisar_avaliacao' and set(e.get('avaliacao_confirmacoes',{}))=={'secretaria','dpo'}
            a['comando_id']=str(uuid4())
            fonte_ato={'executar_medida':'execucao','verificar':'verificacao','aprender':'aprendizagem','informar_ripd':'referencia_ripd'}.get(a['acao'])
            a['valores']={**a.get('valores',{}),**dict(e.get(fonte_ato,{}) if fonte_ato else {})}
            if a['acao']=='planejar':a['valores'].update(plano=e.get('plano',''),cargo=e.get('cargo_responsavel',''),duracao_dias=e.get('duracao_dias',''))
            a['valores']={k:('sim' if v else 'nao') if isinstance(v,bool) else v for k,v in a['valores'].items()}
            a['resumo']=f"{'Risco' if ref.form==3 else 'Ação'} {codigo_risco} ({s.get(Registro,obj.registro_id).codigo_lgpd}): {a['titulo']}. A autoria será registrada."
            if a['acao']=='aprovar_plano':
                from app.prazos_plano34 import vencimento_na_aprovacao
                from app.apresentacao_atos34 import data_br
                from app.eventos import agora_utc
                try:
                    previsto = vencimento_na_aprovacao(e, agora_utc())
                    prazo_previsto = f"até {data_br(previsto)}, se aprovar hoje" if e.get('duracao_dias') else 'a Secretaria precisa registrar a duração antes da aprovação'
                except ValueError as erro_prazo:
                    prazo_previsto = str(erro_prazo)
                a['resumo'] += f" Plano: {e.get('plano','')}. Cargo: {e.get('cargo_responsavel','')}. Prazo: {prazo_previsto}."
            for c in a['campos']:
                c['uid']=a['acao']+'-'+c['nome']
                if a['acao']=='manifestar_comite' and c['nome']=='favoravel':c['rotulo']='O Comitê é favorável ao tratamento proposto para o risco residual (RIPD e controles)?'
                c['lista']=(list(enumerate(PROBABILIDADE if c['nome'] in ('p','pr') else IMPACTO,1)) if c['tipo']=='number' else [('sim','Sim'),('nao','Não')] if c['tipo']=='bool' else listas.get(c['tipo'],c.get('opcoes',())))
                if c['tipo']=='number':c['lista']=[(k,f'{k} — {v}') for k,v in c['lista']]
            if a['acao']=='confirmar_avaliacao' and e.get('avaliacao'):
                av=e.get('reavaliacao',e)['avaliacao'];a['resumo']=f"Risco {obj.codigo.split('-')[-1]}: inerente {av['inerente']['nota']} ({av['inerente']['faixa']}), residual {av['residual']['nota']} ({av['residual']['faixa']}). Confirmar esta proposta?"
            if a['acao']=='confirmar_avaliacao':
                a['resumo']+=' Com a sua confirmação, a nota passa a valer como nota conjunta.'
                faixa=e.get('reavaliacao',e).get('avaliacao',{}).get('residual',{}).get('faixa')
                if faixa=='Crítico':a['resumo']+=' O risco Crítico segue para triagem de RIPD, manifestação do Comitê e aceitação pelo Prefeito.'
            if a['acao']=='confirmar_triagem' and proposta_tr:
                a['resumo']=f"Risco {codigo_risco}: confirmar a triagem proposta por {proposta_tr['lado']} — "+RESULTADOS.get(e['triagem']['resultado'],'')
            from app.apresentacao_atos34 import conteudo_decisao
            a['leitura']=conteudo_decisao(a['acao'],e,autores,unidades_nomes)
            if a['acao']=='manifestar_comite':
                for campo,quadro in (('avaliacao',proposta_reavaliacao or proposta_av),('triagem',proposta_tr)):
                    alvo=e.get('reavaliacao',e) if campo=='avaliacao' else e
                    if alvo.get(campo+'_sem_consenso') and quadro:
                        a['leitura'].extend([('Proposta de',quadro['autor']),*quadro['linhas']])
                        a['leitura'].extend([('Posição do DPO' if lado=='dpo' else 'Posição da Secretaria',texto) for lado,texto in alvo.get(campo+'_posicoes',{}).items()])
            if a['leitura']:a['resumo']+='\n'+'\n'.join(f'{k}: {v}' for k,v in a['leitura'])
            if a['acao']=='executar_medida':a['resumo']='Confirmar o registro da execução? '+a['resumo']
            if a['acao']=='aceitar_residual':
                residual=e['avaliacao']['residual'];a['resumo']+=f"\nRisco residual: {residual['nota']} — {residual['faixa']}"
            a['escala']={c['nome']:c for c in a['campos'] if c['nome'] in ('p','i','pr','ir')}
        proposta=next((a for a in atos if a['acao'] in ('propor_avaliacao','revisar_avaliacao')),None)
        restantes=[a for a in atos if a is not proposta]
        encaminhamento_destacado=(e.get('respostas',{}).get('F3-3.59')=='Sim' and
                                  'Providência no FORM 4' in e.get('respostas',{}).get('F3-3.61',[]))
        destaques=[a for a in restantes if not a.get('recolhido') and ref.form==3 and bloco==16 and
                   (a['acao']=='concluir_avaliacao' or a['acao']=='encaminhar_acao' and encaminhamento_destacado)]
        destaques.sort(key=lambda a:a['acao']!='encaminhar_acao')
        restantes=[a for a in restantes if a not in destaques]
        principal=next((a for a in restantes if not a.get('recolhido')), None)
        from app.encerramento_form4 import aviso_anterior
        aviso_regra_anterior = aviso_anterior(e)
        grade_atual=grade(ref.form,e['respostas'],e)
        registro=s.get(Registro,obj.registro_id)
        from app.apresentacao_atos34 import data_br
        valores = {'F3-3.1':registro.codigo_lgpd,'F4-4.1':registro.codigo_lgpd,
                   'F3-3.53': 'Sim' if alto_risco_referencia(e['respostas']) else 'Não' if e['respostas'].get('F3-3.10') and e['respostas']['F3-3.10']!=['A confirmar'] else 'A confirmar',
                   'F3-3.59':'Providência encaminhada por lacuna' if e.get('encaminhamentos_lacunas') else 'Defina o destino e a prioridade na lista de lacunas deste bloco.',
                   'F4-4.1.1':obj.codigo,'F3-3.2':s.get(Unidade,uid).nome,
                   'F3-3.3':{'em_atendimento':'Em atendimento','aguardando':'Aguardando responsável','concluida':'Análise concluída'}.get(e.get('situacao_form2'),'Situação preservada na origem'),
                   'F4-4.15':e['situacao'],'F4-4.10':data_br(e.get('prazo')),
                   'F4-4.23':(e.get('residual_acao') or {}).get('faixa','Ainda não avaliado') if set(e.get('residual_acao_confirmacoes',{}))=={'secretaria','dpo'} else 'Aguardando nota residual conjunta',
                   'F4-4.24':'Aceitação posterior registrada' if e.get('aceitacao_residual_acao') else 'Aceitação pendente de autoridade competente',
                   'F3-3.52.5':'Aceitação registrada' if e.get('aceitacao') else 'Pendente de autoridade competente'}
        valores.update({'F4-4.6':unidades_nomes.get(e.get('unidade_responsavel_id') or (uid if e.get('plano') else None),'Ainda não informado'),
                        'F4-4.7':e.get('cargo_responsavel') or ('Cargo não informado no ato anterior' if e.get('plano') else 'Ainda não informado')})
        if ref.form==3 and e.get('situacao_form2')!='concluida':
            import json
            fonte_leitura=json.loads(ref.fonte_canonica) if isinstance(ref.fonte_canonica,str) else ref.fonte_canonica
            quando=fonte_leitura.get('ocorrido_em')
            valores['F3-3.3']='Risco encaminhado pelo AAL durante a análise do FORM 2'+(f' (versão de {data_br(quando)}).' if quando else '. Data preservada no histórico da origem.')
        if ref.form==4:
            for q in itens:
                if q['id']=='F4-4.9' and e.get('prioridade_origem'):q['ajuda']='Prioridade herdada do FORM 3: '+e['prioridade_origem']
                if q['id']=='F4-4.27' and e.get('faixa_origem')=='Crítico':q['ajuda']='Sugestão para risco Crítico: revisar em seis meses.'
        if e.get('triagem'):
            valores.update({'F3-3.55':RESULTADOS.get(e['triagem'].get('resultado'),'Ainda não avaliado'),
                            'F3-3.56':e['triagem'].get('justificativa',''),
                            'F3-3.57':unidades_nomes.get(e['triagem'].get('unidade_id'),'Não indicada para este resultado')})
        if e.get('avaliacao'):
            valores.update({'F3-3.52':e['respostas'].get('F3-3.52') or 'Ainda não avaliado','F3-3.52.4':'; '.join((c.get('descricao','')+' — '+c.get('evidencia','')).strip(' —') for c in e['avaliacao'].get('controles',[])) or 'Ainda não avaliado'})
            if e.get('aceitacao'):
                dec=e['aceitacao'];autor=s.get(Pessoa,dec['pessoa_id']);valores['F3-3.52.6']=f"{dec['justificativa']} · {autor.nome} · {data_local(dec['em'])}"
            for ident, tipo, chave in [('F3-3.49','inerente','probabilidade'),('F3-3.50','inerente','impacto'),
                    ('F3-3.51','inerente','nota'),('F3-3.52.1','residual','probabilidade'),
                    ('F3-3.52.2','residual','impacto'),('F3-3.52.3','residual','nota')]:
                valores[ident] = descricao_nota34(e['avaliacao'][tipo][chave],chave) if chave in ('probabilidade','impacto') else e['avaliacao'][tipo][chave] if e['avaliacao'][tipo][chave] is not None else 'Não avaliado'
        if ref.form==3 and bloco==14:
            for q in itens:q['tipo']='ato'
        from app.atos_forms34_interface import ATOS
        ato=ato_registrado(s,request.query_params.get('registrado'),conta_id,registro_id=registro.id,participacao_id=obj.id)
        if ato:
            evento_sucesso=next((h for h in hist if h['comando_id']==request.query_params.get('registrado')),None)
            ato['nome']=evento_sucesso['nome'] if evento_sucesso else 'Ato registrado'
            if evento_sucesso and evento_sucesso['acao']=='encerramento_automatico':
                ato['autor']='Sistema'
                ato['automatico']=True
        ultimo=next((h for h in hist if h['ato']),None)
        situacao_topo=(ultimo['nome']+' em '+ultimo['quando']) if ultimo else e['situacao']
        if ref.form == 4:
            v = e.get('verificacao', {})
            ex = e.get('execucao', {})
            valores.update(v.get('respostas', {}))
            valores['F4-4.19'] = ('Evidência informada pela Secretaria: '+ex['evidencia']+' · '+autores.get(ex.get('pessoa_id'), 'Autor registrado')+' · '+str(data_local(ex['em']))) if ex else 'Aguardando referência da execução'
            valores['F4-4.18.1'] = (autores.get(v.get('pessoa_id'), 'Autor registrado')+' · '+unidades_nomes.get(v.get('unidade_id'), 'Secretaria registrada no ato')+' · '+str(data_local(v['em']))) if v else 'Aguardando verificação'
            for q in itens:
                if q['id'] == 'F4-4.18.1':q['enunciado'] = 'Responsável pela verificação'
            for k in ('F4-4.10.1','F4-4.10.2','F4-4.10.3'):
                valores[k] = 'Não houve pedido de prorrogação' if not e.get('prorrogacoes') and not e.get('decisoes_pendentes', {}).get('prorrogacao') else 'Consulte os atos de prorrogação no histórico'
            if not e.get('prorrogacoes') and not e.get('decisoes_pendentes',{}).get('prorrogacao'):
                valores['F4-4.10.1']='Prorrogação: não solicitada'
                itens=[q for q in itens if q['id'] not in ('F4-4.10.2','F4-4.10.3')]
            valores['F4-4.15.1'] = f"{ultimo['quando']} — {ultimo['autor']}, {ultimo['nome']}" if ultimo else 'Nenhuma alteração registrada'
            for k in ('F4-4.15.2',):
                valores[k] = 'Não há pedido de cancelamento' if not e.get('cancelada') and not e.get('decisoes_pendentes', {}).get('cancelamento') else 'Consulte os atos de cancelamento no histórico'
            valores['F4-4.16'] = f"{ultimo['quando']} — {ultimo['autor']}, {ultimo['nome']}" if ultimo else 'Nenhum ato registrado'
        from app.apresentacao_atos34 import ripd,mensagem_decisao,data_br
        origem_texto=f'FORM {ref.fonte_form} deste Registro, referência examinada preservada.'
        if ref.form==4 and ref.fonte_form==3:
            import json
            fonte=json.loads(ref.fonte_canonica) if isinstance(ref.fonte_canonica,str) else ref.fonte_canonica
            fonte=fonte.get('conteudo',fonte)
            fonte=fonte.get('estado',fonte)
            av=fonte.get('avaliacao') or {};res=av.get('residual',{})
            risco=s.get(IdentidadeForms34,e.get('risco_id'))
            origem_texto=f"Risco {risco.codigo.split('-')[-1] if risco else 'registrado'} — {res.get('faixa',e.get('faixa_origem','Não avaliado'))} ({res.get('nota','nota não disponível')}), "+('aceito pelo '+('Prefeito' if res.get('faixa')=='Crítico' else 'Secretário') if fonte.get('aceitacao') else 'sem aceitação registrada na origem')+(f" em {data_br(fonte['aceitacao']['em'])}" if fonte.get('aceitacao',{}).get('em') else '')
            if risco:
                from app.acompanhamento_forms34 import titulo
                origem_texto = titulo(risco, {**fonte, 'form':3})+' — '+origem_texto.split(' — ',1)[1]
            valores['F4-4.2.1'] = origem_texto
        from app.etapas_forms34 import motivo_bloqueio, situacao_aprendizagem, pode_preencher
        from app.acompanhamento_forms34 import resumo as resumo_acompanhamento
        acompanhamento = resumo_acompanhamento(s,obj,e,papeis,pessoa.id)
        situacao_topo = acompanhamento['situacao']
        tarefa_atual = next((a for a in atos if acompanhamento['bloco'] == bloco
                            and a['acao'] == acompanhamento['ato']), None)
        if tarefa_atual is proposta and tarefa_atual:
            proposta = None
        if tarefa_atual in destaques:
            destaques = [a for a in destaques if a is not tarefa_atual]
        if tarefa_atual in restantes:
            restantes = [a for a in restantes if a is not tarefa_atual]
        if tarefa_atual:
            principal = None
        bloqueio_edicao = motivo_bloqueio(e, bloco)
        if registro.estado_atual=='encerrado_nao_cabe':
            bloqueio_edicao='Registro encerrado: instrumentos preservados somente para leitura.'
            atos=[];proposta=None;principal=None;restantes=[];destaques=[]
        vinculadas = []
        for aid in e.get('acoes', []):
            try:
                aobj, _, ae, *_ = dominio.consultar(s, conta_id, aid)
                ingresso_acao = next((ev for ev in dominio.historico(s, aid) if ev.tipo_evento == 'f34_ingresso'), None)
                vinculadas.append(dict(id=aid, codigo=aobj.codigo.split('-')[-1], numero=int(aobj.codigo.split('-')[-1][1:]),
                    autor=autores.get(ingresso_acao.ator_id, 'Autor registrado') if ingresso_acao else '',
                    quando=str(data_local(ingresso_acao.ocorrido_em)) if ingresso_acao else ''))
            except (ValueError, PermissionError):pass
        from app.restrito_forms34 import pode_ler
        from app.clausulas_lgpd import aplica4,itens4,pendencias4,catalogo as catalogo_clausulas
        from app.lacunas_form3 import listar as listar_lacunas, incoerencias, DESTINOS
        return paginas.TemplateResponse(request=request,name='forms34_bloco.html',status_code=status,context={
            'clausulas_acao':itens4(e.get('fornecedor_guarda_dados',False)) if ref.form==4 and aplica4(e['respostas']) else [],
            'clausulas_pendentes':pendencias4(e) if ref.form==4 else [],'clausulas_aviso':catalogo_clausulas()['aviso_fixo'],
            'lacunas':listar_lacunas(e) if ref.form==3 else [], 'destinos_lacunas':DESTINOS, 'alto_risco_referencia':alto_risco_referencia(e['respostas']),
            'incoerencias_controles':incoerencias(e) if ref.form==3 else [],
            'temas_acao':nomes_temas(s,e.get('temas')) if ref.form==4 else [],
            'temas_aprendizagem':nomes_temas(s,e.get('aprendizagem',{}).get('temas')) if ref.form==4 else [],
            'pode_preencher':pode_preencher(ref.form,papeis),
            'conclusao_automatica':next((h['nome'] for h in hist if h['acao']=='encerramento_automatico'),''),
            'bloqueio_edicao':bloqueio_edicao, 'acoes_vinculadas':vinculadas,
            'acompanhamento':acompanhamento, 'tarefa_atual':tarefa_atual,
            'situacao_aprendizagem':situacao_aprendizagem(e),
            'contexto_nome':getattr(s.get(ContextoAtuacao,registro.contexto_atuacao_id),'nome',''),'aviso_regra_anterior':aviso_regra_anterior,'destaques':destaques,'encaminhamento_destacado':encaminhamento_destacado,'origem_texto':origem_texto,'ripd_texto':ripd(e),'decisoes_gabinete':mensagem_decisao(e),'prazo_br':data_br(e.get('prazo')),
            'atos_salvos':[h for h in hist if h['ato'] and h['bloco']==bloco] if ref.form==4 else [],
            'falhas_r17':falhas_r17,'conferencia_r17':conferencia34(ref.form,e),'base_r17':f'/forms34/{obj.id}/blocos',
            'erros_campos':erros_campos,'acao_erro':acao_erro,'revisar':revisar,
            'ato_proposta':proposta,'ato_principal':principal,'outros_atos':[a for a in restantes if a is not principal],
            'valores_formulario':valores_enviados if acao_erro else valores_proposta(e.get('reavaliacao',e)),
            'matriz':matriz(),'situacao_avaliacao':situacao_avaliacao(e),
            'grade_visual':grade_visual(grade_atual,obj.id,conta_id,bloco,e),
            'titulo_bloco':titulo_bloco(next(g['titulo'] for g in grade_atual if g['numero']==bloco)),
            'proposta_reavaliacao':proposta_reavaliacao,'proposta_av':proposta_av,'proposta_tr':proposta_tr,'situacao_topo':situacao_topo,
            'historico_visual':hist,'so_atos':request.query_params.get('historico')=='atos' if request.query_params.get('filtrar') else request.query_params.get('historico','atos')!='todos',
            'manifestacoes':[h for h in hist if h['acao'] in ('manifestar_dpo','manifestar_comite','aceitar_residual','aprovar_plano','verificar','cancelar') and not (ref.form==4 and h['bloco']==bloco)],
            'valores_triagem':e.get('triagem') or {},
            'valores_comite':dict(autor_avaliacao=(proposta_reavaliacao or proposta_av or {}).get('autor','autor da proposta'),autor_triagem=(proposta_tr or {}).get('autor','autor da proposta')),
            'obj':obj,'ref':ref,'estado':e,'pessoa':pessoa,'papeis':papeis,'registro':registro,
            'conta_id':conta_id,'bloco':bloco,'itens':itens,'grade':grade(ref.form,e['respostas'],e),
            'atos':atos,'escolhas':escolhas(s,ref,papeis,uid),'comando_id':str(uuid4()),'ato':ato,
            'valores':valores,'autores':{p.id:p.nome for p in s.scalars(select(Pessoa))},
            'rotulos_atos':{'f34_'+k:v[3] for k,v in ATOS.items()},
            'atraso':dominio.em_atraso(e),'origem_nova':bool(origem and origem.versao!=ref.fonte_versao),
            'pode_restrito':pode_ler(s,conta_id,obj.id,e),
            'papeis_visiveis':[{'leitor_unidade':'Consulta da própria Secretaria','secretaria':'Secretaria — preenchimento','aal':'AAL','dpo':'Encarregado de Dados (DPO)','secretario':'Secretário(a)','gabinete':'Gabinete do Prefeito','executor_unidade':'Executor habilitado da unidade','verificador':'Verificador do Comitê','relator':'Relator do Comitê'}[p] for p in sorted(papeis)],
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
        erros_restritos={};status_restrita=200
        if request.method=='POST':
            d=await request.form()
            try:
                r=dominio.registrar_referencia_restrita(s,conta_id=conta_id,comando_id=d.get('comando_id'),
                    identidade_id=objeto_id,versao=int(d.get('versao','0')),
                    dados={k:d.get(k,'') for k in ('referencia','questao','conclusao','localizacao')})
                if not r.get('permitido'):raise ValueError(r.get('motivo'))
                s.commit()
                return RedirectResponse(f'/forms34/{objeto_id}/referencia-restrita?'+urlencode({'conta_id':conta_id}),303)
            except ErrosCampos as exc:
                s.rollback();erros_restritos=exc.erros;status_restrita=409
                from types import SimpleNamespace
                item=SimpleNamespace(conteudo=dict(d))
            except (ValueError,PermissionError) as exc:
                s.rollback();return erro(request,conta_id,exc)
        return paginas.TemplateResponse(request=request,name='forms34_restrita.html',status_code=status_restrita,context={
            'erros':erros_restritos,
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


@router.get('/forms34/{objeto_id}/proposta-impacto')
def proposta_impacto(request:Request,objeto_id:str,conta_id:str):
    from app.documentos_interface import blocos_documento
    with Session(motor) as s:
        try:dominio.consultar(s,conta_id,objeto_id)
        except (PermissionError,ValueError) as exc:return erro(request,conta_id,exc,403)
    arquivo=Path(__file__).resolve().parent.parent/'docs/planejamento/PROPOSTA_TABELA_IMPACTO_FORM3.md'
    if not arquivo.is_file():return erro(request,conta_id,'Proposta de impacto ainda não instalada.',503)
    return paginas.TemplateResponse(request=request,name='forms34_proposta_impacto.html',context={
        'conta_id':conta_id,'objeto_id':objeto_id,'blocos_documento':blocos_documento(arquivo.read_text(encoding='utf8'))})
