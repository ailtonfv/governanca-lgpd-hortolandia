"""Ajustes de 19/11: somente massa sintética e banco isolado."""
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from html.parser import HTMLParser
import re
class Pagina(HTMLParser):
    def __init__(self,html,*_):
        super().__init__();self.tags=[];self.textos=[];self.feed(html);self.html=html
    def handle_starttag(self,tag,attrs):self.tags.append((tag,dict(attrs)))
    def handle_data(self,texto):self.textos.append(texto)
    def get_text(self):return ' '.join(self.textos)
    def select(self,seletor):
        tag=seletor.split('[')[0];attrs=re.findall(r'\[([\w-]+)(?:="([^"]*)")?\]',seletor)
        return [a for t,a in self.tags if (not tag or tag==t) and all(k in a and (not v or a[k]==v) for k,v in attrs)]
BeautifulSoup=Pagina
from app.main import app
from testes.test_lote12 import protecoes,entrada,entrar,ato,estado,fonte
from app.validacao_atos34 import ErrosCampos
from app.opcao_outro import validar_outro


def propor(s,obj):
    ato(s,obj,'propor_avaliacao',evento='Evento fictício',causa='Causa fictícia',consequencia='Consequência fictícia',p=5,i=5,pr=5,ir=5,justificativa='Justificativa fictícia',controles=[])

def test_proponente_nao_confirma_e_revisao_preserva_versoes(sessao,entrada):
    obj=entrar(sessao,entrada);propor(sessao,obj);antes=estado(sessao,obj)
    with pytest.raises(PermissionError,match='propôs'):ato(sessao,obj,'confirmar_avaliacao')
    assert estado(sessao,obj)==antes
    with pytest.raises(PermissionError,match='outro lado'):ato(sessao,obj,'sem_consenso',campo='avaliacao',posicao='Posição fictícia')
    assert estado(sessao,obj)==antes
    ato(sessao,obj,'revisar_avaliacao',evento='Evento revisto fictício',causa='Causa fictícia',consequencia='Consequência fictícia',p=4,i=5,pr=4,ir=5,justificativa='Revisão fictícia',controles=[])
    assert estado(sessao,obj)['versao']==antes['versao']+1
    ato(sessao,obj,'confirmar_avaliacao',conta='CONTA-E1')
    assert len(estado(sessao,obj)['avaliacao_confirmacoes'])==2

def test_tela_separa_proponente_confirmante_matriz_e_detalhes(sessao,entrada):
    obj=entrar(sessao,entrada);propor(sessao,obj);client=TestClient(app)
    html=BeautifulSoup(client.get(f'/forms34/{obj}/blocos/14?conta_id=CONTA-B1').text,'html.parser')
    assert not html.select('input[value="confirmar_avaliacao"]')
    assert not html.select('input[value="propor_avaliacao"]')
    assert len(html.select('[data-p][data-i]'))==25
    assert 'Ver detalhes da avaliação' in html.get_text()
    assert 'Revisar proposta de avaliação' in html.get_text()
    assert 'D11' not in html.get_text()
    assert len(html.select('[aria-current="page"]'))==1
    outro=BeautifulSoup(client.get(f'/forms34/{obj}/blocos/14?conta_id=CONTA-E1').text,'html.parser')
    assert outro.select('input[value="confirmar_avaliacao"]')
    assert outro.select('input[value="sem_consenso"]')
    revisao=BeautifulSoup(client.get(f'/forms34/{obj}/blocos/14?conta_id=CONTA-B1&revisar=1').text,'html.parser')
    assert re.search(r'<textarea[^>]*name="evento"[^>]*>Evento fictício</textarea>',revisao.html)
    assert len(re.findall('<option',re.search(r'<select[^>]*name="p"[^>]*>(.*?)</select>',revisao.html,re.S)[1]))==6

def test_campos_invalidos_mantem_dados_na_pagina(sessao,entrada):
    obj=entrar(sessao,entrada)
    r=TestClient(app).post(f'/forms34/{obj}/blocos/14?conta_id=CONTA-B1',data={'acao':'propor_avaliacao','versao':estado(sessao,obj)['versao'],'comando_id':str(uuid4()),'evento':'Evento fictício'})
    assert r.status_code==409
    html=BeautifulSoup(r.text,'html.parser')
    assert html.select('[name="causa"][aria-invalid="true"]')
    assert re.search(r'<textarea[^>]*name="evento"[^>]*>Evento fictício</textarea>',html.html)
    assert estado(sessao,obj)['avaliacao'] is None

