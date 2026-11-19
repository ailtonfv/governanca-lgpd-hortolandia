"""Regras demonstrativas; massa sintética e atos reais do domínio."""
from testes.apoio_r17 import completo2, preencher34
from copy import deepcopy
from datetime import date, timedelta
from uuid import uuid4
import pytest
from sqlalchemy import select, func
from app.banco import motor
from app.modelos import (Evento, ParticipacaoForm2, IdentidadeForms34, Designacao, Conta,
                         ReferenciaParticipacaoForms34, ReferenciaRestritaForms34)
from app.fluxo_forms34 import ingressar, executar, estado, em_atraso, consultar, registrar_referencia_restrita
from app.avaliacao_risco34 import pontuar, propor_avaliacao
from app.fila_form2 import executar as ato_fila
from testes.test_lote11 import fonte

SECRETARIO = 'CONTA-DEMO34-SECULT'
PREFEITO = 'CONTA-DEMO34-GAB'  # Registra a decisão formal do Prefeito.
RELATOR = 'CONTA-DEMO34-RELAT'
VERIFICADOR = 'CONTA-DEMO34-VERIF'


@pytest.fixture(scope='module', autouse=True)
def protecoes(esquema):
    from migracoes.atos_forms34 import aplicar
    aplicar(motor)


@pytest.fixture
def entrada(sessao, fonte):
    from carga_ficticia.atores_forms34 import semear
    semear(sessao)
    p = sessao.get(ParticipacaoForm2, fonte['form2_id'])
    sessao.add(Designacao(pessoa_id='PESSOA-B', unidade_id=p.unidade_id,papel='aal_form2',ativa=True))
    sessao.flush()
    ato_fila(sessao, conta_id='CONTA-B1', comando_id=str(uuid4()), participacao_id=p.id,
             acao='assumir', versao=p.versao)
    # Massa sintética autoriza secretário na unidade do teste, sem mudar a carga demonstrativa.
    sessao.add(Designacao(pessoa_id='PESSOA-DEMO34-SECULT', unidade_id=p.unidade_id,
                         papel='demo34_secretario'))
    p.conteudo = completo2({'rascunho_form2_rev21_2': {'14': {'opcao:F2-14.5':['SIM'], 'opcao:F2-14.6':['SIM']}}})
    sessao.commit()
    return p


def entrar(s, p, form=3, **kw):
    d = dict(conta_id='CONTA-B1', comando_id=str(uuid4()), participacao_id=p.id,
             versao=p.versao, form=form)
    d.update(kw)
    r = ingressar(s, **d)
    s.commit()
    return r['identidade_id']


def ato(s, obj, acao, conta='CONTA-B1', **dados):
    r = executar(s, conta_id=conta, comando_id=str(uuid4()), identidade_id=obj,
                 versao=estado(s,obj)['versao'], acao=acao, dados=dados)
    s.commit()
    return r


def avaliar(s, obj, nota=2):
    ato(s,obj,'propor_avaliacao',evento='Evento fictício',causa='Causa fictícia',
        consequencia='Consequência fictícia',p=nota,i=nota,pr=nota,ir=nota,
        justificativa='Justificativa fictícia', controles=[])
    ato(s,obj,'confirmar_avaliacao',conta='CONTA-E1')


@pytest.mark.parametrize('p,i', [(p,i) for p in range(1,6) for i in range(1,6)])
def test_escala_25_combinacoes(p,i):
    r = pontuar(p,i)
    assert r['nota']==p*i
    assert r['faixa']==('Pequeno' if p*i<=3 else 'Moderado' if p*i<=6 else 'Alto' if p*i<=12 else 'Crítico')
    assert r['d11']


@pytest.mark.parametrize('p,i', [(None,None),(None,4),(3,None)])
def test_nao_avaliado_nao_zero(p,i):
    assert pontuar(p,i)['nota'] is None
    assert pontuar(p,i)['faixa']=='Não avaliado'


@pytest.mark.parametrize('valor', [0,6,True,'3',2.5])
def test_escala_recusa_invalido(valor):
    with pytest.raises(ValueError):pontuar(valor,2)


@pytest.mark.parametrize('controles', [[],[{'implementado':False,'evidencia':'Fictícia'}],[{'implementado':True,'evidencia':''}]])
def test_reducao_sem_controle_comprovado_recusada(controles):
    with pytest.raises(ValueError,match='implementado'):
        propor_avaliacao(dict(p=5,i=5,pr=2,ir=2,controles=controles,justificativa='Fictícia'))


