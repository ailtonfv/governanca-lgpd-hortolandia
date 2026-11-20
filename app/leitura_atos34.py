"""Leitura dos atos preservados. Não executa comandos nem altera eventos."""
from app.apresentacao_form2 import data_local

RESULTADOS = {'elaborar':'Elaborar RIPD', 'revisar':'Revisar RIPD',
    'nao_indicado':'Não indicado neste momento',
    'analise_adicional':'Precisa de análise adicional antes de decidir',
    'determinado_anpd':'Determinação da ANPD'}
NOMES = {
    'informar_ripd':'Referência do RIPD informada', 'propor_avaliacao':'Proposta de avaliação registrada', 'revisar_avaliacao':'Nova proposta de avaliação registrada',
    'confirmar_avaliacao':'Nota conjunta confirmada', 'propor_triagem':'Proposta de triagem registrada',
    'confirmar_triagem':'Triagem confirmada', 'manifestar_dpo':'Manifestação do DPO registrada',
    'manifestar_comite':'Deliberação do Comitê registrada', 'aceitar_residual':'Aceitação do residual registrada',
    'sem_consenso':'Ausência de consenso registrada', 'concluir_avaliacao':'Avaliação concluída',
    'encaminhar_acao':'Providência encaminhada', 'planejar':'Plano registrado', 'aprovar_plano':'Plano aprovado',
    'executar_medida':'Execução registrada', 'verificar':'Verificação registrada',
    'pedir_prorrogacao':'Prorrogação solicitada', 'decidir_prorrogacao':'Prorrogação decidida',
    'pedir_cancelamento':'Cancelamento solicitado', 'cancelar':'Cancelamento aprovado',
    'aprender':'Aprendizagem registrada', 'conferir_aprendizagem':'Aprendizagem conferida',
    'autorizar_aprendizagem':'Aprendizagem autorizada', 'ingresso':'Ingresso registrado',
    'encerramento_automatico':'Ação concluída', 'abrir_detalhes':'Detalhes do bloco mantidos visíveis',
    'confirmar_gatilho_juridico':'Necessidade de manifestação registrada',
    'enviar_juridico':'Consulta encaminhada ao Jurídico', 'autorizar_referencia':'Consulta restrita autorizada',
    'referencia_registrada':'Referência jurídica registrada', 'adicionar_risco':'Novo risco registrado',
    'ciencia_prefeito':'Ciência ao Prefeito registrada'}

def horario(valor):
    return str(data_local(valor)) if valor else 'data não disponível'

def proposta(e, campo, autores, unidades, eventos=()):
    valor=e.get(campo)
    if not valor:return None
    confirmacoes=e.get(campo+'_confirmacoes',{})
    # A proposta mais recente traz autor/data mesmo após deliberação ou confirmação.
    ev=next((x for x in eventos if x.tipo_evento in ('f34_propor_'+campo,'f34_revisar_'+campo)),None)
    p=e.get(campo+'_proponente') or {}
    if not p and ev:
        ce=(ev.conteudo.get('estado') or {}).get(campo+'_confirmacoes',{})
        p=next((dict(v,lado=k) for k,v in ce.items()),{})
    if not p:p=next((dict(v,lado=k) for k,v in confirmacoes.items()),{})
    linhas=[]
    if campo=='triagem':
        linhas=[('Resultado',RESULTADOS.get(valor.get('resultado'),valor.get('resultado',''))),
                ('Unidade',unidades.get(valor.get('unidade_id'),'Não indicada para este resultado')),
                ('Justificativa',valor.get('justificativa',''))]
    else:
        from app.apresentacao_forms34 import descricao_nota34
        linhas=[('Evento',e.get('evento','')),('Causa',e.get('causa','')),('Consequência para o titular',e.get('consequencia',''))]
        for tipo in ('inerente','residual'):
            av=valor.get(tipo,{})
            linhas.extend([(tipo.capitalize()+' — probabilidade',descricao_nota34(av.get('probabilidade'),'probabilidade')),
                           (tipo.capitalize()+' — impacto',descricao_nota34(av.get('impacto'),'impacto')),
                           (tipo.capitalize()+' — nota',f"{av.get('nota')} — {av.get('faixa')}")])
        linhas += [('Controle',f"{c.get('descricao','')} · Implementado: {'Sim' if c.get('implementado') else 'Não'} · Evidência: {c.get('evidencia','')}") for c in valor.get('controles',[])]
        linhas.append(('Justificativa',valor.get('justificativa','')))
    lado='DPO' if p.get('lado')=='dpo' else 'Secretaria'
    confirmado=set(confirmacoes)=={'secretaria','dpo'}
    data=max((v.get('em','') for v in confirmacoes.values()),default='') if confirmado else p.get('em')
    if e.get(campo+'_sem_consenso'):
        status='Sem consenso — aguardando deliberação do Comitê'
    elif confirmado:
        status=('Triagem' if campo=='triagem' else 'Nota conjunta')+' confirmada pela Secretaria e pelo DPO em '+horario(data)
    else:
        status=('Triagem' if campo=='triagem' else 'Avaliação')+f" proposta {'pelo DPO' if lado=='DPO' else 'pela Secretaria'} em {horario(data)} · aguardando confirmação {'da Secretaria' if lado=='DPO' else 'do DPO'}"
    if campo=='triagem':
        status+=': '+RESULTADOS.get(valor.get('resultado'),'')
        if valor.get('unidade_id'):status+=', instruído por '+unidades.get(valor['unidade_id'],'unidade registrada')
    return dict(titulo='Proposta de '+('triagem' if campo=='triagem' else 'avaliação'),linhas=linhas,
                autor=autores.get(p.get('pessoa_id'),'Autor registrado'),quando=horario(p.get('em')),
                lado=lado,pessoa_id=p.get('pessoa_id'),status=status,confirmada=confirmado,data_nota=horario(data))

