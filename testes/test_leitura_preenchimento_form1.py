"""Consulta e preenchimento: destinos reais, ausência de escrita e permissões."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import shutil
import subprocess

from fastapi.testclient import TestClient
from app.main import app
from app.modelos import RascunhoForm1Integral
from app.rascunho_form1_integral import salvar_bloco_5_form1_integral, salvar_bloco_2_form1_integral
from testes.test_conferencia_interna_form1_integral_8ac import _preparar
from testes.test_p1_usabilidade_form1 import Elementos

cliente = TestClient(app)


def test_apa_consulta_campos_sem_controles_e_sem_modificar_rascunho(sessao):
    registro = _preparar(sessao, 'LEITURA-APA')
    rid = registro['registro_id']
    assert salvar_bloco_5_form1_integral(sessao, comando_id='LEITURA-B5', conta_id='CONTA-G1', registro_id=rid, versao_lida=1, respostas={'5.1': ['Nome', 'Outro']}, complemento_outro='Categoria fictícia complementar')['permitido']
    sessao.commit()
    original = deepcopy(sessao.get(RascunhoForm1Integral, rid).conteudo)
    pagina = cliente.get(f'/registros/{rid}?conta_id=CONTA-A1')
    assert pagina.status_code == 200
    html = pagina.text
    elementos = Elementos(html).elementos
    ids = [a['id'] for _, a, _ in elementos if a.get('id')]
    assert not [i for i, n in Counter(ids).items() if n > 1]
    assert 'consulta-integral-5.1' in ids and 'consulta-integral-2.4' in ids
    assert 'Somente leitura — modo de consulta' in html and 'Responsável pelo preenchimento: matrícula' in html
    assert 'Categoria fictícia complementar' in html and 'Nome' in html
    assert 'Consultar pergunta' in html
    assert not any(a.get('name') == 'campo__5.1' for _, a, _ in elementos)
    assert not any('formulario-integral' in a.get('class', '').split() for _, a, _ in elementos)
    assert any(a.get('id') == 'consulta-integral-5.1' and a.get('tabindex') == '-1' for _, a, _ in elementos)
    sessao.expire_all()
    assert sessao.get(RascunhoForm1Integral, rid).conteudo == original
    assert sessao.get(RascunhoForm1Integral, rid).versao_rascunho == 2
    recusado = salvar_bloco_5_form1_integral(sessao, comando_id='LEITURA-NEGADA', conta_id='CONTA-A1', registro_id=rid, versao_lida=2, respostas={'5.1': ['Nome']})
    assert not recusado['permitido']
    sessao.rollback()
    assert cliente.get(f'/registros/{rid}?conta_id=CONTA-C1').status_code == 403


def test_arp_mantem_campos_editaveis_sem_hachurado_e_destinos(sessao):
    registro = _preparar(sessao, 'LEITURA-ARP')
    html = cliente.get(f'/registros/{registro["registro_id"]}?conta_id=CONTA-G1').text
    elementos = Elementos(html).elementos
    for campo in ('5.1', '2.4'):
        controles = [(a, pais) for _, a, pais in elementos if a.get('name') == 'campo__' + campo]
        assert controles
        assert all(not any('area-somente-leitura' in p.get('class', '').split() for _, p in pais) for _, pais in controles)
        assert f'data-pendencia-campo="{campo}"' in html
    assert 'consulta-integral-5.1' not in html and 'Ir à pergunta' in html
    assert 'area-somente-leitura' in html and 'Somente leitura · controles de consulta disponíveis' in html
    assert 'conclusão institucional do FORM 1 ainda não está habilitada' in html


def test_consulta_distingue_condicional_inativa_e_nao_respondida(sessao):
    registro = _preparar(sessao, 'LEITURA-COND')
    rid = registro['registro_id']
    assert salvar_bloco_2_form1_integral(sessao, comando_id='LEITURA-COND-B2', conta_id='CONTA-G1', registro_id=rid, versao_lida=1, respostas={'2.12': 'Não', '2.3': 'Fluxo institucional fictício'})['permitido']
    sessao.commit()
    html = cliente.get(f'/registros/{rid}?conta_id=CONTA-A1').text
    assert 'Fluxo institucional fictício' in html
    trecho = html.split('id="consulta-integral-2.12.1"')[1].split('</section>')[0]
    assert 'Não aplicável às respostas salvas atuais' in trecho
    assert 'Ainda não respondido.' in html.split('id="consulta-integral-5.1"')[1].split('</section>')[0]
    assert 'consulta-integral-14.2.3' in html and 'consulta-integral-3.5.1' in html


def test_navegacao_real_javascript_consulta_edicao_fallback_e_foco():
    raiz = Path(__file__).resolve().parents[1]
    resultado = subprocess.run([shutil.which('node'), str(raiz / 'testes/apoio_leitura_preenchimento.cjs')], cwd=raiz, capture_output=True, text=True)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr


def test_consulta_preserva_ocorrencias_de_participantes_e_destinatarios(sessao):
    from app.atribuicao_form1_integral import atribuir_arp_form1_integral
    from app.rascunho_form1_integral import salvar_cabecalho_bloco_3_form1_integral, adicionar_participante_form1_integral
    from testes.test_destinatarios_10_2_1_form1_integral import _preparar as preparar_destinatarios, _adicionar
    registro = preparar_destinatarios(sessao, 'LEITURA-REP', ['Outra Secretaria'])
    rid = registro['registro_id']
    assert _adicionar(sessao, registro, 'LEITURA-DEST', 2)['permitido']
    sessao.commit()
    assert salvar_cabecalho_bloco_3_form1_integral(sessao, comando_id='LEITURA-CAB', conta_id='CONTA-A1', registro_id=rid, versao_lida=3, resposta_3_1='Sim')['permitido']
    sessao.commit()
    for indice in (1, 2):
        assert adicionar_participante_form1_integral(sessao, comando_id=f'LEITURA-P{indice}', conta_id='CONTA-A1', registro_id=rid, versao_lida=3+indice, respostas={'3.2': ['Outra Secretaria'], '3.3': f'Unidade fictícia {indice}', '3.5': 'Não'})['permitido']
        sessao.commit()
    assert atribuir_arp_form1_integral(sessao, comando_id='LEITURA-DESIG', conta_id='CONTA-A1', registro_id=rid, modo='outro', arp_pessoa_id='PESSOA-G', versao_lida=1)['permitido']
    sessao.commit()
    original = deepcopy(sessao.get(RascunhoForm1Integral, rid).conteudo)
    html = cliente.get(f'/registros/{rid}?conta_id=CONTA-A1').text
    for texto in ('Unidade fictícia 1', 'Unidade fictícia 2', 'Participante 2', 'Ato fictício 01', 'Destinatário 1'):
        assert texto in html
    elementos = Elementos(html).elementos
    assert not any('formulario-integral' in a.get('class', '').split() for _, a, _ in elementos)
    assert 'consulta-integral-3.3' in html and 'consulta-integral-10.2.1' in html
    sessao.expire_all()
    assert sessao.get(RascunhoForm1Integral, rid).conteudo == original
