from testes.test_lote12 import entrada,fonte,protecoes,entrar,ato
from app.fluxo_forms34 import estado
from app.questionario_forms34 import perguntas

def test_a6_copia_contexto_sem_avaliacao_e_edita_independente(sessao,entrada):
    obj=entrar(sessao,entrada)
    q=next(q for q in perguntas(3) if q['bloco']==6 and q['tipo']=='single' and not q['depende'])
    valor=q['opcoes'][0]
    ato(sessao,obj,'salvar_bloco',bloco=6,campos={q['id']:valor})
    r=ato(sessao,obj,'adicionar_risco',motivo='Outro risco fictício')
    novo=r.get('destino_id') or r.get('identidade_id')
    assert novo!=obj
    e=estado(sessao,novo)
    assert e['respostas'][q['id']]==valor and e['contexto_copiado'][q['id']]['codigo']=='R01'
    assert not e['avaliacao'] and not e['triagem']
    outro=next(v for v in q['opcoes'] if v!=valor)
    ato(sessao,novo,'salvar_bloco',bloco=6,campos={q['id']:outro})
    assert estado(sessao,obj)['respostas'][q['id']]==valor
    assert q['id'] not in estado(sessao,novo)['contexto_copiado']
