"""A10: nomes, entrada única e identificação legível."""
from testes.apoio_entrada import ClienteAposApresentacao as TestClient
from app.main import app
from testes.test_lote12 import entrada, fonte, protecoes, entrar, ato


def test_nomes_troca_e_link_so_aal(sessao,entrada):
    obj=entrar(sessao,entrada)
    titulo='Evento fictício extenso para conferir o nome completo: '+'descrição fictícia '*12
    ato(sessao,obj,'propor_avaliacao',evento=titulo,causa='Causa fictícia',consequencia='Consequência fictícia',p=2,i=2,pr=2,ir=2,justificativa='Fictícia',controles=[])
    c=TestClient(app)
    central=c.get('/central?conta_id=CONTA-B1').text
    assert 'Providências e aprendizado' in central
    assert 'Que riscos o tratamento apresenta e que cuidados já existem?' in central
    assert central.count('>Abrir Riscos e providências</a>')==2
    for conta in ('CONTA-B1','CONTA-E1'):
        pagina=c.get('/forms34?conta_id='+conta)
        assert pagina.status_code==200
        assert titulo.rstrip() in pagina.text
        assert 'troca-compacta34' not in pagina.text
        assert ('Ir às filas do FORM 2' in pagina.text)==(conta=='CONTA-B1')
    assert 'Ver como: trocar servidor fictício' not in c.get('/dashboard?conta_id=CONTA-B1').text


def test_cartao_separa_concluidos():
    from app.central_instrumentos import cartoes_em_andamento
    a=dict(texto='Risco fictício concluído',pendente=False,concluido=True,concluido_em='2026-11-26',href='/ficticio')
    b=dict(texto='Risco fictício em andamento',pendente=False,concluido=False,href='/ficticio2')
    c=cartoes_em_andamento(None,'CONTA-B1',{3:[a,b]})[3]
    assert c['concluidos']==[a] and c['acompanhamento']==[b]