def conteudo_ato(acao,e,autores,unidades):
    """Lista explícita; nunca expor referência jurídica restrita nem estado bruto."""
    if acao in ('revisar_avaliacao','sem_consenso') and e.get('reavaliacao'):e=e['reavaliacao']
    chaves={'manifestar_dpo':'manifestacao_dpo','manifestar_comite':'manifestacao_comite',
            'aceitar_residual':'aceitacao','aprovar_plano':'plano_aprovado','executar_medida':'execucao',
            'verificar':'verificacao','cancelar':'cancelada','aprender':'aprendizagem',
            'informar_ripd':'referencia_ripd','conferir_aprendizagem':'aprendizagem_conferida','autorizar_aprendizagem':'aprendizagem_autorizada'}
    if acao in ('propor_avaliacao','revisar_avaliacao','confirmar_avaliacao','propor_triagem','confirmar_triagem'):
        p=proposta(e,'triagem' if 'triagem' in acao else 'avaliacao',autores,unidades)
        return p['linhas'] if p else []
    if acao=='sem_consenso':
        return [(('DPO' if lado=='dpo' else 'Secretaria')+' — '+('Avaliação' if campo=='avaliacao' else 'Triagem'), texto)
                for campo in ('avaliacao','triagem') for lado,texto in e.get(campo+'_posicoes',{}).items()]
    valor=e.get(chaves.get(acao,''),{})
    if acao=='aprender':valor={**valor, 'contexto':valor.get('contexto','Não informado')}
    if acao=='executar_medida':valor={**valor, 'resumo':valor.get('resumo','Não informado'),
                                    'cargo_responsavel':valor.get('cargo_responsavel') or 'Cargo não informado no ato anterior'}
    if acao=='manifestar_comite' and e.get('reavaliacao',{}).get('manifestacao_comite'):valor=e['reavaliacao']['manifestacao_comite']
    if acao=='planejar':valor={k:e.get(k) for k in ('plano','executor_id','cargo_responsavel','unidade_responsavel_id','prazo')}
    if acao.startswith('pedir_'):valor=e.get('decisoes_pendentes',{}).get(acao.removeprefix('pedir_'),{})
    nomes={'contexto':'Contexto (relato impessoal)','resumo':'Resumo do que foi feito','texto':'Texto','justificativa':'Justificativa','ata':'Referência à ata','finalidade':'Finalidade',
           'favoravel':'Favorável','evidencia':'Evidência','aprovada':'Aprovada','plano':'Plano',
           'executor_id':'Executor registrado no ato anterior','cargo_responsavel':'Cargo responsável','unidade_responsavel_id':'Unidade responsável','referencia':'Referência do RIPD','documento':'Documento formal da decisão','prazo':'Prazo','diretriz':'Diretriz','escopo':'Escopo'}
    from app.regras_atos34 import FINALIDADES
    from app.apresentacao_atos34 import data_br
    return [(rotulo,autores.get(v,v) if k=='executor_id' else unidades.get(v,v) if k=='unidade_responsavel_id' else FINALIDADES.get(v,v) if k=='finalidade' else data_br(v) if k=='prazo' else 'Sim' if v is True else 'Não' if v is False else v)
            for k,rotulo in nomes.items() if (v:=valor.get(k)) is not None]

