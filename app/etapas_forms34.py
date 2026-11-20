"""Proteções e responsabilidades por etapa, decisões do lote 12-F.

Não modifica atos anteriores; aplicada apenas a comandos futuros.
"""
from app.obrigatoriedade_forms import perguntas34, resumir

VERIFICACAO = ('F4-4.18', 'F4-4.20', 'F4-4.21', 'F4-4.22')
BLOCOS_PLANO = frozenset((1, 2, 3, 4, 5))


def pode_preencher(form, papeis):
    """Responsabilidade de preenchimento, compartilhada pela tela e pelo domínio."""
    return bool({'secretaria', 'dpo'} & set(papeis)) if form == 3 else 'secretaria' in papeis and 'dpo' not in papeis


def conferencia_etapa(estado, etapa):
    blocos = BLOCOS_PLANO if etapa == 'plano' else frozenset((6,))
    return resumir([q for q in perguntas34(4, estado) if q['bloco'] in blocos])


def motivo_bloqueio(estado, bloco):
    if estado['form'] == 3:
        if estado.get('conclusao') or estado.get('acoes') and not estado.get('revisao_aberta'):
            return 'Conteúdo preservado. Use Reavaliar o risco para abrir uma nova rodada.'
        if bloco == 14 and set(estado.get('avaliacao_confirmacoes', {})) == {'secretaria', 'dpo'}:
            return 'Nota conjunta confirmada. Mudanças exigem Reavaliar o risco.'
        if bloco == 15 and set(estado.get('triagem_confirmacoes', {})) == {'secretaria', 'dpo'}:
            return 'Triagem confirmada. Mudanças exigem Reavaliar o risco.'
    else:
        if estado.get('encerrada') or estado.get('cancelada'):
            return 'Ação encerrada: perguntas somente para leitura. Mudanças exigem reavaliação do risco.'
        if bloco == 7:
            return 'As respostas deste bloco são registradas no ato de verificação independente.'
        if estado.get('plano_aprovado') and bloco in BLOCOS_PLANO:
            return 'Plano aprovado: conteúdo somente para leitura. Novo plano ainda não está disponível; prorrogação tem ato próprio.'
    return ''


def validar_verificacao(dados):
    from app.questionario_forms34 import perguntas
    from app.validacao_atos34 import ErrosCampos
    itens = {q['id']: q for q in perguntas(4)}
    erros = {k: 'Responda esta pergunta da verificação.' for k in VERIFICACAO
             if dados.get(k) not in itens[k]['opcoes']}
    if erros:
        raise ErrosCampos(erros)
    return {k: dados[k] for k in VERIFICACAO}


def situacao_aprendizagem(e):
    if not e.get('verificada'):
        return 'Aguardando verificação' if not e.get('verificacao') else 'Requer ajuste na execução'
    if not e.get('aprendizagem'):
        return 'Aprendizagem não registrada'
    if e.get('aprendizagem_devolvida'):
        return 'Aprendizagem devolvida à Secretaria para ajustes'
    if not e.get('aprendizagem_conferida'):
        return 'Aguardando conferência do DPO'
    if not e.get('aprendizagem_autorizada'):
        return 'Aguardando autorização da Secretaria'
    return 'Aprendizagem autorizada para consulta'
