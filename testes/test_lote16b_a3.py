"""A3/C163: leitura e navegação sem alteração de atos."""
import pytest
from testes.test_lote12 import entrada, fonte, protecoes, entrar, avaliar, ato
from testes.apoio_entrada import ClienteAposApresentacao
from app.main import app
from html.parser import HTMLParser
class Tags(HTMLParser):
    def __init__(self,html):
        super().__init__();self.tags=[];self.feed(html)
    def handle_starttag(self,tag,attrs):self.tags.append((tag,dict(attrs)))
    def classe(self,n):return [a for t,a in self.tags if n in a.get('class','').split()]
    def id(self,n):return next((a for t,a in self.tags if a.get('id')==n),None)



def test_a3_situacao_perguntas_e_manifestacoes_no_bloco_certo(sessao,entrada):
    obj=entrar(sessao,entrada)
    avaliar(sessao,obj,4)
    ato(sessao,obj,'manifestar_dpo',conta='CONTA-E1',texto='Orientação fictícia para teste de leitura')
    cliente=ClienteAposApresentacao(app)
    for bloco in (1,3,14):
        r=cliente.get(f'/forms34/{obj}/blocos/{bloco}?conta_id=CONTA-B1')
        assert r.status_code==200
        soup=Tags(r.text)
        assert soup.classe('situacao-bloco34')
        quadro=r.text.split('aria-label="Situação e próxima providência"',1)[1].split('</section>',1)[0]
        assert ' · por ' in quadro and 'Você atua como:' in quadro
        assert 'As perguntas seguem a numeração' not in r.text
        assert 'Detalhe disponível para consulta' not in r.text
        assert bool(soup.id('manifestacoes34'))==(bloco==14)
        if bloco!=14:
            assert any('/blocos/14?' in a.get('href','') and a['href'].endswith('#manifestacoes34') for t,a in soup.tags)
            assert r.text.index('id="perguntas34"')<r.text.index('Histórico de registros e salvamentos')
            assert len(soup.classe('barra-salvar-bloco'))==1
        else:
            assert len(soup.classe('matriz34'))==1
            assert '<summary>Histórico da proposta de avaliação</summary>' in r.text


def test_a3_condicional_fechada_oculta_sem_apagar(sessao,entrada):
    from app.fluxo_forms34 import estado
    obj=entrar(sessao,entrada)
    ato(sessao,obj,'salvar_bloco',bloco=9,campos={'F3-3.32':'Não'})
    r=ClienteAposApresentacao(app).get(f'/forms34/{obj}/blocos/9?conta_id=CONTA-B1')
    assert r.status_code==200
    q=Tags(r.text).id('F3-3.33')
    assert 'hidden' in q and 'disabled' in q
    assert estado(sessao,obj)['respostas']['F3-3.32']=='Não'


def test_c163_form2_tem_uma_barra_de_salvamento(sessao,entrada):
    r=ClienteAposApresentacao(app).get(f'/form2/participacoes/{entrada.id}/blocos/2?conta_id=CONTA-B1')
    assert r.status_code==200
    soup=Tags(r.text)
    barra=soup.classe('barra-salvar-bloco')
    assert len(barra)==1 and 'Salvar bloco 2' in r.text
