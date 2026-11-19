"""Rótulos de leitura; não altera estados, referências ou eventos."""
from app.apresentacoes_form1 import rotulo_apresentacao
from app.modelos import VersaoForm1Integral


def situacao_origem(historico):
    rotulos={'devolvida_para_ajustes':'Devolvido para ajustes',
             'conferencia_interna_confirmada':'Conferência interna confirmada',
             'aguardando_conferencia_interna_apa':'Aguardando conferência do APA'}
    texto=rotulos.get(historico.situacao)
    return f'{rotulo_apresentacao(historico)} — {texto}' if texto else None


def situacoes_complementacao(sessao, pendencias):
    saida=[]
    for p in pendencias:
        sid=p.get('snapshot_resposta_id')
        origem=next(iter(p.get('origens',[])),{})
        v=sessao.get(VersaoForm1Integral,sid or origem.get('snapshot_id')) if sid or origem.get('snapshot_id') else None
        versao=rotulo_apresentacao(v) if v else 'Apresentação não identificada no histórico'
        estado=p['estado']
        texto=('definir unidade responsável pela resposta' if estado=='aberta' and not p.get('unidade_id') else
               'aguardando resposta' if estado=='aberta' else
               'resposta recebida, aguardando conferência pelo AAL' if estado=='respondida' else
               'resposta aceita' if estado=='resolvida' else 'consulte o histórico')
        rotulo=f'{versao} — {texto}' if sid else f'Solicitação sobre {versao} — {texto}'
        if rotulo not in saida:saida.append(rotulo)
    return ' · '.join(saida)
