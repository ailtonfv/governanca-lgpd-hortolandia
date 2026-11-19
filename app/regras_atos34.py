"""Políticas dos atos, compartilhadas pelo domínio e pela apresentação."""
CARGOS = ('Chefia da unidade', 'Ponto focal LGPD da Secretaria', 'Equipe da unidade executora')
FINALIDADES = {'avaliacao':'Avaliação sem consenso','triagem':'Triagem sem consenso',
 'residual':'Risco residual','prorrogacao':'Prorrogação','cancelamento':'Cancelamento'}

def finalidades(e):
    if e.get('form')==4:
        return [k for k in ('prorrogacao','cancelamento') if e.get('decisoes_pendentes',{}).get(k)]
    alvo=e.get('reavaliacao',e)
    return ([k for k in ('avaliacao','triagem') if (alvo if k=='avaliacao' else e).get(k+'_sem_consenso')]
            + (['residual'] if e.get('avaliacao') else []))
