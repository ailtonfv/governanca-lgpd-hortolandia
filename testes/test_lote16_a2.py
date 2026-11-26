"""A2: condições explícitas, referência conjunta e consulta jurídica."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.fluxo_forms34 import estado
from testes.test_lote12 import entrada, fonte, protecoes, entrar, ato, avaliar, SECRETARIO, PREFEITO, RELATOR, VERIFICADOR
from testes.apoio_r17 import preencher34
from app.etapas_forms34 import VERIFICACAO


def condicionado(s,p):
    r=entrar(s,p)
    avaliar(s,r,2)
    ato(s,r,'aceitar_residual',conta=SECRETARIO,justificativa='Aceitação fictícia',condicoes=[
        dict(texto='RIPD fictício',tipo='Elaborar/revisar RIPD'),
        dict(texto='Acessos fictícios',tipo='Revisar acesso/perfis')])
    return r


def test_duas_condicoes_duas_acoes_e_selo(sessao,entrada):
    r=condicionado(sessao,entrada)
    e=estado(sessao,r)
    ids=[c['acao_id'] for c in e['condicoes_aceitacao']]
    assert len(set(ids))==2
    for aid in ids:
        a=estado(sessao,aid)
        assert a['risco_id']==r and a['respostas']['F4-4.9']=='Imediata'
        assert len(a['respostas']['F4-4.4'])==1 and not a.get('plano_aprovado')
    c=TestClient(app)
    for url in (f'/forms34/{r}/blocos/14?conta_id=CONTA-B1','/forms34?conta_id=CONTA-B1',f'/registros/{entrada.registro_id}?conta_id=CONTA-B1'):
        resposta=c.get(url)
        assert resposta.status_code==200
        assert 'Aceitação condicionada: 2 condições em aberto' in resposta.text


def test_ripd_aguarda_confirmacao_e_condicao_bloqueia_aprender(sessao,entrada):
    r=condicionado(sessao,entrada)
    aid=estado(sessao,r)['condicoes_aceitacao'][0]['acao_id']
    preencher34(sessao,aid)
    ato(sessao,aid,'planejar',plano='Plano fictício para elaboração conjunta do RIPD.',cargo='Equipe da unidade executora',duracao_dias=30)
    ato(sessao,aid,'aprovar_plano',conta=SECRETARIO,justificativa='Aprovação fictícia')
    ato(sessao,aid,'executar_medida',resumo='RIPD fictício elaborado e juntado ao processo.',evidencia='Processo fictício 02')
    ato(sessao,aid,'verificar',conta=VERIFICADOR,aprovada=True,evidencia='Conferência fictícia',**{k:'Sim' for k in VERIFICACAO})
    assert not estado(sessao,aid).get('encerrada')
    ato(sessao,r,'informar_ripd',referencia='Processo fictício RIPD-02')
    assert not estado(sessao,aid).get('encerrada')
    with pytest.raises(PermissionError):ato(sessao,r,'confirmar_ripd')
    ato(sessao,r,'confirmar_ripd',conta='CONTA-E1')
    assert estado(sessao,aid)['encerrada']
    with pytest.raises(ValueError):ato(sessao,aid,'aprender',contexto='Fictício',diretriz='Fictícia',escopo='Fictício')


def test_critico_registra_decisao_juridica(sessao,entrada):
    r=entrar(sessao,entrada)
    avaliar(sessao,r,5)
    ato(sessao,r,'manifestar_dpo',conta='CONTA-E1',texto='Manifestação fictícia')
    ato(sessao,r,'manifestar_comite',conta=RELATOR,finalidade='residual',ata='Ata fictícia',texto='Manifestação fictícia',favoravel=True)
    with pytest.raises(ValueError,match='manifestação jurídica'):
        ato(sessao,r,'aceitar_residual',conta=PREFEITO,justificativa='Fictícia',documento='Despacho fictício')
    ato(sessao,r,'aceitar_residual',conta=PREFEITO,justificativa='Fictícia',documento='Despacho fictício',
        solicitar_juridico=False,motivo_juridico='Dispensa fictícia fundamentada para este ensaio')
    assert estado(sessao,r)['consulta_juridica_aceitacao']['solicitada'] is False


def test_tipo_unico_preserva_multiplos_antigos():
    from app.questionario_forms34 import salvar, perguntas
    q=next(q for q in perguntas(4) if q['id']=='F4-4.4')
    tipos=q['opcoes'][:2]
    dados={'bloco':q['bloco'],'campos':{'F4-4.4':tipos}}
    with pytest.raises(ValueError,match='um tipo'):salvar(4,{},dados,{})
    assert salvar(4,{'F4-4.4':tipos},dados,{})['F4-4.4']==tipos
