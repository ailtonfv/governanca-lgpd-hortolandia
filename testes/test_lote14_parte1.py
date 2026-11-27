"""Providências pessoais: estados sintéticos e atos reais, sem alteração de permissões."""
from uuid import uuid4
import pytest
from testes.apoio_entrada import ClienteAposApresentacao as TestClient
from app.main import app
from app.providencias import classificar
from app.central_instrumentos import itens_em_andamento
from app.caminho_central import caminho, filtrar
from app.fluxo_forms34 import estado
from app.fila_form2 import executar as fila
from testes.test_lote12 import entrada, fonte, protecoes, entrar, ato, avaliar, VERIFICADOR, SECRETARIO
from testes.apoio_r17 import preencher34


def item(s, conta, form, obj):
    return next(i for i in itens_em_andamento(s, conta)[form] if obj in i['href'])


def test_proposta_aguarda_outro_lado(sessao, entrada):
    obj = entrar(sessao, entrada)
    ato(sessao, obj, 'propor_avaliacao', evento='Evento fictício', causa='Causa fictícia',
        consequencia='Consequência fictícia', p=2, i=2, pr=2, ir=2,
        justificativa='Justificativa fictícia', controles=[])
    assert not item(sessao, 'CONTA-B1', 3, obj)['pendente']
    assert item(sessao, 'CONTA-E1', 3, obj)['ato'] == 'confirmar_avaliacao'


def test_manifestacao_dpo_pendente_contada_sem_conceder_decisao(sessao, entrada):
    obj = entrar(sessao, entrada)
    avaliar(sessao, obj, 5)
    antes = item(sessao, 'CONTA-E1', 3, obj)
    assert antes['pendente'] and antes['ato'] == 'manifestar_dpo'
    assert not item(sessao, 'CONTA-DEMO34-GAB', 3, obj)['pendente']
    ato(sessao, obj, 'manifestar_dpo', conta='CONTA-E1', texto='Manifestação consultiva fictícia')
    assert item(sessao, 'CONTA-E1', 3, obj)['ato'] != 'manifestar_dpo'
    assert not estado(sessao, obj).get('aceitacao')


def test_consulta_form2_aguarda_dpo_e_nao_beta(sessao, entrada):
    fila(sessao, conta_id='CONTA-B1', comando_id=str(uuid4()), participacao_id=entrada.id,
         versao=entrada.versao, acao='consultar', tipo='dpo', texto='Consulta fictícia')
    sessao.commit()
    assert not item(sessao, 'CONTA-B1', 2, entrada.id)['pendente']
    consultas = itens_em_andamento(sessao, 'CONTA-E1')[2]
    assert len(consultas) == 1 and consultas[0]['pendente']
    assert consultas[0]['etapa'] == 'apoio'


def test_execucao_aguarda_verificador_nao_secretaria(sessao, entrada):
    obj = entrar(sessao, entrada, 4)
    preencher34(sessao, obj)
    ato(sessao, obj, 'planejar', plano='Plano fictício para revisar e documentar os acessos.', cargo='Equipe da unidade executora', duracao_dias=30)
    assert not item(sessao, 'CONTA-B1', 4, obj)['pendente']
    ato(sessao, obj, 'aprovar_plano', conta=SECRETARIO, justificativa='Aprovação fictícia')
    ato(sessao, obj, 'executar_medida', resumo='Execução fictícia: acessos revisados e documentados.', evidencia='Arquivo fictício 01')
    assert not item(sessao, 'CONTA-B1', 4, obj)['pendente']
    assert item(sessao, VERIFICADOR, 4, obj)['ato'] == 'verificar'
    pagina = TestClient(app).get('/forms34', params={'conta_id':'CONTA-B1'})
    assert pagina.status_code == 200 and '<h2>Em andamento</h2>' in pagina.text
    assert f'/forms34/{obj}/blocos/' in pagina.text


