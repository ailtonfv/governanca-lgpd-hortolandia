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
 'sem_consenso':(3,14,S,'Registrar divergência e encaminhar ao Comitê',[
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
        ('nao_indicado','Não indicado neste momento'),('analise_adicional','Análise adicional'),('determinado_anpd','Determinação da ANPD'))),
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


def disponiveis(form, bloco, papeis):
    return [dict(acao=k,titulo=v[3],campos=v[4]) for k,v in ATOS.items()
            if v[0] in (0,form) and (v[1] in (0,bloco) or k=='sem_consenso' and bloco==15)
            and set(v[2]).intersection(papeis)]


def interpretar(acao, formulario):
    if acao not in ATOS:
        raise ValueError('Ato desconhecido.')
    dados={}
    for c in ATOS[acao][4]:
        valor=formulario.get(c['nome'],'')
        if c['tipo']=='bool':
            if valor not in ('sim','nao'):
                raise ValueError('Selecione Sim ou Não explicitamente.')
            valor=valor=='sim'
        elif c['tipo']=='number':
            valor=int(valor) if valor else None
        dados[c['nome']]=valor
    if acao=='propor_avaliacao':
        dados['controles']=[dict(descricao=dados.pop('controle'),implementado=dados.pop('implementado'),
                                  evidencia=dados.pop('evidencia'))]
    return dados
