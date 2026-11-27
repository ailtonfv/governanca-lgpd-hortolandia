"""Temas fechados, validação no domínio e versão pública preservada."""
from uuid import uuid4
from types import SimpleNamespace
import pytest
from sqlalchemy import select, func
from app.modelos import Tema, Evento
from app.temas_form4 import validar, nomes
from app.fluxo_forms34 import estado, executar
from app.pedidos_tema import consultar as pedidos
from app.aprendizados_publicos import consultar
from app.main import app
from testes.apoio_entrada import ClienteAposApresentacao as TestClient
from testes.test_lote12 import entrada, fonte, protecoes, entrar, ato, SECRETARIO, VERIFICADOR
from testes.apoio_r17 import preencher34
from app.etapas_forms34 import VERIFICACAO


def test_catalogo_nao_reutiliza_nem_reativa(sessao):
    from carga_ficticia.temas_form4 import semear
    assert sessao.scalar(select(func.count()).select_from(Tema))==19
    t=sessao.get(Tema,'T07');t.ativo=False;sessao.flush();semear(sessao)
    assert not t.ativo
    assert 'desativado' in nomes(sessao,{'principal':'T07'})[0]
    with pytest.raises(ValueError):validar(sessao,'T07')
    t.nome='Outro tema fictício';sessao.flush()
    with pytest.raises(ValueError,match='já utilizado'):semear(sessao)


def test_migracao_recusa_outras_copias():
    from migracoes.temas_form4 import aplicar
    for nome in ('lgpd_lote13_020f86384138','lgpd_lote12_3be0186939a7','lgpd_poc','lgpd_lote14_outro'):
        for excepcional in (False,True):
            with pytest.raises(RuntimeError):aplicar(SimpleNamespace(url=SimpleNamespace(database=nome)),vistoria_8015=excepcional)


def test_plano_exige_tema_sem_bloquear_parcial(sessao,entrada):
    obj=entrar(sessao,entrada,4)
    preencher34(sessao,obj)
    assert not estado(sessao,obj).get('temas')
    c=TestClient(app)
    assert 'Tema não informado' in c.get(f'/forms34/{obj}/blocos/3?conta_id=CONTA-B1').text
    ato(sessao,obj,'salvar_temas',tema_principal='',temas_complementares=[])
    antes=estado(sessao,obj)
    for principal,complementares in [('',[]),('T07',['T01','T02','T03']),('T07',['T07']),('T07',['T01','T01']),('T99',[])]:
        with pytest.raises(ValueError):
            ato(sessao,obj,'planejar',plano='Plano fictício para revisar e documentar os acessos.',cargo='Equipe da unidade executora',duracao_dias=30,tema_principal=principal,temas_complementares=complementares)
        sessao.rollback()
        assert estado(sessao,obj)==antes
    ato(sessao,obj,'planejar',plano='Plano fictício para revisar e documentar os acessos.',cargo='Equipe da unidade executora',duracao_dias=30,tema_principal='T07',temas_complementares=['T09','T04'])
    assert estado(sessao,obj)['temas']['principal']=='T07'
    assert obj in c.get('/forms34?conta_id=CONTA-B1&tema=T04').text
    assert obj not in c.get('/forms34?conta_id=CONTA-B1&tema=T03').text
    ato(sessao,obj,'aprovar_plano',conta=SECRETARIO,justificativa='Aprovação fictícia')
    with pytest.raises(ValueError):ato(sessao,obj,'salvar_temas',tema_principal='T01')


def test_pedido_idempotente_nao_cria_tema(sessao,entrada):
    obj=entrar(sessao,entrada,4)
    cmd=str(uuid4());versao=estado(sessao,obj)['versao']
    kw=dict(conta_id='CONTA-B1',comando_id=cmd,identidade_id=obj,versao=versao,acao='solicitar_tema',dados={'nome_sugerido':'Tema fictício proposto','justificativa':'Justificativa fictícia'})
    r=executar(sessao,**kw);sessao.commit()
    repetido=executar(sessao,**kw)
    assert repetido['reexecutado'] and repetido['versao']==r['versao']
    assert sessao.scalar(select(func.count()).select_from(Tema))==19
    assert len(pedidos(sessao,'CONTA-E1'))==1
    assert pedidos(sessao,'CONTA-E1')[0]['situacao']=='Em análise'
    assert TestClient(app).get('/temas/pedidos?conta_id=CONTA-B1').status_code==403
    assert TestClient(app).get('/temas/pedidos?conta_id=CONTA-E1').status_code==200
    with pytest.raises(ValueError):ato(sessao,obj,'solicitar_tema',nome_sugerido='Fictício',justificativa='')


