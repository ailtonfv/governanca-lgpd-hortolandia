"""Rotas GET do dashboard, em transação PostgreSQL somente leitura."""
from datetime import datetime, timezone, date
from pathlib import Path
from urllib.parse import urlencode
from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.banco import motor
from app.dashboard.fontes import escopo_da_conta, carregar, categorias_circulacao
from app.dashboard import consultas as c

router=APIRouter()
paginas=Jinja2Templates(directory=Path(__file__).parents[1]/'paginas')
paginas.env.filters['data_dashboard']=c.data_br
TELAS={'abertura':'Visão geral da governança LGPD','risco':'Quais riscos existem e quanto os controles os reduzem?',
       'correcao':'As providências estão sendo cumpridas?','operacao':'Onde os Registros estão esperando?',
       'cobertura':'Quais Secretarias já mapearam seus serviços, processos e atividades?',
       'aprendizados':'O que a Prefeitura mudou por causa disso?','circulacao':'Para onde os dados pessoais vão?'}
CORES={'Pequeno':'#2e9e44','Moderado':'#e2a90f','Alto':'#e3651d','Crítico':'#b3261e'}


def linha_tempo(l,agora,limites=None):
    marcas=[('Plano aprovado',l['inicio']),('Prazo original',l['prazo_original']),('Prazo vigente',l['prazo']),('Fim',l['fim']),('Hoje',agora)]
    marcas += [(str(p['numero'])+'ª prorrogação',p['prazo']) for p in l['prorrogacoes']]
    datas=[c.momento(v).astimezone(c.LOCAL).date() for _,v in marcas if v]
    minimo,maximo=limites or (min(datas),max(datas));delta=max(1,(maximo-minimo).days)
    return [dict(nome=nome,data=v,x=5+90*(c.momento(v).astimezone(c.LOCAL).date()-minimo).days/delta,y=25+22*n)
            for n,(nome,v) in enumerate(marcas) if v]


