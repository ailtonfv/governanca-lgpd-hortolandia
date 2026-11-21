"""Publicação de orientações autorizadas; nunca concede acesso à origem."""
from app.fila_form2 import pessoa_ativa
from app.dashboard.fontes import carregar, Escopo
from app.dashboard.consultas import aprendizados, momento, data_br


def consultar(sessao, conta, *, secretaria='', palavra='', fonte=None):
    pessoa_ativa(sessao, conta)
    dados = fonte if fonte is not None else carregar(sessao, Escopo('Consulta de aprendizados', None, None))
    unidades = [dict(id=u.id, nome=u.nome) for u in dados['secretarias']]
    if secretaria and secretaria not in {u['id'] for u in unidades}:
        raise ValueError('Secretaria indisponível.')
    publicados = aprendizados(dados)[0]['lista']
    campos = ('registro', 'item', 'unidade_id', 'secretaria', 'contexto', 'diretriz', 'limites', 'autorizado')
    linhas = [{k:l[k] for k in campos} for l in publicados
              if not secretaria or l['unidade_id'] == secretaria]
    busca = palavra.strip().casefold()
    if busca:
        linhas = [l for l in linhas if busca in ' '.join(str(l[k]) for k in ('contexto','diretriz','limites','secretaria')).casefold()]
    linhas.sort(key=lambda l: momento(l['autorizado']), reverse=True)
    for l in linhas:
        l['autorizado_texto'] = data_br(l['autorizado'])
    return dict(itens=linhas, total=len(linhas), destaque=linhas[0] if linhas else None,
                secretarias=unidades, secretaria=secretaria, palavra=palavra)
