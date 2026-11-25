"""Campos exigidos pelos atos; não classifica perguntas do catálogo."""
class ErrosCampos(ValueError):
    def __init__(self, erros):
        self.erros=erros
        super().__init__(' '.join(erros.values()))

OBRIGATORIOS={
 'informar_ripd':('referencia',),
 'adicionar_risco':('motivo',),
 'propor_avaliacao':('evento','causa','consequencia','justificativa'),
 'revisar_avaliacao':('evento','causa','consequencia','justificativa'),
 'sem_consenso':('campo','posicao'),
 'manifestar_comite':('finalidade','ata','texto','favoravel'),
 'manifestar_dpo':('texto',),
 'propor_triagem':('resultado','justificativa'),
 'aceitar_residual':('justificativa',), 'encaminhar_acao':('justificativa',),
 'confirmar_gatilho_juridico':('restringe_direitos',),
 'enviar_juridico':('destinatario_id','motivo'),
 'autorizar_referencia':('pessoa_id','necessidade'),
 'planejar':('plano','cargo','prazo'), 'aprovar_plano':('justificativa',),
 'solicitar_tema':('nome_sugerido','justificativa'),
 'executar_medida':('resumo','evidencia'), 'verificar':('aprovada','evidencia'),
 'pedir_prorrogacao':('prazo','justificativa'),
 'decidir_prorrogacao':('aprovar','justificativa'),
 'pedir_cancelamento':('justificativa',), 'cancelar':('justificativa',),
 'aprender':('contexto','diretriz','escopo'), 'conferir_aprendizagem':('sem_dados_pessoais',),
 'abrir_detalhes':('motivo',), 'registrar_referencia':('referencia',)
}

def obrigatorios(acao,dados):
    campos=set(OBRIGATORIOS.get(acao,()))
    if acao == 'conferir_aprendizagem' and dados.get('sem_dados_pessoais') is False:
        campos.add('observacao')
    if acao=='propor_triagem' and dados.get('resultado') in ('elaborar','revisar','determinado_anpd'):
        campos.add('unidade_id')
    return campos

def validar(acao,dados):
    erros={k:'Preencha este campo obrigatório.' for k in obrigatorios(acao,dados)
           if dados.get(k) is None or isinstance(dados.get(k),str) and not dados[k].strip()}
    if acao in ('propor_avaliacao','revisar_avaliacao'):
        try:
            numeros=[int(dados[k]) for k in ('p','i','pr','ir')]
        except (ValueError,TypeError,KeyError):numeros=[]
        if numeros and numeros[2]*numeros[3]<numeros[0]*numeros[1]:
            evidencias=[c.get('evidencia','') for c in dados.get('controles',[]) if isinstance(c,dict)] if 'controles' in dados else [dados.get('evidencia','')]
            if not any(isinstance(v,str) and v.strip() for v in evidencias):erros['evidencia']='Redução residual exige controle implementado e evidência.'
    if erros:raise ErrosCampos(erros)
