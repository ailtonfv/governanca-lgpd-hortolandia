"""Encaminhamento agrupado, origem preservada e idempotência do FORM 3."""
from uuid import uuid4

from fastapi.testclient import TestClient

from app.grupos_lacunas import grupos_para_tela
from app.main import app
from testes.test_lote12 import ato, entrada, entrar, estado, fonte, protecoes

ACESSO = {
    'F3-3.16': 'Não', 'F3-3.17': 'Não', 'F3-3.18': 'Sim',
    'F3-3.19': 'Não', 'F3-3.19.1': 'Não', 'F3-3.20': 'Não',
}
IDS = ['LAC-' + k for k in ACESSO]
DESTINO = 'Providência no FORM 4'


def preparar(sessao, entrada):
    risco = entrar(sessao, entrada)
    ato(sessao, risco, 'salvar_bloco', bloco=6, campos=ACESSO)
    return risco


def encaminhar(sessao, risco, ids, prioridade='Média'):
    return ato(sessao, risco, 'encaminhar_acao', lacunas_ids=ids,
               destino=DESTINO, prioridade=prioridade)['identidade_id']


def test_seis_lacunas_geram_uma_providencia_com_seis_vinculos(sessao, entrada):
    risco = preparar(sessao, entrada)
    cliente = TestClient(app)
    url = f'/forms34/{risco}/blocos/16?conta_id=CONTA-B1'
    tela = cliente.get(url)
    assert tela.status_code == 200
    assert 'Revisar acesso/perfis — 6 lacunas' in tela.text
    assert all(f'value="{i}" checked' in tela.text for i in IDS)

    ato(sessao, risco, 'destinar_lacuna', lacuna_id=IDS[0],
        destino=DESTINO, prioridade='Alta')
    retorno = cliente.post(url, data={
        'acao': 'encaminhar_acao', 'lacunas_ids': IDS, 'destino': DESTINO,
        'prioridade': 'Baixa', 'comando_id': str(uuid4()),
        'versao': estado(sessao, risco)['versao'],
    })
    assert retorno.status_code == 200
    sessao.expire_all()
    e = estado(sessao, risco)
    assert len(e['acoes']) == 1
    obj = e['acoes'][0]
    assert set(e['encaminhamentos_lacunas']) == set(IDS)
    assert {v['acao_id'] for v in e['encaminhamentos_lacunas'].values()} == {obj}
    assert {l['id'] for l in estado(sessao, obj)['origem_lacunas']} == set(IDS)
    assert estado(sessao, obj)['prioridade_origem'] == 'Alta'
    assert 'Lacunas cobertas pela providência' in retorno.text
    assert all(i in retorno.text for i in IDS)


def test_separar_uma_lacuna_e_reencaminhar_grupo(sessao, entrada):
    risco = preparar(sessao, entrada)
    grupo, avulsa = IDS[:-1], IDS[-1:]
    ato(sessao, risco, 'destinar_lacuna', lacunas_ids=grupo, destino=DESTINO, prioridade='Média')
    primeira = encaminhar(sessao, risco, grupo)
    segunda = encaminhar(sessao, risco, avulsa)
    assert primeira != segunda
    assert encaminhar(sessao, risco, list(reversed(grupo))) == primeira
    e = estado(sessao, risco)
    assert e['acoes'] == [primeira, segunda]
    assert e['encaminhamentos_lacunas'][avulsa[0]]['acao_id'] == segunda


def test_sugestao_igual_nao_inclui_automaticamente_verificacao_ou_a_confirmar():
    lacunas = [dict(id=str(i), natureza=natureza, acao_sugerida='Uma sugestão')
               for i, natureza in enumerate(['lacuna', 'verificacao', 'a_confirmar'])]
    grupos = grupos_para_tela({}, lacunas)
    assert [[item['id'] for item in g['itens']] for g in grupos] == [['0']]


def test_juntar_lacunas_de_sugestoes_diferentes(sessao, entrada):
    risco = preparar(sessao, entrada)
    ato(sessao, risco, 'salvar_bloco', bloco=7, campos={'F3-3.21': 'Sim'})
    ids = [IDS[0], 'LAC-F3-3.21']
    ato(sessao, risco, 'destinar_lacuna', lacunas_ids=ids, destino=DESTINO, prioridade='Baixa')
    cliente = TestClient(app)
    tela = cliente.get(f'/forms34/{risco}/blocos/16?conta_id=CONTA-B1')
    assert 'Providência selecionada pela Secretaria — 2 lacunas' in tela.text
    obj = encaminhar(sessao, risco, ids, 'Baixa')
    assert {l['id'] for l in estado(sessao, obj)['origem_lacunas']} == set(ids)
