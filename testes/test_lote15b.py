"""Regressões do Lote 15-B: dados fictícios, somente banco _teste."""
from copy import deepcopy
from uuid import uuid4
import re
from html import unescape
from sqlalchemy import select
from testes.apoio_entrada import ClienteAposApresentacao as TestClient
from app.main import app
from app.modelos import RascunhoForm1Integral
from app.rev22_form1 import definicoes, contagem_blocos
from app.consultas_interface import carregar_registro
from testes.test_conferencia_interna_form1_integral_8ac import _preparar
from testes.test_cartilha_local_form1 import documento_local


def abrir(sessao):
    reg=_preparar(sessao,'L15B')
    cliente=TestClient(app,client=('127.0.0.1',50000))
    url=f"/registros/{reg['registro_id']}/form1-rev22"
    assert cliente.get(url+'?conta_id=CONTA-G1').status_code==200
    sessao.expire_all()
    return reg,cliente,url


def salvar(sessao,reg,cliente,url,bloco,campos,versao=None):
    sessao.expire_all()
    r=sessao.get(RascunhoForm1Integral,reg['registro_id'])
    dados=dict(conta_id='CONTA-G1',comando_id=str(uuid4()),versao=versao or r.versao_rascunho,bloco=bloco)
    dados.update(campos)
    return cliente.post(url,data=dados)


def test_c164_texto_iniciado_por_outro_e_nome_vazio_contam(sessao):
    reg,c,url=abrir(sessao)
    resposta=salvar(sessao,reg,c,url,1,{'r:1.3':'Outros atendimentos de demonstração'})
    assert resposta.status_code==200
    sessao.expire_all()
    assert sessao.get(RascunhoForm1Integral,reg['registro_id']).conteudo['respostas']['1.3']=='Outros atendimentos de demonstração'
    com=contagem_blocos({'respostas':{'1.1':'Não','1.3':'Nome fictício'}})[1]
    sem=contagem_blocos({'respostas':{'1.1':'Não','1.3':' '}})[1]
    assert com['respondidas']==sem['respondidas']+1
    assert 'Em preenchimento' in sem['texto']


def test_c165_erro_real_preserva_campos_no_bloco(sessao):
    reg,c,url=abrir(sessao)
    # Alternativa de lista, nunca enunciado privado publicado no teste.
    q=next(q for q in definicoes().values() if q['block']==2 and q['kind'] in ('single','multi') and any(str(o).startswith('Outro') for o in q['options']))
    outro=next(o for o in q['options'] if str(o).startswith('Outro'))
    antes=deepcopy(sessao.get(RascunhoForm1Integral,reg['registro_id']).conteudo)
    resposta=salvar(sessao,reg,c,url,2,{'r:'+q['id']:outro,'r:2.11':'Nome fictício preservado'})
    assert resposta.status_code==409
    assert 'Nome fictício preservado' in resposta.text and 'role="alert"' in resposta.text
    assert '<html' in resposta.text and 'Qual?' in resposta.text
    sessao.expire_all()
    assert sessao.get(RascunhoForm1Integral,reg['registro_id']).conteudo==antes


def test_c165_c185_concorrencia_nao_sobrescreve_e_preserva_tentativa(sessao):
    reg,c,url=abrir(sessao)
    versao=sessao.get(RascunhoForm1Integral,reg['registro_id']).versao_rascunho
    assert salvar(sessao,reg,c,url,1,{'r:1.3':'Primeira aba fictícia'},versao).status_code==200
    recusa=salvar(sessao,reg,c,url,1,{'r:1.3':'Segunda aba fictícia'},versao)
    assert recusa.status_code==409
    assert 'Este bloco foi alterado em outra aba. Recarregue a página antes de salvar.' in recusa.text
    assert 'Segunda aba fictícia' in recusa.text
    sessao.expire_all()
    assert sessao.get(RascunhoForm1Integral,reg['registro_id']).conteudo['respostas']['1.3']=='Primeira aba fictícia'


def test_c168_c162_abrir_nao_inicia_nem_muda_data(sessao):
    reg=_preparar(sessao,'L15B-INICIO')
    antes=carregar_registro(sessao,'CONTA-G1',reg['registro_id'])[1]['etapa_atual']
    sessao.commit()
    c=TestClient(app)
    resposta=c.get(f"/registros/{reg['registro_id']}/form1-rev22?conta_id=CONTA-G1")
    assert resposta.status_code==200
    sessao.expire_all()
    depois=carregar_registro(sessao,'CONTA-G1',reg['registro_id'])[1]['etapa_atual']
    assert antes['situacao']==depois['situacao']=='Não iniciado'
    assert antes['desde']==depois['desde']
    assert 'Consultar respostas anteriores à atualização' not in resposta.text


def test_c171_c172_instrumentos_sem_instancia_nao_abrem_fila(sessao):
    reg,c,url=abrir(sessao)
    html=c.get(f"/registros/{reg['registro_id']}?conta_id=CONTA-G1").text
    for numero in (2,3,4):
        card=re.search(fr'<li data-instrumento="FORM{numero}">(.*?)</li>',html,re.S).group(1)
        assert '<a ' not in card
        assert f'O FORM {numero} começa' in card


def test_c180_c182_c185_cartilha_em_todos_blocos_isolada(sessao,documento_local):
    reg,c,url=abrir(sessao)
    for bloco in range(1,15):
        html=c.get(url+f'?conta_id=CONTA-G1&bloco={bloco}').text
        link=re.search(r'<a[^>]+href="([^"]*/cartilha/[^"]+)"',html)
        assert link, bloco
        pagina=c.get(unescape(link.group(1)))
        assert pagina.status_code==200
        assert 'Para voltar ao FORM, feche esta aba.' in pagina.text
        assert "img-src 'self' data:" in pagina.headers['content-security-policy']
        links=re.findall(r'<a[^>]+href="([^"]+)"',pagina.text)
        assert not any(a.startswith(('/central','/registros','/form')) for a in links)
    imagem=re.search(r'<img[^>]+src="([^"]+)"',pagina.text)
    assert imagem and c.get(unescape(imagem.group(1))).status_code==200


def test_c157_acesso_recusado_em_layout_sem_respostas(sessao):
    reg,c,url=abrir(sessao)
    r=c.get(url+'?conta_id=CONTA-INEXISTENTE')
    assert r.status_code==403 and '<html' in r.text
    assert 'Seu perfil não permite acessar esta página.' in r.text
    assert 'r:1.3' not in r.text


def test_c187_c190_post_duplicado_recusado(sessao):
    from app.modelos import ObjetoCatalogo,Registro
    from testes.apoio import CADASTRO,g1
    from sqlalchemy import func
    primeiro=g1('L15B-DUP',CADASTRO,'CTX-TRIB-01')
    objeto=sessao.get(ObjetoCatalogo,CADASTRO)
    antes=sessao.scalar(select(func.count()).select_from(Registro))
    c=TestClient(app)
    resposta=c.post('/registros',data=dict(conta_id='CONTA-A1',comando_id='L15B-DUP-POST',tipo_objeto=objeto.tipo_objeto,objeto_principal_id=objeto.id,unidade_id='UNID-NORTE',contexto_id='CTX-TRIB-01',situacao_canais='nenhum'))
    assert resposta.status_code==200
    assert primeiro['codigo_lgpd'] in resposta.text
    assert 'Já existe' in resposta.text
    assert sessao.scalar(select(func.count()).select_from(Registro))==antes
    assert re.search(r'<button[^>]*id="confirmar-abertura"[^>]*disabled',resposta.text)
