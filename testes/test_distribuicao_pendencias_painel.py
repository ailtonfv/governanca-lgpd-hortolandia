"""Distribuição consultiva das contagens existentes; somente dados fictícios."""
from copy import deepcopy
from html import unescape
import re

import pytest
from fastapi.testclient import TestClient

from app import consultas_interface
from app.atribuicao_form1_integral import atribuir_arp_form1_integral
from app.main import app
from app.modelos import RascunhoForm1Integral
from testes.apoio import g1
from testes.test_conferencia_interna_form1_integral_8ac import _preparar, _solicitar
from testes.test_confirmacao_conferencia_form1_integral_8ag import _preparar_s2, _confirmar
from testes.test_p1_usabilidade_form1 import Elementos

cliente = TestClient(app)


def _distribuicao(html):
    return html.split('id="distribuicao-pendencias-painel"', 1)[1].split('</details>', 1)[0]


def test_varios_registros_somam_o_contador_sem_incluir_outro_arp(sessao):
    registro = _preparar(sessao, 'DIST-ATIVO')
    inicial = g1('DIST-INICIAL', 'OBJ-PRC-001', 'CTX-TRIB-02', titulo='Processo fictício inicial')
    outro = g1('DIST-OUTRO', 'OBJ-SRV-001', 'CTX-TRIB-03', titulo='Serviço fictício de outro ARP')
    for item, modo in ((inicial, 'outro'), (outro, 'proprio')):
        assert atribuir_arp_form1_integral(sessao, comando_id='DIST-ATR-'+item['registro_id'],
            conta_id='CONTA-A1', registro_id=item['registro_id'], modo=modo,
            arp_pessoa_id='PESSOA-G' if modo == 'outro' else None, versao_lida=0)['permitido']
        sessao.commit()
    projecao = consultas_interface.carregar_painel(sessao, 'CONTA-G1')
    anterior = deepcopy(sessao.get(RascunhoForm1Integral, registro['registro_id']).conteudo)

    pagina = cliente.get('/?conta_id=CONTA-G1')
    distribuicao = _distribuicao(pagina.text)

    assert pagina.status_code == 200
    ids = re.findall(r'data-registro-pendencias="([^"]+)"', distribuicao)
    assert set(ids) == {registro['registro_id'], inicial['registro_id']} and len(ids) == 2
    assert outro['codigo_lgpd'] not in distribuicao
    quantidades = list(map(int, re.findall(r'<p>(\d+) campo\(s\)', distribuicao)))
    assert sum(quantidades) == projecao['quantidade_campos_obrigatorios_pendentes']
    assert f'aria-label="{sum(quantidades)} campo(s) obrigatório(s) pendente(s)"' in pagina.text
    for resumo in projecao['registros']:
        if resumo['preenchimento_arp']:
            assert resumo['codigo_lgpd'] in distribuicao and resumo['titulo'] in distribuicao
    assert pagina.text.count('class="cartao-mapeamento"') == 3
    assert 'rascunho ainda não iniciado' in distribuicao
    assert f'href="#cartao-registro-{inicial["registro_id"]}"' in distribuicao
    assert f'id="cartao-registro-{inicial["registro_id"]}" tabindex="-1"' in pagina.text
    assert sessao.get(RascunhoForm1Integral, inicial['registro_id']) is None
    assert sessao.get(RascunhoForm1Integral, registro['registro_id']).conteudo == anterior


@pytest.mark.parametrize('conta', ['CONTA-A1', 'CONTA-B1', 'CONTA-C1'])
def test_apa_outro_arp_e_perfis_sem_preenchimento_nao_recebem_contagens(sessao, conta):
    registro = _preparar(sessao, 'DIST-PERMISSAO')

    pagina = cliente.get('/?conta_id='+conta)
    distribuicao = _distribuicao(pagina.text)

    assert pagina.status_code == 200
    assert 'data-registro-pendencias=' not in distribuicao
    assert 'Nenhum Registro com preenchimento autorizado' in distribuicao
    assert 'aria-label="0 campo(s) obrigatório(s) pendente(s)"' in pagina.text
    if conta == 'CONTA-C1':
        assert registro['codigo_lgpd'] not in pagina.text
    else:
        assert registro['codigo_lgpd'] in pagina.text  # consulta não autoriza preenchimento


