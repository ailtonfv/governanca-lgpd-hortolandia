"""Contratos de entrada/apresentação; autorizações permanecem no domínio."""

def campo(nome, rotulo, tipo='text', opcoes=()):
    return dict(nome=nome, rotulo=rotulo, tipo=tipo, opcoes=opcoes)

J = campo('justificativa', 'Justificativa', 'textarea')
E = campo('evidencia', 'Referência da evidência (sem dados pessoais)', 'textarea')
S = ('secretaria', 'dpo')
ATOS = {
 'adicionar_risco':(3,4,S,'Registrar outro risco na mesma origem',[campo('motivo','Evento ou motivo do novo risco','textarea')]),
 'propor_avaliacao': (3,14,S,'Registrar proposta de avaliação',[
    campo('evento','Evento de risco','textarea'), campo('causa','Causa','textarea'),
    campo('consequencia','Consequência para o titular','textarea'),
    campo('p','Probabilidade inerente (1 a 5)','number'),campo('i','Impacto inerente (1 a 5)','number'),
    campo('pr','Probabilidade residual (1 a 5)','number'),campo('ir','Impacto residual (1 a 5)','number'),
    campo('controle','Controle existente','textarea'),campo('implementado','Controle implementado','bool'),E,J]),
 'confirmar_avaliacao':(3,14,S,'Confirmar avaliação proposta',[]),
 'sem_consenso':(3,14,S,'Sem consenso: encaminhar ao Comitê',[
    campo('campo','Proposta','select',(('avaliacao','Avaliação'),('triagem','Triagem de RIPD'))),
    campo('posicao','Sua posição (até 300 caracteres)','textarea')]),
 'manifestar_comite':(0,0,('relator',),'Registrar deliberação do Comitê',[
    campo('finalidade','Finalidade','select',tuple((k,v) for k,v in (
        ('avaliacao','Avaliação sem consenso'),('triagem','Triagem sem consenso'),
        ('residual','Risco residual'),('prorrogacao','Prorrogação'),('cancelamento','Cancelamento')))),
    campo('ata','Referência à ata'),campo('texto','Deliberação do colegiado','textarea'),
    campo('favoravel','Manifestação favorável','bool')]),
 'manifestar_dpo':(0,0,('dpo',),'Registrar manifestação do DPO',[campo('texto','Manifestação','textarea')]),
 'propor_triagem':(3,15,S,'Registrar proposta de triagem',[
    campo('resultado','Resultado','select',(('elaborar','Elaborar RIPD'),('revisar','Revisar RIPD'),
        ('nao_indicado','Não indicado neste momento'),('analise_adicional','Precisa de análise adicional antes de decidir'),('determinado_anpd','Determinação da ANPD'))),
    J,campo('unidade_id','Unidade que instruirá (quando houver RIPD)','unidade')]),
 'confirmar_triagem':(3,15,S,'Confirmar triagem proposta',[]),
 'aceitar_residual':(3,14,('secretario','prefeito'),'Registrar aceitação do residual',[J]),
 'concluir_avaliacao':(3,16,S,'Concluir avaliação conjunta',[]),
 'encaminhar_acao':(3,16,('aal',),'Encaminhar providência ao FORM 4',[J]),
 'confirmar_gatilho_juridico':(3,16,('aal',),'Confirmar necessidade de manifestação',[
    campo('restringe_direitos','O tratamento apoia decisão que restringe direitos?','bool')]),
 'enviar_juridico':(3,16,('aal',),'Encaminhar consulta ao Jurídico',[
    campo('destinatario_id','Participante do Jurídico','juridico'),campo('motivo','Motivo','textarea')]),
 'autorizar_referencia':(3,16,('aal',),'Autorizar consulta restrita pela autoridade do caso',[
    campo('pessoa_id','Autoridade participante','autoridade'),campo('necessidade','Necessidade de acesso','textarea')]),
 'planejar':(4,3,('secretaria',),'Registrar plano e responsável',[
    campo('plano','Plano de ação','textarea'),campo('executor_id','Executor da unidade','executor'),campo('prazo','Prazo','date')]),
 'aprovar_plano':(4,3,('secretario','prefeito'),'Aprovar plano',[J]),
 'executar_medida':(4,6,('secretaria',),'Registrar execução da medida',[E]),
 'verificar':(4,7,('verificador',),'Registrar verificação independente',[
    campo('aprovada','Verificação aprovada','bool'),E]),
 'pedir_prorrogacao':(4,4,('secretaria',),'Solicitar prorrogação',[campo('prazo','Nova data proposta','date'),J]),
 'decidir_prorrogacao':(4,4,('secretario',),'Decidir pedido de prorrogação',[
    campo('aprovar','Aprovar a prorrogação','bool'),J]),
 'pedir_cancelamento':(4,6,('secretaria',),'Solicitar cancelamento',[J]),
 'cancelar':(4,6,('secretario',),'Aprovar cancelamento',[J]),
 'aprender':(4,9,('secretaria',),'Registrar aprendizagem',[
    campo('diretriz','Diretriz de procedimento','textarea'),campo('escopo','Escopo de aplicação','textarea')]),
 'conferir_aprendizagem':(4,9,('dpo',),'Conferir aprendizagem',[
    campo('sem_dados_pessoais','Conferi a ausência de dados pessoais','bool')]),
 'autorizar_aprendizagem':(4,9,('secretaria',),'Autorizar versão para consulta',[]),
}