def test_migracao_aditiva_idempotente_e_tela(sessao,entrada):
    from migracoes.temas_form4 import aplicar
    from app.banco import motor
    obj=entrar(sessao,entrada,4)
    antes=estado(sessao,obj)
    aplicar(motor);aplicar(motor)
    assert estado(sessao,obj)==antes
    assert sessao.scalar(select(func.count()).select_from(Tema))==19
    c=TestClient(app)
    url=f'/forms34/{obj}/blocos/3?conta_id=CONTA-B1'
    pagina=c.get(url)
    assert pagina.status_code==200 and 'Use quando:' in pagina.text
    assert 'name="temas_complementares"' in pagina.text
    resposta=c.post(url,data=dict(acao='salvar_temas',versao=antes['versao'],comando_id=str(uuid4()),tema_principal='T07',temas_complementares=['T04','T09']))
    assert resposta.status_code==200
    assert estado(sessao,obj)['temas']=={'principal':'T07','complementares':['T04','T09']}
    antes=estado(sessao,obj)
    recusado=c.post(url,data=dict(acao='planejar',titulo_providencia='Revisar acessos fictícios',versao=antes['versao'],comando_id=str(uuid4()),plano='Plano fictício para revisar e documentar os acessos.',cargo='Equipe da unidade executora',duracao_dias=30,tema_principal=''))
    assert recusado.status_code==409 and 'tema principal' in recusado.text
    assert estado(sessao,obj)==antes


def test_temas_aprendizado_versao_e_busca_outra_unidade(sessao,entrada):
    obj=entrar(sessao,entrada,4);preencher34(sessao,obj)
    ato(sessao,obj,'planejar',plano='Plano fictício para revisar e documentar os acessos.',cargo='Equipe da unidade executora',duracao_dias=30,tema_principal='T07',temas_complementares=['T09'])
    ato(sessao,obj,'aprovar_plano',conta=SECRETARIO,justificativa='Aprovação fictícia')
    ato(sessao,obj,'executar_medida',resumo='Execução fictícia: acessos revisados e documentados.',evidencia='Arquivo fictício')
    ato(sessao,obj,'verificar',conta=VERIFICADOR,aprovada=True,evidencia='Verificação fictícia',**{k:'Sim' for k in VERIFICACAO})
    ato(sessao,obj,'aprender',contexto='Contexto fictício',diretriz='Diretriz fictícia',escopo='Limites fictícios')
    ato(sessao,obj,'conferir_aprendizagem',conta='CONTA-E1',sem_dados_pessoais=True,sem_falha_exposta=True)
    ato(sessao,obj,'autorizar_aprendizagem')
    assert consultar(sessao,'CONTA-C1',tema='T09')['total']==1
    ato(sessao,obj,'aprender',contexto='Contexto fictício revisto',diretriz='Diretriz fictícia nova',escopo='Limites fictícios',tema_principal='T01',temas_complementares=['T02'])
    assert estado(sessao,obj)['aprendizagem']['versao']==2
    assert consultar(sessao,'CONTA-C1',tema='T09')['total']==1
    assert consultar(sessao,'CONTA-C1',tema='T02')['total']==0
    ato(sessao,obj,'conferir_aprendizagem',conta='CONTA-E1',sem_dados_pessoais=True,sem_falha_exposta=True)
    ato(sessao,obj,'autorizar_aprendizagem')
    assert consultar(sessao,'CONTA-C1',tema='T09')['total']==0
    assert consultar(sessao,'CONTA-C1',tema='T02')['total']==1
    assert TestClient(app).get(f'/forms34/{obj}/blocos/1?conta_id=CONTA-C1').status_code==403
