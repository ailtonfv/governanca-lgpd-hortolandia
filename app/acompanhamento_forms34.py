"""Leitura compartilhada da Central, listas e cabeçalho, sem novos atos."""
from app.leitura_atos34 import NOMES, horario
from app.infra_forms34 import historico


def rotulo_objeto(obj):
    return f"{'Risco' if obj.tipo == 'R' else 'Providência'} {obj.numero}"


def descricao_objeto(e):
    texto = e.get('evento') if e['form'] == 3 else e.get('respostas', {}).get('F4-4.3') or e.get('plano')
    if not isinstance(texto, str):texto = None
    if texto:
        texto = ' '.join(texto.split())
    return texto or 'Título ainda não informado'


def titulo(obj, e):
    return f"{rotulo_objeto(obj)}: {descricao_objeto(e)}"


def situacao_nota_posterior(estado):
    nota = estado.get('residual_acao')
    if not nota:
        return 'Ainda não avaliado'
    rotulo = f"{nota['nota']} — {nota['faixa']}"
    confirmacao = estado.get('residual_acao_confirmacoes', {}).get('dpo', {})
    if confirmacao.get('em'):
        return f"{rotulo} (nota conjunta confirmada em {horario(confirmacao['em']).split()[0]})"
    return f"Proposta: {rotulo}, aguardando confirmação do DPO"


def resumo(sessao, obj, e, papeis, pessoa_id):
    from app.providencias import classificar
    proxima = classificar(e['form'], e, papeis, pessoa_id)
    ultimo = next((ev for ev in reversed(historico(sessao,obj.id)) if ev.tipo_evento.startswith('f34_')
                   and ev.tipo_evento not in ('f34_salvar_bloco','f34_abrir_detalhes')), None)
    situacao = NOMES.get(ultimo.tipo_evento.removeprefix('f34_'), e['situacao'])+' em '+horario(ultimo.ocorrido_em) if ultimo else e['situacao']
    if ultimo and ultimo.tipo_evento == 'f34_encerramento_automatico':
        situacao = f'Providência concluída automaticamente em {horario(ultimo.ocorrido_em)}, após a verificação aprovada'
    if e.get('aprendizagem_devolvida'):
        situacao = 'Aprendizagem devolvida à Secretaria para ajustes em '+horario(e['aprendizagem_devolvida']['em'])
    if e.get('registro_encerrado'):situacao='Registro encerrado — histórico somente leitura'
    concluido = bool(e.get('concluida') or e.get('cancelada') or e.get('registro_encerrado')
                      or (e.get('encerrada') and e.get('aprendizagem_autorizada')))
    return dict(titulo=titulo(obj,e), descricao=descricao_objeto(e), rotulo=rotulo_objeto(obj),
                situacao=situacao, concluido=concluido and not proxima['pendente'], **proxima)