def test_reducao_com_evidencia():
    a=propor_avaliacao(dict(p=5,i=5,pr=2,ir=2,controles=[{'implementado':True,'evidencia':'Fictícia'}],justificativa='Fictícia'))
    assert a['residual']['nota']==4


def test_ingresso_fonte_congelada_idempotencia(sessao,entrada):
    chave=str(uuid4())
    obj=entrar(sessao,entrada,comando_id=chave)
    ref=sessao.get(ReferenciaParticipacaoForms34,sessao.get(IdentidadeForms34,obj).participacao_id)
    lacre=ref.fonte_lacre
    assert entrar(sessao,entrada,comando_id=chave)==obj
    entrada.conteudo={'fato_posterior':'Fictício'};entrada.versao+=1;sessao.commit()
    sessao.refresh(ref)
    assert ref.fonte_lacre==lacre
    assert 'fato_posterior' not in ref.fonte_canonica


@pytest.mark.parametrize('conta',['CONTA-A1','CONTA-G1','CONTA-E1',PREFEITO])
def test_ingresso_so_aal(sessao,entrada,conta):
    with pytest.raises(PermissionError):entrar(sessao,entrada,conta_id=conta)
    assert sessao.scalar(select(func.count()).select_from(IdentidadeForms34))==0


def test_sinal_exige_fundamentacao_acao_direta(sessao,entrada):
    entrada.conteudo=completo2({'rascunho_form2_rev21_2':{'4':{'opcao:F2-4.1':['SIM']},'14':{'opcao:F2-14.5':['NAO'],'opcao:F2-14.6':['SIM']}}})
    sessao.commit()
    with pytest.raises(ValueError,match='justificativa'):entrar(sessao,entrada,4)
    obj=entrar(sessao,entrada,4,justificativa='Correção imediata fictícia, avaliação posterior fundamentada.')
    assert estado(sessao,obj)['avaliacao'] is None


def test_nota_sem_segunda_confirmacao_e_sem_consenso(sessao,entrada):
    obj=entrar(sessao,entrada)
    ato(sessao,obj,'propor_avaliacao',evento='Fictício',causa='Fictícia',consequencia='Fictícia',p=2,i=2,pr=2,ir=2,justificativa='Fictícia')
    with pytest.raises(ValueError,match='duas confirmações'):ato(sessao,obj,'aceitar_residual',conta=SECRETARIO,justificativa='Fictícia')
    ato(sessao,obj,'sem_consenso',conta='CONTA-E1',campo='avaliacao',posicao='Discordância fictícia')
    e=estado(sessao,obj)
    assert e['avaliacao']['residual']['nota']==4 and e['avaliacao_confirmacoes']=={}
    with pytest.raises(ValueError,match='Sem consenso'):ato(sessao,obj,'confirmar_avaliacao',conta='CONTA-E1')


def test_prefeito_fora_critico_e_dpo_aceitando_recusados(sessao,entrada):
    obj=entrar(sessao,entrada);avaliar(sessao,obj)
    for conta in (PREFEITO,'CONTA-E1','CONTA-B1'):
        with pytest.raises(PermissionError):ato(sessao,obj,'aceitar_residual',conta=conta,justificativa='Fictícia')
    ato(sessao,obj,'aceitar_residual',conta=SECRETARIO,justificativa='Fictícia')
    assert estado(sessao,obj)['aceitacao']['pessoa_id']=='PESSOA-DEMO34-SECULT'


def preparar_acao(s,p):
    obj=entrar(s,p,4)
    preencher34(s,obj)
    ato(s,obj,'planejar',plano='Plano fictício',cargo='Chefia da unidade',prazo=(date.today()-timedelta(days=2)).isoformat())
    ato(s,obj,'aprovar_plano',conta=SECRETARIO,justificativa='Fictícia')
    return obj


