"""Decisão de 19/11: proposta separada da nota conjunta vigente."""
from copy import deepcopy
import json,re
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.modelos import Evento
from app.fluxo_forms34 import _faixa
from testes.test_lote12 import protecoes,entrada,fonte,entrar,ato,estado,avaliar,SECRETARIO,RELATOR

def preparar(s,p):
    obj=entrar(s,p);avaliar(s,obj,2)
    ato(s,obj,'propor_triagem',resultado='nao_indicado',justificativa='Triagem fictícia da nota vigente')
    ato(s,obj,'confirmar_triagem',conta='CONTA-E1')
    ato(s,obj,'aceitar_residual',conta=SECRETARIO,justificativa='Aceitação fictícia da nota vigente')
    return obj

def revisar(s,obj):
    ato(s,obj,'revisar_avaliacao',evento='Novo evento fictício',causa='Nova causa fictícia',
        consequencia='Nova consequência fictícia',p=5,i=5,pr=5,ir=5,controles=[],justificativa='Nova avaliação fictícia')

def test_vigente_preservada_durante_proposta_e_matriz(sessao,entrada):
    obj=preparar(sessao,entrada);antes=deepcopy(estado(sessao,obj));revisar(sessao,obj);e=estado(sessao,obj)
    for k in ('avaliacao','avaliacao_confirmacoes','triagem','triagem_confirmacoes','aceitacao','evento','causa','consequencia'):
        assert e[k]==antes[k]
    assert _faixa(e)=='Moderado' and e['reavaliacao']['avaliacao']['residual']['nota']==25
    c=TestClient(app)
    for conta in ('CONTA-B1','CONTA-E1'):
        html=c.get(f'/forms34/{obj}/blocos/14?conta_id={conta}').text
        assert 'Reavaliação em andamento' in html and 'Nova avaliação fictícia' in html
        assert 'inerente 25, residual 25' in html
        from html import unescape
        matrizes=re.findall(r"data-inicial='(.*?)'",html)
        assert len(matrizes)==1 and json.loads(unescape(matrizes[0]))['residual']['nota']==4
        assert ('name="acao" value="confirmar_avaliacao"' in html)==(conta=='CONTA-E1')
    assert estado(sessao,obj)==e

def test_substitui_somente_na_confirmacao_e_preserva_historico(sessao,entrada):
    obj=preparar(sessao,entrada)
    antigos=[(e.id,e.hash,deepcopy(e.conteudo)) for e in sessao.scalars(select(Evento).where(Evento.cadeia_id==obj).order_by(Evento.id))]
    revisar(sessao,obj)
    with pytest.raises(PermissionError):ato(sessao,obj,'confirmar_avaliacao')
    assert estado(sessao,obj)['avaliacao']['residual']['nota']==4
    ato(sessao,obj,'confirmar_avaliacao',conta='CONTA-E1');e=estado(sessao,obj)
    assert e['avaliacao']['residual']['nota']==25 and _faixa(e)=='Crítico'
    assert set(e['avaliacao_confirmacoes'])=={'secretaria','dpo'} and 'reavaliacao' not in e
    # Comportamento anterior dos atos dependentes mantido, agora só na substituição efetiva.
    assert not e.get('aceitacao') and not e.get('triagem')
    assert [(x.id,x.hash,x.conteudo) for x in sessao.scalars(select(Evento).where(Evento.cadeia_id==obj,Evento.id<=antigos[-1][0]).order_by(Evento.id))]==antigos

def test_sem_consenso_preserva_vigente_ate_deliberacao(sessao,entrada):
    obj=preparar(sessao,entrada);antes=deepcopy(estado(sessao,obj));revisar(sessao,obj)
    ato(sessao,obj,'sem_consenso',conta='CONTA-E1',campo='avaliacao',posicao='Divergência fictícia')
    e=estado(sessao,obj)
    assert e['avaliacao']==antes['avaliacao'] and e['aceitacao']==antes['aceitacao']
    assert e['triagem']==antes['triagem'] and _faixa(e)=='Moderado'
    assert e['reavaliacao']['avaliacao_sem_consenso']
    with pytest.raises(ValueError,match='Sem consenso'):ato(sessao,obj,'confirmar_avaliacao',conta='CONTA-E1')
    with pytest.raises(ValueError,match='Sem consenso'):revisar(sessao,obj)
    ato(sessao,obj,'manifestar_comite',conta=RELATOR,finalidade='avaliacao',ata='Ata fictícia',texto='Deliberação fictícia',favoravel=True)
    assert estado(sessao,obj)['avaliacao']==antes['avaliacao']
    revisar(sessao,obj)
    assert estado(sessao,obj)['avaliacao']==antes['avaliacao']
