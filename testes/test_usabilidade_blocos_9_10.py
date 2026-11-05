"""Ordenação e rótulos de apresentação sem alterar valores canônicos."""
from copy import deepcopy
from pathlib import Path
import json
import re
import shutil
import subprocess

from fastapi.testclient import TestClient
from app.main import app
from app.modelos import RascunhoForm1Integral
from app.form1_integral import campos_por_id
from testes.test_p1_usabilidade_form1 import Elementos
from testes.test_destinatarios_10_2_1_form1_integral import _preparar, _adicionar

cliente = TestClient(app)


def test_cadastro_na_sequencia_sem_forms_aninhados_e_controles_associados(sessao):
    r = _preparar(sessao, 'UX910-ORDEM', ['Outra Secretaria'])
    html = cliente.get(f'/registros/{r["registro_id"]}?conta_id=CONTA-A1').text
    assert html.index('id="rotulo-integral-10.2.1"') < html.index('id="titulo-destinatarios-10-2-1"') < html.index('id="rotulo-integral-10.3"')
    assert html.count('id="titulo-destinatarios-10-2-1"') == 1
    assert 'id="instrucao-integral-10.2.1"' not in html
    elementos = Elementos(html).elementos
    ordem_esperada = ['10.1', '10.2', '10.2.1', '10.3', '10.4', '10.5',
                      '10.6', '10.7', '10.7.1', '10.8', '10.8.1', '10.9']
    assert re.findall(r'id="rotulo-integral-(10\.[\d.]+)"', html) == ordem_esperada
    for _, attrs, pais in elementos:
        if attrs.get('id') in ('rotulo-integral-10.2', 'rotulo-integral-10.2.1'):
            recipiente = next(a for _, a in reversed(pais) if 'data-condicoes' in a)
            assert json.loads(recipiente['data-condicoes']) == [['10.1', ['Sim', 'Em alguns casos']]]
    consulta = cliente.get(f'/registros/{r["registro_id"]}?conta_id=CONTA-B1')
    assert consulta.status_code == 200
    assert re.findall(r'id="rotulo-consulta-(10\.[\d.]+)"', consulta.text) == ordem_esperada
    for tag, attrs, pais in elementos:
        if tag == 'form':
            assert not any(t == 'form' for t, _ in pais), attrs
        if attrs.get('name', '').startswith(('campo__10.', 'complemento_outro__10.')):
            dono = attrs.get('form') or next((a.get('id') for t, a in reversed(pais) if t == 'form'), None)
            assert dono == 'formulario-bloco-10', attrs
        if attrs.get('name', '').startswith('destinatario__'):
            assert 'form' not in attrs
            dono = next(a for t, a in reversed(pais) if t == 'form')
            assert '/destinatarios' in dono['action']
    assert "campoId === '10.2.1'" in html
    assert 'formulario_associado_form1.js' in html


def test_duas_unidades_recuperadas_e_preservadas_ao_salvar_bloco_e_avancar(sessao):
    r = _preparar(sessao, 'UX910-DUAS', ['Outra Secretaria'])
    for versao, unidade in ((2, 'UNID-SUL'), (3, 'UNID-NORTE')):
        assert _adicionar(sessao, r, f'UX910-D-{versao}', versao, unidade_id=unidade)['permitido']
        sessao.commit()
    rid = r['registro_id']
    anteriores = deepcopy(sessao.get(RascunhoForm1Integral, rid).conteudo['destinatarios_10_2_1'])
    pagina = cliente.get(f'/registros/{rid}?conta_id=CONTA-A1')
    for unidade in ('UNID-SUL', 'UNID-NORTE'):
        assert f'value="{unidade}" selected' in pagina.text
    resposta = cliente.post(f'/registros/{rid}/form1-integral/bloco-10/salvar', data={
        'conta_id': 'CONTA-A1', 'comando_id': 'UX910-AVANCAR', 'versao_lida': '4',
        'acao_pos_salvar': 'proximo', 'campo__10.1': 'Sim', 'campo__10.2': ['Outra Secretaria'],
        'campo__10.3': ['Sistema'], 'campo__10.4': ['Nome'], 'campo__10.6': 'Finalidade institucional fictícia',
        'campo__10.9': 'Titular',
    }, follow_redirects=False)
    assert resposta.headers['location'].endswith('#titulo-bloco-11')
    recarga = cliente.get(resposta.headers['location'])
    assert 'Finalidade institucional fictícia' in recarga.text
    sessao.expire_all()
    atual = sessao.get(RascunhoForm1Integral, rid).conteudo
    assert atual['destinatarios_10_2_1'] == anteriores
    assert atual['respostas']['10.4'] == ['Nome']


def test_rotulos_novos_preservam_valores_antigos_e_consulta(sessao):
    r = _preparar(sessao, 'UX910-ROTULO', ['Outra Secretaria'])
    alternativas = campos_por_id()['9.1'].alternativas[:3]
    resultado = cliente.post(f'/registros/{r["registro_id"]}/form1-integral/bloco-9/salvar', data={
        'conta_id':'CONTA-A1', 'comando_id':'UX910-B9', 'versao_lida':'2',
        'campo__9.1':list(alternativas), 'campo__9.2':'Sim',
    })
    assert resultado.status_code == 200
    for valor in alternativas:
        assert f'value="{valor}" checked' in resultado.text
        assert valor.replace('AGENTE PÚBLICO AUTORIZADO', 'Servidor com acesso autorizado') in resultado.text
    assert '10.1 — Neste serviço, processo ou atividade, os dados pessoais são enviados ou disponibilizados' in resultado.text
    assert 'não atribui o papel institucional de APA' in resultado.text
    sessao.expire_all()
    assert sessao.get(RascunhoForm1Integral,r['registro_id']).conteudo['respostas']['9.1'] == list(alternativas)
    consulta = cliente.get(f'/registros/{r["registro_id"]}?conta_id=CONTA-B1').text
    assert 'Servidor com acesso autorizado da unidade responsável' in consulta


def test_complementares_nao_viram_obrigatorios_nem_sao_removidos(sessao):
    r = _preparar(sessao, 'UX910-COMPL', ['Outra Secretaria', 'Empresa contratada', 'Outro órgão público'])
    assert _adicionar(sessao,r,'UX910-COMP-D',2, identificacao='Identificação fictícia preservada')['permitido']
    sessao.commit()
    html = cliente.get(f'/registros/{r["registro_id"]}?conta_id=CONTA-A1').text
    assert 'CNPJ não é exigido para essa categoria' in html
    assert 'value="Identificação fictícia preservada"' in html
    for tag, attrs, _ in Elementos(html).elementos:
        if attrs.get('name', '').startswith('destinatario__') and attrs['name'] not in ('destinatario__categoria','destinatario__modalidade'):
            assert 'required' not in attrs and 'disabled' not in attrs
    raiz=Path(__file__).resolve().parents[1]
    processo=subprocess.run([shutil.which('node'),str(raiz/'testes/apoio_formulario_associado.cjs')],cwd=raiz,capture_output=True,text=True)
    assert processo.returncode == 0, processo.stdout + processo.stderr
