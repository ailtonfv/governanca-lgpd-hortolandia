"""Condições estruturadas; nunca extrai obrigações de texto livre."""
from app.validacao_atos34 import ErrosCampos


def validar_condicoes(valor):
    from app.questionario_forms34 import perguntas
    tipos = next(q['opcoes'] for q in perguntas(4) if q['id']=='F4-4.4')
    if not isinstance(valor, list):raise ErrosCampos({'condicoes':'Informe uma lista de condições.'})
    resultado=[]
    for c in valor:
        if not isinstance(c,dict) or not isinstance(c.get('texto'),str) or not 1<=len(c['texto'].strip())<=200 or c.get('tipo') not in tipos:
            raise ErrosCampos({'condicoes':'Cada condição exige descrição de até 200 caracteres e tipo do catálogo.'})
        resultado.append(dict(texto=c['texto'].strip(),tipo=c['tipo']))
    return resultado


def abertas(sessao, risco):
    from app.fluxo_forms34 import estado
    return [c for c in risco.get('condicoes_aceitacao',[]) if not estado(sessao,c['acao_id']).get('encerrada')]


def selo(sessao, risco):
    n=len(abertas(sessao,risco))
    return f"Aceitação condicionada: {n} {'condição em aberto' if n==1 else 'condições em aberto'}" if n else ''


def enriquecer(sessao,e):
    from app.fluxo_forms34 import estado
    risco=estado(sessao,e['risco_id']) if e.get('risco_id') else e
    e['selo_condicoes']=selo(sessao,risco)
    e['condicoes_abertas']=len(abertas(sessao,risco))
    e['ripd_confirmado']=bool(risco.get('referencia_ripd') and set(risco.get('referencia_ripd_confirmacoes',{}))=={'secretaria','dpo'})
    return e
