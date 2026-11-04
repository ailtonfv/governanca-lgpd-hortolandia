"""Jornada coordenada reutiliza os comandos, sem modificar seu contrato."""
from copy import deepcopy
from pathlib import Path
import shutil
import subprocess

from fastapi.testclient import TestClient
from app.main import app
from app.modelos import RascunhoForm1Integral
from app.pre_validacao_form1_integral import pre_validar_form1_integral
from testes.test_destinatarios_10_2_1_form1_integral import _preparar, _adicionar

cliente = TestClient(app)


def test_javascript_jornada_e_html_sem_salvamento_preparatorio(sessao):
    r = _preparar(sessao, 'JORNADA-FICTICIA-HTML', ['Outra Secretaria'])
    html = cliente.get(f'/registros/{r["registro_id"]}?conta_id=CONTA-A1').text
    assert 'Salvar respostas do Bloco 10' not in html
    assert 'Salvar e incluir este destinatário' in html
    assert 'jornada_destinatarios_form1.js' in html
    assert 'Categoria deste destinatário' in html
    assert 'Categoria selecionada em 10.2' not in html
    assert 'data-destinatario-novo="true"' in html
    assert 'aria-describedby="destinatario-novo-orientacao-categoria"' in html
    assert html.index('titulo-destinatarios-10-2-1') < html.index('rotulo-integral-10.3')
    raiz = Path(__file__).resolve().parents[1]
    resultado = subprocess.run([shutil.which('node'), str(raiz/'testes/apoio_jornada_destinatarios.cjs')], cwd=raiz, capture_output=True, text=True)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr


def test_sequencia_http_duas_ocorrencias_edicao_remocao_e_outros_blocos(sessao):
    r = _preparar(sessao, 'JORNADA-FICTICIA-HTTP', ['Outra Secretaria'])
    rid = r['registro_id']
    base = f'/registros/{rid}/form1-integral/bloco-10'
    anteriores = deepcopy(sessao.get(RascunhoForm1Integral, rid).conteudo)

    def enviar(rota, versao, comando, **dados):
        resposta = cliente.post(base + rota, data={'conta_id':'CONTA-A1', 'comando_id':comando,
            'versao_lida':str(versao), **dados}, follow_redirects=False)
        assert resposta.status_code == 303 and 'erro=0' in resposta.headers['location']
        sessao.expire_all()
        return resposta

    enviar('/salvar',2,'JORNADA-FICTICIA-B10', **{'campo__10.1':'Sim','campo__10.2':'Outra Secretaria','campo__10.6':'Finalidade fictícia'})
    for versao, unidade in ((3,'UNID-SUL'),(4,'UNID-NORTE')):
        enviar('/destinatarios/adicionar',versao,f'JORNADA-FICTICIA-D{versao}', **{
            'destinatario__categoria':'Outra Secretaria','destinatario__modalidade':'identificado',
            'destinatario__unidade_id':unidade})
    conteudo = deepcopy(sessao.get(RascunhoForm1Integral,rid).conteudo)
    itens = conteudo['destinatarios_10_2_1']
    assert len(itens) == 2
    html = cliente.get(f'/registros/{rid}?conta_id=CONTA-A1').text
    assert 'value="UNID-SUL" selected' in html and 'value="UNID-NORTE" selected' in html
    enviar(f'/destinatarios/{itens[0]["id"]}/atualizar',5,'JORNADA-FICTICIA-EDITAR', **{
        'destinatario__categoria':'Outra Secretaria','destinatario__modalidade':'identificado',
        'destinatario__unidade_id':'UNID-SUL','destinatario__instrumento':'Norma fictícia revisada'})
    enviar(f'/destinatarios/{itens[1]["id"]}/remover',6,'JORNADA-FICTICIA-REMOVER')
    final = sessao.get(RascunhoForm1Integral,rid).conteudo
    assert len(final['destinatarios_10_2_1']) == 1
    assert len(final['destinatarios_10_2_1_inativos']) == 2
    assert final['respostas']['10.6'] == 'Finalidade fictícia'
    assert {k:v for k,v in final['respostas'].items() if not k.startswith('10.')} == {
        k:v for k,v in anteriores['respostas'].items() if not k.startswith('10.')}
    pre = pre_validar_form1_integral(conteudo,nome_institucional='Agente Fictício')
    detalhes = [i['detalhe'] for i in pre['incompletos'] if i['campo_id']=='10.2.1']
    assert any('instrumento' in d for d in detalhes)
    assert not any('cnpj' in d for d in detalhes)


def test_mudar_10_2_preserva_categoria_e_dados_da_ocorrencia_no_historico(sessao):
    r = _preparar(sessao, 'CATEGORIA-FICTICIA-HIST', ['Outra Secretaria', 'Outro órgão público'])
    assert _adicionar(sessao, r, 'CATEGORIA-FICTICIA-INCLUIR', 2)['permitido']
    sessao.commit()
    rid = r['registro_id']
    anterior = deepcopy(sessao.get(RascunhoForm1Integral, rid).conteudo['destinatarios_10_2_1'][0])
    resposta = cliente.post(f'/registros/{rid}/form1-integral/bloco-10/salvar', data={
        'conta_id':'CONTA-A1', 'comando_id':'CATEGORIA-FICTICIA-REVER', 'versao_lida':'3',
        'campo__10.1':'Sim', 'campo__10.2':'Outro órgão público',
    }, follow_redirects=False)
    assert resposta.status_code == 303 and 'erro=0' in resposta.headers['location']
    sessao.expire_all()
    conteudo = sessao.get(RascunhoForm1Integral, rid).conteudo
    assert not conteudo['destinatarios_10_2_1']
    historico = conteudo['destinatarios_10_2_1_inativos'][0]
    assert all(historico[k] == v for k, v in anterior.items())
    assert historico['motivo_desativacao']
    html = cliente.get(f'/registros/{rid}?conta_id=CONTA-A1').text
    assert 'Outra Secretaria' in html and 'Outro órgão público' in html
