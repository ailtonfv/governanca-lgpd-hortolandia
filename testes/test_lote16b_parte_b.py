from types import SimpleNamespace
from app.textos_parte_b16 import grupo_fila,TITULO12
from app.respostas_form2 import definicao_revisao
from app.fatos_abertura_form2 import projetar_fatos_abertura
from testes.test_lote12 import entrada,fonte,protecoes,entrar
from app.main import app
from testes.apoio_entrada import ClienteAposApresentacao

def test_b_grupos_dependem_do_responsavel():
    def c(autor):return {'participacoes':[SimpleNamespace(estado='em_atendimento',responsavel_id=autor)]}
    assert grupo_fila(c('beta'),'beta')=='Sua análise'
    assert grupo_fila(c(None),'beta')=='Aguardando responsável'
    assert grupo_fila(c('eta'),'beta')=='Da sua unidade, com outro AAL'

def test_b_textos_e_ordem():
    assert definicao_revisao(12)['itens'][0]['id']=='F2-12.8'
    assert definicao_revisao(12)['titulo']==TITULO12
    q=next(q for q in definicao_revisao(10)['itens'] if q['id']=='F2-10.5')
    assert 'SAA' in q['enunciado']

def test_b_referencias_incluem_fatos_e_identificador_vazio():
    q={'id':'F2-7.1','referencias_form1':[]}
    projetar_fatos_abertura([q],{'perguntas':[{'id':'10.8','respondida':True,'valor':'Sim'}],'conteudo':{}})
    assert q['fatos_abertura'][0]['referencia']=='F1-10.8'
    q={'id':'F2-9.8','referencias_form1':[]}
    projetar_fatos_abertura([q],{'perguntas':[],'conteudo':{}})
    assert len(q['referencias_exibidas'])==5 and not q['fatos_abertura']

def test_b_telas_nao_mostram_asteriscos(sessao,entrada):
    cliente=ClienteAposApresentacao(app)
    resposta=cliente.get(f'/form2/participacoes/{entrada.id}?conta_id=CONTA-B1')
    assert resposta.status_code==200 and 'Análise do FORM 2' in resposta.text
    obj=entrar(sessao,entrada)
    resposta=cliente.get(f'/forms34/{obj}/blocos/1?conta_id=CONTA-B1')
    assert resposta.status_code==200
    assert '**** Preenchido' not in resposta.text and '* Obrigatório' not in resposta.text


def test_g4_navegacao_unica_depois_das_perguntas_e_lacunas(sessao, entrada):
    cliente = ClienteAposApresentacao(app)
    form2 = cliente.get(f'/form2/participacoes/{entrada.id}/blocos/14?conta_id=CONTA-B1')
    risco = entrar(sessao, entrada, 3)
    form3 = cliente.get(f'/forms34/{risco}/blocos/13?conta_id=CONTA-B1')
    for resposta, conteudo in ((form2, 'Salvar bloco 14'), (form3, 'Lacunas encontradas e verificações')):
        assert resposta.status_code == 200
        assert resposta.text.count('class="moldura-navegacao-blocos"') == 1
        assert resposta.text.index(conteudo) < resposta.text.index('class="moldura-navegacao-blocos"')
