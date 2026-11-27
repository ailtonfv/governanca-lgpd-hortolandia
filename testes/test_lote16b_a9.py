"""A9: indicadores baseados em fatos; somente cenários fictícios."""
from types import SimpleNamespace as NS
from copy import deepcopy
import pytest
from app.dashboard import consultas as c
from app.dashboard.fontes import categorias_circulacao
from app.form2_rev212 import RASCUNHO
from testes.test_dashboard import dados, AGORA
from testes.test_lote12 import entrada, fonte, protecoes


@pytest.mark.parametrize('salvo,ativa,respostas,sem,nao_chegou', [
    (False,True,set(),0,1), (True,True,set(),1,0),
    (True,False,set(),0,0), (True,False,{'Sim'},0,0),
    (True,True,{'A confirmar'},0,0), (True,True,{'Não'},0,0),
])
def test_a97_contagens_exclusivas(dados,salvo,ativa,respostas,sem,nao_chegou):
    rid=dados['registros'][0].id
    fonte={rid:dict(categorias=set(),instrumentos=respostas,bloco8_salvo=salvo,pergunta_ativa=ativa)}
    indicadores={q['chave']:q for q in c.circulacao(dados,fonte)}
    assert indicadores['instrumento_3']['numero']==sem
    assert indicadores['instrumento_4']['numero']==nao_chegou
    assert 'Condicional fechada fica fora' in indicadores['instrumento_3']['regra']
    assert 'bloco 9' in indicadores['instrumento_3']['regra']


def test_a97_fonte_distingue_salvamento_vazio_de_ausencia(monkeypatch):
    from app import respostas_form2, contrato_form2_respostas
    monkeypatch.setattr(respostas_form2,'definicao_revisao',lambda _: {'itens':[
        {'id':'F2-8.7','alternativas':[{'codigo':'SIM','rotulo':'Sim'}]}]})
    monkeypatch.setattr(contrato_form2_respostas,'carregar_contrato',lambda: {'condicoes':[
        dict(alvo='F2-8.7',origem='F2-8.1',operador='IGUAL',codigo_valor='SIM',combinar='E')]})
    p=NS(tipo='principal',registro_id='ficticio',conteudo={})
    d=dict(registros=[NS(id='ficticio')],participacoes=[p],apresentacoes=[],snapshots={})
    assert not categorias_circulacao(d)['ficticio']['bloco8_salvo']
    p.conteudo={'respostas_etapa1':{'F2-8.1':'NAO'}}
    assert not categorias_circulacao(d)['ficticio']['pergunta_ativa']
    p.conteudo={RASCUNHO:{'8':{}}}
    assert categorias_circulacao(d)['ficticio']['bloco8_salvo']
    assert not categorias_circulacao(d)['ficticio']['pergunta_ativa']
    p.conteudo[RASCUNHO]['8']={'opcao:F2-8.1':['SIM']}
    assert categorias_circulacao(d)['ficticio']['pergunta_ativa']
    assert not categorias_circulacao(d)['ficticio']['instrumentos']
    p.conteudo[RASCUNHO]['8']['opcao:F2-8.7#1']=['SIM']
    assert categorias_circulacao(d)['ficticio']['instrumentos']=={'Sim'}
    p.conteudo[RASCUNHO]['8']['opcao:F2-8.1']=['NAO']
    assert not categorias_circulacao(d)['ficticio']['instrumentos']


def test_condicao_aberta_so_fecha_ao_encerrar_acao(dados):
    risco=next(i for i in dados['objetos'] if i['obj'].tipo=='R')
    acao=next(i for i in dados['objetos'] if i['obj'].tipo=='A')
    risco['estado']['condicoes_aceitacao']=[{'acao_id':acao['obj'].id}]
    acao['estado']['verificada']=True
    assert next(q for q in c.atencao(dados,AGORA) if q['chave']=='condicoes')['numero']==1
    acao['estado']['encerrada']={'em':AGORA.isoformat()}
    assert next(q for q in c.atencao(dados,AGORA) if q['chave']=='condicoes')['numero']==0


def test_verificacao_separada_da_deliberacao_comite(dados):
    a=next(i for i in dados['objetos'] if i['obj'].tipo=='A')
    a['estado']['execucao']={'em':AGORA.isoformat()}
    filas={q['chave']:q for q in c.operacao(dados,AGORA)}
    assert filas['fila_Verificação (Comitê)']['numero']==1
    assert filas['fila_Comitê']['numero']==0


