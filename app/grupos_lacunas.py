"""Grupos de encaminhamento do FORM 3, com vínculos por lacuna."""
from app.lacunas_form3 import sugestao_para_tela

PRIORIDADES = ('Imediata', 'Alta', 'Média', 'Baixa', 'A confirmar')


def prioridade_grupo(estado, ids, escolha=''):
    salvas = estado.get('destinos_lacunas', {})
    selecao = set(ids)
    grupos = estado.get('grupos_lacunas', [])
    persistida = next((g.get('prioridade') for g in grupos if set(g['ids']) == selecao), None)
    candidatas = [escolha, persistida, *(salvas.get(i, {}).get('prioridade') for i in ids)]
    return next((p for p in PRIORIDADES if p in candidatas), '')


def grupos_para_tela(estado, lacunas):
    pendentes = {l['id']: l for l in lacunas
                 if l['id'] not in estado.get('encaminhamentos_lacunas', {})}
    grupos = []

    def montar(itens, destino=''):
        sugestoes = {i['acao_sugerida'] for i in itens}
        sugestao = sugestoes.pop() if len(sugestoes) == 1 else ''
        return dict(itens=itens, titulo=sugestao or 'Providência selecionada pela Secretaria',
                    destino=destino or itens[0].get('destino') or '',
                    prioridade=prioridade_grupo(estado, [i['id'] for i in itens]))

    for grupo in estado.get('grupos_lacunas', []):
        itens = [pendentes.pop(i) for i in grupo['ids'] if i in pendentes]
        if itens:
            grupos.append(montar(itens, grupo['destino']))
    automaticos = {}
    for lacuna in pendentes.values():
        sugestao = sugestao_para_tela(lacuna.get('acao_sugerida'))
        if lacuna['natureza'] == 'lacuna' and sugestao:
            automaticos.setdefault(sugestao, []).append(lacuna)
    return grupos + [montar(itens) for itens in automaticos.values()]


def registrar_grupo(estado, ids, destino, prioridade):
    selecionadas = set(ids)
    grupos = []
    for grupo in estado.get('grupos_lacunas', []):
        restantes = [i for i in grupo['ids'] if i not in selecionadas]
        if restantes:
            grupos.append(dict(ids=restantes, destino=grupo['destino']))
    estado['grupos_lacunas'] = grupos + [dict(ids=ids, destino=destino, prioridade=prioridade)]
    destinos = estado.setdefault('destinos_lacunas', {})
    for i in ids:
        anterior = destinos.get(i, {}).get('prioridade')
        destinos[i] = dict(destino=destino, prioridade=prioridade if len(ids) == 1 else anterior or prioridade)


def selecionar(estado, lacunas, ids):
    if not isinstance(ids, list) or not ids or any(not isinstance(i, str) or not i for i in ids):
        raise ValueError('Selecione pelo menos uma lacuna.')
    if len(ids) != len(set(ids)):
        raise ValueError('Cada lacuna deve aparecer uma única vez no grupo.')
    encaminhadas = estado.get('encaminhamentos_lacunas', {})
    vinculadas = [encaminhadas[i]['acao_id'] for i in ids if i in encaminhadas]
    if vinculadas:
        if len(vinculadas) == len(ids) and len(set(vinculadas)) == 1:
            return [], vinculadas[0]
        raise ValueError('O grupo contém lacunas que já têm providência. Atualize a página.')
    ativas = {l['id']: l for l in lacunas}
    if not set(ids) <= ativas.keys():
        raise ValueError('Lacuna não está ativa nesta versão. Atualize a página.')
    return [ativas[i] for i in sorted(ids)], None
