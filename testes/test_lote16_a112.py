"""A11.2: sub-blocos condicionados à origem, inclusive no POST."""
import pytest
from app.form2_rev212 import ramos_origem, aplicavel, subbloco_visivel
from app.respostas_form2 import aplicar_revisao
from app.rev22_form1 import definicoes, LACRES_HISTORICOS, VERSAO
from app.extensao_medidas_form1 import versao_estrutura
from testes.test_lote12 import entrada, fonte, protecoes, entrar


def test_gatilhos_da_origem_e_pergunta_local():
    assert definicoes()['8.10']['block']==8
    r=ramos_origem({'conteudo':{'respostas':{'8.10':'Sim','5.1':['Dados de saúde']}}})
    assert subbloco_visivel('F2-9W.1',r) and subbloco_visivel('F2-11S.1',r)
    assert not aplicavel('F2-9W.1','',{},set(),{})
    assert not aplicavel('F2-11S.1','',{},set(),{})
    assert not aplicavel('F2-9.4','',{},r,{})
    assert subbloco_visivel('F2-11S.1',ramos_origem({'secretaria_saude':True}))
    for h in LACRES_HISTORICOS:
        assert versao_estrutura({'revisao_22':{'versao':VERSAO,'catalogo_sha256':h}})==VERSAO


def test_servidor_recusa_resposta_wifi_fora_da_condicao():
    from app.respostas_form2 import definicao_revisao
    q=next(q for q in definicao_revisao(9)['itens'] if q['id']=='F2-9W.1')
    valor=q['alternativas'][0]['codigo']
    with pytest.raises(ValueError):
        aplicar_revisao({},9,{'opcao:F2-9W.1':[valor]},set(),demonstrativo=True)


def test_html_oculta_subblocos_na_origem_sem_declaracao(sessao,entrada):
    from fastapi.testclient import TestClient
    from app.main import app
    c=TestClient(app)
    page=c.get(f'/form2/participacoes/{entrada.id}/blocos/9?conta_id=CONTA-B1')
    assert page.status_code==200
    assert 'id="F2-9W.1"' not in page.text and 'id="F2-9.4"' not in page.text
