"""Cartões da Central: limites, permissões e destinos sem executar atos."""
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from app.main import app
from app.modelos import Evento, EventoAuditoria, Designacao
from app.central_instrumentos import itens_em_andamento, cartoes_em_andamento
from testes.test_lote12 import protecoes, entrada, fonte, entrar


def test_limite_tres_e_excedentes(monkeypatch):
    import app.central_instrumentos as central
    linhas={n:[dict(texto=f'Fictício {i}',href=f'/ficticio/{i}') for i in range(6)] for n in range(1,5)}
    monkeypatch.setattr(central,'itens_em_andamento',lambda s,c:linhas)
    cards=cartoes_em_andamento(None,'CONTA-B1')
    for n in range(1,5):
        assert len(cards[n]['itens'])==3 and cards[n]['mais']==3
        assert cards[n]['lista']==f'/central/itens/{n}?conta_id=CONTA-B1'


def test_cartoes_filtram_escopo_e_nao_gravam(sessao,entrada):
    risco=entrar(sessao,entrada,3);acao=entrar(sessao,entrada,4)
    antes=[sessao.scalar(select(func.count()).select_from(m)) for m in (Evento,EventoAuditoria)]
    beta=itens_em_andamento(sessao,'CONTA-B1')
    assert any(risco in i['href'] for i in beta[3])
    assert any(acao in i['href'] for i in beta[4])
    assert len(beta[2])==1 and 'Abrir participação' not in beta[2][0]['texto']
    alfa=itens_em_andamento(sessao,'CONTA-A1')
    assert not alfa[2] and not alfa[3] and not alfa[4]
    c=TestClient(app)
    for n in range(1,5):
        r=c.get(f'/central/itens/{n}?conta_id=CONTA-B1')
        assert r.status_code==200
    assert c.get('/central/itens/5?conta_id=CONTA-B1').status_code==404
    assert c.get(f'/forms34/{risco}/blocos/1?conta_id=CONTA-A1').status_code==403
    assert [sessao.scalar(select(func.count()).select_from(m)) for m in (Evento,EventoAuditoria)]==antes


def test_lista_forms34_filtra_sem_conceder_acesso(sessao,entrada):
    risco=entrar(sessao,entrada,3);acao=entrar(sessao,entrada,4)
    c=TestClient(app)
    r=c.get('/forms34?conta_id=CONTA-B1&form=3')
    assert risco in r.text and acao not in r.text
    r=c.get('/forms34?conta_id=CONTA-B1&form=4')
    assert acao in r.text and risco not in r.text
    assert c.get('/forms34?conta_id=CONTA-B1&form=5').status_code==422
    for d in sessao.scalars(select(Designacao).where(Designacao.pessoa_id=='PESSOA-B',Designacao.papel=='aal_form2')):d.ativa=False
    sessao.commit()
    itens=itens_em_andamento(sessao,'CONTA-B1')
    assert not itens[2] and not itens[3] and not itens[4]