def test_verificacao_segregacao_encerramento_aprendizagem(sessao,entrada):
    obj=preparar_acao(sessao,entrada)
    with pytest.raises(ValueError,match='após verificação'):ato(sessao,obj,'aprender',diretriz='Fictícia',escopo='Fictício')
    with pytest.raises(PermissionError):ato(sessao,obj,'executar_medida',conta='CONTA-E1',evidencia='Fictícia')
    ato(sessao,obj,'executar_medida',evidencia='Fictícia')
    for conta in ('CONTA-B1','CONTA-E1',RELATOR):
        with pytest.raises(PermissionError):ato(sessao,obj,'verificar',conta=conta,aprovada=True,evidencia='Fictícia')
    ato(sessao,obj,'verificar',conta=VERIFICADOR,aprovada=True,evidencia='Fictícia')
    assert estado(sessao,obj)['encerrada']
    assert not em_atraso(estado(sessao,obj))
    ato(sessao,obj,'aprender',diretriz='Diretriz fictícia',escopo='Escopo fictício')
    with pytest.raises(ValueError,match='DPO'):ato(sessao,obj,'autorizar_aprendizagem')
    ato(sessao,obj,'conferir_aprendizagem',conta='CONTA-E1',sem_dados_pessoais=True)
    ato(sessao,obj,'autorizar_aprendizagem')
    assert estado(sessao,obj)['aprendizagem_autorizada']


def test_segunda_prorrogacao_exige_comite_e_ciencia_prefeito(sessao,entrada):
    obj=preparar_acao(sessao,entrada)
    assert em_atraso(estado(sessao,obj))
    ato(sessao,obj,'pedir_prorrogacao',prazo=(date.today()+timedelta(days=1)).isoformat(),justificativa='Fictícia')
    assert em_atraso(estado(sessao,obj))
    ato(sessao,obj,'decidir_prorrogacao',conta=SECRETARIO,aprovar=True,justificativa='Fictícia')
    ato(sessao,obj,'pedir_prorrogacao',prazo=(date.today()+timedelta(days=2)).isoformat(),justificativa='Fictícia')
    with pytest.raises(ValueError,match='Comitê'):ato(sessao,obj,'decidir_prorrogacao',conta=SECRETARIO,aprovar=True,justificativa='Fictícia')
    ato(sessao,obj,'manifestar_comite',conta=RELATOR,finalidade='prorrogacao',ata='Ata fictícia',texto='Contrária',favoravel=False)
    ato(sessao,obj,'decidir_prorrogacao',conta=SECRETARIO,aprovar=True,justificativa='Manutenção fundamentada fictícia')
    assert estado(sessao,obj)['ciencia_prefeito']['automatica']
    assert sessao.scalar(select(Evento.id).where(Evento.cadeia_id==obj,Evento.tipo_evento=='f34_ciencia_prefeito'))


def test_cancelamento_nao_conclusao(sessao,entrada):
    obj=preparar_acao(sessao,entrada)
    ato(sessao,obj,'pedir_cancelamento',justificativa='Fictícia')
    assert em_atraso(estado(sessao,obj))
    ato(sessao,obj,'cancelar',conta=SECRETARIO,justificativa='Fictícia')
    e=estado(sessao,obj)
    assert e['cancelada'] and not e['verificada'] and not e.get('encerrada')


def test_versao_desatualizada_sem_evento(sessao,entrada):
    obj=entrar(sessao,entrada)
    antes=sessao.scalar(select(func.count()).select_from(Evento))
    with pytest.raises(ValueError,match='mudou'):
        executar(sessao,conta_id='CONTA-B1',comando_id=str(uuid4()),identidade_id=obj,
                 versao=1,acao='manifestar_dpo',dados={'texto':'Fictício'})
    assert sessao.scalar(select(func.count()).select_from(Evento))==antes


@pytest.mark.parametrize('nome',['lgpd_poc','lgpd_lote9_ce2bb69b0f22','lgpd_lote11_exemplo','lgpd_lote12_outro','lgpd_lote12_3be0186939a7_teste'])
def test_migracao_excecao_exata(nome):
    from types import SimpleNamespace
    from migracoes.base_forms34 import aplicar_copia_8013
    with pytest.raises(RuntimeError):aplicar_copia_8013(SimpleNamespace(url=SimpleNamespace(database=nome)))


