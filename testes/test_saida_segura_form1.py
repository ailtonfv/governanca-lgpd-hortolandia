"""Saída para o painel reutiliza o salvamento autorizado, inclusive incompleto."""
from pathlib import Path
import shutil
import subprocess
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.modelos import RascunhoForm1Integral
from testes.test_bloco5_form1_integral import _rascunho_pronto


def test_retorno_javascript_com_falhas_e_multiplos_blocos():
    node = shutil.which('node')
    if not node:
        pytest.skip('Requer Node; inspeção visual permanece separada.')
    raiz = Path(__file__).resolve().parents[1]
    resultado = subprocess.run([node, str(raiz / 'testes/apoio_saida_form1.cjs')], cwd=raiz, capture_output=True, text=True)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr


def test_barra_unica_dialogo_e_destino_da_conta_sem_legado(sessao):
    registro = _rascunho_pronto(sessao, 'SAIDA-HTML-FICTICIA')
    cliente = TestClient(app)
    for conta in ('CONTA-A1', 'CONTA-B1'):
        pagina = cliente.get(f'/registros/{registro["registro_id"]}?conta_id={conta}')
        assert pagina.status_code == 200
        assert pagina.text.count('← Voltar ao painel') == 1
        assert f'href="/?conta_id={conta}"' in pagina.text
        assert 'aria-labelledby="titulo-saida-form1"' in pagina.text
        assert 'data-continuar-preenchendo autofocus' in pagina.text
        assert 'saida_form1.js' in pagina.text
        assert 'id="titulo-bloco-14"' in pagina.text
    css = cliente.get('/estaticos/estilo.css').text
    assert '.retorno-painel-form1 { position: sticky;' in css
    assert 'var(--altura-retorno-form1, 0px)' in css
    assert '.acoes-saida-form1 { flex-direction: column;' in css


def test_salvamento_reutilizado_incompleto_repetido_e_recusa_preservam_rascunho(sessao):
    registro = _rascunho_pronto(sessao, 'SAIDA-SALVAR-FICTICIA')
    cliente = TestClient(app)
    url = f'/registros/{registro["registro_id"]}/form1-integral/bloco-2/salvar'
    dados = {'conta_id': 'CONTA-A1', 'comando_id': 'SAIDA-FICTICIA-B2',
             'versao_lida': '1', 'acao_pos_salvar': 'permanecer', 'campo__2.12': 'Sim'}
    primeira = cliente.post(url, data=dados, follow_redirects=True)
    repetida = cliente.post(url, data=dados, follow_redirects=True)
    assert primeira.url.params['erro'] == repetida.url.params['erro'] == '0'
    sessao.expire_all()
    rascunho = sessao.get(RascunhoForm1Integral, registro['registro_id'])
    assert rascunho.versao_rascunho == 2
    assert rascunho.conteudo['respostas']['2.12'] == 'Sim'
    for alteracao in ({'comando_id': 'SAIDA-DESATUALIZADA', 'campo__2.12': 'Não'},
                      {'comando_id': 'SAIDA-NEGADA', 'conta_id': 'CONTA-B1', 'versao_lida': '2'},
                      {'comando_id': 'SAIDA-INVALIDA', 'versao_lida': '2', 'campo__2.12': 'FORJADA'}):
        resposta = cliente.post(url, data={**dados, **alteracao}, follow_redirects=True)
        assert resposta.url.params['erro'] == '1'
    sessao.expire_all()
    assert rascunho.versao_rascunho == 2
    assert rascunho.conteudo['respostas']['2.12'] == 'Sim'
