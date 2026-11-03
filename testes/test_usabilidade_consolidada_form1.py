"""Correção consolidada: projeção de ajuda e jornada com JavaScript executado."""

from dataclasses import replace
from pathlib import Path
import shutil
import subprocess

import pytest

from fastapi.testclient import TestClient

from app.consultas_interface import instrucao_para_interface
from app.form1_integral import campos_por_id
from app.main import app
from testes.test_bloco5_form1_integral import _rascunho_pronto


def test_instrucoes_repetidas_sao_omitidas_sem_alterar_catalogo():
    # Arrange
    campos = campos_por_id()
    # Act / Assert: também cobre controles múltiplos e participantes.
    for identificador in ['2.1', '2.12', '2.13', '2.5', '3.2', '1.4']:
        campo = campos[identificador]
        original = campo.instrucao
        assert instrucao_para_interface(campo) == ''
        assert campo.instrucao == original
    for identificador in ['2.6', '2.8', '2.12.2', '1.1.1']:
        assert instrucao_para_interface(campos[identificador]) == campos[identificador].instrucao
    campo = campos['2.12']
    com_orientacao = replace(campo, instrucao=campo.instrucao + ' Não informe dados individuais.')
    assert instrucao_para_interface(com_orientacao) == com_orientacao.instrucao


def test_html_preserva_opcoes_e_reduz_rodape_sem_falsos_controles(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, 'UX-CONSOLIDADA-FICTICIA')
    # Act
    pagina = TestClient(app).get(f'/registros/{registro["registro_id"]}?conta_id=CONTA-A1')
    # Assert
    assert pagina.status_code == 200
    assert '○ Sim' not in pagina.text
    assert '☐ Termo em papel' not in pagina.text
    assert 'name="campo__2.12"' in pagina.text
    assert 'name="campo__2.13"' in pagina.text
    assert 'value="Em alguns casos"' in pagina.text
    assert 'Não informe protocolo, número de atendimento' in pagina.text
    assert 'value="permanecer" aria-label="Salvar rascunho do FORM 1 e permanecer neste bloco">Salvar rascunho</button>' in pagina.text
    assert 'Próximo: Bloco 3' in pagina.text
    assert 'Conferência interna pelo APA' in pagina.text
    assert 'Pendências antes da futura submissão' in pagina.text
    salvo = TestClient(app).post(
        f'/registros/{registro["registro_id"]}/form1-integral/bloco-2/salvar',
        data={
            'conta_id': 'CONTA-A1', 'comando_id': 'UX-SALVAR-FICTICIO',
            'versao_lida': '1', 'acao_pos_salvar': 'permanecer',
            'campo__2.12': 'Sim', 'campo__2.13': 'Em alguns casos',
        }, follow_redirects=False,
    )
    assert salvo.status_code == 303
    assert salvo.headers['location'].endswith('#titulo-bloco-2')
    retomada = TestClient(app).get(salvo.headers['location'])
    assert '<option value="Em alguns casos" selected>' in retomada.text
    assert 'data-depende-de="campo__2.12" data-valores="Sim"' in retomada.text
    assert 'data-depende-de="campo__2.13" data-valores="Sim||Em alguns casos"' in retomada.text


def test_javascript_navega_com_sessao_antiga_e_storage_indisponivel():
    # Arrange
    raiz = Path(__file__).resolve().parents[1]
    node = shutil.which('node')
    if not node:
        pytest.skip('Ensaio JavaScript requer Node disponível; aceitação visual continua separada.')
    # Act
    resultado = subprocess.run([node, str(raiz / 'testes/apoio_navegacao_form1.cjs')], cwd=raiz, capture_output=True, text=True)
    # Assert
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