def historico_visual(eventos, autores, unidades, mapa_blocos, identidade=None, referencia=None):
    saida=[];anterior={}
    for ev in reversed(eventos):
        acao=ev.tipo_evento.removeprefix('f34_'); e=ev.conteudo.get('estado',{})
        nome=NOMES.get(acao, 'Registro de '+acao.replace('_',' '))
        if ev.tipo_evento == 'base34_identidade_reservada' and identidade:
            codigo=identidade.codigo.split('-')[-1]
            nome=f"{'Risco' if identidade.tipo=='R' else 'Ação'} criado (identificador {codigo} reservado)"
        if acao == 'ingresso' and referencia:
            if e.get('form') == 3:
                nome=f'Risco recebido no FORM 3, encaminhado pelo FORM 2 (versão {referencia.fonte_versao})'
            else:
                nome=f'Ação recebida no FORM 4, encaminhada pelo FORM {referencia.fonte_form}'
        if acao=='salvar_bloco':
            respostas=e.get('respostas',{});ant=anterior.get('respostas',{})
            blocos=sorted({mapa_blocos[k] for k in respostas if respostas[k]!=ant.get(k) and k in mapa_blocos})
            nome=('Bloco '+str(blocos[0])+' salvo') if len(blocos)==1 else ('Blocos '+', '.join(map(str,blocos))+' salvos') if blocos else 'Bloco salvo sem alteração de respostas'
        if acao in ('aceitar_residual','aprovar_plano'):
            d=e.get('aceitacao' if acao=='aceitar_residual' else 'plano_aprovado',{})
            if d.get('registrador')=='Gabinete':nome=f"Decisão do Prefeito, registrada pelo Gabinete em {horario(d['em'])}, conforme {d['documento']}"
        if e:anterior=e
        saida.append(dict(id=ev.id,comando_id=ev.comando_id,nome=nome,acao=acao,
                          ato=acao not in ('salvar_bloco','abrir_detalhes') and ev.tipo_evento.startswith('f34_'),
                          autor=autores.get(ev.ator_id,ev.ator_id),quando=horario(ev.ocorrido_em),
                          linhas=conteudo_ato(acao,e,autores,unidades)))
    return list(reversed(saida))

def situacao_bloco(form,n,e):
    if form==3 and n in (14,15):
        campo='avaliacao' if n==14 else 'triagem';c=e.get(campo+'_confirmacoes',{})
        if e.get(campo+'_sem_consenso'):return 'Sem consenso · aguardando Comitê'
        if set(c)=={'secretaria','dpo'}:return ('Nota conjunta vigente · reavaliação sem consenso' if e.get('reavaliacao',{}).get('avaliacao_sem_consenso') else 'Nota conjunta vigente · reavaliação em andamento' if e.get('reavaliacao') else 'Nota conjunta confirmada') if n==14 else 'Triagem confirmada'
        if e.get(campo):return 'Proposta registrada · aguardando '+('Secretaria' if 'dpo' in c else 'DPO')
        return 'Aguardando avaliação' if n==14 else 'Aguardando triagem'
    if form==3 and n==16:return 'Avaliação concluída' if e.get('concluida') else 'Aguardando conclusão'
    if form==4:
        if n==9:
            from app.etapas_forms34 import situacao_aprendizagem
            return situacao_aprendizagem(e)
        return {3:'Plano aprovado' if e.get('plano_aprovado') else 'Plano registrado · aguardando aprovação' if e.get('plano') else 'Aguardando plano',
                4:'Prorrogação aguardando decisão' if e.get('decisoes_pendentes',{}).get('prorrogacao') else '',
                6:'Cancelamento aprovado' if e.get('cancelada') else 'Execução registrada' if e.get('execucao') else 'Aguardando execução',
                7:'Verificação aprovada' if e.get('verificada') else 'Verificação requer ajuste' if e.get('verificacao') else 'Aguardando verificação',
                9:'Aprendizagem autorizada' if e.get('aprendizagem_autorizada') else 'Aprendizagem conferida' if e.get('aprendizagem_conferida') else 'Aprendizagem registrada' if e.get('aprendizagem') else 'Aguardando aprendizagem'}.get(n,'')
    return ''


def situacao_atual(e):
    if e.get('form')==3:
        if e.get('concluida'):return e['situacao']
        if e.get('triagem') or e.get('triagem_sem_consenso'):return situacao_bloco(3,15,e)
        if e.get('avaliacao') or e.get('avaliacao_sem_consenso'):return situacao_bloco(3,14,e)
    return e.get('situacao','Em preenchimento')
