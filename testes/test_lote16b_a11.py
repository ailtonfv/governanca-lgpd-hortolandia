import pytest
from app.resultado_analise_form2 import resultado_salvo
from app.form2_rev212 import RASCUNHO, subbloco_visivel
from app.respostas_form2 import definicao_revisao

def test_a11_resultado_unico_preserva_complemento():
    q=next(q for q in definicao_revisao(14)['itens'] if q['id']=='F2-14.1')
    a=q['alternativas'][0]
    c={RASCUNHO:{'14':{'opcao:F2-14.1':[a['codigo']],'texto:F2-14.1':'Complemento fictício'}}}
    assert resultado_salvo(c)==a['rotulo']+' · Complemento fictício'
    with pytest.raises(ValueError):resultado_salvo({})
    with pytest.raises(ValueError):resultado_salvo({RASCUNHO:{'14':{'opcao:F2-14.1':['INEXISTENTE']}}})

def test_a11_consultas_indefinidas_inativas_e_canal_institucional():
    assert not subbloco_visivel('F2-14.8.1',set())
    assert not subbloco_visivel('F2-14.8.2',set())
    q=next(q for q in definicao_revisao(13)['itens'] if q['id']=='F2-13.1')
    assert 'canal institucional' in q['enunciado']
    assert any('Encarregado de Dados' in a for a in q['ajudas_usuario'])

from testes.test_lote12 import entrada,fonte,protecoes
from uuid import uuid4

def test_a11_conclusao_nao_aceita_resultado_paralelo(sessao,entrada):
    from app.fila_form2 import executar
    esperado=resultado_salvo(entrada.conteudo)
    r=executar(sessao,conta_id='CONTA-B1',comando_id=str(uuid4()),participacao_id=entrada.id,acao='concluir',versao=entrada.versao,texto='Resultado forjado fictício')
    assert r['permitido']
    assert entrada.conteudo['conclusao_analise']['resultado']==esperado