ATOS['revisar_avaliacao']=(*ATOS['propor_avaliacao'][:3],'Registrar revisão da proposta',ATOS['propor_avaliacao'][4])

def disponiveis(form, bloco, papeis, estado=None, pessoa_id=None, revisar=False):
    candidatos=[dict(acao=k,titulo=v[3],campos=[dict(c) for c in v[4]]) for k,v in ATOS.items()
            if v[0] in (0,form) and (v[1] in (0,bloco) or k=='sem_consenso' and bloco==15)
            and set(v[2]).intersection(papeis)]

    if estado is None:return candidatos
    from app.validacao_atos34 import obrigatorios
    lado='dpo' if 'dpo' in papeis else 'secretaria'
    saida=[]
    for a in candidatos:
        k=a['acao'];campo='triagem' if bloco==15 else 'avaliacao'
        proposta_atual=estado.get('reavaliacao',estado) if campo=='avaliacao' else estado
        confirmacoes=proposta_atual.get(campo+'_confirmacoes',{})
        confirmou=any(v['pessoa_id']==pessoa_id for v in confirmacoes.values())
        if k=='propor_triagem' and estado.get('triagem'):
            if not revisar or not confirmou or len(confirmacoes)==2 or estado.get('triagem_sem_consenso'):continue
            a['titulo']='Revisar proposta de triagem'
        if k=='propor_avaliacao' and estado.get('avaliacao'):continue
        if k=='revisar_avaliacao' and (not estado.get('avaliacao') or not revisar or proposta_atual.get('avaliacao_sem_consenso')):continue
        if k in ('confirmar_avaliacao','confirmar_triagem','sem_consenso'):
            if not proposta_atual.get(campo) or confirmou or proposta_atual.get(campo+'_sem_consenso'):continue
        if k=='aceitar_residual' and (set(estado.get('avaliacao_confirmacoes',{}))!={'secretaria','dpo'} or estado.get('aceitacao')):continue
        if k=='aceitar_residual':
            critico=estado['avaliacao']['residual']['faixa']=='Crítico'
            if critico and 'prefeito' not in papeis or not critico and 'secretario' not in papeis:continue
        if k=='manifestar_dpo' and estado.get('manifestacao_dpo'):continue
        obrig=obrigatorios(k,{})
        for c in a['campos']:
            c['obrigatorio']=c['nome'] in obrig or c['tipo']=='bool'
            c['condicional']=(c['nome']=='unidade_id' and k=='propor_triagem') or (c['nome']=='evidencia' and k in ('propor_avaliacao','revisar_avaliacao'))
        saida.append(a)
    prioridade={'propor_avaliacao':0,'revisar_avaliacao':0,'confirmar_avaliacao':1,'confirmar_triagem':1,'aceitar_residual':2}
    saida.sort(key=lambda a:prioridade.get(a['acao'],5))
    return saida


def interpretar(acao, formulario):
    if acao not in ATOS:
        raise ValueError('Ato desconhecido.')
    from app.validacao_atos34 import validar,ErrosCampos
    validar(acao,formulario)
    dados={}
    for c in ATOS[acao][4]:
        valor=formulario.get(c['nome'],'')
        if c['tipo']=='bool':
            if valor not in ('sim','nao'):
                raise ErrosCampos({c['nome']:'Escolha Sim ou Não para este campo obrigatório.'})
            valor=valor=='sim'
        elif c['tipo']=='number':
            valor=int(valor) if valor else None
        dados[c['nome']]=valor
    if acao in ('propor_avaliacao','revisar_avaliacao'):
        dados['controles']=[dict(descricao=dados.pop('controle'),implementado=dados.pop('implementado'),
                                  evidencia=dados.pop('evidencia'))]
    return dados
