"""12-G grupo 1: responsabilidades, devolução e leitura de eventos reais."""
from uuid import uuid4
import re
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.fluxo_forms34 import estado
from app.etapas_forms34 import VERIFICACAO, pode_preencher
from app.atos_forms34_interface import disponiveis
from testes.test_lote12 import entrada, fonte, protecoes, entrar, ato, avaliar, SECRETARIO, VERIFICADOR, RELATOR
from testes.apoio_r17 import preencher34


def acao_verificada(s, entrada):
    obj = entrar(s, entrada, 4)
    preencher34(s, obj)
    ato(s, obj, 'planejar', plano='Plano fictício para revisar e documentar os acessos.', cargo='Equipe da unidade executora', duracao_dias=30)
    ato(s, obj, 'aprovar_plano', conta=SECRETARIO, justificativa='Decisão fictícia')
    ato(s, obj, 'executar_medida', resumo='Execução fictícia: acessos revisados e documentados.', evidencia='Processo fictício 01')
    ato(s, obj, 'verificar', conta=VERIFICADOR, aprovada=True, evidencia='Referência fictícia',
        **{k: ('Sim' if k=='F4-4.22' else 'A confirmar') for k in VERIFICACAO})
    return obj


def test_grupo1_responsabilidade_dominio_e_todos_blocos(sessao, entrada):
    obj = entrar(sessao, entrada, 4)
    anterior = estado(sessao, obj)
    client = TestClient(app)
    for bloco in range(1, 10):
        tela = client.get(f'/forms34/{obj}/blocos/{bloco}?conta_id=CONTA-E1')
        assert tela.status_code == 200
        assert f'Salvar bloco {bloco}' not in tela.text
        assert 'data-somente-leitura' in tela.text
        resposta = client.post(f'/forms34/{obj}/blocos/{bloco}?conta_id=CONTA-E1',
            data=dict(acao='salvar_bloco', versao=anterior['versao'], comando_id=str(uuid4())))
        assert resposta.status_code == 403
    assert estado(sessao, obj) == anterior
    for conta in (SECRETARIO, VERIFICADOR, RELATOR):
        with pytest.raises(PermissionError):
            ato(sessao, obj, 'salvar_bloco', conta=conta, bloco=9, campos={})
    assert pode_preencher(3, {'dpo'})  # corresponsabilidade do FORM 3 preservada
    assert pode_preencher(4, {'secretaria'})
    for papel in ('dpo', 'verificador', 'relator', 'secretario', 'gabinete'):
        assert not pode_preencher(4, {papel})


def test_grupo1_encerramento_bloqueia_perguntas_e_exibe_autoria_automatica(sessao, entrada):
    obj = acao_verificada(sessao, entrada)
    anterior = estado(sessao, obj)
    assert anterior['encerrada']
    with pytest.raises(ValueError, match='encerrada'):
        ato(sessao, obj, 'salvar_bloco', bloco=9, campos={'F4-4.27': 'Mudança fictícia'})
    assert estado(sessao, obj) == anterior
    tela = TestClient(app).get(f'/forms34/{obj}/blocos/9?conta_id=CONTA-B1')
    assert tela.status_code == 200
    assert 'Salvar bloco 9' not in tela.text
    assert 'Ação concluída automaticamente em ' in tela.text
    assert 'após a verificação aprovada' in tela.text
    from app.leitura_atos34 import historico_visual
    from app.fluxo_forms34 import historico
    hs = historico_visual(list(reversed(historico(sessao,obj))), {}, {}, {})
    encerramento = next(h for h in hs if h['acao']=='encerramento_automatico')
    assert encerramento['autor']=='Sistema'


def test_grupo1_devolucao_exige_observacao_e_nova_conferencia(sessao, entrada):
    obj = acao_verificada(sessao, entrada)
    ato(sessao,obj,'aprender',contexto='Contexto fictício',diretriz='Diretriz fictícia',escopo='Limites fictícios')
    anterior = estado(sessao,obj)
    client=TestClient(app)
    tela=client.get(f'/forms34/{obj}/blocos/9?conta_id=CONTA-E1')
    assert 'data-obrigatorio-observacao' in tela.text
    assert 'Observação do DPO' in tela.text
    resposta=client.post(f'/forms34/{obj}/blocos/9?conta_id=CONTA-E1',data={
        'acao':'conferir_aprendizagem','versao':anterior['versao'],'comando_id':str(uuid4()),
        'sem_dados_pessoais':'nao','observacao':''})
    assert resposta.status_code==409 and 'Preencha este campo obrigatório.' in resposta.text
    with pytest.raises(ValueError):
        ato(sessao,obj,'conferir_aprendizagem',conta='CONTA-E1',sem_dados_pessoais=False,sem_falha_exposta=True,observacao=' ')
    assert estado(sessao,obj)==anterior
    ato(sessao,obj,'conferir_aprendizagem',conta='CONTA-E1',sem_dados_pessoais=False,sem_falha_exposta=True,
        observacao='Orientação fictícia: retirar identificadores individuais.')
    e=estado(sessao,obj)
    assert e['aprendizagem_devolvida']['versao']==1
    assert not e.get('aprendizagem_conferida') and not e.get('aprendizagem_autorizada')
    assert any(a['acao']=='aprender' for a in disponiveis(4,9,{'secretaria'},e))
    assert not any(a['acao']=='conferir_aprendizagem' for a in disponiveis(4,9,{'dpo'},e))
    with pytest.raises(ValueError):ato(sessao,obj,'autorizar_aprendizagem')
    tela=TestClient(app).get(f'/forms34/{obj}/blocos/9?conta_id=CONTA-B1')
    assert 'Orientação fictícia: retirar identificadores individuais.' in tela.text
    ato(sessao,obj,'aprender',contexto='Contexto fictício revisto',diretriz='Diretriz fictícia',escopo='Limites fictícios')
    e=estado(sessao,obj)
    assert e['aprendizagem']['versao']==2 and not e.get('aprendizagem_devolvida')
    with pytest.raises(ValueError):ato(sessao,obj,'autorizar_aprendizagem')
    ato(sessao,obj,'conferir_aprendizagem',conta='CONTA-E1',sem_dados_pessoais=True,sem_falha_exposta=True,observacao='Conferência fictícia da nova versão.')
    assert estado(sessao,obj)['aprendizagem_conferida']['observacao']=='Conferência fictícia da nova versão.'
    ato(sessao,obj,'autorizar_aprendizagem')
    assert estado(sessao,obj)['aprendizagem_autorizada']


def test_grupo1_todos_une_abas_inclusive_risco_concluido_relator(sessao, entrada):
    risco=entrar(sessao,entrada)
    preencher34(sessao,risco)
    avaliar(sessao,risco,1)
    ato(sessao,risco,'propor_triagem',resultado='nao_indicado',justificativa='Triagem fictícia')
    ato(sessao,risco,'confirmar_triagem',conta='CONTA-E1')
    ato(sessao,risco,'aceitar_residual',conta=SECRETARIO,justificativa='Decisão fictícia')
    ato(sessao,risco,'concluir_avaliacao')
    acao=entrar(sessao,entrada,4)
    client=TestClient(app)
    listas=[]
    for filtro in ('','&form=3','&form=4'):
        resposta=client.get(f'/forms34?conta_id={RELATOR}{filtro}')
        assert resposta.status_code==200
        listas.append(set(re.findall(r'/forms34/([\w-]+)/blocos/',resposta.text)))
    assert risco in listas[1] and acao in listas[2]
    assert listas[0]==listas[1]|listas[2]
