"""Lote 15-C: regressões com dados fictícios, somente banco _teste."""
from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace as NS
import pytest
from testes.test_lote15b import abrir
from testes.apoio_entrada import ClienteAposApresentacao as TestClient
from app.main import app
from app.modelos import RascunhoForm1Integral


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
