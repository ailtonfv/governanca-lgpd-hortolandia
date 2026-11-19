"""Vistoria 12-C: apresentação, sem novos atos de negócio."""
from pathlib import Path
from types import SimpleNamespace
import os,re
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.apresentacao_forms34 import descricao_nota34, PROBABILIDADE, IMPACTO
from app.apresentacao_situacoes_form2 import situacao_origem,situacoes_complementacao
from app.documentos_interface import blocos_documento
from testes.test_lote12 import protecoes, entrada, fonte, entrar, ato, estado
from testes.test_lote12_ajustes import propor


def evidencia(nome,html):
    destino=os.environ.get('LGPD_EVIDENCIAS_12C')
    if destino:
        p=Path(destino);p.mkdir(parents=True,exist_ok=True)
        raiz=Path(__file__).resolve().parent.parent/'app/estaticos'
        def css(m):
            f=raiz/m[1].split('?')[0]
            return '<style>'+f.read_text(encoding='utf8')+'</style>' if f.is_file() else ''
        def js(m):
            f=raiz/m[1].split('?')[0]
            return '<script>'+f.read_text(encoding='utf8')+'</script>' if f.is_file() else ''
        html=re.sub(r'<link[^>]*href="(?:http://testserver)?/estaticos/([^"]+)"[^>]*>',css,html)
        html=re.sub(r'<script[^>]*src="(?:http://testserver)?/estaticos/([^"]+)"[^>]*></script>',js,html)
        html=re.sub(r'<img[^>]+>','',html)
        (p/(nome+'.html')).write_text(html,encoding='utf8')


@pytest.mark.parametrize('eixo,textos',[('probabilidade',PROBABILIDADE),('impacto',IMPACTO)])
def test_significados_iguais_as_listas(eixo,textos):
    for n in range(1,6):assert descricao_nota34(n,eixo)==f'{n} — {textos[n-1]}'
    assert descricao_nota34(None,eixo)=='Ainda não avaliado'


def test_painel_leitura_definicao_e_eixos(sessao,entrada):
    obj=entrar(sessao,entrada);c=TestClient(app)
    inicial=c.get(f'/forms34/{obj}/blocos/14?conta_id=CONTA-B1');assert inicial.status_code==200
    evidencia('form3_edicao',inicial.text)
    propor(sessao,obj);antes=estado(sessao,obj)
    r=c.get(f'/forms34/{obj}/blocos/14?conta_id=CONTA-B1')
    assert r.status_code==200
    assert 'Probabilidade: 5 — Muito alta: esperado ou recorrente' in r.text
    assert 'Impacto: 5 — Muito alto: consequência grave ou irreversível' in r.text
    assert 'Mede só o dano à pessoa' in r.text and 'Como avaliar' in r.text
    assert 'P / I' not in r.text and 'eixo-vertical34">Probabilidade' in r.text
    assert len(re.findall('class="nome-faixa34"',r.text))==25
    assert estado(sessao,obj)==antes
    evidencia('form3_leitura',r.text)
    evidencia('riscos_lista',c.get('/forms34?conta_id=CONTA-B1').text)


def test_proposta_somente_leitura_e_acesso(sessao,entrada):
    obj=entrar(sessao,entrada);c=TestClient(app);url=f'/forms34/{obj}/proposta-impacto?conta_id=CONTA-B1'
    r=c.get(url);assert r.status_code==200
    assert '<table>' in r.text and 'Deliberações pendentes' in r.text
    assert 'Em deliberação' in r.text and '<form' not in r.text
    assert c.post(url).status_code==405
    assert c.get(url.replace('CONTA-B1','CONTA-A1')).status_code==403
    evidencia('proposta_impacto',r.text)


@pytest.mark.parametrize('tres,quatro,frase',[(True,False,'avaliar os riscos'),(False,True,'providência direta'),(True,True,'avaliar os riscos e providência direta')])
def test_destinos_texto_e_indicacao(sessao,entrada,tres,quatro,frase):
    from copy import deepcopy
    d=deepcopy(entrada.conteudo);d['rascunho_form2_rev21_2']['14'].update({'opcao:F2-14.5':['SIM' if tres else 'NAO'],'opcao:F2-14.6':['SIM' if quatro else 'NAO']});entrada.conteudo=d;sessao.commit()
    c=TestClient(app);r=c.get(f'/form2/participacoes/{entrada.id}/encaminhar34?conta_id=CONTA-B1');assert r.status_code==200
    assert f'Você indicou no bloco 14: {frase}.' in r.text
    assert 'title="F2-14.5"' in r.text and 'title="F2-14.6"' in r.text
    assert '>Avaliar os riscos (FORM 3)</option>' in r.text
    assert '>Providência direta, sem avaliação de risco (FORM 4)</option>' in r.text
    evidencia('encaminhamento',r.text)


def test_navegacao_e_tipo_no_cartao(sessao,entrada):
    c=TestClient(app)
    r=c.get(f'/form2/participacoes/{entrada.id}/blocos/14?conta_id=CONTA-B1');assert r.status_code==200
    assert 'Voltar ao resumo do FORM 2' in r.text
    assert 'navegacao-form2' in r.text
    evidencia('form2_bloco14',r.text)
    fila=c.get('/form2/filas?conta_id=CONTA-B1');assert fila.status_code==200
    from app.modelos import Registro
    reg=sessao.get(Registro,entrada.registro_id)
    tipo={'processo':'Processo','servico':'Serviço','atividade':'Atividade'}[reg.tipo_objeto]
    assert tipo+' · ' in fila.text
    evidencia('fila',fila.text)
    obj=entrar(sessao,entrada,4)
    evidencia('form4_bloco1',c.get(f'/forms34/{obj}/blocos/1?conta_id=CONTA-B1').text)
    evidencia('central',c.get('/central?conta_id=CONTA-B1').text)


def test_situacoes_identificam_apresentacao_e_conferente(sessao,entrada):
    from app.modelos import VersaoForm1Integral
    v=sessao.get(VersaoForm1Integral,entrada.snapshot_id)
    h=SimpleNamespace(numero_apresentacao=2,versao_rascunho=7,situacao='conferencia_interna_confirmada')
    assert situacao_origem(h)=='Apresentação 2 (rascunho 7) — Conferência interna confirmada'
    p={'estado':'respondida','snapshot_resposta_id':v.id,'origens':[]}
    t=situacoes_complementacao(sessao,[p])
    assert 'Apresentação' in t and 'aguardando conferência pelo AAL' in t
    assert 'Conferência interna confirmada' not in t


def test_documento_nao_interpreta_html():
    b=blocos_documento('# Teste fictício\n<script>ficticio</script>\n| A | B |\n| --- | --- |\n| 1 | 2 |')
    assert b[1]['texto']=='<script>ficticio</script>'
    assert b[2]['linhas']==[['A','B'],['1','2']]
