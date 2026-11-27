"""Ajustes editoriais aprovados; preserva códigos e respostas históricas."""
TEXTOS2 = {
 'F2-2.2':'Em qual competência da Secretaria esta finalidade se apoia? (ex.: arrecadação de tributos)',
 'F2-2.3':'Em uma frase: para que os dados são usados?',
 'F2-2.8':'Guardar o dado e mostrar o dado a outros são coisas diferentes. Você avaliou as duas separadamente?',
 'F2-10.5':'As pessoas da Prefeitura que atuam neste fluxo foram tratadas como Servidores com Acesso Autorizado (SAA), conforme suas atribuições, e não automaticamente como Operadores?',
}
AJUDAS2 = {
 'F2-6.4':"Para crianças, a LGPD pede consentimento específico de pai, mãe ou responsável quando o consentimento for a base legal; o tratamento também pode se apoiar em outras hipóteses legais, sempre no melhor interesse da criança ou do adolescente. Em dúvida, marque 'Requer análise jurídica'.",
 'F2-12.1':'O acesso à rede da Prefeitura de fora não é permitido. Quando há trabalho fora, ele costuma acontecer com processos em papel. Registre como acontece de fato.',
}
TITULO12='Trabalho fora da Prefeitura: processos em papel, dispositivos e campo'

def ajustar2(q):
    if q['id'] in TEXTOS2:q['enunciado']=TEXTOS2[q['id']]
    if q['id'] in AJUDAS2:q['ajudas_usuario']=[AJUDAS2[q['id']]]
    for a in q['alternativas']:
        if a['codigo']=='AGUARDA_DEFINICAO_INSTITUCIONAL':a['rotulo']='Aguarda a tabela de temporalidade da Prefeitura'

def grupo_fila(cartao,pessoa_id):
    ativos=[p for p in cartao['participacoes'] if p.estado!='concluida']
    if any(p.responsavel_id==pessoa_id for p in ativos):return 'Sua análise'
    if any(not p.responsavel_id for p in ativos):return 'Aguardando responsável'
    return 'Da sua unidade, com outro AAL' if ativos else 'Em acompanhamento'
