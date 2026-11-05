"""Pendências na sequência canônica, sem modificar respostas ou ocorrências."""

from copy import deepcopy
import re

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modelos import RascunhoForm1Integral
from app.pre_validacao_form1_integral import pre_validar_form1_integral
from testes.test_destinatarios_10_2_1_form1_integral import _preparar


def _validar(conteudo):
    anterior = deepcopy(conteudo)
    resultado = pre_validar_form1_integral(conteudo, nome_institucional="Agente fictício")
    assert conteudo == anterior
    assert resultado['consultiva'] and not resultado['submissao_habilitada']
    assert resultado['quantidades']['incompletos'] == len(resultado['incompletos'])
    return resultado


@pytest.mark.parametrize('respostas,primeiro,seguinte', [
    ({'2.5': ['Outro']}, '2.5', '2.11'),
    ({'4.2': 'Sim', '4.2.1': ['Outro']}, '4.2.1', '4.2.5'),
    ({'8.4': 'Sim', '8.4.1': ['Outro']}, '8.4.1', '8.4.3'),
    ({'10.1': 'Sim', '10.3': ['Outro']}, '10.3', '10.8'),
    ({'12.1': 'Sim', '12.1.2': ['Outro']}, '12.1.2', '12.2'),
    ({'14.2': 'Sim', '14.2.1': ['Outro']}, '14.2.1', '14.2.3'),
])
def test_complemento_aparece_antes_da_pergunta_posterior(respostas, primeiro, seguinte):
    resultado = _validar({'respostas': respostas})

    ids = [i['campo_id'] for i in resultado['incompletos']]
    grupo = next(g for g in resultado['por_bloco'] if g['bloco'] == primeiro.split('.')[0])
    ids_bloco = [i['campo_id'] for i in grupo['itens']]
    assert ids.index(primeiro) < ids.index(seguinte)
    assert ids_bloco.index(primeiro) < ids_bloco.index(seguinte)
    assert any(i['campo_id'] == primeiro and 'complemento descritivo' in i['detalhe']
               for i in grupo['itens'])


def test_complementos_de_participantes_preservam_identificacao_individual():
    conteudo = {'respostas': {'3.1': 'Sim'}, 'participantes': [
        {'id': 'PART-FICT-1', 'respostas': {'3.2': ['Outro'], '3.5': 'Sim'}},
        {'id': 'PART-FICT-2', 'respostas': {'3.2': ['Outro'], '3.5': 'Sim'}},
    ]}

    resultado = _validar(conteudo)

    itens = next(g['itens'] for g in resultado['por_bloco'] if g['bloco'] == '3')
    assert [i['campo_id'] for i in itens] == [
        '3.2', '3.2', '3.3', '3.3', '3.4', '3.4', '3.4.1', '3.4.1', '3.5.1', '3.5.1']
    for campo in ('3.2', '3.3', '3.4', '3.4.1', '3.5.1'):
        ocorrencias = [i for i in itens if i['campo_id'] == campo]
        assert [i['ocorrencia'] for i in ocorrencias] == [1, 2]
        assert all(f"participante {i['ocorrencia']}" in i['detalhe'] for i in ocorrencias)


def test_destinatarios_precedem_10_3_preservando_ocorrencias_e_detalhes():
    conteudo = {'respostas': {'10.1': 'Sim', '10.2': ['Outra Secretaria']},
                'destinatarios_10_2_1': [
                    {'id': 'DEST-FICT-1', 'categoria': 'Outra Secretaria', 'modalidade': 'identificado'},
                    {'id': 'DEST-FICT-2', 'categoria': 'Outra Secretaria', 'modalidade': 'identificado'},
                ]}

    resultado = _validar(conteudo)

    itens = next(g['itens'] for g in resultado['por_bloco'] if g['bloco'] == '10')
    assert [i['campo_id'] for i in itens[:5]] == ['10.2.1'] * 4 + ['10.3']
    assert '10.2' not in [i['campo_id'] for i in itens]
    assert [(i['ocorrencia'], i['categoria_destinatario']) for i in itens[:4]] == [
        ('DEST-FICT-1', 'Outra Secretaria'), ('DEST-FICT-1', 'Outra Secretaria'),
        ('DEST-FICT-2', 'Outra Secretaria'), ('DEST-FICT-2', 'Outra Secretaria')]
    assert [i['detalhe'].split(': falta ')[1] for i in itens[:4]] == [
        'unidade id', 'instrumento', 'unidade id', 'instrumento']


@pytest.mark.parametrize('categoria,esperado', [
    ('Outra Secretaria', ['10.2.1', '10.3', '10.4', '10.5', '10.6', '10.7', '10.8']),
    ('Outro', ['10.2', '10.2.1', '10.3', '10.4', '10.5', '10.6', '10.7', '10.8']),
])
def test_html_pendencias_ordena_10_2_1_sem_alterar_rascunho(sessao, categoria, esperado):
    registro = _preparar(sessao, 'ORDEM-FICT-10', [categoria])
    rascunho = sessao.get(RascunhoForm1Integral, registro['registro_id'])
    anterior = deepcopy(rascunho.conteudo)
    versao = rascunho.versao_rascunho

    pagina = TestClient(app).get(f"/registros/{registro['registro_id']}?conta_id=CONTA-A1")

    assert pagina.status_code == 200
    secao = pagina.text.split('id="titulo-pre-validacao-form1"', 1)[1].split('</section>', 1)[0]
    assert re.findall(r'data-pendencia-campo="(10\.[\d.]+)"', secao) == esperado
    sessao.refresh(rascunho)
    assert rascunho.conteudo == anterior and rascunho.versao_rascunho == versao