@pytest.mark.parametrize('conta', ['CONTA-B1','CONTA-A1','CONTA-E1',VERIFICADOR,'CONTA-DEMO34-GAB'])
def test_contagem_corresponde_lista_e_escopo(sessao, entrada, conta):
    entrar(sessao, entrada)
    listas = itens_em_andamento(sessao, conta)
    fluxos = caminho(sessao, conta, listas)
    c = TestClient(app)
    for etapa in fluxos:
        itens = filtrar([i for lista in listas.values() for i in lista], etapa['chave'])
        assert etapa['quantidade'] == len(itens)
        r = c.get(etapa['lista'])
        assert r.status_code == 200
        corpo = r.text.split('<main class="conteudo">', 1)[1].split('</main>', 1)[0]
        assert corpo.count('<li>') == len(itens)
        if len(itens) == 1: assert etapa['href'] == itens[0]['href']
    assert c.get('/central', params={'conta_id':conta}).status_code == 200
    partes = {e['chave'] for e in fluxos if e['sua_parte']}
    esperado = {'CONTA-B1':'f2-analisa', 'CONTA-A1':'f1-confere', 'CONTA-E1':'apoio',
                VERIFICADOR:'f4-verifica', 'CONTA-DEMO34-GAB':'f4-plano'}
    assert esperado[conta] in partes


def test_zero_sem_numero_e_volume_tres_mais_antigos(sessao, entrada):
    from app.main import paginas
    linhas = [dict(pendente=True, etapa='f2-analisa', desde=f'2026-11-{i:02d}', href=f'/ficticio/{i}', texto=f'Item fictício {i}') for i in (5,1,3,2,4)]
    fluxos = caminho(sessao, 'CONTA-B1', {2:linhas})
    etapa = next(e for e in fluxos if e['chave']=='f2-analisa')
    assert [i['desde'] for i in etapa['itens']] == ['2026-11-01','2026-11-02','2026-11-03']
    html = paginas.env.get_template('_caminho_central.html').render(caminho=fluxos)
    assert 'Ver todos (5)' in html and '0 providência' not in html


def test_form2_complemento_recebido_exige_ato_mesmo_com_consulta_aberta():
    e = dict(tipo='principal', estado='em_atendimento', complemento='aberta', consultas_abertas=False)
    assert not classificar(2, e)['pendente']
    e.update(complemento='respondida', consultas_abertas=True)
    assert classificar(2, e)['ato'] == 'avaliar_resposta'


def test_dashboard_nao_depende_classificacao_pessoal():
    # Guarda explícita contra adoção acidental da nova classificação no dashboard.
    from pathlib import Path
    for p in (Path(__file__).parents[1]/'app/dashboard').glob('*.py'):
        texto = p.read_text(encoding='utf8')
        assert 'app.providencias' not in texto
        assert 'app.acompanhamento_forms34' not in texto
        assert 'app.central_instrumentos' not in texto


def test_novo_pedido_nao_e_respondido_por_manifestacao_anterior():
    e = dict(form=4, faixa_origem='Crítico', decisoes_pendentes={
        'cancelamento': {'em':'2026-11-21T10:00:00+00:00'}},
        manifestacao_dpo={'em':'2026-11-20T10:00:00+00:00'})
    assert classificar(4, e, {'dpo'}, 'DPO-FICTICIO')['ato'] == 'manifestar_dpo'
    assert not classificar(4, e, {'secretario'}, 'SECRETARIO-FICTICIO')['pendente']
    e['manifestacao_dpo']['em'] = '2026-11-21T11:00:00+00:00'
    assert not classificar(4, e, {'dpo'}, 'DPO-FICTICIO')['pendente']
    assert classificar(4, e, {'secretario'}, 'SECRETARIO-FICTICIO')['ato'] == 'cancelar'


def test_reavaliacao_nao_esconde_manifestacao_da_nota_vigente():
    e = dict(form=3, avaliacao={'inerente':{'faixa':'Crítico'}, 'residual':{'faixa':'Crítico'}},
             avaliacao_confirmacoes={'secretaria':{'pessoa_id':'S'},'dpo':{'pessoa_id':'D'}},
             reavaliacao={'avaliacao':{'residual':{'faixa':'Moderado'}},
                          'avaliacao_confirmacoes':{'dpo':{'pessoa_id':'D'}}})
    assert classificar(3, e, {'dpo'}, 'D')['ato'] == 'manifestar_dpo'


@pytest.mark.parametrize('conta', ['CONTA-B1','CONTA-A1','CONTA-E1',VERIFICADOR,'CONTA-DEMO34-GAB'])
def test_links_de_apoio_preservam_conta_e_svg(sessao, entrada, conta):
    c = TestClient(app)
    central = c.get('/central', params={'conta_id':conta})
    for pagina in ('como-funciona', 'fluxograma'):
        assert f'/{pagina}?conta_id={conta}' in central.text
        r = c.get('/'+pagina, params={'conta_id':conta})
        assert r.status_code == 200 and f'/central?conta_id={conta}' in r.text
        if pagina == 'fluxograma':
            assert '<svg' in r.text and 'bFit' in r.text and 'bReal' in r.text
