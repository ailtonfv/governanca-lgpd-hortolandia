"""Classificação de leitura da Central e dos FORMs; não altera atos ou dashboard.

Uma providência é uma atuação exigida agora, não todo botão disponível.
Os chamadores fornecem apenas itens previamente autorizados.
"""
from app.atos_forms34_interface import disponiveis
from app.avaliacao_risco34 import exige_triagem
from datetime import datetime


def manifestacao_dpo_solicitada(estado):
    """Reconhece a solicitação vigente; manifestação anterior não responde pedido novo."""
    manifestacao = estado.get('manifestacao_dpo')
    if estado['form'] == 3:
        return (set(estado.get('avaliacao_confirmacoes', {})) == {'secretaria', 'dpo'}
                and estado.get('avaliacao', {}).get('residual', {}).get('faixa') in ('Alto', 'Crítico')
                and not manifestacao and not estado.get('aceitacao'))
    pedido = estado.get('decisoes_pendentes', {}).get('cancelamento')
    if not pedido or estado.get('faixa_origem') not in ('Alto', 'Crítico'):
        return False
    if not manifestacao:
        return True
    return bool(pedido.get('em') and manifestacao.get('em') and
                datetime.fromisoformat(manifestacao['em']) < datetime.fromisoformat(pedido['em']))


def classificar(form, estado, papeis=(), pessoa_id=None):
    """Ponto único para grupo, etapa e próximo ato. Sem gravação ou autorização nova."""
    def resultado(etapa, bloco, ato=None, titulo=None):
        return dict(pendente=bool(ato), etapa=etapa, bloco=bloco,
                    ato=ato, botao=titulo or 'Acompanhar',
                    pendencia=titulo or 'Nenhuma providência sua neste momento')

    if form == 1:
        for p in estado.get('providencias', []):
            if p['categoria'] == 'conferencia_form1':
                return resultado('f1-confere', 1, 'conferir', p['acao_rotulo'])
            if p['categoria'] == 'preenchimento_form1':
                return resultado('f1-levanta', 1, p['acao_tipo'], p['acao_rotulo'])
        if estado.get('designar_arp'):
            return resultado('f1-abre', 1, 'designar_arp', 'Designar responsável pelo preenchimento')
        return resultado('f1-levanta', 1)

    if form == 2:
        etapa = 'f2-analisa' if estado['tipo'] == 'principal' else 'apoio'
        if estado['estado'] == 'concluida':
            return resultado('f2-conclui', 1)
        if estado.get('complemento') == 'respondida':
            return resultado(etapa, 1, 'avaliar_resposta', 'Avaliar resposta da origem')
        if estado.get('complemento') == 'aberta' or estado.get('consultas_abertas'):
            return resultado(etapa, 1)
        return resultado(etapa, 1, 'analisar', 'Analisar' if estado['tipo'] == 'principal' else 'Registrar manifestação')

    # Disponibilidade usa as autorizações existentes. A seleção abaixo retira
    # atos opcionais e os que aguardam requisitos de outro papel.
    candidatos = {}
    for bloco in range(1, 17 if form == 3 else 10):
        for ato in disponiveis(form, bloco, set(papeis), estado, pessoa_id):
            candidatos.setdefault(ato['acao'], (14 if form == 3 and ato['acao'] in ('manifestar_dpo', 'manifestar_comite') else 6 if form == 4 and ato['acao'] == 'manifestar_dpo' else bloco, ato['titulo']))

    def escolher(etapa, *atos):
        for ato in atos:
            if ato in candidatos:
                bloco, titulo = candidatos[ato]
                return resultado(etapa, bloco, ato, titulo)
        return resultado(etapa, 14 if form == 3 else 7)

    if form == 3:
        if estado.get('conclusao') and not estado.get('reavaliacao'):
            return resultado('f3-decide', 16)
        alvo = estado.get('reavaliacao') or estado
        atual = None
        if alvo.get('avaliacao_sem_consenso'):
            atual = escolher('f3-avalia', 'manifestar_comite')
        elif not alvo.get('avaliacao'):
            atual = escolher('f3-avalia', 'propor_avaliacao')
        elif set(alvo.get('avaliacao_confirmacoes', {})) != {'secretaria', 'dpo'}:
            atual = escolher('f3-avalia', 'confirmar_avaliacao')
        if atual and (atual['pendente'] or not estado.get('reavaliacao')):
            return atual
        # Reavaliação não suspende as providências da nota conjunta vigente.
        faixa = estado['avaliacao']['residual']['faixa']
        exigidos = []
        if not estado.get('aceitacao'):
            falta_dpo = manifestacao_dpo_solicitada(estado)
            deliberacao = estado.get('deliberacoes_rodada', {}).get('residual') or estado.get('manifestacao_comite', {})
            falta_comite = faixa == 'Crítico' and deliberacao.get('finalidade') != 'residual'
            if falta_dpo: exigidos.append('manifestar_dpo')
            if falta_comite: exigidos.append('manifestar_comite')
            if not falta_dpo and not falta_comite: exigidos.append('aceitar_residual')
        falta_triagem = exige_triagem(estado['avaliacao'], estado.get('sinais')) and set(estado.get('triagem_confirmacoes', {})) != {'secretaria', 'dpo'}
        if falta_triagem:
            exigidos.append('manifestar_comite' if estado.get('triagem_sem_consenso') else 'confirmar_triagem' if estado.get('triagem') else 'propor_triagem')
        if exigidos or not estado.get('aceitacao') or falta_triagem:
            return escolher('f3-decide', *exigidos)
        respostas = estado.get('respostas', {})
        if respostas.get('F3-3.59') == 'Sim' and 'Providência no FORM 4' in respostas.get('F3-3.61', []) and not estado.get('acoes_rodada', estado.get('acoes')):
            return escolher('f3-decide', 'encaminhar_acao')
        return escolher('f3-decide', 'concluir_avaliacao')

    if estado.get('cancelada'):
        return resultado('f4-executa', 6)
    pedidos = estado.get('decisoes_pendentes', {})
    if pedidos.get('cancelamento'):
        if manifestacao_dpo_solicitada(estado):
            return escolher('f4-executa', 'manifestar_dpo')
        return escolher('f4-executa', 'cancelar')
    if pedidos.get('prorrogacao'):
        if estado.get('prorrogacoes') == 1 and estado.get('manifestacao_comite', {}).get('finalidade') != 'prorrogacao':
            return escolher('f4-executa', 'manifestar_comite')
        return escolher('f4-executa', 'decidir_prorrogacao')
    if not estado.get('plano'):
        return escolher('f4-plano', 'planejar')
    if not estado.get('plano_aprovado'):
        return escolher('f4-plano', 'aprovar_plano')
    if not estado.get('execucao'):
        return escolher('f4-executa', 'executar_medida')
    if not estado.get('verificacao'):
        return escolher('f4-verifica', 'verificar')
    if not estado.get('verificada'):
        return resultado('f4-executa', 6)
    if not estado.get('aprendizagem') or estado.get('aprendizagem_devolvida'):
        return escolher('f4-aprende', 'aprender')
    if not estado.get('aprendizagem_conferida'):
        return escolher('f4-aprende', 'conferir_aprendizagem')
    if not estado.get('aprendizagem_autorizada'):
        return escolher('f4-aprende', 'autorizar_aprendizagem')
    return resultado('f4-aprende', 9)
