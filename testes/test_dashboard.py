"""Cenários fictícios, consultas sem escrita e contagens com composição verificável."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace as NS
import pytest
from sqlalchemy import select, func, event
from fastapi.testclient import TestClient
from app.main import app
from app.banco import motor
from app.dashboard import consultas as c
from app.dashboard.fontes import carregar, escopo_da_conta, Escopo
from app.modelos import Registro, Evento, EventoAuditoria, IdentidadeForms34, Designacao
from testes.test_lote12 import entrada, fonte, protecoes, entrar, avaliar, ato, SECRETARIO

AGORA=datetime(2026,11,20,12,tzinfo=timezone.utc)


@pytest.fixture
def dados(sessao,entrada):
    obj=entrar(sessao,entrada)
    avaliar(sessao,obj,2)
    ato(sessao,obj,'encaminhar_acao',justificativa='Providência fictícia do dashboard')
    escopo=escopo_da_conta(sessao,'CONTA-B1')
    return c.filtrar(carregar(sessao,escopo),escopo,{})


@pytest.mark.parametrize('indicador',['ativos','risco','atencao','correcao','esteira','operacao','cobertura','aprendizados','circulacao'])
def test_indicadores_numero_igual_lista(sessao,dados,indicador):
    if indicador in ('atencao','correcao','operacao'):resultado=getattr(c,indicador)(dados,AGORA)
    elif indicador=='esteira':resultado=c.esteira(dados,{})
    elif indicador=='circulacao':resultado=c.circulacao(dados,{r.id:{'categorias':{'Categoria fictícia'},'instrumentos':{'Sim'}} for r in dados['registros']})
    else:resultado=getattr(c,indicador)(dados)
    for q in resultado if isinstance(resultado,list) else [resultado]:
        assert q['numero']==len(q['lista']) if q['disponivel'] else q['numero'] is None
    assert len(dados['registros'])==1 and len(dados['objetos'])==2


def test_nota_confirmada_reavaliacao_e_pior_risco(sessao,dados):
    r=next(i for i in dados['objetos'] if i['obj'].tipo=='R')
    r['estado']['reavaliacao']={'avaliacao_sem_consenso':True,'avaliacao':{'residual':{'nota':25}}}
    rs={x['chave']:x for x in c.risco(dados)}
    assert rs['riscos']['numero']==1 and rs['riscos']['lista'][0]['residual']['nota']==4
    assert rs['riscos']['lista'][0]['reavaliacao'] and rs['sem_consenso']['numero']==0
    outra=deepcopy(r);outra['obj']=NS(id='risco-ficticio-2',tipo='R',numero=2,codigo='R02',registro_id=r['obj'].registro_id)
    outra['estado']['avaliacao']['residual'].update(nota=25,probabilidade=5,impacto=5,faixa='Crítico')
    dados['objetos'].append(outra)
    dados=c.filtrar(dados,dados['escopo'],{})
    rs={x['chave']:x for x in c.risco(dados)}
    assert rs['riscos']['numero']==2 and rs['faixa_3']['numero']==1 and rs['faixa_1']['numero']==0
    assert rs['matriz_residual_5_5']['numero']==1


def test_proposta_sem_consenso_nao_entra_matriz(sessao,dados):
    r=next(i for i in dados['objetos'] if i['obj'].tipo=='R')
    r['estado']['avaliacao_confirmacoes']={'secretaria':{}}
    r['estado']['avaliacao_sem_consenso']=True
    rs={x['chave']:x for x in c.risco(dados)}
    assert rs['riscos']['numero']==0 and rs['sem_consenso']['numero']==1


def test_ciências_nao_abrem_fila(sessao,dados):
    a=next(i for i in dados['objetos'] if i['obj'].tipo=='A')
    a['estado']['ciencia_prefeito']={'em':AGORA.isoformat()}
    a['estado']['ciencia_comite']={'em':AGORA.isoformat()}
    q={x['chave']:x for x in c.atencao(dados,AGORA)}
    assert q['ciencias']['numero']==1 and q['ciencias']['lista'][0]['dias'] is None
    filas={x['chave']:x for x in c.operacao(dados,AGORA)}
    assert filas['fila_Gabinete']['numero']==0 and filas['fila_Comitê']['numero']==0


def test_marco_dpo_abre_na_confirmacao_fecha_na_manifestacao_e_reabre(sessao,dados):
    i=next(i for i in dados['objetos'] if i['obj'].tipo=='R')
    e=deepcopy(i['estado']);e['avaliacao']['residual']['faixa']='Alto';e['avaliacao']['residual']['nota']=12
    def ev(n,s):return NS(tipo_evento='f34_confirmar_avaliacao',ocorrido_em=AGORA-timedelta(days=n),conteudo={'estado':deepcopy(s)})
    inicial=deepcopy(e);inicial['avaliacao_confirmacoes']={'secretaria':{}}
    fechado=deepcopy(e);fechado['manifestacao_dpo']={'em':(AGORA-timedelta(days=2)).isoformat()}
    i['eventos']=[ev(8,inicial),ev(5,e),ev(2,fechado),ev(1,e)];i['estado']=e
    filas={x['chave']:x for x in c.operacao(dados,AGORA)}
    assert filas['fila_DPO']['numero']==1
    assert filas['fila_DPO']['detalhes'][0]['dias']==1
    i['estado']=fechado
    assert next(x for x in c.operacao(dados,AGORA) if x['chave']=='fila_DPO')['numero']==0


def test_correcao_prazo_original_verificacao_e_cancelamento(sessao,dados):
    a=next(i for i in dados['objetos'] if i['obj'].tipo=='A');e=a['estado']
    e.update(plano_aprovado={'em':'2026-11-01T12:00:00+00:00'},prazo='2026-11-19',execucao={'em':'2026-11-18T12:00:00+00:00'})
    a['eventos'].append(NS(tipo_evento='f34_aprovar_plano',ocorrido_em=AGORA-timedelta(days=10),conteudo={'estado':{'prazo':'2026-11-15'}}))
    q={x['chave']:x for x in c.correcao(dados,AGORA)}
    assert q['atrasadas']['numero']==1 and q['acao_2']['numero']==1
    assert q['acoes']['lista'][0]['prazo_original']=='2026-11-15'
    e.update(verificada=True,verificacao={'aprovada':True,'em':AGORA.isoformat()})
    q={x['chave']:x for x in c.correcao(dados,AGORA)}
    assert q['atrasadas']['numero']==0 and q['acao_3']['numero']==1
    e['cancelada']={'em':AGORA.isoformat()}
    assert c.situacao_acao(e)=='Cancelada'


def test_aprendizado_somente_ultima_versao_autorizada_sem_evidencia(sessao,dados):
    a=next(i for i in dados['objetos'] if i['obj'].tipo=='A')
    e={'verificada':True,'verificacao':{'aprovada':True,'em':AGORA.isoformat(),'evidencia':'SEGREDO-FICTICIO'},
       'aprendizagem':{'diretriz':'Diretriz fictícia autorizada','escopo':'Limites fictícios'},
       'aprendizagem_conferida':{'em':AGORA.isoformat()},'aprendizagem_autorizada':{'em':AGORA.isoformat()}}
    a['eventos'].append(NS(conteudo={'estado':deepcopy(e)}))
    novo=deepcopy(e);novo.pop('aprendizagem_autorizada');novo['aprendizagem']['diretriz']='Não autorizada'
    a['eventos'].append(NS(conteudo={'estado':novo}))
    q=c.aprendizados(dados)[0]
    assert q['numero']==1 and q['lista'][0]['diretriz']=='Diretriz fictícia autorizada'
    assert q['lista'][0]['contexto']=='Contexto não informado' and 'SEGREDO-FICTICIO' not in str(q)


@pytest.mark.parametrize('tela',['','/risco','/correcao','/operacao','/cobertura','/aprendizados','/circulacao'])
def test_telas_get_sem_gravacao_ou_texto_restrito(sessao,dados,tela):
    antes=[sessao.scalar(select(func.count()).select_from(m)) for m in (Evento,EventoAuditoria,Registro)]
    escritas=[]
    def observar(conn,cursor,statement,parameters,context,executemany):
        if statement.lstrip().split(' ',1)[0].upper() in ('INSERT','UPDATE','DELETE','CREATE','ALTER','DROP'):escritas.append(statement)
    event.listen(motor,'before_cursor_execute',observar)
    try:r=TestClient(app).get('/dashboard'+tela+'?conta_id=CONTA-B1')
    finally:event.remove(motor,'before_cursor_execute',observar)
    assert r.status_code==200,r.text
    assert not escritas
    depois=[sessao.scalar(select(func.count()).select_from(m)) for m in (Evento,EventoAuditoria,Registro)]
    assert antes==depois
    for proibido in ('Servidor Beta','Evento fictício','Justificativa fictícia','Providência fictícia do dashboard','PESSOA-B'):
        assert proibido not in r.text
    assert 'Somente leitura' in r.text


def test_secretario_nao_acessa_outra_secretaria_por_url(sessao,entrada):
    propria=entrada.unidade_id
    escopo=escopo_da_conta(sessao,SECRETARIO)
    assert propria in escopo.unidades
    outra=next(u for u in c.filtrar(carregar(sessao,escopo),escopo,{})['secretarias'] if u.id==propria)
    r=TestClient(app).get('/dashboard?conta_id='+SECRETARIO+'&secretaria=SECRETARIA-NAO-AUTORIZADA')
    assert r.status_code==403
    for destino in ('risco','correcao','operacao','cobertura','aprendizados','circulacao'):
        assert TestClient(app).get('/dashboard/'+destino+'?conta_id='+SECRETARIO+'&secretaria=SECRETARIA-NAO-AUTORIZADA').status_code==403


def test_arp_aal_restritos_e_perfis_globais(sessao,entrada):
    assert entrada.registro_id in escopo_da_conta(sessao,'CONTA-B1').registros
    for conta in ('CONTA-E1','CONTA-DEMO34-GAB','CONTA-DEMO34-RELAT','CONTA-DEMO34-VERIF'):
        e=escopo_da_conta(sessao,conta)
        assert e.registros is None and e.unidades is None
    assert TestClient(app).get('/dashboard?conta_id=CONTA-INEXISTENTE').status_code==403


def test_filtros_etapa_faixa_datas_e_segmentos_exclusivos(sessao,dados):
    escopo=dados['escopo']
    f=c.filtrar(dados,escopo,{'faixa':'Moderado'})
    q=c.esteira(f,{'faixa':'Moderado'})
    assert q[0]['numero'] is None and q[1]['numero'] is None
    assert q[2]['numero']==q[3]['numero']==1
    assert not c.filtrar(dados,escopo,{'faixa':'Crítico'})['registros']
    with pytest.raises(ValueError):c.filtrar(dados,escopo,{'inicio':'2026-11-21','fim':'2026-11-20'})


def test_reserva_sem_ingresso_nao_conta(sessao,entrada):
    from testes.test_lote11 import referencia,identidade
    ev=sessao.scalar(select(Evento).where(Evento.cadeia_id==entrada.id).order_by(Evento.id.desc()))
    ref=referencia(sessao,{'registro_id':entrada.registro_id,'fonte_form':2,'fonte_id':str(ev.id),'snapshot_id':entrada.snapshot_id})
    identidade(sessao,ref)
    d=carregar(sessao,escopo_da_conta(sessao,'CONTA-B1'))
    assert d['objetos']==[]


def test_circulacao_ausencia_nao_e_zero(sessao,dados):
    assert c.circulacao(dados,None)[0]['numero'] is None
    q=c.circulacao(dados,{r.id:dict(categorias=set(),instrumentos=set()) for r in dados['registros']})
    assert q[0]['numero']==0 and next(x for x in q if x['chave']=='instrumento_3')['numero']==1


def test_catalogo_circulacao_lido_sem_enunciados_ou_texto_livre(sessao,entrada):
    from app.dashboard.fontes import categorias_circulacao
    from app.respostas_form2 import definicao_revisao
    from app.form2_rev212 import RASCUNHO
    qs={q['id']:q for q in definicao_revisao(8)['itens']}
    categoria=qs['F2-8.2']['alternativas'][0]
    sim=next(a for a in qs['F2-8.7']['alternativas'] if a['rotulo']=='Sim')
    entrada.conteudo={RASCUNHO:{'8':{'opcao:F2-8.2#1':[categoria['codigo']],'opcao:F2-8.7#1':[sim['codigo']],
                                    'texto:F2-8.2#1':'NOME-PESSOAL-FICTICIO-NAO-EXIBIR'}}}
    sessao.commit()
    dados=carregar(sessao,escopo_da_conta(sessao,'CONTA-B1'))
    categorias=categorias_circulacao(dados)
    assert categorias is not None
    assert categoria['rotulo'] in categorias[entrada.registro_id]['categorias']
    assert categorias[entrada.registro_id]['instrumentos']=={'Sim'}
    assert 'NOME-PESSOAL' not in str(categorias)


def test_segunda_secretaria_zero_real_e_segregacao_de_registro(sessao,entrada):
    from uuid import uuid4
    from app.modelos import Unidade
    original=sessao.get(Registro,entrada.registro_id)
    escopo=escopo_da_conta(sessao,SECRETARIO)
    outra=sessao.scalar(select(Unidade).where(Unidade.ativa.is_(True),~Unidade.id.in_(escopo.unidades)))
    novo=Registro(id=str(uuid4()),codigo_lgpd='LGPD-2026-99001',tipo_objeto='processo',titulo_objeto='Objeto fictício externo',
        unidade_principal_atual_id=outra.id,contexto_atuacao_id=original.contexto_atuacao_id,ano_codigo=2026,numero_codigo=99001,
        criado_por=original.criado_por,ciclo_atual=1,estado_atual='em_andamento',sequencia_atual=0)
    sessao.add(novo);sessao.commit()
    client=TestClient(app)
    for conta in ('CONTA-B1',SECRETARIO):
        html=client.get('/dashboard?conta_id='+conta+'&lista=ativos').text
        assert 'LGPD-2026-99001' not in html
        assert client.get('/dashboard?conta_id='+conta+'&secretaria='+outra.id).status_code==403
    assert 'LGPD-2026-99001' in client.get('/dashboard?conta_id=CONTA-E1&lista=ativos').text
    escopo=escopo_da_conta(sessao,'CONTA-E1');d=carregar(sessao,escopo)
    cobertura=c.cobertura(d)
    assert any(l['total']==0 for l in cobertura[1]['lista'])
    assert cobertura[0]['numero']==sum(l['total']>0 for l in cobertura[1]['lista'])


def test_ripd_efeito_e_decisao_nao_inferida(sessao,dados):
    i=next(i for i in dados['objetos'] if i['obj'].tipo=='R');e=i['estado']
    e.update(triagem={'resultado':'elaborar'},triagem_confirmacoes={'secretaria':{},'dpo':{}})
    q={x['chave']:x for x in c.risco(dados)}
    assert q['ripd']['numero']==q['ripd_nao']['numero']==1
    assert q['ripd_sim']['numero']==0 and 'nenhuma redução' in q['efeito']['lista'][0]['situacao']
    assert q['riscos']['lista'][0]['decisao']=='Aguardando decisão'
    e['referencia_ripd']={'referencia':'REFERENCIA-FICTICIA-RESTRITA'}
    q={x['chave']:x for x in c.risco(dados)}
    assert q['ripd_sim']['numero']==1 and 'REFERENCIA-FICTICIA' not in str(q)


def test_composicoes_http_e_metodos_recusados(sessao,dados):
    client=TestClient(app)
    for chave,valor in [('ativos',1),('riscos',1),('matriz_residual_2_2',1),('matriz_residual_5_5',0),('acoes',1)]:
        r=client.get('/dashboard/risco?conta_id=CONTA-B1&lista='+chave)
        assert r.status_code==200
        assert 'Lista que compõe o indicador' in r.text
    assert client.post('/dashboard?conta_id=CONTA-B1',data={'acao':'qualquer'}).status_code==405
    assert client.get('/dashboard?conta_id=CONTA-B1&lista=inventada').status_code==404
    assert 'Abrir dashboard LGPD' in client.get('/central?conta_id=CONTA-B1').text
    # Exportação opcional para inspeção visual local, fora do Git e só com a massa _teste.
    import os
    from pathlib import Path
    pasta=os.getenv('LGPD_DASH_EVIDENCIAS')
    if pasta:
        destino=Path(pasta);destino.mkdir(parents=True,exist_ok=True)
        assets=(Path(__file__).parents[1]/'app/estaticos').as_uri()+'/'
        for tela in ('abertura','risco','correcao','operacao','cobertura','aprendizados','circulacao'):
            resposta=client.get('/dashboard'+('' if tela=='abertura' else '/'+tela)+'?conta_id=CONTA-DEMO34-GAB')
            assert resposta.status_code==200
            html=resposta.text.replace('http://testserver/estaticos/',assets).replace('"/estaticos/','"'+assets)
            (destino/(tela+'.html')).write_text(html,encoding='utf8')


def test_verificacao_recusada_nao_encerra_linha_tempo(sessao,dados):
    a=next(i for i in dados['objetos'] if i['obj'].tipo=='A')
    a['estado'].update(plano_aprovado={'em':AGORA.isoformat()},execucao={'em':AGORA.isoformat()},
        verificada=False,verificacao={'aprovada':False,'em':AGORA.isoformat()})
    linha=c.correcao(dados,AGORA)[0]['lista'][0]
    assert linha['fim'] is None and not linha['encerrada'] and linha['situacao']=='Em execução'


def test_matriz_usa_mesma_faixa_do_form3(sessao,dados):
    from app.avaliacao_risco34 import pontuar
    q={x['chave']:x for x in c.risco(dados)}
    for p in range(1,6):
        for i in range(1,6):
            assert q[f'matriz_residual_{p}_{i}']['faixa']==pontuar(p,i)['faixa']


def test_registro_concluido_nao_e_ativo(sessao,dados):
    dados['registros'][0].estado_atual='concluido'
    assert c.ativos(dados)['numero']==0


def test_link_ato_critico_so_quando_instruido(sessao,dados):
    i=next(i for i in dados['objetos'] if i['obj'].tipo=='R');e=i['estado']
    e['avaliacao']['residual'].update(faixa='Crítico',nota=25)
    q={x['chave']:x for x in c.atencao(dados,AGORA)}
    assert q['criticos']['numero']==0 and q['instrucao']['lista'][0]['ato'] is None
    e.update(manifestacao_dpo={'em':AGORA.isoformat()},manifestacao_comite={'em':AGORA.isoformat(),'finalidade':'residual'})
    q={x['chave']:x for x in c.atencao(dados,AGORA)}
    assert q['criticos']['lista'][0]['ato']==f"/forms34/{i['obj'].id}/blocos/16"


def test_paginas_com_aprendizado_autorizado_e_dados_de_projecao(sessao,dados,monkeypatch):
    """Retrato sintético de leitura; não carrega os casos da demonstração."""
    from app.dashboard import rotas
    from app.avaliacao_risco34 import pontuar
    from pathlib import Path
    import os
    r=next(i for i in dados['objetos'] if i['obj'].tipo=='R')
    r['estado']['avaliacao']['inerente']=pontuar(5,5)
    r['estado']['avaliacao']['residual']=pontuar(5,5)
    r['estado'].update(manifestacao_dpo={'em':AGORA.isoformat(),'texto':'MANIFESTACAO-RESTRITA'},
        manifestacao_comite={'em':AGORA.isoformat(),'finalidade':'residual','texto':'MANIFESTACAO-RESTRITA'})
    r['eventos']=[NS(tipo_evento='f34_manifestar_comite',ocorrido_em=AGORA,conteudo={'estado':deepcopy(r['estado'])})]
    a=next(i for i in dados['objetos'] if i['obj'].tipo=='A');e=a['estado']
    e.update(plano_aprovado={'em':AGORA.isoformat()},prazo='2026-11-25',verificada=True,
        verificacao={'em':AGORA.isoformat(),'aprovada':True},
        aprendizagem={'contexto':'Contexto fictício autorizado.','diretriz':'Orientação fictícia autorizada.','escopo':'Limites fictícios autorizados.'},
        aprendizagem_conferida={'em':AGORA.isoformat()},aprendizagem_autorizada={'em':AGORA.isoformat()})
    a['eventos']=[NS(tipo_evento='f34_aprovar_plano',ocorrido_em=AGORA,conteudo={'estado':deepcopy(e)})]
    monkeypatch.setattr(rotas,'carregar',lambda sessao,escopo:deepcopy(dados))
    monkeypatch.setattr(rotas,'categorias_circulacao',lambda d:{x.id:{'categorias':{'Destinatário fictício'},'instrumentos':{'Sim'}} for x in d['registros']})
    client=TestClient(app)
    for tela in rotas.TELAS:
        resposta=client.get('/dashboard/'+tela+'?conta_id=CONTA-DEMO34-GAB')
        assert resposta.status_code==200 and 'MANIFESTACAO-RESTRITA' not in resposta.text
        if tela=='aprendizados':assert 'Contexto fictício autorizado.' in resposta.text
        if tela=='circulacao':assert 'dash-circulacao' in resposta.text and 'Destinatário fictício' in resposta.text
        pasta=os.getenv('LGPD_DASH_EVIDENCIAS')
        if pasta:
            assets=(Path(__file__).parents[1]/'app/estaticos').as_uri()+'/'
            html=resposta.text.replace('http://testserver/estaticos/',assets).replace('"/estaticos/','"'+assets)
            Path(pasta,tela+'.html').write_text(html,encoding='utf8')


def test_espera_mediana_por_registro_sem_somar_participacoes():
    rs=[NS(id=str(n),codigo_lgpd='LGPD-FICTICIO-'+str(n),unidade_principal_atual_id='U-FICTICIA',tipo_objeto='servico') for n in (1,2)]
    ps=[NS(id=str(n),registro_id=rid,tipo='juridico',concluida_em=None,estado='aguardando',entrada_em=AGORA-timedelta(days=espera))
        for n,(rid,espera) in enumerate([('1',8),('1',2),('2',4)])]
    d=dict(registros=rs,secretarias=[NS(id='U-FICTICIA',nome='Unidade fictícia')],participacoes=ps,objetos=[])
    q={x['chave']:x for x in c.operacao(d,AGORA)}
    assert q['fila_Jurídico']['numero']==2 and q['participacoes']['numero']==3
    assert q['fila_Jurídico']['mediana']==6 and q['fila_Jurídico']['maior']==8


def test_espera_cancelamento_dpo_usa_pedido_atual_e_fecha_na_manifestacao(sessao,dados):
    a=next(i for i in dados['objetos'] if i['obj'].tipo=='A');dados['objetos']=[a]
    e=a['estado'];e['faixa_origem']='Alto'
    e['manifestacao_dpo']={'em':(AGORA-timedelta(days=4)).isoformat()}
    antes=deepcopy(e)
    e['decisoes_pendentes']={'cancelamento':{'em':(AGORA-timedelta(days=3)).isoformat()}}
    a['eventos']=[NS(ocorrido_em=AGORA-timedelta(days=4),conteudo={'estado':antes}),
        NS(ocorrido_em=AGORA-timedelta(days=3),conteudo={'estado':deepcopy(e)})]
    q={x['chave']:x for x in c.operacao(dados,AGORA)}
    assert q['fila_DPO']['numero']==1 and q['fila_DPO']['lista'][0]['dias']==3
    e['manifestacao_dpo']={'em':AGORA.isoformat()}
    a['eventos'].append(NS(ocorrido_em=AGORA,conteudo={'estado':deepcopy(e)}))
    q={x['chave']:x for x in c.operacao(dados,AGORA)}
    assert q['fila_DPO']['numero']==0 and q['fila_Secretário']['lista'][0]['dias']==0
