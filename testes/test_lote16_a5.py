"""A5: polaridade, condições históricas, controles e origem estável."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.lacunas_form3 import listar, incoerencias, configuracao
from app.questionario_forms34 import salvar
from app.fluxo_forms34 import estado
from testes.test_lote12 import entrada, fonte, protecoes, entrar, ato


def test_polaridades_conferidas_e_itens_pendentes():
    respostas={'F3-3.16':'Não','F3-3.17':'Não','F3-3.18':'Sim','F3-3.19':'Não',
        'F3-3.19.1':'Não','F3-3.20':'Não','F3-3.25':'Sim','F3-3.28':'Sim'}
    ids={i['pergunta'] for i in listar({'respostas':respostas})}
    assert set(respostas)-{'F3-3.25'} <= ids
    respostas['F3-3.28']='Não'
    assert 'F3-3.28' not in {i['pergunta'] for i in listar({'respostas':respostas})}
    respostas['F3-3.28']='Parcialmente'
    assert 'F3-3.28' in {i['pergunta'] for i in listar({'respostas':respostas})}
    pendentes={i['id'] for i in configuracao()['itens'] if not i['habilitada']}
    assert pendentes=={'F3-3.22','F3-3.29','F3-3.44'}


def test_condicionais_fechadas_nao_geram_lacunas_historicas():
    e={'respostas':{'F3-3.25':'Não','F3-3.28':'Sim','F3-3.39':'Não','F3-3.41':'Não',
        'F3-3.42':'Não','F3-3.43':'Não','F3-3.44':'Não','F3-3.45':'Não','F3-3.46':'Não'}}
    assert listar(e)==[]


def test_naturezas_institucional_e_controles():
    e={'respostas':{'F3-3.17':'A confirmar','F3-3.25':'Sim','F3-3.25.1':'Sim',
        'F3-3.43':'Sim','F3-3.35':'Em definição pela Prefeitura (grupo de temporalidade)',
        'F3-3.18':'Sim','F3-3.47':['Login individual']},
        'controles_bloco13':{'Login individual':{'implementado':'Parcial','evidencia':'Referência fictícia'}}}
    lista=listar(e)
    assert next(i for i in lista if i['pergunta']=='F3-3.17')['natureza']=='a_confirmar'
    assert all(i['natureza']=='verificacao' for i in lista if i['pergunta'] in ('F3-3.25.1','F3-3.43'))
    assert not any(i['pergunta']=='F3-3.35' for i in lista)
    assert any(i['id'].startswith('LAC-F3-3.47-') for i in lista)
    assert len(incoerencias(e))==1
    with pytest.raises(ValueError,match='sozinho'):
        salvar(3,{}, {'bloco':13,'campos':{'F3-3.47':['Login individual','Nenhum controle identificado']}},{})


def test_encaminhar_lacuna_preserva_origem_e_nao_duplica(sessao,entrada):
    r=entrar(sessao,entrada)
    ato(sessao,r,'salvar_bloco',bloco=6,campos={'F3-3.18':'Sim'})
    dados=dict(lacuna_id='LAC-F3-3.18',destino='Providência no FORM 4',prioridade='Alta')
    ato(sessao,r,'destinar_lacuna',**dados)
    assert estado(sessao,r)['destinos_lacunas']['LAC-F3-3.18']['prioridade']=='Alta'
    a=ato(sessao,r,'encaminhar_acao',**dados)['identidade_id']
    ae=estado(sessao,a)
    assert ae['origem_lacuna']['id']=='LAC-F3-3.18'
    assert ae['respostas']['F4-4.2']=='LAC-F3-3.18'
    assert ae['respostas']['F4-4.9']=='Alta'
    assert ato(sessao,r,'encaminhar_acao',**dados)['identidade_id']==a
    with pytest.raises(ValueError,match='ativa'):
        ato(sessao,r,'encaminhar_acao',**{**dados,'lacuna_id':'LAC-F3-3.41'})
    c=TestClient(app)
    for bloco in (13,16):
        page=c.get(f'/forms34/{r}/blocos/{bloco}?conta_id=CONTA-B1')
        assert page.status_code==200
        assert 'Lacunas encontradas e verificações' in page.text
        assert 'Consultar providência encaminhada' in page.text
    assert 'Salvar destino e prioridade' not in c.get(f'/forms34/{r}/blocos/16?conta_id=CONTA-E1').text
    bloco8 = c.get(f'/forms34/{r}/blocos/8?conta_id=CONTA-B1')
    assert 'Bloco 8 — Terceiros, PPPs, concessões e dependência do fornecedor' in bloco8.text
    with pytest.raises(PermissionError):
        ato(sessao,r,'destinar_lacuna',conta='CONTA-E1',**dados)


def test_controles_pela_rota_e_validacao_da_origem(sessao,entrada):
    from uuid import uuid4
    r=entrar(sessao,entrada)
    c=TestClient(app)
    page=c.post(f'/forms34/{r}/blocos/13?conta_id=CONTA-B1',data={
        'acao':'salvar_bloco','comando_id':str(uuid4()),'versao':str(estado(sessao,r)['versao']),
        'F3-3.47':'Login individual','implementado:Login individual':'Parcial',
        'evidencia:Login individual':'Documento fictício','observacoes_controles':'Observação fictícia'})
    assert page.status_code==200
    sessao.expire_all()
    assert estado(sessao,r)['controles_bloco13']['Login individual']['implementado']=='Parcial'
    assert 'Nenhum controle identificado' in page.text
    from app.questionario_forms34 import perguntas
    assert next(q for q in perguntas(3) if q['id']=='F3-3.59')['tipo']=='computed'
    with pytest.raises(ValueError,match='origem'):
        salvar(4,{'F4-4.2':'LAC-F3-3.18'},dict(bloco=1,campos={'F4-4.2':'texto livre'}),
            {'origem_lacuna':{'id':'LAC-F3-3.18'}})
def test_sugestao_apresenta_topico_institucional_sem_codigo_tecnico():
    from app.lacunas_form3 import sugestao_para_tela

    assert sugestao_para_tela('Ação de guarda do catálogo F4-4.4') == (
        'Providência de guarda (catálogo de providências)')
    assert sugestao_para_tela('Criar/alterar cláusula contratual (ver Anexo E da Cartilha)') == (
        'Criar/alterar cláusula contratual (ver na Cartilha: Cláusulas orientativas para terceiros)')
