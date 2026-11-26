"""Leitura compartilhada da Central, listas e cabeçalho, sem novos atos."""
from app.leitura_atos34 import NOMES, horario
from app.infra_forms34 import historico


def titulo(obj, e):
    codigo = obj.codigo.split('-')[-1]
    especie = 'Risco' if e['form'] == 3 else 'Ação'
    texto = e.get('evento') if e['form'] == 3 else e.get('respostas', {}).get('F4-4.3') or e.get('plano')
    if not isinstance(texto, str):texto = None
    if texto:
        texto = ' '.join(texto.split())
    return f"{especie} {codigo}: {texto or 'Título ainda não informado'}"


def resumo(sessao, obj, e, papeis, pessoa_id):
    from app.providencias import classificar
    proxima = classificar(e['form'], e, papeis, pessoa_id)
    ultimo = next((ev for ev in reversed(historico(sessao,obj.id)) if ev.tipo_evento.startswith('f34_')
                   and ev.tipo_evento not in ('f34_salvar_bloco','f34_abrir_detalhes')), None)
    situacao = NOMES.get(ultimo.tipo_evento.removeprefix('f34_'), e['situacao'])+' em '+horario(ultimo.ocorrido_em) if ultimo else e['situacao']
    if ultimo and ultimo.tipo_evento == 'f34_encerramento_automatico':
        situacao = f'Ação concluída automaticamente em {horario(ultimo.ocorrido_em)}, após a verificação aprovada'
    if e.get('aprendizagem_devolvida'):
        situacao = 'Aprendizagem devolvida à Secretaria para ajustes em '+horario(e['aprendizagem_devolvida']['em'])
    return dict(titulo=titulo(obj,e), situacao=situacao, **proxima)