def test_cobertura_ordena_e_preserva_lista_de_zeros(dados):
    dados['secretarias'].append(NS(id='SEM-REGISTRO-FICTICIO',nome='Sem Registro fictício'))
    tabela=c.cobertura(dados)[1]['lista']
    assert tabela[0]['total']>=tabela[-1]['total']
    assert tabela[-1]['total']==0


def test_decisao_posterior_nao_reutiliza_aceitacao_anterior():
    from app.dashboard.regras_a9 import decisao_posterior
    e=dict(verificada=True,aceitacao={'em':AGORA.isoformat()},
           residual_acao={'nota':25,'faixa':'Crítico'},residual_acao_confirmacoes={'secretaria':{},'dpo':{}})
    assert decisao_posterior(e)['pendente']
    e['decisao_residual_acao']={'opcao':'aceitar'}
    assert decisao_posterior(e)['pendente']
    e['aceitacao_residual_acao']={'em':AGORA.isoformat()}
    assert not decisao_posterior(e)['pendente']
    e['residual_acao_confirmacoes']={'secretaria':{}}
    assert decisao_posterior(e) is None


def test_a97_sobre_numero_aparece_no_html(dados,monkeypatch):
    from app.dashboard import rotas
    from app.main import app
    from testes.apoio_entrada import ClienteAposApresentacao
    monkeypatch.setattr(rotas,'carregar',lambda *_:deepcopy(dados))
    monkeypatch.setattr(rotas,'categorias_circulacao',lambda d:{r.id:dict(categorias=set(),instrumentos=set(),bloco8_salvo=True,pergunta_ativa=True) for r in d['registros']})
    resposta=ClienteAposApresentacao(app).get('/dashboard/circulacao?conta_id=CONTA-B1')
    assert resposta.status_code==200
    assert 'Sobre este número' in resposta.text
    assert 'FORM 2, bloco 8, pergunta F2-8.7' in resposta.text
    assert 'Bloco do FORM 2 salvo com pergunta ativa e vazia: Sem resposta.' in resposta.text
    assert 'Condicional fechada fica fora dessas contagens.' in resposta.text
    assert 'Fornecedores e operadores do bloco 9 não entram nesta conta.' in resposta.text


def test_fila_apa_nao_usa_competencia_secretario(sessao,dados,monkeypatch):
    from app.dashboard import fontes, rotas
    from app import continuidade_apa
    from app.modelos import ConferenciaInternaForm1Integral
    from sqlalchemy.orm import Session
    from app.main import app
    from testes.apoio_entrada import ClienteAposApresentacao
    rid=dados['registros'][0].id
    monkeypatch.setattr(rotas,'carregar',lambda *_:deepcopy(dados))
    pessoa=fontes.pessoa_ativa(sessao,'CONTA-A1')
    original=Session.get
    def get_conferencia(db,model,key,**kwargs):
        if model is ConferenciaInternaForm1Integral and key==rid:return NS(solicitada_em=AGORA)
        return original(db,model,key,**kwargs)
    monkeypatch.setattr(Session,'get',get_conferencia)
    monkeypatch.setattr(continuidade_apa,'conferente_da_apresentacao',lambda *_:pessoa.id)
    resposta=ClienteAposApresentacao(app).get('/dashboard?conta_id=CONTA-A1&lista=minha_fila_APA')
    assert resposta.status_code==200
    assert 'Conferir levantamento' in resposta.text
    assert 'Não inclui decisões do Secretário' in resposta.text


def test_secretaria_nao_espera_por_confirmacao_que_ja_deu(dados):
    from app.dashboard.regras_a9 import secretaria_pendente
    e=deepcopy(next(i['estado'] for i in dados['objetos'] if i['obj'].tipo=='R'))
    e['avaliacao_confirmacoes']={'secretaria':{'pessoa_id':'PESSOA-FICTICIA'}}
    assert secretaria_pendente(e) is None


def test_execucao_esta_na_fila_da_secretaria(dados):
    from app.dashboard.regras_a9 import secretaria_pendente
    e=next(i['estado'] for i in dados['objetos'] if i['obj'].tipo=='A')
    e.update(plano={'titulo':'Plano fictício'},plano_aprovado={'em':AGORA.isoformat()})
    assert secretaria_pendente(e)=='Registrar execução'