def test_critico_triagem_conjunta_e_autoridade(sessao,entrada):
    obj=entrar(sessao,entrada);avaliar(sessao,obj,5)
    with pytest.raises(PermissionError):ato(sessao,obj,'aceitar_residual',conta=SECRETARIO,justificativa='Fictícia')
    with pytest.raises(ValueError,match='DPO'):ato(sessao,obj,'aceitar_residual',conta=PREFEITO,documento='OFICIO-FICTICIO-12E',justificativa='Fictícia')
    ato(sessao,obj,'manifestar_dpo',conta='CONTA-E1',texto='Manifestação fictícia')
    with pytest.raises(ValueError,match='Comitê'):ato(sessao,obj,'aceitar_residual',conta=PREFEITO,documento='OFICIO-FICTICIO-12E',justificativa='Fictícia')
    ato(sessao,obj,'manifestar_comite',conta=RELATOR,finalidade='residual',ata='Ata fictícia',texto='Deliberação fictícia',favoravel=True)
    ato(sessao,obj,'aceitar_residual',conta=PREFEITO,documento='OFICIO-FICTICIO-12E',justificativa='Fictícia')
    with pytest.raises(ValueError,match='triagem'):ato(sessao,obj,'concluir_avaliacao')
    ato(sessao,obj,'propor_triagem',resultado='elaborar',justificativa='Fictícia',unidade_id='UNID-NORTE')
    with pytest.raises(ValueError,match='triagem'):ato(sessao,obj,'concluir_avaliacao')
    ato(sessao,obj,'confirmar_triagem',conta='CONTA-E1')
    ato(sessao,obj,'confirmar_gatilho_juridico',restringe_direitos=True)
    preencher34(sessao,obj)
    ato(sessao,obj,'concluir_avaliacao')
    assert estado(sessao,obj)['situacao']=='Avaliação concluída'
    assert estado(sessao,obj)['juridico']=='manifestação jurídica esperada'


def test_referencia_restrita_nao_vaza_e_recusa_url(sessao,entrada):
    from app.restrito_forms34 import ler
    from fastapi.testclient import TestClient
    from app.main import app
    obj=entrar(sessao,entrada)
    sessao.add(Designacao(pessoa_id='PESSOA-C',unidade_id='SEC-AJ',papel='juridico_form2'))
    sessao.commit()
    ato(sessao,obj,'enviar_juridico',destinatario_id='PESSOA-C',motivo='Questão fictícia')
    registrar_referencia_restrita(sessao,conta_id='CONTA-C1',comando_id=str(uuid4()),identidade_id=obj,
        versao=estado(sessao,obj)['versao'],dados={'referencia':'REF-FICTICIA-RESTRITA','conclusao':'Parecer fictício reservado'})
    sessao.commit()
    assert ler(sessao,'CONTA-C1',obj).conteudo['referencia']=='REF-FICTICIA-RESTRITA'
    with pytest.raises(PermissionError):ler(sessao,SECRETARIO,obj)
    sessao.commit()
    client=TestClient(app)
    assert client.get(f'/forms34/{obj}/referencia-restrita?conta_id={SECRETARIO}').status_code==403
    assert client.get(f'/forms34/{obj}/referencia-restrita?conta_id=CONTA-C1').status_code==200
    texto=client.get(f'/forms34/{obj}/blocos/16?conta_id=CONTA-B1').text
    assert 'REF-FICTICIA-RESTRITA' not in texto and 'Parecer fictício reservado' not in texto
    assert all('REF-FICTICIA-RESTRITA' not in e.payload_canonico for e in sessao.scalars(select(Evento)))


@pytest.mark.parametrize('form,quantidade',[(3,16),(4,9)])
def test_todas_telas_grade_catalogo_privado(sessao,entrada,form,quantidade):
    from fastapi.testclient import TestClient
    from app.main import app
    obj=entrar(sessao,entrada,form)
    client=TestClient(app)
    for bloco in range(1,quantidade+1):
        response=client.get(f'/forms34/{obj}/blocos/{bloco}?conta_id=CONTA-B1')
        assert response.status_code==200,response.text[:500]
        assert response.text.count('aria-current="page"')==1
        assert 'Você está aqui' in response.text
        assert 'Controle candidato' not in response.text
        assert f'F{form}-' in response.text
    assert client.get(f'/forms34/{obj}/blocos/1?conta_id=CONTA-D1').status_code==403


