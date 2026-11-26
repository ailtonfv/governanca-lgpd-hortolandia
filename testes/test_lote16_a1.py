"""A1: duração em dias corridos, sem consumir a espera da aprovação."""
from datetime import datetime, timezone
import pytest
from app.prazos_plano34 import duracao_validada, vencimento_na_aprovacao
from app.validacao_atos34 import ErrosCampos
from app.fluxo_forms34 import estado
from testes.test_lote12 import entrada, fonte, protecoes, entrar, ato, SECRETARIO, VERIFICADOR, PREFEITO, RELATOR, avaliar
from testes.apoio_r17 import preencher34


def test_limite_critico_e_imediato():
    for e in ({'faixa_origem':'Crítico'}, {'respostas':{'F4-4.9':'Imediata'}}):
        assert duracao_validada(e, 30) == 30
        with pytest.raises(ErrosCampos, match='30 dias'):
            duracao_validada(e, 60)
    assert duracao_validada({'faixa_origem':'Moderado'}, 60) == 60
    for valor in (0, -1, True, None, 1.5, 'abc'):
        with pytest.raises(ErrosCampos):duracao_validada({}, valor)


def test_calendario_local_e_data_historica():
    e = {'duracao_dias':30, 'faixa_origem':'Crítico'}
    assert vencimento_na_aprovacao(e, '2026-11-27T01:00:00+00:00') == '2026-12-26'
    assert vencimento_na_aprovacao({'prazo':'2027-01-15'}, '2026-11-27T01:00:00+00:00') == '2027-01-15'


def test_duracao_comeca_na_aprovacao_e_aparece_na_confirmacao(sessao, entrada, monkeypatch):
    import app.fluxo_forms34 as fluxo
    from fastapi.testclient import TestClient
    from app.main import app
    obj = entrar(sessao, entrada, 4)
    preencher34(sessao, obj)
    monkeypatch.setattr(fluxo, 'agora_utc', lambda: datetime(2026,11,20,15,tzinfo=timezone.utc))
    ato(sessao,obj,'planejar',plano='Plano fictício para organizar controles e evidências.',
        cargo='Equipe da unidade executora',duracao_dias=30)
    assert estado(sessao,obj)['prazo'] is None
    monkeypatch.setattr('app.eventos.agora_utc', lambda: datetime(2026,11,26,15,tzinfo=timezone.utc))
    tela = TestClient(app).get(f'/forms34/{obj}/blocos/3?conta_id={SECRETARIO}')
    assert tela.status_code == 200
    assert 'até 26/12/2026, se aprovar hoje' in tela.text
    assert 'Plano fictício para organizar controles e evidências.' in tela.text
    monkeypatch.setattr(fluxo, 'agora_utc', lambda: datetime(2026,11,26,15,tzinfo=timezone.utc))
    ato(sessao,obj,'aprovar_plano',conta=SECRETARIO,justificativa='Aprovação fictícia')
    e = estado(sessao,obj)
    assert e['prazo'] == '2026-12-26'
    assert e['plano_aprovado']['prazo'] == '2026-12-26'
    assert e['plano_registrado_em'].startswith('2026-11-20')


def test_plano_sem_cargo_ou_texto_curto_recusado(sessao, entrada):
    obj = entrar(sessao, entrada, 4)
    antes = estado(sessao,obj)['versao']
    with pytest.raises(ErrosCampos):
        ato(sessao,obj,'planejar',plano='Plano fictício com descrição suficiente para execução.',cargo='',duracao_dias=30)
    with pytest.raises(ErrosCampos, match='30 caracteres'):
        ato(sessao,obj,'planejar',plano='Plano fictício',cargo='Equipe da unidade executora',duracao_dias=30)
    assert estado(sessao,obj)['versao'] == antes


def verificar_acao(s, p, reducao='Parcialmente', risco=False):
    from app.etapas_forms34 import VERIFICACAO
    if risco:
        r = entrar(s,p,3)
        avaliar(s,r,2)
        obj = ato(s,r,'encaminhar_acao',justificativa='Providência fictícia')['identidade_id']
    else:obj = entrar(s,p,4)
    preencher34(s,obj)
    ato(s,obj,'planejar',plano='Plano fictício para corrigir o controle de acesso.',cargo='Equipe da unidade executora',duracao_dias=30)
    ato(s,obj,'aprovar_plano',conta=SECRETARIO,justificativa='Aprovação fictícia')
    ato(s,obj,'executar_medida',resumo='Execução fictícia: acessos revisados e documentados.',evidencia='Processo fictício 01')
    respostas={k:'Sim' for k in VERIFICACAO};respostas['F4-4.22']=reducao
    ato(s,obj,'verificar',conta=VERIFICADOR,aprovada=True,evidencia='Conferência fictícia 01',**respostas)
    return obj


