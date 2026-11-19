"""Vistoria 12-D: leitura de atos sem reexecutar nem alterar fatos anteriores."""
from copy import deepcopy
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.modelos import Evento
from app.leitura_atos34 import situacao_bloco
from app.apresentacao_forms34 import grade_visual
from testes.test_lote12 import protecoes, entrada, fonte, entrar, ato, estado, avaliar

def pagina(client,obj,bloco=15,conta='CONTA-B1',extra=''):
    return client.get(f'/forms34/{obj}/blocos/{bloco}?conta_id={conta}{extra}')

def test_triagem_proposta_conteudo_confirmacao_e_historico(sessao,entrada):
    obj=entrar(sessao,entrada);avaliar(sessao,obj,5)
    ato(sessao,obj,'manifestar_dpo',conta='CONTA-E1',texto='Manifestação fictícia preservada')
    ato(sessao,obj,'propor_triagem',conta='CONTA-E1',resultado='elaborar',unidade_id=entrada.unidade_id,justificativa='Justificativa fictícia integral')
    antes=deepcopy(estado(sessao,obj)); eventos=[(e.id,e.hash,e.conteudo) for e in sessao.scalars(select(Evento).where(Evento.cadeia_id==obj))]
    c=TestClient(app);dpo=pagina(c,obj,conta='CONTA-E1');beta=pagina(c,obj)
    assert dpo.status_code==beta.status_code==200
    assert 'name="acao" value="propor_triagem"' not in dpo.text
    assert 'Revisar proposta de triagem' in dpo.text
    assert 'name="acao" value="confirmar_triagem"' in beta.text
    assert 'Justificativa fictícia integral' in beta.text
    assert 'Elaborar RIPD' in beta.text and 'Modelo Municipal de RIPD' in beta.text
    assert beta.text.index('Justificativa fictícia integral')<beta.text.index('name="acao" value="confirmar_triagem"')
    assert 'Manifestação fictícia preservada' in beta.text
    assert estado(sessao,obj)==antes
    assert [(e.id,e.hash,e.conteudo) for e in sessao.scalars(select(Evento).where(Evento.cadeia_id==obj))]==eventos
    ato(sessao,obj,'confirmar_triagem')
    for conta in ('CONTA-B1','CONTA-E1'):
        html=pagina(c,obj,conta=conta).text
        assert 'Triagem confirmada pela Secretaria e pelo DPO em' in html
        assert 'name="acao" value="propor_triagem"' not in html
        assert 'name="acao" value="confirmar_triagem"' not in html
    assert [(e.id,e.hash,e.conteudo) for e in sessao.scalars(select(Evento).where(Evento.cadeia_id==obj,Evento.id<=eventos[-1][0]))]==eventos

def test_revisao_triagem_preenchida_e_filtro_salvamentos(sessao,entrada):
    obj=entrar(sessao,entrada);avaliar(sessao,obj)
    ato(sessao,obj,'propor_triagem',resultado='analise_adicional',justificativa='Análise fictícia adicional')
    ato(sessao,obj,'salvar_bloco',bloco=1,campos={'F3-3.4':'Não'})
    c=TestClient(app)
    html=pagina(c,obj,extra='&revisar=1').text
    assert 'name="acao" value="propor_triagem"' in html
    assert '>Análise fictícia adicional</textarea>' in html
    assert 'data-historico-ato="nao" hidden><strong>Bloco 1 salvo' in pagina(c,obj).text
    assert 'Bloco 1 salvo' in pagina(c,obj,extra='&historico=todos').text
    assert 'Bloco 1 salvo' in pagina(c,obj,extra='&filtrar=1').text
    assert 'data-historico-ato="nao" hidden><strong>Bloco 1 salvo' in pagina(c,obj,extra='&filtrar=1&historico=atos').text

def test_grade_separa_perguntas_e_atos():
    e={'form':3,'avaliacao':{},'avaliacao_confirmacoes':{'secretaria':{},'dpo':{}},'triagem':None}
    g=[dict(numero=14,titulo='Avaliação',texto='Ainda não preenchido',n=0,m=0,percentual=0),dict(numero=15,titulo='Triagem',texto='Todas as perguntas ativas respondidas',n=2,m=2,percentual=100,a_confirmar=1)]
    visual=grade_visual(g,'obj','conta',14,e)
    assert visual[0]['texto']=='' and visual[0]['situacao_ato']=='Nota conjunta confirmada'
    assert visual[1]['situacao_ato']=='Aguardando triagem'
    assert visual[1]['texto']=='✓ Todas respondidas · 1 a confirmar'
    assert situacao_bloco(4,7,{'verificada':True})=='Verificação aprovada'

def test_confirmacao_e_sucesso_nomeiam_ato(sessao,entrada):
    from testes.test_lote12_ajustes import propor
    obj=entrar(sessao,entrada);propor(sessao,obj);c=TestClient(app)
    html=pagina(c,obj,14,'CONTA-E1').text
    assert 'a nota passa a valer como nota conjunta' in html
    assert 'aceitação pelo Prefeito' in html
    assert 'Justificativa fictícia' in html
    cmd=str(uuid4())
    resposta=c.post(f'/forms34/{obj}/blocos/14?conta_id=CONTA-E1',data={'acao':'confirmar_avaliacao','versao':estado(sessao,obj)['versao'],'comando_id':cmd})
    assert resposta.status_code==200
    assert 'Nota conjunta confirmada em' in resposta.text
    assert 'Operação registrada' not in resposta.text
    assert 'Nota registrada' in resposta.text
    assert 'Prévia do cálculo.' not in resposta.text

def test_historico_nao_expoe_estado_bruto_nem_referencia():
    from app.leitura_atos34 import conteudo_ato
    e={'referencia_restrita_id':'sigilosa','escopos_restritos':['segredo'],'manifestacao_dpo':{'texto':'Texto fictício','em':'ontem','pessoa_id':'x'}}
    assert conteudo_ato('referencia_registrada',e,{}, {})==[]
    assert conteudo_ato('manifestar_dpo',e,{}, {})==[('Texto','Texto fictício')]
