"""12-E: decisões explícitas, leitura e permissões; apenas massa fictícia."""
from copy import deepcopy
from uuid import uuid4
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.modelos import Evento, Designacao
from app.fluxo_forms34 import executar
from app.atos_forms34_interface import disponiveis
from app.regras_atos34 import finalidades
from testes.test_lote12 import (protecoes, entrada, fonte, entrar, ato, estado,
    avaliar, preparar_acao, SECRETARIO, RELATOR, VERIFICADOR)

GABINETE='CONTA-DEMO34-GAB'

def html(obj,bloco,conta='CONTA-B1'):
    r=TestClient(app).get(f'/forms34/{obj}/blocos/{bloco}?conta_id={conta}')
    assert r.status_code==200
    return r.text

def test_ripd_referencia_autoria_idempotencia_e_recusa(sessao,entrada):
    obj=entrar(sessao,entrada)
    assert 'RIPD: referência não informada.' in html(obj,15)
    antes=deepcopy(estado(sessao,obj))
    with pytest.raises(PermissionError):ato(sessao,obj,'informar_ripd',conta=GABINETE,referencia='PROC-FICTICIO')
    assert estado(sessao,obj)==antes
    comando=str(uuid4());versao=antes['versao']
    args=dict(conta_id='CONTA-B1',comando_id=comando,identidade_id=obj,versao=versao,
              acao='informar_ripd',dados={'referencia':'PROCESSO-FICTICIO-12E'})
    primeiro=executar(sessao,**args);sessao.commit()
    repetido=executar(sessao,**args)
    assert repetido['reexecutado'] is True
    assert all(repetido[k]==primeiro[k] for k in ('permitido','identidade_id','versao'))
    sessao.commit()
    assert len(list(sessao.scalars(select(Evento).where(Evento.cadeia_id==obj,Evento.tipo_evento=='f34_informar_ripd'))))==1
    e=estado(sessao,obj)
    assert e['referencia_ripd']['pessoa_id']=='PESSOA-B'
    assert 'RIPD juntado em PROCESSO-FICTICIO-12E' in html(obj,15)
    assert 'por Secretaria.' in html(obj,15)
    ato(sessao,obj,'confirmar_ripd',conta='CONTA-E1')
    assert set(estado(sessao,obj)['referencia_ripd_confirmacoes']) == {'secretaria','dpo'}

def test_execucao_por_outro_habilitado_mesma_unidade_e_verificacao_independente(sessao,entrada):
    obj=preparar_acao(sessao,entrada)
    with pytest.raises(PermissionError):ato(sessao,obj,'executar_medida',conta='CONTA-C1',evidencia='Ref. fictícia', resumo='Execução fictícia: acessos revisados e documentados.')
    sessao.add(Designacao(pessoa_id='PESSOA-C',unidade_id=entrada.unidade_id,papel='preenchedor'))
    sessao.commit()
    ato(sessao,obj,'executar_medida',conta='CONTA-C1',evidencia='Ref. fictícia', resumo='Execução fictícia: acessos revisados e documentados.')
    assert estado(sessao,obj)['execucao']['pessoa_id']=='PESSOA-C'
    with pytest.raises(PermissionError):ato(sessao,obj,'verificar',conta='CONTA-C1',aprovada=True,evidencia='Fictícia', **{k:'A confirmar' for k in ('F4-4.18','F4-4.20','F4-4.21','F4-4.22')})
    ato(sessao,obj,'verificar',conta=VERIFICADOR,aprovada=True,evidencia='Fictícia', **{k:'A confirmar' for k in ('F4-4.18','F4-4.20','F4-4.21','F4-4.22')})
    assert estado(sessao,obj)['verificada']

