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


def test_a11_concluir_encaminha_uma_vez_e_salvar_nao(sessao,entrada):
    from app.fila_form2 import executar
    from app.modelos import IdentidadeForms34
    from sqlalchemy import select
    assert not sessao.scalars(select(IdentidadeForms34).where(IdentidadeForms34.registro_id==entrada.registro_id)).all()
    comando=str(uuid4());v=entrada.versao
    r=executar(sessao,conta_id='CONTA-B1',comando_id=comando,participacao_id=entrada.id,acao='concluir',versao=v)
    sessao.commit()
    ids=entrada.conteudo['conclusao_analise']['encaminhamentos']
    assert len(ids)==2 and len(set(ids))==2
    repetido=executar(sessao,conta_id='CONTA-B1',comando_id=comando,participacao_id=entrada.id,acao='concluir',versao=v)
    assert repetido['permitido'] and repetido['reexecutado'] and repetido['participacao_id']==r['participacao_id']
    assert len(sessao.scalars(select(IdentidadeForms34).where(IdentidadeForms34.registro_id==entrada.registro_id)).all())==2

def test_a11_encerrar_preserva_e_recusa_ato(sessao,entrada):
    from testes.test_lote12 import entrar,ato
    from app.fila_form2 import executar
    from app.fluxo_forms34 import consultar
    from app.modelos import Registro
    obj=entrar(sessao,entrada)
    entrada.conteudo={**entrada.conteudo,'respostas_etapa1':{**entrada.conteudo['respostas_etapa1'],'F2-1.3':'NAO_CABE_REGISTRO'}}
    sessao.commit()
    with pytest.raises(ValueError,match='justificativa'):
        executar(sessao,conta_id='CONTA-B1',comando_id=str(uuid4()),participacao_id=entrada.id,acao='encerrar_nao_cabe',versao=entrada.versao)
    executar(sessao,conta_id='CONTA-B1',comando_id=str(uuid4()),participacao_id=entrada.id,acao='encerrar_nao_cabe',versao=entrada.versao,texto='Justificativa fictícia de situação única')
    sessao.commit()
    assert sessao.get(Registro,entrada.registro_id).estado_atual=='encerrado_nao_cabe'
    assert consultar(sessao,'CONTA-B1',obj)[0].id==obj
    with pytest.raises(ValueError,match='encerrado'):ato(sessao,obj,'adicionar_risco',motivo='Novo fictício')

def test_a11_controlador_somente_leitura():
    q=next(q for q in definicao_revisao(10)['itens'] if q['id']=='F2-10.1')
    assert q['edicao']=='consulta' and not q['alternativas']
    assert 'Município de Hortolândia' in q['controle']