def test_destino_invalido_tem_erro_proprio(sessao,entrada):
    r=TestClient(app).post(f'/form2/participacoes/{entrada.id}/encaminhar34?conta_id=CONTA-B1',data={'versao':entrada.versao,'comando_id':str(uuid4()),'form':''})
    assert r.status_code==409
    assert 'O encaminhamento ocorre ao concluir a análise do FORM 2.' in r.text
    from app.modelos import IdentidadeForms34
    from sqlalchemy import select
    assert not sessao.scalars(select(IdentidadeForms34)).all()

def test_outro_salva_parcial_e_exige_qual_ao_concluir(sessao,entrada):
    from app.questionario_forms34 import perguntas
    obj=entrar(sessao,entrada);q=next(q for q in perguntas(3) if q['id']=='F3-3.14')
    opcao=next(v for v in q['opcoes'] if v.startswith('Outro'))
    value=[opcao] if q['tipo']=='multi' else opcao
    antes=estado(sessao,obj)
    ato(sessao,obj,'salvar_bloco',bloco=q['bloco'],campos={q['id']:value})
    from app.obrigatoriedade_forms import conferencia34
    assert q['id'] in [i['item'] for i in conferencia34(3,estado(sessao,obj))['faltantes']]
    assert estado(sessao,obj)['respostas'][q['id']]==value
    ato(sessao,obj,'salvar_bloco',bloco=q['bloco'],campos={q['id']:value},complementos={q['id']:'Complemento fictício'})
    assert estado(sessao,obj)['complementos'][q['id']]=='Complemento fictício'

@pytest.mark.parametrize('texto',['', ' '*4, 'x'*201])
def test_complemento_outro_recusa_vazio_e_longo(texto):
    with pytest.raises(ValueError):validar_outro(['Outro'],texto,'F3-TESTE')


def test_preview_mesmas_25_notas_do_dominio():
    import shutil,subprocess,json
    from app.avaliacao_risco34 import pontuar
    node=shutil.which('node')
    if not node:pytest.skip('Node não instalado para verificar JavaScript')
    code="const {score}=require('./app/estaticos/avaliacao34.js');console.log(JSON.stringify(Array.from({length:25},(_,n)=>score(Math.floor(n/5)+1,n%5+1))));"
    saida=json.loads(subprocess.check_output([node,'-e',code],text=True,encoding='utf8'))
    for n,s in enumerate(saida):
        d=pontuar(n//5+1,n%5+1)
        assert (s['nota'],s['faixa'])==(d['nota'],d['faixa'])


def test_form2_complemento_vazio_pendente_para_conclusao():
    from app.respostas_form2 import aplicar_revisao
    from app.form2_rev212 import RASCUNHO
    base={RASCUNHO:{'9':{'opcao:F2-9.1':['SIM'],'opcao:F2-9.6.1#1':['SIM'],'texto:F2-9.6.1#1':'Complemento fictício'}}}
    novo,_=aplicar_revisao(base,9,{'texto:F2-9.6.1#1':['']},demonstrativo=True)
    from app.obrigatoriedade_forms import conferencia2
    assert novo[RASCUNHO]['9']['texto:F2-9.6.1#1']==''
    assert 'F2-9.6.1#1' in [i['item'] for i in conferencia2(novo)['faltantes']]
    assert base[RASCUNHO]['9']['texto:F2-9.6.1#1']=='Complemento fictício'


def test_form1_nao_apaga_qual_mantendo_outro(sessao):
    from testes.test_conferencia_interna_form1_integral_8ac import _preparar
    from app.rev22_form1 import adotar,salvar,definicoes
    from app.modelos import RascunhoForm1Integral
    from app.opcao_outro import eh_outro
    rid=_preparar(sessao,'OUTRO-AJUSTE')['registro_id'];draft=sessao.get(RascunhoForm1Integral,rid)
    adotar(sessao,conta_id='CONTA-G1',comando_id=str(uuid4()),registro_id=rid,versao_lida=draft.versao_rascunho,confirmar=True)
    q=definicoes()['2.1'];valor=next(v for v in q['options'] if eh_outro(v))
    result=salvar(sessao,conta_id='CONTA-G1',comando_id=str(uuid4()),registro_id=rid,versao_lida=draft.versao_rascunho,bloco=2,respostas={'2.1':valor},complementos={'2.1':'Canal fictício'})
    assert result['permitido']
    with pytest.raises(ValueError,match='Qual'):
        salvar(sessao,conta_id='CONTA-G1',comando_id=str(uuid4()),registro_id=rid,versao_lida=draft.versao_rascunho,bloco=2,respostas={},complementos={'2.1':''})
    assert draft.conteudo['complementos']['2.1']=='Canal fictício'