def test_link_apos_confirmacao_abre_rascunho_correto_sem_perda(sessao):
    registro, _, _ = _preparar_s2(sessao, 'DIST-CONFIRMADO')
    assert _confirmar(sessao, registro, comando='DIST-CONF')['permitido']
    rid = registro['registro_id']
    anterior = deepcopy(sessao.get(RascunhoForm1Integral, rid).conteudo)

    pagina = cliente.get('/?conta_id=CONTA-G1')
    distribuicao = _distribuicao(pagina.text)
    destino = unescape(re.search(r'href="([^"]+)"', distribuicao)[1])
    detalhe = cliente.get(destino)

    assert f'/registros/{rid}?conta_id=CONTA-G1#titulo-bloco-' in destino
    assert detalhe.status_code == 200
    assert 'name="campo__5.1"' in detalhe.text
    assert f'id="{destino.split("#")[1]}"' in detalhe.text
    assert 'aria-label="0 providência(s) de conferência">0</span>' in pagina.text
    assert 'conclusão institucional do FORM 1 ainda não está habilitada' in detalhe.text
    assert sessao.get(RascunhoForm1Integral, rid).conteudo == anterior


def test_conferencia_pendente_nao_se_confunde_com_distribuicao(sessao):
    registro = _preparar(sessao, 'DIST-CONFERENCIA')
    assert _solicitar(sessao, registro, comando='DIST-SOL')['permitido']

    apa = cliente.get('/?conta_id=CONTA-A1')
    arp = cliente.get('/?conta_id=CONTA-G1')

    assert 'aria-label="1 providência(s) de conferência">1</span>' in apa.text
    assert 'data-registro-pendencias=' not in _distribuicao(apa.text)
    assert f'data-registro-pendencias="{registro["registro_id"]}"' in _distribuicao(arp.text)
    assert 'Não representa providências de conferência nem aprovação' in arp.text


def test_zero_e_acessibilidade_da_distribuicao(sessao, monkeypatch):
    registro = _preparar(sessao, 'DIST-ZERO')
    original = consultas_interface._pre_validar_rascunho_integral

    def sem_incompletos(*args, **kwargs):
        # Isola apresentação de zero; não altera o cálculo real nem a matriz.
        resultado = original(*args, **kwargs)
        resultado['incompletos'] = []
        resultado['quantidades']['incompletos'] = 0
        return resultado

    monkeypatch.setattr(consultas_interface, '_pre_validar_rascunho_integral', sem_incompletos)
    pagina = cliente.get('/?conta_id=CONTA-G1')
    distribuicao = _distribuicao(pagina.text)
    elementos = Elementos(pagina.text).elementos

    assert 'aria-label="0 campo(s) obrigatório(s) pendente(s)"' in pagina.text
    assert '<p>0 campo(s)' in distribuicao and registro['codigo_lgpd'] in distribuicao
    assert any(t == 'summary' and a.get('aria-describedby') == 'contador-campos-pendentes'
               for t, a, _ in elementos)
    assert any(t == 'details' and a.get('id') == 'distribuicao-pendencias-painel' and 'open' not in a
               for t, a, _ in elementos)
    ids = [a['id'] for _, a, _ in elementos if 'id' in a]
    assert len(ids) == len(set(ids))
    for _, atributos, _ in elementos:
        for referencia in atributos.get('aria-describedby', '').split():
            assert referencia in ids
    css = cliente.get('/estaticos/estilo.css').text
    assert '.distribuicao-pendencias-painel > summary:focus-visible' in css
    assert '.distribuicao-pendencias-lista > li { display: flex; flex-wrap: wrap;' in css
    assert 'min-width: 0; overflow-wrap: anywhere;' in css
