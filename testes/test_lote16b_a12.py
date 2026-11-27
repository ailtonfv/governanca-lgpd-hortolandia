import hashlib
from pathlib import Path
import pytest
from app.clausulas_lgpd import catalogo,perguntas2,validar4,pendencias4
from app.form2_rev212 import aplicavel,ramos_origem
from app.respostas_form2 import aplicar_revisao

def test_a12_json_identico_e_contrato_condicional():
    assert hashlib.sha256(Path('app/catalogos/clausulas_lgpd.json').read_bytes()).hexdigest()=='f8b2d174cf86d82495c35a0e5943aee79fdd4c5719b275f188779de455f8ee41'
    assert len(perguntas2())==9
    assert not aplicavel('F2-9F.1','',{},set(),{})
    assert aplicavel('F2-9F.1','',{},ramos_origem({'conteudo':{'respostas':{'8.2.2':'Sim'}}}),{})
    with pytest.raises(ValueError):aplicar_revisao({},9,{'opcao:F2-9F.1':['NAO']},set(),demonstrativo=True)

def test_a12_checklist_e_lacunas():
    respostas={'F4-4.4':['Aditar contrato']}
    assert validar4(respostas,{'B01':'Não'},False)=={'B01':'Não'}
    with pytest.raises(ValueError):validar4({}, {'B01':'Sim'},False)
    assert pendencias4({'respostas':respostas,'clausulas_contrato':{'B01':'Não'}})==[catalogo()['parte_b']['temas'][0]['tema']]
    from app.lacunas_form3 import listar
    assert any(q['id']=='LAC-F2-9F.1' for q in listar({'respostas':{},'fornecedor_guarda_dados':True,'respostas_fornecedor':{'F2-9F.1':['NAO']}}))


def test_a12_quadro_renderiza_abertura_e_quatro_passos():
    from app.rotas_fila_form2 import paginas
    c=catalogo()
    html=paginas.get_template('_clausulas_form2.html').render(numero=9,ativa=lambda *args:True,clausulas_lgpd=c,valores={'opcao:F2-9C.1':['SIM']})
    assert c['abertura'] in html
    assert c['como_usar']['adaptacao_para_tela']['texto_tela'] in html
    assert all(p['titulo'] in html for p in c['como_usar']['passos'])
    assert len(c['parte_b']['temas'])==10
