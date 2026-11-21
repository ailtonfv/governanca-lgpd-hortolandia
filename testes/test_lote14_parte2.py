"""Primeiro acesso real, separado dos cenários operacionais já apresentados."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.apresentacao_entrada import chave


@pytest.mark.parametrize('conta', ['CONTA-A1', 'CONTA-B1', 'CONTA-E1'])
def test_apresentacao_primeiro_acesso_por_conta(conta):
    c = TestClient(app)
    primeiro = c.get('/central', params={'conta_id': conta}, follow_redirects=False)
    assert primeiro.status_code == 303
    assert primeiro.headers['location'] == '/como-funciona?conta_id=' + conta
    apoio = c.get(primeiro.headers['location'])
    assert apoio.status_code == 200
    assert c.cookies.get(chave(conta)) == '1'
    depois = c.get('/central', params={'conta_id': conta}, follow_redirects=False)
    assert depois.status_code == 200 and 'Seu caminho no sistema' in depois.text
    outra = 'CONTA-B1' if conta != 'CONTA-B1' else 'CONTA-A1'
    assert c.get('/central', params={'conta_id': outra}, follow_redirects=False).status_code == 303


def test_marca_nao_concede_acesso():
    c = TestClient(app)
    c.cookies.set(chave('CONTA-INEXISTENTE'), '1')
    assert c.get('/central?conta_id=CONTA-INEXISTENTE&entrar=1').status_code == 404
    assert c.get('/como-funciona?conta_id=CONTA-INEXISTENTE').status_code == 404


def test_entrada_explicita_e_fluxograma_nao_marca_apresentacao():
    c = TestClient(app)
    assert c.get('/fluxograma?conta_id=CONTA-B1').status_code == 200
    assert not c.cookies.get(chave('CONTA-B1'))
    assert c.get('/central?conta_id=CONTA-B1&entrar=1').status_code == 200
    assert c.cookies.get(chave('CONTA-B1')) == '1'
