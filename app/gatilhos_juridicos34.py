"""11-B: sinais categóricos da origem congelada; sem busca em texto livre."""
from app.form2_rev212 import indice_valores


def motivos(conteudo):
    r=indice_valores(conteudo)
    def tem(item,*valores):
        return any(v in valores for k,vs in r.items() if k=='opcao:'+item or k.startswith('opcao:'+item+'#')
                   for v in (vs if isinstance(vs,list) else [vs]))
    incerto=('A_CONFIRMAR','ANALISE_JURIDICA','A confirmar','Requer análise jurídica')
    base_incerta=tem('F2-3.1',*incerto) or tem('F2-3.2','NAO','A_CONFIRMAR') or tem('F2-3.2.2','NAO','PARCIAL',*incerto)
    encontrados=[]
    if tem('F2-4.1','SIM','Sim') and (tem('F2-4.3',*incerto) or tem('F2-4.4','NAO','A_CONFIRMAR')):
        encontrados.append('F2-4.1 / F2-4.3 / F2-4.4')
    if tem('F2-6.1','SIM','Sim') and (base_incerta or tem('F2-3.4','SIM','A_CONFIRMAR')
            or tem('F2-6.2','ANALISE_JURIDICA') or tem('F2-6.4','ANALISE_JURIDICA')):
        encontrados.append('F2-6.1 / fundamento ou melhor interesse a analisar')
    if tem('F2-8.1','SIM','Sim') and (tem('F2-8.6',*incerto) or tem('F2-8.6','ALT_01') and base_incerta):
        encontrados.append('F2-8.1 / F2-8.6')
    return encontrados