def test_questionario_condicoes_exclusividade_e_recolhimento():
    from app.questionario_forms34 import salvar,perguntas,ativa,recolhida,DETALHES4
    assert len(DETALHES4)==15 and len(perguntas(4))==39 and len(perguntas(3))==77
    itens={q['id']:q for q in perguntas(3)}
    for id in ('F3-3.16','F3-3.17','F3-3.20','F3-3.21','F3-3.24','F3-3.35','F3-3.38'):
        assert not recolhida(itens[id],{}, {})
    assert not ativa(itens['F3-3.40'],{'F3-3.39':'Não'}, {})
    with pytest.raises(ValueError,match='bloqueada'):
        salvar(3,{'F3-3.39':'Não'},{'bloco':11,'campos':{'F3-3.40':'Sim'}},{})
    with pytest.raises(ValueError,match='sozinha'):
        salvar(3,{}, {'bloco':3,'campos':{'F3-3.10':['A confirmar','Larga escala']}},{})


def test_http_post_forged_condicional(sessao,entrada):
    from fastapi.testclient import TestClient
    from app.main import app
    obj=entrar(sessao,entrada)
    client=TestClient(app)
    r=client.post(f'/forms34/{obj}/blocos/11?conta_id=CONTA-B1',data={
        'acao':'salvar_bloco','versao':str(estado(sessao,obj)['versao']),'comando_id':str(uuid4()),
        'F3-3.39':'Não','F3-3.40':'Sim'})
    assert r.status_code==409
    assert not estado(sessao,obj)['respostas']


def test_multiplos_riscos_identidade_e_origem(sessao,entrada):
    obj=entrar(sessao,entrada)
    r=ato(sessao,obj,'adicionar_risco',motivo='Outro evento fictício')
    novo=sessao.get(IdentidadeForms34,r['identidade_id'])
    antigo=sessao.get(IdentidadeForms34,obj)
    assert novo.id!=antigo.id and novo.numero==antigo.numero+1
    assert novo.participacao_id==antigo.participacao_id


def test_executor_mesma_pessoa_com_outra_conta_nao_verifica(sessao,entrada):
    obj=preparar_acao(sessao,entrada)
    ato(sessao,obj,'executar_medida',evidencia='Fictícia')
    sessao.add(Conta(id='CONTA-B-EXTRA-FICT',pessoa_id='PESSOA-B'))
    sessao.add(Designacao(pessoa_id='PESSOA-B',unidade_id='SEC-ESP',papel='demo34_verificador'))
    sessao.commit()
    with pytest.raises(PermissionError,match='independente'):
        ato(sessao,obj,'verificar',conta='CONTA-B-EXTRA-FICT',aprovada=True,evidencia='Fictícia')


def test_pedido_pendente_impede_so_encerramento(sessao,entrada):
    obj=preparar_acao(sessao,entrada)
    ato(sessao,obj,'pedir_prorrogacao',prazo=(date.today()+timedelta(days=1)).isoformat(),justificativa='Fictícia')
    ato(sessao,obj,'executar_medida',evidencia='Fictícia')
    ato(sessao,obj,'verificar',conta=VERIFICADOR,aprovada=True,evidencia='Fictícia')
    assert not estado(sessao,obj).get('encerrada')
    ato(sessao,obj,'decidir_prorrogacao',conta=SECRETARIO,aprovar=False,justificativa='Fictícia')
    assert estado(sessao,obj)['encerrada']

def test_modelo_ripd_pagina_interna(sessao,entrada):
    from fastapi.testclient import TestClient
    from app.main import app
    obj=entrar(sessao,entrada)
    client=TestClient(app)
    pagina=client.get(f'/forms34/{obj}/blocos/15?conta_id=CONTA-B1')
    assert f'/forms34/{obj}/modelo-ripd?conta_id=CONTA-B1' in pagina.text
    resposta=client.get(f'/forms34/{obj}/modelo-ripd?conta_id=CONTA-B1')
    assert resposta.status_code==200
    assert resposta.headers['content-type'].startswith('text/html')
    assert 'content-disposition' not in resposta.headers
    assert '[D11] proposta em deliberação' in resposta.text
    assert '13. Histórico de revisões' in resposta.text
    assert 'Voltar ao bloco 15' in resposta.text
    assert '@AILTON' not in resposta.text
    assert client.get(f'/forms34/{obj}/modelo-ripd?conta_id=CONTA-D1').status_code==403