def test_gabinete_documento_obrigatorio_sem_mudar_aceitacao_existente(sessao,entrada):
    obj=entrar(sessao,entrada);avaliar(sessao,obj,5)
    ato(sessao,obj,'manifestar_dpo',conta='CONTA-E1',texto='Texto fictício integral, sem inferência.')
    ato(sessao,obj,'manifestar_comite',conta=RELATOR,finalidade='residual',ata='ATA-FICT',texto='Texto fictício integral.',favoravel=True)
    antes=deepcopy(estado(sessao,obj))
    with pytest.raises(PermissionError):ato(sessao,obj,'aceitar_residual',conta='CONTA-DEMO34-PREF',justificativa='Fictícia')
    with pytest.raises(ValueError):ato(sessao,obj,'aceitar_residual',conta=GABINETE,justificativa='Fictícia')
    assert estado(sessao,obj)==antes
    tela=html(obj,14,GABINETE)
    assert 'Risco residual: 25 — Crítico' in tela
    assert 'RIPD: referência não informada.' in tela
    assert 'Texto fictício integral, sem inferência.' in tela
    ato(sessao,obj,'aceitar_residual',conta=GABINETE,documento='OFICIO-FICT-12E',solicitar_juridico=False,motivo_juridico='Dispensa fictícia fundamentada',justificativa='Fictícia')
    assert estado(sessao,obj)['aceitacao']['decisor']=='Prefeito'
    assert 'Decisão do Prefeito, registrada pelo Gabinete em' in html(obj,14,GABINETE)
    assert 'conforme OFICIO-FICT-12E' in html(obj,14,GABINETE)

def test_plano_conteudo_antes_da_aprovacao_e_campos_calculados(sessao,entrada):
    obj=entrar(sessao,entrada,4)
    ato(sessao,obj,'planejar',plano='Plano fictício para revisar e documentar os acessos.',cargo='Chefia da unidade',duracao_dias=30)
    tela=html(obj,3,SECRETARIO)
    assert 'Plano registrado em' in tela and 'se aprovar hoje' in tela
    assert tela.index('Plano fictício para revisar e documentar os acessos.')<tela.index('value="aprovar_plano"')
    assert 'Plano: Plano fictício para revisar e documentar os acessos.' in tela
    assert 'Cargo responsável: Chefia da unidade' in tela
    assert 'value="planejar"' not in html(obj,3)
    assert 'Chefia da unidade' in html(obj,2)
    assert '0 respostas marcadas' not in tela

def test_comite_finalidades_no_dominio_e_tela(sessao,entrada):
    obj=entrar(sessao,entrada);avaliar(sessao,obj,5)
    assert finalidades(estado(sessao,obj))==['residual']
    tela=html(obj,14,RELATOR)
    assert 'value="residual"' in tela and 'value="prorrogacao"' not in tela
    with pytest.raises(ValueError,match='Finalidade'):
        ato(sessao,obj,'manifestar_comite',conta=RELATOR,finalidade='prorrogacao',ata='Fictícia',texto='Fictício',favoravel=True)
    assert 'manifestacao_comite' not in estado(sessao,obj)

def test_encaminhamento_em_destaque_e_origem_congelada(sessao,entrada):
    obj=entrar(sessao,entrada);avaliar(sessao,obj,5)
    # A5: os encaminhamentos são atos próprios; F3-3.59 é calculada.
    tela=html(obj,16)
    assert tela.index('id="ato-encaminhar_acao"')<tela.index('Outras ações disponíveis')
    assert 'Lacunas encontradas e verificações' in tela
    assert 'value="encaminhar_acao"' in tela
    acao=ato(sessao,obj,'encaminhar_acao',justificativa='Fictícia')['identidade_id']
    origem = html(acao,1)
    assert 'Risco 1: Evento fictício' in origem and 'Crítico (25)' in origem
    assert f'/forms34/{obj}/blocos/16?conta_id=CONTA-B1' in origem

def test_avisos_historico_datas_e_sem_native():
    r=Path(__file__).resolve().parents[1]
    js=(r/'app/estaticos/forms34.js').read_text(encoding='utf8')
    assert 'beforeunload' not in js
    assert "addEventListener('ato-confirmado',()=>dirty=false)" in js
    assert "check.addEventListener('change',filtrar)" in js
    from app.apresentacao_atos34 import data_br
    assert data_br('2027-01-15')=='15/01/2027'
    from app.rotas_fila_form2 import paginas
    assert paginas.env.from_string('{{ prazo|data_br }}').render(prazo='2027-01-15')=='15/01/2027'

