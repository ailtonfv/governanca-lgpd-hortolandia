"""Classificação temática, separada de prioridade, risco e situação."""
from sqlalchemy import select
from app.modelos import Tema


def catalogo(sessao, *, ativos=False):
    q = select(Tema).order_by(Tema.codigo)
    if ativos:
        q = q.where(Tema.ativo.is_(True))
    return list(sessao.scalars(q))


def validar(sessao, principal='', complementares=(), *, obrigatorio=False):
    if not isinstance(principal,str) or not isinstance(complementares,(list,tuple)):
        raise ValueError('Escolha temas do catálogo.')
    principal = principal.strip()
    if obrigatorio and not principal:
        raise ValueError('Escolha um tema principal antes de enviar o plano para aprovação.')
    if len(complementares)>2:
        raise ValueError('Escolha no máximo dois temas complementares.')
    if len(set(complementares)) != len(complementares) or principal in complementares:
        raise ValueError('Os temas complementares devem ser diferentes entre si e do principal.')
    for codigo in ([principal] if principal else []) + list(complementares):
        tema = sessao.get(Tema,codigo)
        if not tema or not tema.ativo:
            raise ValueError('Escolha um tema ativo do catálogo.')
    return dict(principal=principal, complementares=list(complementares))


def codigos(temas):
    temas = temas or {}
    return ([temas['principal']] if temas.get('principal') else []) + list(temas.get('complementares',[]))


def nomes(sessao, temas):
    resultado=[]
    for codigo in codigos(temas):
        t=sessao.get(Tema,codigo)
        resultado.append(codigo+' · '+(t.nome+(' (tema desativado)' if not t.ativo else '') if t else 'Tema não disponível'))
    return resultado or ['Tema não informado']


def corresponde(temas, filtro):
    return not filtro or filtro in codigos(temas)


def configurar_campos(sessao, atos, estado):
    opcoes=[(t.codigo, t.codigo+' · '+t.nome+' — Use quando: '+t.use_quando) for t in catalogo(sessao,ativos=True)]
    for ato in atos:
        for campo in ato['campos']:
            if campo['nome'] in ('tema_principal','temas_complementares'):
                campo['opcoes']=opcoes
        if ato['acao'] in ('planejar','salvar_temas','aprender'):
            temas=(estado.get('aprendizagem',{}).get('temas') if ato['acao']=='aprender' else None) or estado.get('temas',{})
            ato.setdefault('valores',{}).update(tema_principal=temas.get('principal',''),temas_complementares=temas.get('complementares',[]))
