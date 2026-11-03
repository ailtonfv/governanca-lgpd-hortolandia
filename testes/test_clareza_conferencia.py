"""Clareza da conferência: apresentação não modifica governança (AAA)."""
from pathlib import Path
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

from app.consultas_interface import carregar_painel
from app.main import app
from testes.test_conferencia_interna_form1_integral_8ac import _preparar, _solicitar
from testes.test_devolucao_reapresentacao_form1_integral_8af import _devolver, _salvar_ajuste
from testes.test_confirmacao_conferencia_form1_integral_8ag import _confirmar


@pytest.mark.parametrize('mesma_pessoa', [False, True])
def test_fluxo_mostra_estado_versao_e_papel_sem_criar_providencia(sessao, mesma_pessoa):
    # Arrange: a mesma pessoa também exige os dois atos explícitos.
    conta = 'CONTA-A1' if mesma_pessoa else 'CONTA-G1'
    pessoa = 'PESSOA-A' if mesma_pessoa else 'PESSOA-G'
    registro = _preparar(sessao, 'CLAREZA-CICLO', arp=pessoa, conta_arp=conta)

    def fluxo():
        painel = carregar_painel(sessao, conta)
        return next(r['fluxo_conferencia'] for r in painel['registros'] if r['id'] == registro['registro_id'])

    assert fluxo()['atual'] == 'preencher'
    assert fluxo()['versao'] is None
    assert '(ARP)' in fluxo()['responsavel']

    # Act / Assert: somente o estado persistido muda o destaque.
    assert _solicitar(sessao, registro, comando='CLAREZA-S1', conta=conta)['permitido']
    assert fluxo()['atual'] == 'conferir'
    assert fluxo()['versao'] == 1
    assert '(APA)' in fluxo()['responsavel']
    assert _devolver(sessao, registro, comando='CLAREZA-DEV')['permitido']
    assert fluxo()['atual'] == 'devolver'
    assert '(ARP)' in fluxo()['responsavel']
    assert '(APA)' in fluxo()['decidida_por']
    ajuste = _salvar_ajuste(sessao, registro, comando='CLAREZA-AJUSTE', conta=conta)
    assert fluxo()['versao'] == 1  # salvar não reapresenta nem confirma
    assert fluxo()['versao_atual'] == ajuste['versao_rascunho']
    assert _solicitar(sessao, registro, comando='CLAREZA-S2', conta=conta, versao=ajuste['versao_rascunho'])['permitido']
    assert fluxo()['atual'] == 'conferir'
    assert _confirmar(sessao, registro, comando='CLAREZA-CONF')['permitido']
    assert fluxo()['atual'] == 'confirmar'
    assert fluxo()['versao'] == ajuste['versao_rascunho']
    assert fluxo()['decidida_em'] is not None
    assert fluxo()['responsavel'] == 'Sem providência de conferência pendente'
    for ator in ('CONTA-A1', conta):
        painel = carregar_painel(sessao, ator)
        cartao = next(r for r in painel['registros'] if r['id'] == registro['registro_id'])
        assert cartao['providencias'] == []


def test_decisoes_distintas_com_ciencia_dialogo_e_autorizacao_preservada(sessao):
    # Arrange
    registro = _preparar(sessao, 'CLAREZA-HTML')
    _solicitar(sessao, registro, comando='CLAREZA-HTML-S1')
    cliente = TestClient(app)
    base = f'/registros/{registro["registro_id"]}'
    consulta = base + '/form1-integral/conferencia-interna'

    # Act
    pagina = cliente.get(consulta + '?conta_id=CONTA-A1')
    painel = cliente.get('/?conta_id=CONTA-A1')

    # Assert: mesmos destinos e parâmetros, ciência somente na interação.
    assert pagina.status_code == 200
    html = pagina.text
    assert 'Opção A — Confirmar conferência interna' in html
    assert 'Opção B — Devolver para ajustes' in html
    assert 'id="ciencia-confirmacao" required' in html
    assert 'name="ciencia-confirmacao"' not in html
    assert 'Confirmar a conferência da versão 1?' in html
    assert 'data-cancelar-confirmacao autofocus' in html
    assert 'name="justificativa" maxlength="2000" required' in html
    assert 'decisao_conferencia.js' in html
    assert consulta + '/confirmar' in html and consulta + '/devolver' in html
    assert 'Conferir não exige que todos os campos obrigatórios estejam preenchidos.' in html
    assert 'aria-current="step"><strong>APA confere' in painel.text
    assert '#historico-conferencias-form1' in painel.text
    for ator in ('CONTA-G1', 'CONTA-B1'):
        assert cliente.get(consulta + '?conta_id=' + ator).status_code == 403
    detalhe = cliente.get(base + '?conta_id=CONTA-A1#historico-conferencias-form1')
    assert 'id="historico-conferencias-form1"' in detalhe.text
    assert 'destinoInicial.open = true' in detalhe.text
    assert _confirmar(sessao, registro, comando='CLAREZA-HTML-CONF')['permitido']
    confirmada = cliente.get(consulta + '?conta_id=CONTA-G1')
    assert confirmada.status_code == 200
    assert 'Decisão registrada por:' in confirmada.text
    assert 'Sem providência de conferência pendente' in confirmada.text
    assert 'form-confirmar-conferencia' not in confirmada.text
    assert 'form1-integral/submeter' not in confirmada.text


def test_dialogo_exige_decisao_explicita_e_cancelamento_nao_envia():
    node = shutil.which('node')
    if not node:
        pytest.skip('Ensaio de interação requer Node; não é aceite visual.')
    raiz = Path(__file__).resolve().parents[1]
    resultado = subprocess.run([node, str(raiz / 'testes/apoio_decisao_conferencia.cjs')], cwd=raiz, capture_output=True, text=True)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
