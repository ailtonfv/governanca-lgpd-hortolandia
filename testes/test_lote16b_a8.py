"""A8: painel e dashboard usam a mesma consulta pendente, sem contar ofício."""
from uuid import uuid4
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.fila_form2 import executar, manifestar_de_oficio
from app.modelos import ParticipacaoForm2
from app.dashboard.fontes import carregar, escopo_da_conta
from app.dashboard.consultas import operacao
from testes.test_lote12 import entrada, fonte, protecoes


def test_mesma_regra_no_painel_e_dashboard(sessao, entrada):
    client=TestClient(app)
    # Sem questão, orientação de ofício não é espera pelo DPO.
    manifestar_de_oficio(sessao,conta_id='CONTA-E1',participacao_id=entrada.id,comando_id=str(uuid4()),texto='Orientação fictícia de ofício.')
    sessao.commit()
    def comparar(esperado):
        painel=client.get('/form2/painel-dpo?conta_id=CONTA-E1')
        assert painel.status_code==200
        ids={l['consulta'].id for l in painel.context['grupos_dpo']['aguardando_dpo']}
        dados=carregar(sessao,escopo_da_conta(sessao,'CONTA-E1'))
        fila=next(q for q in operacao(dados,datetime.now(timezone.utc)) if q['chave']=='fila_DPO')
        assert len(ids)==fila['numero']==esperado
        assert ids=={l['id'] for l in fila['lista']}
    comparar(0)
    r=executar(sessao,conta_id='CONTA-B1',participacao_id=entrada.id,comando_id=str(uuid4()),versao=entrada.versao,acao='consultar',tipo='dpo',texto='Consulta fictícia sobre F2-2.9')
    sessao.commit();comparar(1)
    consulta=sessao.get(ParticipacaoForm2,r['participacao_id'])
    executar(sessao,conta_id='CONTA-E1',participacao_id=consulta.id,comando_id=str(uuid4()),versao=consulta.versao,acao='assumir')
    executar(sessao,conta_id='CONTA-E1',participacao_id=consulta.id,comando_id=str(uuid4()),versao=consulta.versao,acao='concluir',texto='Orientação fictícia solicitada.')
    sessao.commit();comparar(0)
    manifestar_de_oficio(sessao,conta_id='CONTA-B1',participacao_id=consulta.id,comando_id=str(uuid4()),texto='Providência fictícia registrada.',decisao='Acolhida')
    sessao.commit()
    painel=client.get('/form2/painel-dpo?conta_id=CONTA-E1')
    assert [l['consulta'].id for l in painel.context['grupos_dpo']['respondidas']]==[consulta.id]


def test_orientacao_sem_pergunta_e_ordem(sessao,entrada):
    pagina=TestClient(app).get(f'/form2/participacoes/{entrada.id}/orientacao?conta_id=CONTA-E1')
    assert pagina.status_code==200
    assert 'Nenhuma consulta pendente. Você pode registrar uma orientação de ofício.' in pagina.text
    assert 'Nenhuma manifestação registrada neste Registro.' in pagina.text
    assert pagina.text.index('Perguntas do AAL') < pagina.text.index('name="texto"') < pagina.text.index('Manifestações registradas')


def test_respostas_com_enunciado_e_valor_legivel(sessao,entrada):
    from app.respostas_form2 import definicao_bloco
    entrada.conteudo={'respostas_etapa1':{'F2-2.9':'A_CONFIRMAR'}}
    sessao.commit()
    pagina=TestClient(app).get(f'/form2/participacoes/{entrada.id}/orientacao?conta_id=CONTA-E1')
    pergunta=next(q for q in definicao_bloco(2)['itens'] if q['id']=='F2-2.9')
    assert pagina.status_code==200
    assert pergunta['enunciado'] in pagina.text
    assert 'A confirmar' in pagina.text and 'A_CONFIRMAR' not in pagina.text
    assert 'Bloco 2' in pagina.text
