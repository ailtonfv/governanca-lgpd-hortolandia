"""Lote 15-C: regressões com dados fictícios, somente banco _teste."""
from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace as NS
import pytest
from testes.test_lote15b import abrir
from testes.apoio_entrada import ClienteAposApresentacao as TestClient
from app.main import app
from app.modelos import RascunhoForm1Integral
from testes.test_cartilha_local_form1 import documento_local


@pytest.mark.parametrize('antiga', [True, False])
def test_c212_detalhes_preservam_estrutura_anterior(sessao, antiga):
    reg,c,url=abrir(sessao)
    r=sessao.get(RascunhoForm1Integral,reg['registro_id'])
    conteudo=deepcopy(r.conteudo)
    if antiga:
        conteudo['revisao_22']['catalogo_sha256']='estrutura-anterior-ficticia'
        r.conteudo=conteudo;sessao.commit()
    pagina=c.get('/registros/'+reg['registro_id']+'?conta_id=CONTA-A1')
    assert pagina.status_code==200
    assert ('As respostas continuam guardadas.' in pagina.text)==antiga
    sessao.expire_all()
    assert sessao.get(RascunhoForm1Integral,reg['registro_id']).conteudo==conteudo


def test_c197_arp_sem_dashboard_mantem_aprendizados(sessao):
    from app.modelos import Designacao
    sessao.add(Designacao(pessoa_id='PESSOA-B',unidade_id='UNID-NORTE',papel='aal_form2',ativa=True))
    sessao.commit()
    c=TestClient(app)
    assert '/dashboard?conta_id=CONTA-G1' not in c.get('/central?conta_id=CONTA-G1').text
    for tela in ('','/risco','/operacao','/cobertura'):
        assert c.get('/dashboard'+tela+'?conta_id=CONTA-G1').status_code==403
    assert c.get('/dashboard?conta_id=CONTA-B1').status_code==200
    assert c.get('/dashboard/aprendizados?conta_id=CONTA-G1').status_code==200


def test_c198_fila_pessoal_nao_conta_outro_responsavel(sessao,monkeypatch):
    from app.dashboard import fontes
    def operacao(d,agora):
        return [dict(chave='fila_AAL',lista=d['participacoes'],numero=len(d['participacoes']))]
    monkeypatch.setattr('app.dashboard.consultas.operacao',operacao)
    meus=NS(responsavel_id='PESSOA-B')
    dados=dict(participacoes=[meus,NS(responsavel_id='PESSOA-G'),NS(responsavel_id=None)],objetos=[])
    q=fontes.pendencias_do_aal(sessao,'CONTA-B1',dados,datetime.now(timezone.utc))
    assert q['numero']==1 and q['lista']==[meus]
    assert len(dados['participacoes'])==3


def test_c202_links_de_preenchimento_abrem_blocos(sessao):
    reg,c,url=abrir(sessao)
    from app.central_instrumentos import itens_em_andamento
    itens=itens_em_andamento(sessao,'CONTA-G1')[1]
    alvo=next(i for i in itens if reg['registro_id'] in i['href'])
    assert '/form1-rev22?' in alvo['href']
    pagina=c.get('/?conta_id=CONTA-G1&instrumento=form1')
    assert url+'?conta_id=CONTA-G1' in pagina.text


def test_c192_c193_c194_c195_orientacoes(sessao):
    c=TestClient(app)
    for conta,apa in [('CONTA-A1',True),('CONTA-G1',False)]:
        html=c.get('/central?conta_id='+conta).text
        assert 'Use Ver Registros da Secretaria para acompanhar os Registros' in html
        assert ('ou Iniciar novo Registro para mapear um serviço novo' in html)==apa
        assert 'Sua parte: etapas em que o seu papel pode atuar.' in html
    html=c.get('/como-funciona?conta_id=CONTA-G1').text
    assert html.count('class="regra"')==7
    assert 'Um Registro por serviço e contexto.' in html
    assert 'As competências descritas aqui ainda serão aprovadas pela Prefeitura.' in html


def test_c201_c203_c205_c206_cartoes_e_nome(sessao):
    import re
    from testes.test_lote15b import salvar
    reg,c,url=abrir(sessao)
    vazio=salvar(sessao,reg,c,url,1,{'r:1.3':''})
    assert vazio.status_code==200
    aviso=re.search(r'<p[^>]*id="aviso-nome-catalogo".*?</p>',vazio.text,re.S).group()
    assert 'Informe o nome. No catálogo:' in aviso and 'O nome difere' not in aviso
    html=c.get('/painel?conta_id=CONTA-G1&secretaria_id=UNID-NORTE').text
    card=re.search(r'<article[^>]*id="cartao-registro-'+reg['registro_id']+r'".*?</article>',html,re.S).group()
    assert 'de 14 com respostas' in card and 'Como funciona o FORM 1' in card
    assert 'resumo-conferencia-cartao' not in card and 'providencia-registro' not in card
    detalhe=c.get('/registros/'+reg['registro_id']+'?conta_id=CONTA-G1').text
    assert 'Versão de trabalho: 1 salvamentos.' in detalhe
    assert 'Rascunho e apresentação:' not in detalhe
    instrumentos=detalhe[detalhe.index('id="instrumentos-registro"'):]
    assert url+'?conta_id=CONTA-G1' in instrumentos and 'Ir ao preenchimento' in instrumentos


def test_c207_c210_c211_grupos_e_pendencias(sessao):
    from app.rev22_form1 import pendencias_automaticas
    from testes.test_lote15b import salvar
    reg,c,url=abrir(sessao)
    for b in (3,10):
        html=c.get(url+f'?conta_id=CONTA-G1&bloco={b}').text
        assert 'Informe cada '+('participante' if b==3 else 'destinatário')+' separadamente.' in html
        assert 'data-condicao-aviso=' not in html and 'data-condicao-grupo=' in html
    vazio=c.get(url+'?conta_id=CONTA-G1&bloco=14').text
    assert 'Nenhuma pendência automática até agora.' in vazio
    assert vazio.index('id="pendencias-automaticas"') < vazio.index('id="pergunta-14.1"')
    assert salvar(sessao,reg,c,url,1,{'r:1.1':'A confirmar'}).status_code==200
    html=c.get(url+'?conta_id=CONTA-G1&bloco=14').text
    assert '#pergunta-1.1' in html and 'Nenhuma pendência automática até agora.' not in html
    assert pendencias_automaticas({'respostas':{'1.1':'A confirmar'}})[0]['id']=='1.1'


def test_c209_cartilha_explicita_como_fechar(sessao,documento_local):
    reg,c,url=abrir(sessao)
    html=c.get('/registros/'+reg['registro_id']+'/cartilha/REV30.13/levantamento?conta_id=CONTA-G1').text
    assert html.count('Para voltar ao FORM, feche esta aba (no × da aba ou com Ctrl+W).')==2


def test_c207_agrupa_mesma_condicao_sem_contar_abertas():
    from app.rev22_form1 import grupos_condicionais
    texto='Disponível quando a resposta a F1-3.1 for Sim.'
    grupos=grupos_condicionais([dict(id=str(i),ativa=i==3,orientacao_condicional=texto) for i in range(4)])
    assert len(grupos)==1 and grupos[0]['quantidade']==3
    assert grupos[0]['ids']==['0','1','2','3']
