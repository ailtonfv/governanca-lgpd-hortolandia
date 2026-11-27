"""A11: efeitos dos destinos salvos apenas no ato de conclusão."""
from uuid import uuid5,NAMESPACE_URL
from sqlalchemy import select

def encaminhar(sessao,p,conta_id,comando_id):
    from app.form2_rev212 import indice_valores
    from app.fluxo_forms34 import ingressar
    from app.modelos import IdentidadeForms34
    valores=indice_valores(p.conteudo or {})
    destinos=[]
    for form,item in ((3,'F2-14.5'),(4,'F2-14.6')):
        if 'SIM' not in valores.get('opcao:'+item,[]):continue
        existente=sessao.scalar(select(IdentidadeForms34).where(IdentidadeForms34.registro_id==p.registro_id,IdentidadeForms34.chave_origem==f'f2:{p.id}:v{p.versao}:f{form}'))
        if existente:destinos.append(existente.id);continue
        r=ingressar(sessao,conta_id=conta_id,comando_id=str(uuid5(NAMESPACE_URL,f'{comando_id}/conclusao/f{form}')),participacao_id=p.id,versao=p.versao,form=form,justificativa=valores.get('texto:'+item,''))
        destinos.append(r['identidade_id'])
    return destinos
