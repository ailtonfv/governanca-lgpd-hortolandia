"""A4, itens 1/4/5/6: condições, fonte congelada e cálculo de referência."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.questionario_forms34 import salvar, perguntas, ativa
from app.criterios_form3 import volume, alto_risco_referencia, projetar_guarda, GUARDA
from app.fluxo_forms34 import estado
from testes.test_lote12 import entrada, fonte, protecoes, entrar, ato


@pytest.mark.parametrize('ident,origem',[('F3-3.33','F3-3.32'),('F3-3.41','F3-3.39'),('F3-3.42','F3-3.39')])
def test_condicional_preserva_historico_e_recusa_resposta_nova(ident,origem):
    q=next(i for i in perguntas(3) if i['id']==ident)
    anterior={origem:'Não',ident:'Sim'}
    assert not ativa(q,anterior,{})
    with pytest.raises(ValueError,match='bloqueada'):
        salvar(3,anterior,{'bloco':q['bloco'],'campos':{ident:'Não'}},{})
    assert salvar(3,anterior,{'bloco':q['bloco'],'campos':{}},{})[ident]=='Sim'
    assert ativa(q,{origem:'Sim'},{})


def test_volume_e_criterios_somente_referencia():
    assert '2.502' in volume() and '25.020' in volume()
    assert alto_risco_referencia({'F3-3.10':['Larga escala','Crianças/adolescentes']})
    assert not alto_risco_referencia({'F3-3.10':['Crianças/adolescentes']})
    q=next(i for i in perguntas(3) if i['id']=='F3-3.53')
    with pytest.raises(ValueError,match='ato próprio'):
        salvar(3,{},dict(bloco=q['bloco'],campos={q['id']:'Sim'}),{})


def test_guarda_usa_snapshot_indicado_sem_gravar():
    from types import SimpleNamespace
    class Sessao:
        def get(self,modelo,chave):
            assert chave=='versao-congelada'
            return SimpleNamespace(conteudo={'form1_integral':{'respostas':{'12.1':{'valor':GUARDA}}}})
    e={'form':3,'respostas':{}}
    projetar_guarda(Sessao(),SimpleNamespace(snapshot_form1_id='versao-congelada'),e)
    assert e['respostas']['F3-3.35']==GUARDA
    e['respostas']['F3-3.35']='Sim'
    projetar_guarda(Sessao(),SimpleNamespace(snapshot_form1_id='versao-congelada'),e)
    assert e['respostas']['F3-3.35']=='Sim'


def test_paginas_condicionais_e_calculo(sessao,entrada):
    r=entrar(sessao,entrada)
    ato(sessao,r,'salvar_bloco',bloco=3,campos={'F3-3.10':['Larga escala','Crianças/adolescentes']})
    ato(sessao,r,'salvar_bloco',bloco=9,campos={'F3-3.32':'Não'})
    c=TestClient(app)
    for bloco in (3,15):
        page=c.get(f'/forms34/{r}/blocos/{bloco}?conta_id=CONTA-B1')
        assert page.status_code==200
        assert 'Possível alto risco, pelos critérios de referência' in page.text
    page=c.get(f'/forms34/{r}/blocos/9?conta_id=CONTA-B1')
    from html.parser import HTMLParser
    class Campos(HTMLParser):
        atributos=None
        def handle_starttag(self,tag,attrs):
            if dict(attrs).get('id')=='F3-3.33':self.atributos=dict(attrs)
    parser=Campos();parser.feed(page.text)
    assert parser.atributos is not None and 'hidden' in parser.atributos