def test_recusa_cargo_arbitrario_e_mantem_legado(sessao,entrada):
    obj=entrar(sessao,entrada,4);antes=deepcopy(estado(sessao,obj))
    with pytest.raises(ValueError):ato(sessao,obj,'planejar',plano='Fictício',cargo='Pessoa fictícia',duracao_dias=30)
    assert estado(sessao,obj)==antes
    from app.leitura_atos34 import conteudo_ato
    legado={'plano':'Fictício','executor_id':'p','prazo':'2027-01-15'}
    linhas=conteudo_ato('planejar',legado,{'p':'Autor fictício'}, {})
    assert ('Executor registrado no ato anterior','Autor fictício') in linhas
    assert 'cargo_responsavel' not in legado
    e={'form':4,'faixa_origem':'Crítico','plano':'Fictício'}
    assert 'aprovar_plano' not in {a['acao'] for a in disponiveis(4,3,{'secretario'},e)}
    atos=disponiveis(4,3,{'gabinete'},e)
    aprovacao=next(a for a in atos if a['acao']=='aprovar_plano')
    assert any(c['nome']=='documento' and c['obrigatorio'] for c in aprovacao['campos'])


def test_percurso_http_encaminha_planeja_e_exibe_proposta_sem_repetir_ato(sessao,entrada):
    """Percurso real no _teste; HTML restrito opcional para conferência visual local."""
    import os
    cliente=TestClient(app)
    risco=entrar(sessao,entrada);avaliar(sessao,risco)
    # A5: providência registrada pelo ato próprio, sem edição da calculada.
    paginas={'item4_encaminhamento':html(risco,16)}
    comando=str(uuid4())
    resposta=cliente.post(f'/forms34/{risco}/blocos/16?conta_id=CONTA-B1',data={
        'acao':'encaminhar_acao','comando_id':comando,'versao':estado(sessao,risco)['versao'],
        'justificativa':'Providência fictícia para conferência do fluxo.'})
    assert resposta.status_code==200 and 'FORM 4 · Bloco 1' in resposta.text
    acao=estado(sessao,risco)['acoes'][-1]
    paginas['item1_apos_encaminhar']=resposta.text
    comando=str(uuid4())
    resposta=cliente.post(f'/forms34/{acao}/blocos/3?conta_id=CONTA-B1',data={
        'acao':'planejar','tema_principal':'T07','comando_id':comando,'versao':estado(sessao,acao)['versao'],
        'plano':'Plano fictício: restringir o acesso à equipe autorizada e registrar a evidência.',
        'cargo':'Chefia da unidade','duracao_dias':30})
    assert resposta.status_code==200 and 'Plano registrado em' in resposta.text
    assert 'name="acao" value="planejar"' not in resposta.text
    paginas['item2_plano_registrado']=resposta.text
    versao=estado(sessao,acao)['versao']
    paginas['item3_aprovacao']=html(acao,3,SECRETARIO)
    assert 'Plano: Plano fictício' in paginas['item3_aprovacao']
    assert 'se aprovar hoje' in paginas['item3_aprovacao']
    assert estado(sessao,acao)['versao']==versao
    destino=os.environ.get('LGPD_EVIDENCIAS_12E')
    if destino:
        pasta=Path(destino);pasta.mkdir(parents=True,exist_ok=True)
        for nome,conteudo in paginas.items():(pasta/(nome+'.html')).write_text(conteudo,encoding='utf8')


def test_cadastro_gabinete_isolado_idempotente(sessao,fonte):
    from carga_ficticia.atores_forms34 import semear
    from app.modelos import Pessoa,Conta
    antes={p.id for p in sessao.scalars(select(Pessoa))}
    semear(sessao,somente='GAB');sessao.commit()
    assert {p.id for p in sessao.scalars(select(Pessoa))}-antes=={'PESSOA-DEMO34-GAB'}
    assert sessao.get(Conta,GABINETE).pessoa_id=='PESSOA-DEMO34-GAB'
    semear(sessao,somente='GAB');sessao.commit()
    d=list(sessao.scalars(select(Designacao).where(Designacao.pessoa_id=='PESSOA-DEMO34-GAB')))
    assert len(d)==1 and d[0].papel=='demo34_gabinete' and d[0].unidade_id=='SEC-GOV'