def test_http_encaminhamento_abre_primeiro_bloco_form4(sessao,entrada):
    from fastapi.testclient import TestClient
    from app.main import app
    obj=entrar(sessao,entrada)
    client=TestClient(app)
    r=client.post(f'/forms34/{obj}/blocos/16?conta_id=CONTA-B1',data={
        'acao':'encaminhar_acao','versao':str(estado(sessao,obj)['versao']),
        'comando_id':str(uuid4()),'justificativa':'Providência fictícia'},follow_redirects=False)
    assert r.status_code==303
    assert '/blocos/1?' in r.headers['location']
    assert f'/forms34/{obj}/' not in r.headers['location']
    pagina=client.get(r.headers['location'])
    assert pagina.status_code==200 and 'FORM 4 · Bloco 1' in pagina.text


def test_http_limpar_selecao_multipla(sessao,entrada):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.questionario_forms34 import perguntas
    obj=entrar(sessao,entrada)
    q=next(q for q in perguntas(3) if q['id']=='F3-3.10')
    ato(sessao,obj,'salvar_bloco',bloco=q['bloco'],campos={q['id']:[q['opcoes'][0]]})
    response=TestClient(app).post(f'/forms34/{obj}/blocos/{q["bloco"]}?conta_id=CONTA-B1',data={
        'acao':'salvar_bloco','versao':str(estado(sessao,obj)['versao']),
        'comando_id':str(uuid4()),'presente:'+q['id']:'1'},follow_redirects=False)
    assert response.status_code==303
    assert estado(sessao,obj)['respostas'][q['id']]==[]
    assert 'F3-3.10' not in estado(sessao,obj)['sinais']


def test_nao_cria_risco_dentro_form4(sessao,entrada):
    obj=entrar(sessao,entrada,4)
    preencher34(sessao,obj)
    antes=estado(sessao,obj)
    with pytest.raises(ValueError,match='FORM 3'):
        ato(sessao,obj,'adicionar_risco',motivo='Fictício')
    assert estado(sessao,obj)==antes

def test_percurso_critico_dez_passos_sem_secretario_de_outra_unidade(sessao,entrada):
    # Arrange: same domain acts as the 8013 walkthrough; no Secretary approval.
    risco=entrar(sessao,entrada)
    avaliar(sessao,risco,5)
    ato(sessao,risco,'manifestar_dpo',conta='CONTA-E1',texto='Manifestação fictícia')
    ato(sessao,risco,'propor_triagem',resultado='elaborar',unidade_id=entrada.unidade_id,
        justificativa='Triagem fictícia')
    ato(sessao,risco,'confirmar_triagem',conta='CONTA-E1')
    ato(sessao,risco,'manifestar_comite',conta=RELATOR,finalidade='residual',
        ata='ATA-FICT-12',texto='Deliberação fictícia',favoravel=True)
    ato(sessao,risco,'aceitar_residual',conta=PREFEITO,documento='OFICIO-FICTICIO-12E',justificativa='Aceitação fictícia')
    preencher34(sessao,risco)
    ato(sessao,risco,'concluir_avaliacao')
    # Act: pass from the frozen risk version to an action and complete the cycle.
    acao=ato(sessao,risco,'encaminhar_acao',justificativa='Providência fictícia')['identidade_id']
    assert acao!=risco
    ato(sessao,acao,'planejar',plano='Plano fictício verificável',cargo='Chefia da unidade',
        prazo=(date.today()+timedelta(days=10)).isoformat())
    ato(sessao,acao,'aprovar_plano',conta=PREFEITO,documento='OFICIO-FICTICIO-12E',justificativa='Aprovação fictícia')
    ato(sessao,acao,'executar_medida',evidencia='Evidência fictícia')
    preencher34(sessao,acao)
    ato(sessao,acao,'verificar',conta=VERIFICADOR,aprovada=True,evidencia='Conferência fictícia')
    ato(sessao,acao,'aprender',diretriz='Diretriz fictícia',escopo='Escopo fictício')
    ato(sessao,acao,'conferir_aprendizagem',conta='CONTA-E1',sem_dados_pessoais=True)
    ato(sessao,acao,'autorizar_aprendizagem')
    # Assert: correct origin, independent verification and explicit learning authorization.
    e=estado(sessao,acao)
    assert e['faixa_origem']=='Crítico' and e['risco_id']==risco
    assert e['encerrada'] and e['verificacao']['pessoa_id']!='PESSOA-B'
    assert e['aprendizagem_autorizada']
