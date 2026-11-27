from testes.test_lote12 import entrada,fonte,protecoes,entrar,ato
from app.fluxo_forms34 import estado
from app.questionario_forms34 import perguntas,ativa
from app.main import app
from testes.apoio_entrada import ClienteAposApresentacao

def test_a4_referencias_e_pergunta_retirada(sessao,entrada):
    obj=entrar(sessao,entrada)
    cliente=ClienteAposApresentacao(app)
    html=cliente.get(f'/forms34/{obj}/blocos/7?conta_id=CONTA-B1').text
    assert 'No FORM 1 (F1-8' in html
    q=next(q for q in perguntas(3) if q['id']=='F3-3.38')
    assert not ativa(q,{}, {})
    assert all('Requer análise' not in q['opcoes'] for q in perguntas(3))
    assert any(q['id']=='F3-3.46' and 'Fluxo institucional' in q['ajuda'] for q in perguntas(3))


def test_a4_normaliza_leitura_sem_reescrever_evento(monkeypatch):
    from types import SimpleNamespace
    import app.fluxo_forms34 as fluxo
    anterior={'form':3,'respostas':{'F3-3.8':'Requer análise'}}
    ev=SimpleNamespace(conteudo={'estado':anterior},tipo_evento='f34_salvar_bloco',sequencia_cadeia=4)
    monkeypatch.setattr(fluxo,'historico',lambda *args:[ev])
    monkeypatch.setattr(fluxo,'verificar_cadeia',lambda *args:(True,None))
    assert fluxo.estado(None,'ficticio')['respostas']['F3-3.8']=='A confirmar'
    assert anterior['respostas']['F3-3.8']=='Requer análise'
