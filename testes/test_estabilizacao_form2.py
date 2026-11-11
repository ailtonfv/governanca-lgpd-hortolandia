"""Aceite funcional demonstrativo: persistência, condições e ausência de homologação."""
import pytest
from html.parser import HTMLParser
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.modelos import ParticipacaoForm2, Designacao, ComplementoForm2
from app.fila_form2 import executar
from app.form2_rev212 import RASCUNHO
from app.respostas_form2 import definicao_revisao
from testes.test_filas_form2_rev22 import origem

class CamposHTML(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.campos={}; self.pilhas=[]; self.campo=None; self.opcao=None
        self.feed(html)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='fieldset': self.pilhas.append('disabled' in a)
        if tag in ('select','textarea','input') and 'name' in a:
            self.campo=a
            a['inativo']='disabled' in a or any(self.pilhas)
            a['texto']='';a['opcoes']=[]
            self.campos[a['name']]=a
            if tag=='input':self.campo=None
        if tag=='option' and self.campo is not None:
            self.opcao=a;a['texto']='';self.campo['opcoes'].append(a)
    def handle_data(self,data):
        if self.opcao is not None:self.opcao['texto']+=data
        elif self.campo is not None:self.campo['texto']+=data
    def handle_endtag(self,tag):
        if tag=='fieldset':self.pilhas.pop()
        if tag=='option':self.opcao=None
        if tag in ('select','textarea'):self.campo=None

@pytest.fixture
def participacao(sessao):
    r = origem(sessao)
    p = sessao.scalar(select(ParticipacaoForm2).where(ParticipacaoForm2.registro_id == r['registro_id']))
    sessao.add(Designacao(pessoa_id='PESSOA-B', unidade_id='UNID-NORTE', papel='aal_form2', ativa=True))
    sessao.commit()
    executar(sessao, conta_id='CONTA-B1', comando_id='EST-ASSUMIR', participacao_id=p.id, acao='assumir', versao=p.versao)
    sessao.commit()
    return p

def salvar_http(sessao, p, bloco, campos):
    url = f'/form2/participacoes/{p.id}/blocos/{bloco}'
    with TestClient(app) as c:
        result = c.post(url, data=dict(conta_id='CONTA-B1', comando_id=f'EST-SALVAR-{bloco}-{p.versao}', versao=str(p.versao), **campos), follow_redirects=False)
        assert result.status_code == 303, result.text
        sessao.refresh(p)
        page = c.get(url+'?conta_id=CONTA-B1')
        assert page.status_code == 200
        return CamposHTML(page.text).campos

def test_d11_salva_resposta_candidata_sem_homologacao(sessao, participacao):
    p = participacao
    q = next(q for q in definicao_revisao(3)['itens'] if q['id']=='F2-3.1')
    code = q['alternativas'][0]['codigo']
    salvar_http(sessao,p,3,{'opcao:F2-3.1':code})
    assert p.conteudo[RASCUNHO]['3']['opcao:F2-3.1']==[code]
    assert p.conteudo['regime_respostas']['homologado'] is False
    assert p.conteudo['regime_respostas']['uso']=='demonstracao_ficticia'

def test_resultado_14_1_candidato_nao_conclui_form2(sessao, participacao):
    p = participacao
    q = next(q for q in definicao_revisao(14)['itens'] if q['id']=='F2-14.1')
    code = q['alternativas'][0]['codigo']
    salvar_http(sessao,p,14,{'opcao:F2-14.1':code})
    assert p.conteudo[RASCUNHO]['14']['opcao:F2-14.1']==[code]
    assert p.estado=='em_atendimento' and p.concluida_em is None
    assert p.conteudo['regime_respostas']['homologado'] is False
    with pytest.raises((ValueError,PermissionError)):
        executar(sessao,conta_id='CONTA-B1',comando_id='EST-CONCLUIR',participacao_id=p.id,acao='concluir',versao=p.versao,texto='Ensaio fictício')
    sessao.rollback();sessao.refresh(p)
    assert p.estado=='em_atendimento' and p.concluida_em is None

def test_1_3_1_abre_com_secretaria_divergente_e_origem_suficiente(sessao, participacao):
    p = participacao
    nota = 'Conferir a unidade responsável no ensaio fictício.'
    soup = salvar_http(sessao,p,1,{'resposta_F2-1.2':'DIVERGENTE','resposta_F2-1.3':'SIM','resposta_F2-1.3.1':nota})
    campo = soup['resposta_F2-1.3.1']
    assert not campo['inativo']
    assert p.conteudo['respostas_etapa1']['F2-1.3.1']==nota
    pend = sessao.scalar(select(ComplementoForm2).where(ComplementoForm2.participacao_id==p.id))
    assert pend.solicitacao==nota and pend.estado=='aberta'
    assert pend.snapshot_origem_id==p.snapshot_id

# Cada um dos doze controles antes informativos é exercitado pela rota real.
CASOS = [
 ('2.1','opcao','NAO',{}), ('2.1.1','texto','Complemento fictício',{'opcao:F2-2.1':'NAO'}),
 ('2.2','texto','Finalidade fictícia',{}), ('2.3','texto','Descrição fictícia',{}),
 ('2.4','opcao','SIM',{}), ('2.4.1','texto','Finalidade adicional fictícia',{'opcao:F2-2.4':'SIM'}),
 ('2.5','opcao','SIM',{}), ('2.6','opcao','NAO',{}),
 ('2.6.1','texto','Dado fictício',{'opcao:F2-2.6':'NAO'}), ('2.7','opcao','SIM',{}),
 ('2.7.1','texto','Justificativa fictícia',{'opcao:F2-2.7':'SIM'}), ('2.8','opcao','SIM',{})]

@pytest.mark.parametrize('item,tipo,valor,pais',CASOS,ids=[c[0] for c in CASOS])
def test_bloco2_cada_controle_salva_e_reabre(sessao,participacao,item,tipo,valor,pais):
    key=f'{tipo}:F2-{item}'
    soup=salvar_http(sessao,participacao,2,{**pais,key:valor})
    assert participacao.conteudo[RASCUNHO]['2'][key]==([valor] if tipo=='opcao' else valor)
    field=soup[key]
    assert field is not None
    if tipo=='opcao':
        assert next(a for a in field['opcoes'] if 'selected' in a)['value']==valor
    else:
        assert field['texto'].strip()==valor or field.get('value')==valor

def test_9_7_2_outra_hipotese_persiste_complemento(sessao,participacao):
    key='texto:F2-9.7.2#1'; nota='Hipótese fictícia para apreciação jurídica.'
    soup=salvar_http(sessao,participacao,9,{'opcao:F2-9.1':'SIM','opcao:F2-9.7.1#1':'SIM','opcao:F2-9.7.2#1':'OUTRA',key:nota})
    assert participacao.conteudo[RASCUNHO]['9'][key]==nota
    assert soup[key]['texto'].strip()==nota
    option=next(a for a in soup['opcao:F2-9.7.2#1']['opcoes'] if a.get('value')=='OUTRA')
    assert option['texto'].strip()=='Outra hipótese do art. 33 (especificar)'

def test_rotulos_confirmar_preservam_codigos_estaveis():
    from app.contrato_form2_respostas import carregar_contrato
    alternativas=carregar_contrato()['alternativas']
    especiais=[a for a in alternativas if a['codigo']=='A_CONFIRMAR']
    assert len(especiais)==176
    assert all(a['rotulo']=='A confirmar' for a in especiais)
    assert not any(a['rotulo']=='A CONFIRMAR' for a in alternativas)
