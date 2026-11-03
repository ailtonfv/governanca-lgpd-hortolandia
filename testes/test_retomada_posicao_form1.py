"""Posição de leitura é estado de navegação, nunca resposta REV13."""
from pathlib import Path
import shutil
import subprocess
import pytest
from fastapi.testclient import TestClient
from app.main import app
from testes.test_bloco5_form1_integral import _rascunho_pronto


def test_javascript_retomada_de_posicao_sem_alterar_respostas():
    node = shutil.which('node')
    if not node:
        pytest.skip('Ensaio JavaScript requer Node; aceite visual permanece separado.')
    raiz = Path(__file__).resolve().parents[1]
    resultado = subprocess.run([node, str(raiz / 'testes/apoio_posicao_form1.cjs')], cwd=raiz, capture_output=True, text=True)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr


def test_salvar_permanecer_e_avancar_preservam_destinos_e_respostas(sessao):
    registro = _rascunho_pronto(sessao, 'RETOMADA-POSICAO-FICTICIA')
    cliente = TestClient(app)
    base = f'/registros/{registro["registro_id"]}'
    for versao, acao, resposta, bloco in ((1, 'permanecer', 'Sim', 2), (2, 'proximo', 'Não', 3)):
        salvo = cliente.post(base + '/form1-integral/bloco-2/salvar', data={
            'conta_id': 'CONTA-A1', 'comando_id': f'POSICAO-FICTICIA-{versao}',
            'versao_lida': str(versao), 'acao_pos_salvar': acao, 'campo__2.12': resposta,
        }, follow_redirects=False)
        assert salvo.status_code == 303
        assert salvo.headers['location'].endswith(f'#titulo-bloco-{bloco}')
        pagina = cliente.get(salvo.headers['location'])
        recarga = cliente.get(salvo.headers['location'])
        assert f'<option value="{resposta}" selected>' in recarga.text
        assert 'posicao_form1.js' in pagina.text
        assert 'window.retomadaForm1.antesDeSalvar(formulario, acionador)' in pagina.text
        assert "window.addEventListener('pageshow', restaurarRegiao" in pagina.text
        assert 'saida_form1.js' in pagina.text