@router.get('/dashboard')
@router.get('/dashboard/{tela}')
def dashboard(request:Request,tela:str='abertura',conta_id:str='CONTA-B1'):
    if tela not in TELAS:raise HTTPException(404,'Tela indisponível.')
    filtros={k:request.query_params.get(k,'') for k in ('secretaria','tipo','inicio','fim','etapa','faixa')}
    agora=datetime.now(timezone.utc)
    try:
        with Session(motor,autoflush=False) as sessao:
            sessao.execute(text('SET TRANSACTION READ ONLY'))
            escopo=escopo_da_conta(sessao,conta_id)
            fonte=carregar(sessao,escopo)
            dados=c.filtrar(fonte,escopo,filtros)
            if escopo.unidades is not None and len(escopo.unidades)==1 and not filtros['secretaria']:
                filtros['secretaria']=next(iter(escopo.unidades))
            tipos={t:sum(r.tipo_objeto==t for r in dados['registros']) for t in c.TIPOS}
            risco=c.risco(dados);correcao=c.correcao(dados,agora);operacao=c.operacao(dados,agora)
            cobertura=c.cobertura(dados);aprendizados=c.aprendizados(dados)
            circulacao=c.circulacao(dados,categorias_circulacao(dados))
            esteira=c.esteira(dados,filtros);atencao=c.atencao(dados,agora)
            quadros=[c.ativos(dados),*risco,*correcao,*operacao,*cobertura,*aprendizados,*circulacao,*esteira,*atencao]
            # Listas de cobertura são também quadros: todo número abre sua composição.
            for n,l in enumerate(cobertura[1]['lista']):
                for k in ('registros','confirmados','concluidos','externos'):
                    quadros.append(c.quadro(f'cobertura_{n}_{k}',l['secretaria']+' · '+k,l[k]))
                for t in c.TIPOS:
                    quadros.append(c.quadro(f'cobertura_{n}_{t}',l['secretaria']+' · '+t,[r for r in l['registros'] if r['tipo']==t]))
            indices={q['chave']:q for q in quadros}
            segmentos={}
            for q in esteira:
                segmentos[q['chave']]=[]
                for n,situacao in enumerate(sorted({l['situacao'] for l in q['lista']})):
                    sub=c.quadro(q['chave']+'_situacao_'+str(n),q['titulo']+' · '+situacao,
                                 [l for l in q['lista'] if l['situacao']==situacao])
                    indices[sub['chave']]=sub;segmentos[q['chave']].append(sub)
            def url(destino=tela,**extras):
                valores={'conta_id':conta_id,**{k:v for k,v in filtros.items() if v},**extras}
                return '/dashboard'+('' if destino=='abertura' else '/'+destino)+'?'+urlencode(valores)
            lista=request.query_params.get('lista')
            if lista and lista not in indices:raise HTTPException(404,'Indicador indisponível neste escopo.')
            selecao=indices.get(lista)
            # Nenhuma referência de evidência, nome de pessoa, objeto ORM ou estado cru vai ao template.
            secretarias=[dict(id=u.id,nome=u.nome) for u in fonte['secretarias']]
            linhas_risco=indices['riscos']['lista']
            linhas_acoes=indices['acoes']['lista']
            datas=[c.momento(m['data']).astimezone(c.LOCAL).date() for l in linhas_acoes for m in linha_tempo(l,agora)]
            limites=(min(datas),max(datas)) if datas else None
            for l in linhas_acoes:l['marcas']=linha_tempo(l,agora,limites)
            escolhas={'risco':['registros_avaliados','riscos'],
                      'correcao':['acoes','atrasadas'],
                      'operacao':['esperando','participacoes'], 'cobertura':['secretarias'],
                      'aprendizados':['aprendizados'],'circulacao':['circulacao',*[f'instrumento_{n}' for n in range(4)]]}
            perfil=escopo.perfil
            titulo_perfil={'Gabinete':'Precisa da sua atenção','DPO':'Pendências com o Gabinete e o Comitê',
                           'Comitê':'Pendente para o Comitê','Secretário':'Aguardando sua decisão','AAL/ARP':'Seus itens pendentes'}[perfil]
            atencao_perfil=atencao if perfil in ('Gabinete','DPO') else [indices['fila_'+('AAL' if perfil=='AAL/ARP' else perfil)]]
            # A lista que compõe cada fila mantém somente metadados, mesmo nos perfis globais.
            pagina=max(0,int(request.query_params.get('pagina','0')))
            arts=indices['aprendizados']['lista'];pagina=min(pagina,max(0,len(arts)-1))
            mostrando=[]
            if filtros['secretaria']:mostrando.append(next(u['nome'] for u in secretarias if u['id']==filtros['secretaria']))
            if filtros['tipo']:mostrando.append({'servico':'Serviço','processo':'Processo','atividade':'Atividade'}[filtros['tipo']])
            for k,rotulo in [('inicio','Criado desde'),('fim','Criado até')]:
                if filtros[k]:mostrando.append(rotulo+' '+date.fromisoformat(filtros[k]).strftime('%d/%m/%Y'))
            if filtros['faixa']:mostrando.append(filtros['faixa'])
            if filtros['etapa']:mostrando.append('FORM '+filtros['etapa'])
            return paginas.TemplateResponse(request=request,name='dashboard.html',context=dict(
                conta_id=conta_id,tela=tela,titulo=TELAS[tela],telas=TELAS,perfil=perfil,titulo_perfil=titulo_perfil,
                filtros=filtros,secretarias=secretarias,travada=escopo.unidades is not None,faixas=c.FAIXAS,cores=CORES,
                q=indices,url=url,selecao=selecao,quadros=[indices[k] for k in escolhas.get(tela,[]) if k in indices],
                atencao=atencao_perfil,esteira=esteira,segmentos=segmentos,risco=linhas_risco,correcao=indices['acoes']['lista'],
                filas=[indices['fila_'+k] for k in ('AAL','Jurídico','DPO','Secretário','Comitê','Gabinete')],
                cobertura=cobertura[1]['lista'],circulacao=[x for x in circulacao if x['chave'].startswith('circulacao_')],
                aprendizado=arts[pagina] if arts else None,pagina=pagina,aprendizados_total=len(arts),
                lado='inerente' if request.query_params.get('lado')=='inerente' else 'residual',
                escala_cobertura=max([l['total'] for l in cobertura[1]['lista']]+[1]),
                agora=agora,tipos=tipos,mostrando=' · '.join(mostrando) or 'Todo o seu escopo'))
    except PermissionError as exc:raise HTTPException(403,str(exc)) from exc
    except (ValueError,KeyError) as exc:raise HTTPException(400,'Consulta indisponível: '+str(exc)) from exc
