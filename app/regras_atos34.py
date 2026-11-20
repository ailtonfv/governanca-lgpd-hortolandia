"""Políticas dos atos, compartilhadas pelo domínio e pela apresentação."""
CARGOS = ('Chefia da unidade', 'Ponto focal LGPD da Secretaria', 'Equipe da unidade executora')
FINALIDADES = {'avaliacao':'Avaliação sem consenso','triagem':'Triagem sem consenso',
 'residual':'Risco residual','prorrogacao':'Prorrogação','cancelamento':'Cancelamento'}

def finalidades(e):
    if e.get('form')==4:
        candidatos = [k for k in ('prorrogacao','cancelamento') if e.get('decisoes_pendentes',{}).get(k)]
        m = e.get('manifestacao_comite', {})
        return [k for k in candidatos if m.get('finalidade') != k or m.get('em', '') < e['decisoes_pendentes'][k].get('em', '')]
    alvo=e.get('reavaliacao',e)
    candidatos = ([k for k in ('avaliacao','triagem') if (alvo if k=='avaliacao' else e).get(k+'_sem_consenso')]
                  + (['residual'] if e.get('avaliacao') and not e.get('aceitacao') else []))
    def deliberada(k):
        fonte = alvo if k == 'avaliacao' else e
        return k in fonte.get('deliberacoes_rodada', {}) or fonte.get('manifestacao_comite', {}).get('finalidade') == k
    return [k for k in candidatos if not deliberada(k)]