def test_parcial_nao_encerra_e_secretaria_cria_novo_plano(sessao, entrada):
    obj=verificar_acao(sessao,entrada)
    assert not estado(sessao,obj).get('encerrada')
    with pytest.raises(ValueError, match='risco'):
        ato(sessao,obj,'aprender',contexto='Fictício',diretriz='Fictícia',escopo='Fictício')
    ato(sessao,obj,'propor_residual_acao',pr=2,ir=2,justificativa='Nota fictícia posterior')
    with pytest.raises(PermissionError):ato(sessao,obj,'confirmar_residual_acao')
    ato(sessao,obj,'confirmar_residual_acao',conta='CONTA-E1')
    with pytest.raises(PermissionError):
        ato(sessao,obj,'decidir_residual_acao',conta='CONTA-E1',opcao='nova_providencia',justificativa='Fictícia')
    novo=ato(sessao,obj,'decidir_residual_acao',opcao='nova_providencia',justificativa='Novo plano fictício')['identidade_id']
    assert novo!=obj and not estado(sessao,novo).get('plano_aprovado')
    assert estado(sessao,novo)['acao_anterior_id']==obj
    assert estado(sessao,obj)['encerrada']


def test_critico_posterior_exige_gabinete_e_documento(sessao, entrada):
    obj=verificar_acao(sessao,entrada)
    ato(sessao,obj,'propor_residual_acao',pr=5,ir=5,justificativa='Nota fictícia posterior')
    ato(sessao,obj,'confirmar_residual_acao',conta='CONTA-E1')
    ato(sessao,obj,'decidir_residual_acao',opcao='nova_providencia',justificativa='Nova medida fictícia')
    assert not estado(sessao,obj).get('encerrada')
    with pytest.raises(PermissionError):ato(sessao,obj,'aceitar_residual_acao',conta=SECRETARIO,justificativa='Fictícia')
    with pytest.raises(ValueError, match='DPO'):ato(sessao,obj,'aceitar_residual_acao',conta=PREFEITO,justificativa='Fictícia',documento='Despacho fictício 01')
    ato(sessao,obj,'manifestar_dpo',conta='CONTA-E1',texto='Manifestação fictícia sobre o residual posterior.')
    ato(sessao,obj,'manifestar_comite',conta=RELATOR,finalidade='residual',ata='Ata fictícia 01',texto='Manifestação fictícia posterior.',favoravel=True)
    with pytest.raises(ValueError):ato(sessao,obj,'aceitar_residual_acao',conta=PREFEITO,justificativa='Fictícia')
    ato(sessao,obj,'aceitar_residual_acao',conta=PREFEITO,justificativa='Decisão fictícia',documento='Despacho fictício 01')
    assert estado(sessao,obj)['encerrada']
    assert estado(sessao,obj)['aceitacao_residual_acao']['registrador']=='Gabinete'


def test_reavaliar_preserva_nota_vigente_e_vinculo(sessao, entrada):
    obj=verificar_acao(sessao,entrada,risco=True)
    r=estado(sessao,obj)['risco_id'];anterior=estado(sessao,r)['avaliacao']
    ato(sessao,obj,'propor_residual_acao',pr=2,ir=2,justificativa='Nota fictícia posterior')
    ato(sessao,obj,'confirmar_residual_acao',conta='CONTA-E1')
    res=ato(sessao,obj,'decidir_residual_acao',opcao='reavaliar',justificativa='Reavaliação fictícia')
    assert res['identidade_id']==r
    assert estado(sessao,r)['revisao_aberta']
    assert estado(sessao,r)['avaliacao']==anterior


def test_falha_exposta_devolve_aprendizagem(sessao, entrada):
    obj=verificar_acao(sessao,entrada,reducao='Sim')
    ato(sessao,obj,'aprender',contexto='Contexto fictício',diretriz='Diretriz fictícia',escopo='Limites fictícios')
    ato(sessao,obj,'conferir_aprendizagem',conta='CONTA-E1',sem_dados_pessoais=True,
        sem_falha_exposta=False,observacao='Relato fictício precisa omitir a fragilidade.')
    assert estado(sessao,obj)['aprendizagem_devolvida']
    assert not estado(sessao,obj).get('aprendizagem_conferida')


def test_aviso_anterior_sem_reabrir_e_sem_aprender():
    from app.encerramento_form4 import aviso_anterior, pode_encerrar
    from app.atos_forms34_interface import disponiveis
    e={'form':4,'encerrada':True,'verificada':True,'respostas':{'F4-4.22':'Parcialmente'}}
    assert 'regra anterior' in aviso_anterior(e)
    assert not pode_encerrar(e)
    assert e['encerrada']
    assert not any(a['acao']=='aprender' for a in disponiveis(4,9,{'secretaria'},e))
    assert any(a['acao']=='propor_residual_acao' for a in disponiveis(4,8,{'secretaria'},e))
