"""Pacote P1: apresentação acessível e orientação sem novas regras institucionais."""
from collections import Counter
from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path
import shutil
import subprocess

from fastapi.testclient import TestClient
from app.main import app
from app.modelos import RascunhoForm1Integral, VersaoForm1Integral
from app.pre_validacao_form1_integral import pre_validar_form1_integral, perguntas_para_localizacao
from app.rascunho_form1_integral import salvar_bloco_2_form1_integral
from testes.test_bloco5_form1_integral import _rascunho_pronto
from testes.test_conferencia_interna_form1_integral_8ac import _preparar, _solicitar
from testes.test_devolucao_reapresentacao_form1_integral_8af import _devolver
from testes.test_destinatarios_10_2_1_form1_integral import _preparar as preparar_destinatarios, _adicionar

cliente = TestClient(app)

class Elementos(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.elementos = []
        self.pais = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elementos.append((tag, attrs, tuple(self.pais)))
        if tag not in {'input', 'br', 'hr', 'meta', 'link', 'img'}:
            self.pais.append((tag, attrs))

    def handle_endtag(self, tag):
        for i in range(len(self.pais)-1, -1, -1):
            if self.pais[i][0] == tag:
                del self.pais[i:]
                break


def test_controles_e_grupos_possuem_nome_acessivel_e_referencias_validas(sessao):
    # Arrange: dois destinatários e uma nova ocorrência na mesma página.
    registro = preparar_destinatarios(sessao, 'P1-A11Y', ['Outra Secretaria'])
    assert _adicionar(sessao, registro, 'P1-A11Y-D1', 2)['permitido']
    sessao.commit()
    assert _adicionar(sessao, registro, 'P1-A11Y-D2', 3, unidade_id='UNID-NORTE')['permitido']
    sessao.commit()
    # Act
    html = cliente.get(f'/registros/{registro["registro_id"]}?conta_id=CONTA-A1').text
    elementos = Elementos(html).elementos
    ids = [a['id'] for _, a, _ in elementos if a.get('id')]
    # Assert: todos os IDs e referências de acessibilidade são únicos/resolvidos.
    assert not [i for i, n in Counter(ids).items() if n > 1]
    controles = []
    for tag, attrs, pais in elementos:
        for atributo in ('aria-labelledby', 'aria-describedby'):
            assert all(i in ids for i in attrs.get(atributo, '').split()), attrs
        integral = any('formulario-integral' in a.get('class', '').split() for _, a in pais)
        if integral and tag in {'input', 'select', 'textarea'} and attrs.get('type') != 'hidden':
            controles.append(attrs)
            associado = any(t == 'label' for t, _ in pais) or attrs.get('aria-labelledby') or attrs.get('aria-label')
            associado = associado or any(t == 'label' and a.get('for') == attrs.get('id') for t, a, _ in elementos if a.get('for'))
            assert associado, attrs
    assert len(controles) > 100
    for campo in ['2.3', '2.12.1', '2.12.2']:
        controle = next(a for a in controles if a.get('name') == 'campo__' + campo)
        assert controle['aria-labelledby'] == 'rotulo-integral-' + campo
    repetidos = [a['id'] for a in controles if a.get('name') == 'destinatario__identificacao']
    assert len(repetidos) == len(set(repetidos)) == 3
    css = cliente.get('/estaticos/estilo.css').text
    assert '.form1-integral .formulario-integral input:not([type])' in css
    assert 'box-sizing: border-box; width: 100%; max-width: 100%; min-width: 0;' in css


def test_facultativos_a_confirmar_geram_avisos_sem_aumentar_obrigatorios():
    conteudo = {'respostas': {'2.12': 'A confirmar', '8.4': ['A confirmar'], '5.1': ['A confirmar'], '2.12.1': 'referência fictícia'}}
    original = deepcopy(conteudo)
    base = pre_validar_form1_integral({'respostas': {'5.1': ['A confirmar']}}, nome_institucional='Agente fictício')
    resultado = pre_validar_form1_integral(conteudo, nome_institucional='Agente fictício')
    assert {i['campo_id'] for i in resultado['avisos']} == {'2.12', '8.4'}
    assert resultado['quantidades']['incompletos'] == base['quantidades']['incompletos']
    assert '5.1' in {i['campo_id'] for i in resultado['incompletos']}
    assert '2.12.1' in {i['campo_id'] for i in resultado['nao_aplicaveis']}
    assert resultado['submissao_habilitada'] is False and resultado['consultiva']
    assert conteudo == original


def test_respostas_conclusivas_ou_vazias_nao_geram_aviso_facultativo():
    resultado = pre_validar_form1_integral({'respostas': {'2.12': 'Não', '8.4': [], '13.4': 'Não se aplica'}}, nome_institucional='Agente fictício')
    assert resultado['avisos'] == [] and resultado['quantidades']['avisos'] == 0


def test_avisos_sao_apresentados_separadamente_e_nao_impedem_salvar(sessao):
    registro = _rascunho_pronto(sessao, 'P1-AVISOS')
    salvo = salvar_bloco_2_form1_integral(sessao, comando_id='P1-AVISO-SALVAR', conta_id='CONTA-A1', registro_id=registro['registro_id'], versao_lida=1, respostas={'2.12': 'A confirmar'})
    sessao.commit()
    pagina = cliente.get(f'/registros/{registro["registro_id"]}?conta_id=CONTA-A1')
    assert salvo['permitido'] and pagina.status_code == 200
    assert '1 aviso(s) informativo(s)' in pagina.text
    assert 'não entram no contador de obrigatórios incompletos' in pagina.text
    assert 'data-pendencia-campo="2.12"' in pagina.text
    assert 'Sem alterações para salvar.' in pagina.text
    assert 'Rascunho confirmado no servidor.' not in pagina.text
    assert 'Suas respostas são salvas no rascunho deste Registro LGPD. Você poderá continuar depois. Salvar não conclui nem submete o FORM 1.' in pagina.text


def test_devolucao_localiza_catalogo_preservando_justificativa_snapshot_e_permissoes(sessao):
    registro = _preparar(sessao, 'P1-LOCALIZAR')
    s1 = _solicitar(sessao, registro, comando='P1-LOCALIZAR-S1')
    justificativa = 'Rever a pergunta 2.4 no fluxo fictício; manter o levantamento anterior.'
    assert _devolver(sessao, registro, comando='P1-LOCALIZAR-DEV', justificativa=justificativa)['permitido']
    snapshot = deepcopy(sessao.get(VersaoForm1Integral, s1['snapshot_id']).conteudo)
    rascunho = deepcopy(sessao.get(RascunhoForm1Integral, registro['registro_id']).conteudo)
    arp = cliente.get(f'/registros/{registro["registro_id"]}?conta_id=CONTA-G1')
    apa = cliente.get(f'/registros/{registro["registro_id"]}?conta_id=CONTA-A1')
    assert justificativa in arp.text
    assert 'id="localizar-pergunta-devolucao"' in arp.text
    assert 'data-localizar-id="2.4"' in arp.text and 'data-localizar-id="14.2.3"' in arp.text
    assert 'Não identifica automaticamente uma pergunta' in arp.text
    assert 'id="localizar-pergunta-devolucao"' not in apa.text
    assert sessao.get(VersaoForm1Integral, s1['snapshot_id']).conteudo == snapshot
    assert sessao.get(RascunhoForm1Integral, registro['registro_id']).conteudo == rascunho
    destinos = perguntas_para_localizacao()
    assert len(destinos) == 125
    assert {d['etapa'] for d in destinos} == {1, 2, 3, 4}
    assert next(d for d in destinos if d['campo_id'] == '3.2')['destino_tipo'] == 'secao'


def test_busca_e_feedback_executados_em_javascript_sem_inspecao_visual():
    raiz = Path(__file__).resolve().parents[1]
    node = shutil.which('node')
    assert node, 'Node necessário para executar os testes de comportamento da interface.'
    resultado = subprocess.run([node, str(raiz / 'testes/apoio_p1_usabilidade.cjs')], cwd=raiz, capture_output=True, text=True)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
