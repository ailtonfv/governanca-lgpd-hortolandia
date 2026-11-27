"""A4: referências da origem congelada, sem preencher respostas do avaliador."""
import json

def referencias(sessao,ref,itens):
    if ref.form!=3:return {}
    from app.origem_form2 import ler_origem
    from app.form2_rev212 import indice_valores
    from app.respostas_form2 import definicao_revisao
    f1=ler_origem(sessao,ref.registro_id,ref.snapshot_form1_id)['conteudo'].get('respostas',{})
    fonte=json.loads(ref.fonte_canonica)
    f2=indice_valores(fonte.get('conteudo',{}).get('conteudo',{})) if ref.fonte_form==2 else {}
    rotulos={q['id']:{a['codigo']:a['rotulo'] for a in q['alternativas']} for n in (2,9) for q in definicao_revisao(n)['itens']}
    def texto(v):
        if isinstance(v,list):return ' · '.join(map(str,v)) or 'Sem resposta nesta versão'
        return str(v) if v not in (None,'') else 'Sem resposta nesta versão'
    def linhas1(prefixos):
        chaves=sorted({k for k in f1 if any(k==p or k.startswith(p+'.') for p in prefixos)} or set(prefixos))
        return [dict(referencia='F1-'+k,valor=texto(f1.get(k))) for k in chaves]
    def linhas2(prefixos):
        saida=[]
        for k,v in f2.items():
            ident=k.partition(':')[2].partition('#')[0]
            if not any(ident==p or ident.startswith(p+'.') for p in prefixos):continue
            if isinstance(v,list):v=[rotulos.get(ident,{}).get(c,c) for c in v]
            saida.append(dict(referencia=ident,valor=texto(v)))
        return saida or [dict(referencia=p,valor='Sem resposta nesta versão') for p in prefixos]
    saida={}
    for q in itens:
        id=q['id']
        if id=='F3-3.6':saida[id]=linhas1(['2.8','2.9','2.10'])
        if id in ('F3-3.8','F3-3.35'):saida[id]=linhas1(['12'])
        if id=='F3-3.34':saida[id]=linhas2(['F2-2.3'])
    if itens:
        b=itens[0]['bloco'];id=itens[0]['id']
        if b==6:saida[id]=linhas1(['9.1','9.2'])
        if b==7:saida[id]=linhas1(['8','WPP'])
        if b==8:saida[id]=linhas2(['F2-9'])
    return saida
