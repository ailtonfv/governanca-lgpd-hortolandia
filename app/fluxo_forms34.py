"""Atos demonstrativos dos FORMs 3/4. Decisões 18/11 + complemento 11-B.

Estado derivado exclusivamente de eventos; transação e bloqueio por Registro.
Nenhum ato é concedido por um campo enviado pelo navegador.
"""
from app.obrigatoriedade_forms import conferencia_participacao, conferencia34, retrato, exigir as exigir_r17
from copy import deepcopy
from datetime import date
from uuid import uuid4, uuid5, NAMESPACE_URL
from sqlalchemy import select, func
from app.modelos import (ReferenciaParticipacaoForms34 as Referencia, IdentidadeForms34,
                         Evento, ParticipacaoForm2, Pessoa)
from app.infra_forms34 import _atomica, _abrir, _registro, historico
from app.base_forms34 import fixar_referencia, reservar_identidade
from app.comandos import fechar_comando
from app.eventos import agora_utc, verificar_cadeia
from app.fila_form2 import pessoa_ativa, autorizado, evento as evento_form2
from app.permissoes_forms34 import contexto, exigir
from app.avaliacao_risco34 import propor_avaliacao, exige_triagem


def _gravar(sessao, cmd, cadeia, cadeia_id, registro_id, tipo, dados):
    from app.eventos import registrar_evento, registrar_auditoria
    ordem = (sessao.scalar(select(func.max(Evento.ordem_no_comando)).where(
        Evento.comando_id == cmd.id)) or 0) + 1
    ev = registrar_evento(sessao, cmd, cadeia, cadeia_id, tipo, dados,
        registro_id=registro_id, ordem_no_comando=ordem, versao_regra='FORMS34-DEMO-v1')
    registrar_auditoria(sessao, tipo, 'pessoa', cmd.ator_id,
        {'registro_id': registro_id, 'objeto_id': cadeia_id}, comando_id=cmd.id)
    return ev


def _texto(d, chave, limite=1000):
    valor = d.get(chave)
    if not isinstance(valor, str) or not 1 <= len(valor.strip()) <= limite:
        raise ValueError(f'Informe {chave.replace("_", " ")} em até {limite} caracteres.')
    return valor.strip()


def _subchave(comando_id, sufixo):
    return str(uuid5(NAMESPACE_URL, str(comando_id) + '/' + sufixo))


def estado(sessao, identidade_id):
    eventos = historico(sessao, identidade_id)
    if not eventos:
        raise ValueError('Objeto inexistente.')
    if not verificar_cadeia(sessao, identidade_id)[0]:
        raise ValueError('Histórico divergente.')
    dados = next((deepcopy(e.conteudo['estado']) for e in reversed(eventos)
                  if e.tipo_evento.startswith('f34_') and 'estado' in e.conteudo), None)
    if dados is None:
        raise ValueError('Identidade técnica sem ingresso autorizado.')
    if dados.get('form')==3:
        dados['respostas']={k:('A confirmar' if v=='Requer análise' else ['A confirmar' if x=='Requer análise' else x for x in v] if isinstance(v,list) else v) for k,v in dados.get('respostas',{}).items()}
    dados['versao'] = eventos[-1].sequencia_cadeia
    return dados


def consultar(sessao, conta_id, identidade_id):
    obj = sessao.get(IdentidadeForms34, identidade_id)
    if not obj:
        raise ValueError('Objeto inexistente.')
    ref = sessao.get(Referencia, obj.participacao_id)
    pessoa, papeis, uid = contexto(sessao, conta_id, ref)
    exigir(papeis, 'secretaria', 'dpo', 'secretario', 'gabinete', 'verificador', 'relator', 'executor_unidade', 'leitor_unidade')
    from app.condicoes_aceitacao34 import enriquecer
    from app.criterios_form3 import projetar_guarda
    return obj, ref, projetar_guarda(sessao,ref,enriquecer(sessao, estado(sessao, obj.id))), pessoa, papeis, uid


def _gravar_estado(sessao, comando, obj, acao, e):
    ev = _gravar(sessao, comando, 'forms34_objeto', obj.id, obj.registro_id,
                 'f34_' + acao, {'estado': deepcopy(e)})
    return ev


def _criar(sessao, comando, conta_id, registro_id, form, fonte_form, fonte_id, chave, inicial):
    refid = str(uuid5(NAMESPACE_URL, f'forms34/{registro_id}/{form}/{chave}'))
    fixar_referencia(sessao, comando_id=_subchave(comando.id, 'ref:'+refid), conta_id=conta_id,
                     participacao_id=refid, registro_id=registro_id, form=form,
                     fonte_form=fonte_form, fonte_id=str(fonte_id))
    reservado = reservar_identidade(sessao, comando_id=_subchave(comando.id, 'identidade:'+refid),
        conta_id=conta_id, participacao_id=refid, tipo='R' if form == 3 else 'A', chave_origem=chave)
    obj = sessao.get(IdentidadeForms34, reservado['identidade_id'])
    if not reservado['existente']:
        _gravar_estado(sessao, comando, obj, 'ingresso', inicial)
    return obj


def sinais_form2(conteudo):
    from app.form2_rev212 import indice_valores
    r = indice_valores(conteudo)
    # Identificadores categóricos: nunca busca palavras em texto livre.
    return [k for k in ('F2-4.1', 'F2-6.1', 'F2-7.1', 'F2-9.7.1')
            if any(v in ('Sim', 'SIM') for v in r.get('opcao:' + k, []))]


@_atomica
def ingressar(sessao, *, conta_id, comando_id, participacao_id, versao, form, justificativa=''):
    p = sessao.get(ParticipacaoForm2, participacao_id)
    pessoa = pessoa_ativa(sessao, conta_id)
    if not p:
        raise ValueError('Participação inexistente.')
    _registro(sessao, p.registro_id)
    sessao.refresh(p, with_for_update=True)
    if (p.tipo != 'principal' or p.responsavel_id != pessoa.id or
            not (p.estado == 'em_atendimento' or p.estado == 'concluida' and (p.conteudo or {}).get('conclusao_analise')) or not autorizado(sessao, pessoa, p)):
        raise PermissionError('Somente o AAL responsável encaminha pelos itens F2-14.5/14.6.')
    dados = dict(participacao_id=p.id, versao=versao, form=form, justificativa=justificativa)
    cmd, repeticao = _abrir(sessao, comando_id, conta_id, 'f34_ingressar', dados)
    if repeticao is not None:
        return repeticao
    if type(form) is not int or form not in (3,4):
        from app.validacao_atos34 import ErrosCampos
        raise ErrosCampos({'form':'Escolha para onde encaminhar: Riscos (FORM 3) ou Providência (FORM 4).'})
    if p.versao != versao:
        raise ValueError('Instrumento ou versão inválida. Atualize a página.')
    from app.form2_rev212 import indice_valores
    respostas = indice_valores(p.conteudo or {})
    item = 'F2-14.5' if form == 3 else 'F2-14.6'
    if not any(v in ('Sim', 'SIM') for v in respostas.get('opcao:' + item, [])):
        raise ValueError(f'Confirme {item} no FORM 2 antes deste ato.')
    sinais = sinais_form2(p.conteudo or {})
    from app.origem_form2 import ler_origem
    from app.clausulas_lgpd import guarda_fornecedor
    fornecedor=guarda_fornecedor(ler_origem(sessao,p.registro_id,p.snapshot_id)['conteudo'].get('respostas',{}))
    from app.gatilhos_juridicos34 import motivos
    gatilhos = motivos(p.conteudo or {})
    if form == 4 and sinais and not any(v in ('Sim', 'SIM') for v in respostas.get('opcao:F2-14.5', [])):
        if not isinstance(justificativa,str) or not justificativa.strip():
            from app.validacao_atos34 import ErrosCampos
            raise ErrosCampos({'justificativa':'Informe a justificativa para encaminhar diretamente apesar do sinal de risco.'})
        _texto({'justificativa': justificativa}, 'justificativa')
    r17 = exigir_r17(conferencia_participacao(sessao,p), f'/form2/participacoes/{p.id}/blocos')
    p.conteudo = {**(p.conteudo or {}), 'conferencia_r17':r17}
    # Um novo evento fonte contém a versão exata, antes de criar o contexto 3/4.
    evento_form2(sessao, cmd, p, 'form2_encaminhamento34')
    fonte = sessao.scalar(select(Evento).where(Evento.comando_id == cmd.id,
        Evento.cadeia_tipo == 'participacao_form2').order_by(Evento.id.desc()))
    chave = f'f2:{p.id}:v{p.versao}:f{form}'
    existente = sessao.scalar(select(IdentidadeForms34).where(
        IdentidadeForms34.registro_id == p.registro_id, IdentidadeForms34.chave_origem == chave))
    if existente:
        raise ValueError('Esta versão já foi encaminhada; consulte o objeto existente.')
    obj = _criar(sessao, cmd, conta_id, p.registro_id, form, 2, fonte.id, chave,
        dict(form=form, respostas={}, respostas_fornecedor={k.removeprefix('opcao:'):v for k,v in respostas.items() if fornecedor and k.startswith('opcao:F2-9F.')},fornecedor_guarda_dados=fornecedor, sinais=sinais, sinais_origem=sinais, origem_form2_id=p.id, situacao_form2=p.estado,
             decisao_nao_encaminhar=justificativa, situacao='Em preenchimento',
             avaliacao=None, confirmacoes={}, triagem=None, triagem_confirmacoes={},
             prorrogacoes=0, prazo=None, executor_id=None, decisoes_pendentes={},
             juridico='manifestação jurídica esperada' if gatilhos else 'não solicitado',
             motivos_juridicos=gatilhos, escopos_restritos=[]))
    return fechar_comando(cmd, {'permitido': True, 'identidade_id': obj.id})


def _lado(papeis):
    # DPO não se torna Secretaria mesmo com designação acumulada.
    if 'dpo' in papeis:
        return 'dpo'
    exigir(papeis, 'secretaria')
    return 'secretaria'


def _consenso(e, campo):
    return set(e.get(campo + '_confirmacoes', {})) == {'secretaria', 'dpo'}


def _confirmar(e, campo, pessoa_id, papeis, agora):
    lado = _lado(papeis)
    confirmacoes = e.setdefault(campo + '_confirmacoes', {})
    if not e.get(campo):
        raise ValueError('Registre a proposta antes de confirmar.')
    if e.get(campo + '_sem_consenso'):
        raise ValueError('Sem consenso: aguarda deliberação registrada pelo Relator.')
    if any(c['pessoa_id'] == pessoa_id for l, c in confirmacoes.items() if l != lado):
        raise PermissionError('As confirmações exigem pessoas distintas.')
    if any(c['pessoa_id']==pessoa_id for c in confirmacoes.values()):
        raise PermissionError('Quem propôs ou já confirmou não confirma novamente; aguarde o outro lado.')
    confirmacoes[lado] = dict(pessoa_id=pessoa_id, em=agora)


def _faixa(e):
    a = e.get('avaliacao')
    return a['residual']['faixa'] if a and _consenso(e, 'avaliacao') else e.get('faixa_origem', 'Não avaliado')


def _pareceres(e, faixa):
    if faixa in ('Alto', 'Crítico') and not e.get('manifestacao_dpo'):
        raise ValueError('Aguarda manifestação prévia do DPO.')
    residual = e.get('deliberacoes_rodada', {}).get('residual') or e.get('manifestacao_comite', {})
    if faixa == 'Crítico' and residual.get('finalidade') != 'residual':
        raise ValueError('Aguarda manifestação do Comitê registrada pelo Relator.')


def _sem_pendencia(e):
    return not e.get('decisoes_pendentes')


def em_atraso(e, hoje=None):
    if not e.get('prazo') or e.get('verificada') or e.get('cancelada'):
        return False
    return date.fromisoformat(e['prazo']) < (hoje or date.today())


@_atomica
def executar(sessao, *, conta_id, comando_id, identidade_id, versao, acao, dados):
    obj, ref, e, pessoa, papeis, uid = consultar(sessao, conta_id, identidade_id)
    _registro(sessao, obj.registro_id)
    e = estado(sessao, obj.id)
    from app.condicoes_aceitacao34 import enriquecer
    enriquecer(sessao,e)
    from app.criterios_form3 import projetar_guarda
    projetar_guarda(sessao,ref,e)
    cmd, repeticao = _abrir(sessao, comando_id, conta_id, 'f34_ato',
        dict(identidade_id=obj.id, versao=versao, acao=acao, dados=dados))
    if repeticao is not None:
        return repeticao
    if type(versao) is not int or versao != e.pop('versao'):
        raise ValueError('O Registro mudou. Atualize antes de confirmar.')
    if not isinstance(dados, dict):
        raise ValueError('Dados inválidos.')
    from app.validacao_atos34 import validar
    validar(acao,dados)
    agora = agora_utc().isoformat()
    f3 = e['form'] == 3
    from app.etapas_forms34 import motivo_bloqueio, conferencia_etapa, validar_verificacao
    if f3 and e.get('conclusao') and acao not in ('revisar_avaliacao', 'informar_ripd', 'confirmar_ripd'):
        raise ValueError('Avaliação concluída: use Reavaliar o risco para abrir uma nova rodada.')
    if 'dpo' in papeis and acao in ('aceitar_residual','aprovar_plano','decidir_prorrogacao','cancelar','executar_medida','verificar'):
        raise PermissionError('O DPO não exerce estes atos de autoridade, execução ou verificação.')
    if acao in ('propor_avaliacao', 'revisar_avaliacao', 'confirmar_avaliacao', 'propor_triagem', 'confirmar_triagem',
                'sem_consenso', 'aceitar_residual', 'concluir_avaliacao', 'encaminhar_acao', 'informar_ripd', 'confirmar_ripd') and not f3:
        raise ValueError('Ato exclusivo do FORM 3.')
    if acao in ('planejar', 'aprovar_plano', 'executar_medida', 'verificar', 'pedir_prorrogacao',
                'decidir_prorrogacao', 'pedir_cancelamento', 'cancelar', 'aprender',
                'conferir_aprendizagem', 'autorizar_aprendizagem', 'salvar_temas', 'solicitar_tema',
                'propor_residual_acao', 'confirmar_residual_acao', 'decidir_residual_acao', 'aceitar_residual_acao') and f3:
        raise ValueError('Ato exclusivo do FORM 4.')
    if e.get('cancelada') or e.get('encerrada'):
        permitidos = ('aprender', 'conferir_aprendizagem', 'autorizar_aprendizagem')
        if not e.get('cancelada'):
            permitidos += ('propor_residual_acao', 'confirmar_residual_acao', 'decidir_residual_acao', 'aceitar_residual_acao', 'manifestar_dpo', 'manifestar_comite')
        if acao not in permitidos:
            raise ValueError('Ação encerrada; seu histórico permanece preservado.')
    destino_id = obj.id
    if acao in ('conferir_aprendizagem', 'autorizar_aprendizagem'):
        from app.encerramento_form4 import pode_encerrar
        if not pode_encerrar(e) or e.get('condicoes_abertas'):
            raise ValueError('Aguarda decisão sobre o risco residual após a ação antes da aprendizagem.')
    if acao == 'adicionar_risco':
        if not f3:
            raise ValueError('Novo risco exige origem no FORM 3.')
        exigir(papeis,'secretaria','dpo')
        if not f3:raise ValueError('Risco pertence ao FORM 3.')
        motivo = _texto(dados,'motivo',300)
        r = reservar_identidade(sessao,comando_id=_subchave(cmd.id,'novo_risco'),conta_id=conta_id,
            participacao_id=ref.id,tipo='R',chave_origem='risco:'+cmd.id)
        novo=sessao.get(IdentidadeForms34,r['identidade_id'])
        inicial=dict(form=3,respostas={},sinais=list(e.get('sinais',[])),origem_form2_id=e.get('origem_form2_id'),
            situacao_form2=e.get('situacao_form2'),situacao='Em preenchimento',avaliacao=None,
            avaliacao_confirmacoes={},triagem=None,triagem_confirmacoes={},juridico='não solicitado',
            escopos_restritos=[],motivo=motivo)
        from app.contexto_novo_risco import copiar
        inicial.update(copiar(dict(e,versao=versao),obj.codigo.split('-')[-1]))
        _gravar_estado(sessao,cmd,novo,'ingresso',inicial)
        destino_id=novo.id
    elif acao == 'salvar_bloco':
        exigir(papeis, 'secretaria', 'dpo')
        from app.etapas_forms34 import pode_preencher
        if not pode_preencher(e['form'], papeis):
            raise PermissionError('As perguntas do FORM 4 são preenchidas pela Secretaria; o DPO realiza seus atos próprios.')
        bloqueio = motivo_bloqueio(e, dados.get('bloco'))
        if bloqueio:
            raise ValueError(bloqueio)
        from app.questionario_forms34 import salvar
        anteriores=e.get('respostas',{})
        novas=salvar(e['form'], anteriores, dados, e)
        e['contexto_copiado']={k:v for k,v in e.get('contexto_copiado',{}).items() if novas.get(k)==anteriores.get(k)}
        e['respostas'] = novas
        if f3 and 'F3-3.46' in dados.get('campos',{}):e['revisao_texto_346']=True
        if not f3 and dados.get('bloco')==2:
            from app.clausulas_lgpd import validar4
            e['clausulas_contrato']=validar4(novas,dados.get('clausulas_contrato',{}),e.get('fornecedor_guarda_dados',False))
        if f3 and dados.get('bloco') == 13:
            from app.lacunas_form3 import salvar_controles
            salvar_controles(e, dados)
        complementos=dados.get('complementos',{})
        if not isinstance(complementos,dict) or set(complementos)-set(dados.get('campos',{})) or any(not isinstance(v,str) or len(v)>200 for v in complementos.values()):raise ValueError('Complemento inválido.')
        e.setdefault('complementos',{}).update(complementos)
        if f3:
            e['sinais'] = sorted(set(e.get('sinais_origem', [])) | ({'F3-3.10'} if e['respostas'].get('F3-3.10') else set()) |
                ({'F3-3.54'} if e['respostas'].get('F3-3.54') in ('Sim','Requer análise','A confirmar') else set()))
    elif acao == 'abrir_detalhes':
        exigir(papeis, 'secretaria', 'dpo')
        bloco = dados.get('bloco')
        if type(bloco) is not int or not 1 <= bloco <= (16 if f3 else 9):
            raise ValueError('Bloco inválido.')
        e.setdefault('aberturas', {})[str(bloco)] = _texto(dados, 'motivo', 300)
    elif acao in ('propor_avaliacao','revisar_avaliacao'):
        if acao=='propor_avaliacao' and e.get('avaliacao'):
            raise ValueError('Para corrigir a avaliação registrada, use Revisar proposta.')
        if acao=='revisar_avaliacao' and not e.get('avaliacao'):
            raise ValueError('Ainda não há proposta para revisar.')
        vigente = _consenso(e, 'avaliacao')
        alvo = e.get('reavaliacao', {}) if vigente else e
        if alvo.get('avaliacao_sem_consenso'):
            raise ValueError('Sem consenso: aguarda deliberação do Comitê antes de reapresentar.')
        lado = _lado(papeis)
        if acao == 'revisar_avaliacao':e['revisao_aberta'] = True
        nova = dict(evento=_texto(dados, 'evento'), causa=_texto(dados, 'causa'),
            consequencia=_texto(dados, 'consequencia'), avaliacao=propor_avaliacao(dados),
            avaliacao_proponente=dict(lado=lado,pessoa_id=pessoa.id,em=agora),
            avaliacao_confirmacoes={lado:dict(pessoa_id=pessoa.id,em=agora)}, avaliacao_sem_consenso=False)
        if vigente:
            # Proposta separada: nenhum consumidor da avaliação vigente muda antes do consenso.
            e['reavaliacao'] = nova
            if e.get('conclusao'):
                e.setdefault('conclusoes_anteriores', []).append(e.pop('conclusao'))
            e['concluida'] = False
            e['revisao_aberta'] = True
        else:
            e.update(nova)
            for k in ('aceitacao', 'manifestacao_dpo', 'manifestacao_comite', 'triagem'):
                e.pop(k, None)
            e['triagem_confirmacoes'] = {}
            e['situacao'] = 'Aguardando DPO' if lado == 'secretaria' else 'Aguardando Secretaria'
    elif acao in ('confirmar_avaliacao', 'confirmar_triagem'):
        campo = acao.removeprefix('confirmar_')
        alvo = e.get('reavaliacao', e) if campo=='avaliacao' else e
        if _consenso(alvo, campo):
            raise ValueError('Resultado conjunto já confirmado. Use Reavaliar o risco.')
        _confirmar(alvo, campo, pessoa.id, papeis, agora)
        if alvo is not e and _consenso(alvo, 'avaliacao'):
            e.update(e.pop('reavaliacao'))
            # Mesmo tratamento dos atos dependentes já existente na substituição da nota.
            for k in ('aceitacao', 'manifestacao_dpo', 'manifestacao_comite', 'triagem'):
                e.pop(k, None)
            e['triagem_confirmacoes'] = {}
            e['deliberacoes_rodada'] = {}
            e['acoes_rodada'] = []
        e['situacao'] = 'Avaliação conjunta registrada' if _consenso(e, campo) else 'Aguardando confirmação'
    elif acao == 'sem_consenso':
        campo = dados.get('campo')
        if campo not in ('avaliacao', 'triagem'):
            raise ValueError('Indique a proposta em discussão.')
        alvo = e.get('reavaliacao', e) if campo=='avaliacao' else e
        if _consenso(alvo, campo):
            raise ValueError('Resultado conjunto já confirmado. Use Reavaliar o risco.')
        if not alvo.get(campo):raise ValueError('Indique a proposta em discussão.')
        lado = _lado(papeis)
        if any(c['pessoa_id']==pessoa.id for c in alvo.get(campo+'_confirmacoes',{}).values()):
            raise PermissionError('Quem propôs deve revisar a proposta; o outro lado registra a ausência de consenso.')
        alvo.setdefault(campo + '_posicoes', {})[lado] = _texto(dados, 'posicao', 300)
        alvo[campo + '_sem_consenso'] = True
        alvo[campo + '_confirmacoes'] = {}
        if alvo is e:e['situacao'] = 'Sem consenso — encaminhado ao Comitê'
    elif acao == 'manifestar_comite':
        exigir(papeis, 'relator')
        if papeis.intersection(('verificador', 'dpo')):
            raise PermissionError('Relator distinto do verificador e do DPO.')
        finalidade = dados.get('finalidade')
        from app.regras_atos34 import finalidades
        if finalidade not in finalidades(e):
            raise ValueError('Finalidade da manifestação inválida.')
        m = dict(ata=_texto(dados, 'ata', 200), texto=_texto(dados, 'texto'),
                 favoravel=dados.get('favoravel') is True, finalidade=finalidade,
                 pessoa_id=pessoa.id, em=agora)
        alvo_deliberacao = e.get('reavaliacao', e) if finalidade == 'avaliacao' else e
        alvo_deliberacao.setdefault('deliberacoes_rodada', {})[finalidade] = m
        if finalidade=='avaliacao' and e.get('reavaliacao',{}).get('avaliacao_sem_consenso'):
            e['reavaliacao']['manifestacao_comite'] = m
            e['reavaliacao']['avaliacao_sem_consenso'] = False
        else:
            e['manifestacao_comite'] = m
        if finalidade in ('avaliacao', 'triagem') and e.get(finalidade + '_sem_consenso'):
            e[finalidade + '_sem_consenso'] = False
            e['situacao'] = 'Deliberação registrada — reapresentar proposta conjunta'
            # Não escolhe nota/posição; participantes devem propor e confirmar novamente.
    elif acao == 'manifestar_dpo':
        exigir(papeis, 'dpo')
        e['manifestacao_dpo'] = dict(texto=_texto(dados, 'texto'), pessoa_id=pessoa.id, em=agora)
    elif acao == 'confirmar_gatilho_juridico':
        exigir(papeis, 'aal')
        if not f3 or type(dados.get('restringe_direitos')) is not bool:
            raise ValueError('Confirme explicitamente se o tratamento restringe direitos.')
        e['restringe_direitos'] = dados['restringe_direitos']
        e['juridico'] = 'manifestação jurídica esperada' if dados['restringe_direitos'] or e.get('motivos_juridicos') else 'gatilho não confirmado'
    elif acao == 'enviar_juridico':
        exigir(papeis, 'aal')
        from app.fila_form2 import unidades
        destinatario = sessao.get(Pessoa, dados.get('destinatario_id'))
        if not f3 or not destinatario or not destinatario.ativa or not unidades(sessao, destinatario.id, 'juridico_form2'):
            raise ValueError('Escolha o participante habilitado do Jurídico.')
        _texto(dados, 'motivo', 300)
        e['juridico'] = 'consulta encaminhada ao Jurídico'
        e['escopos_restritos'] = sorted(set(e.get('escopos_restritos', [])) | {pessoa.id, destinatario.id})
        e['juridico_destinatario_id'] = destinatario.id
    elif acao == 'autorizar_referencia':
        exigir(papeis, 'aal')
        from app.modelos import Conta
        alvo_conta = sessao.scalar(select(Conta).where(Conta.pessoa_id == dados.get('pessoa_id'), Conta.ativa.is_(True)))
        if not alvo_conta:
            raise ValueError('Participante indisponível.')
        _, alvo_papeis, _ = contexto(sessao, alvo_conta.id, ref)
        exigir(alvo_papeis, 'secretario', 'gabinete')
        _texto(dados, 'necessidade', 300)
        e['escopos_restritos'] = sorted(set(e.get('escopos_restritos', [])) | {alvo_conta.pessoa_id})
    elif acao == 'propor_triagem':
        if _consenso(e, 'triagem'):
            raise ValueError('Triagem confirmada: use Reavaliar o risco.')
        if e.get('triagem_sem_consenso'):
            raise ValueError('Sem consenso: aguarda deliberação do Comitê antes de reapresentar.')
        lado = _lado(papeis)
        if not _consenso(e, 'avaliacao'):
            raise ValueError('Confirme a avaliação em conjunto antes do resultado da triagem.')
        resultado = dados.get('resultado')
        if resultado not in ('elaborar', 'revisar', 'nao_indicado', 'analise_adicional', 'determinado_anpd'):
            raise ValueError('Resultado da triagem inválido.')
        e['triagem'] = dict(resultado=resultado, justificativa=_texto(dados, 'justificativa'))
        if resultado in ('elaborar', 'revisar', 'determinado_anpd'):
            from app.modelos import Unidade
            unidade = sessao.get(Unidade, dados.get('unidade_id'))
            if not unidade or not unidade.ativa:
                raise ValueError('Informe a unidade que instruirá o RIPD.')
            e['triagem']['unidade_id'] = unidade.id
        e['triagem_sem_consenso'] = False
        e['triagem_confirmacoes'] = {lado: dict(pessoa_id=pessoa.id, em=agora)}
    elif acao == 'informar_ripd':
        exigir(papeis,'secretaria')
        if 'dpo' in papeis:raise PermissionError('A Secretaria informa a referência; o DPO confirma.')
        e['referencia_ripd_confirmacoes']={'secretaria':dict(pessoa_id=pessoa.id,em=agora)}
        e['referencia_ripd']=dict(referencia=_texto(dados,'referencia',200),pessoa_id=pessoa.id,
                                  em=agora,papel='DPO' if 'dpo' in papeis else 'Secretaria')
    elif acao == 'confirmar_ripd':
        exigir(papeis,'dpo')
        if _consenso(e,'referencia_ripd'):raise ValueError('Referência já confirmada.')
        _confirmar(e,'referencia_ripd',pessoa.id,papeis,agora)
        _gravar_estado(sessao,cmd,obj,'referencia_ripd_confirmada',e)
        from app.encerramento_form4 import pode_encerrar
        for aid in e.get('acoes',[]):
            ae=estado(sessao,aid)
            enriquecer(sessao,ae)
            if 'Elaborar/revisar RIPD' in ae.get('respostas',{}).get('F4-4.4',[]) and pode_encerrar(ae) and not ae.get('encerrada'):
                ae['encerrada']=True
                ae['situacao']='Concluída com verificação'
                _gravar_estado(sessao,cmd,sessao.get(IdentidadeForms34,aid),'encerramento_automatico',ae)
    elif acao == 'aceitar_residual':
        if not _consenso(e, 'avaliacao'):
            raise ValueError('A nota ainda não tem as duas confirmações.')
        faixa = _faixa(e)
        if faixa == 'Não avaliado':
            raise ValueError('Risco não avaliado não pode ser aceito.')
        exigir(papeis, 'gabinete' if faixa == 'Crítico' else 'secretario')
        if 'gabinete' in papeis and faixa != 'Crítico':
            raise PermissionError('Prefeito atua somente no risco Crítico.')
        _pareceres(e, faixa)
        if e.get('aceitacao'):raise ValueError('Aceitação já registrada; preserve o ato anterior.')
        from app.condicoes_aceitacao34 import validar_condicoes
        condicoes=validar_condicoes(dados.get('condicoes',[]))
        if faixa=='Crítico':
            if type(dados.get('solicitar_juridico')) is not bool:raise ValueError('Informe se deseja solicitar manifestação jurídica.')
            if dados['solicitar_juridico']:
                from app.fila_form2 import unidades
                destinatario=sessao.get(Pessoa,dados.get('destinatario_id'))
                if not destinatario or not destinatario.ativa or not unidades(sessao,destinatario.id,'juridico_form2'):raise ValueError('Escolha o participante habilitado do Jurídico.')
                e['juridico']='consulta encaminhada ao Jurídico'
                e['juridico_destinatario_id']=destinatario.id
                e['escopos_restritos']=sorted(set(e.get('escopos_restritos',[]))|{pessoa.id,destinatario.id})
            e['consulta_juridica_aceitacao']=dict(solicitada=dados['solicitar_juridico'],motivo=_texto(dados,'motivo_juridico',300),pessoa_id=pessoa.id,em=agora)
        e['aceitacao'] = dict(pessoa_id=pessoa.id, em=agora, justificativa=_texto(dados, 'justificativa'))
        if faixa=='Crítico':e['aceitacao'].update(decisor='Prefeito',registrador='Gabinete',documento=_texto(dados,'documento',200))
        if faixa in ('Alto', 'Crítico'):
            e['ciencia_comite'] = dict(em=agora, motivo='aceitação residual')
        if condicoes:
            fonte=_gravar_estado(sessao,cmd,obj,'aceitacao_condicionada',e)
            e['condicoes_aceitacao']=[]
            for n,c in enumerate(condicoes):
                a=_criar(sessao,cmd,conta_id,obj.registro_id,4,3,fonte.id,f'condicao:{cmd.id}:{n}',
                    dict(form=4,respostas={'F4-4.4':[c['tipo']],'F4-4.9':'Imediata'},
                         prioridade_origem='Imediata',situacao='Em preenchimento',risco_id=obj.id,
                         faixa_origem=faixa,motivo=c['texto'],condicao_aceitacao=True,
                         prorrogacoes=0,prazo=None,executor_id=None,decisoes_pendentes={},escopos_restritos=[]))
                e['condicoes_aceitacao'].append(dict(c,acao_id=a.id))
                e.setdefault('acoes',[]).append(a.id)
                e.setdefault('acoes_rodada',[]).append(a.id)
    elif acao == 'concluir_avaliacao':
        exigir(papeis, 'secretaria', 'dpo')
        if not _consenso(e, 'avaliacao'):
            raise ValueError('Aguardando confirmação conjunta; medidas de proteção continuam disponíveis.')
        if exige_triagem(e['avaliacao'], e.get('sinais')) and not _consenso(e, 'triagem'):
            raise ValueError('A triagem exige confirmação conjunta.')
        if not e.get('aceitacao'):
            raise ValueError('Pendente de autoridade competente.')
        if e.get('reavaliacao'):
            raise ValueError('Conclua a reavaliação em andamento antes de concluir a avaliação do risco.')
        respostas = e.get('respostas', {})
        indicadas = respostas.get('F3-3.59') == 'Sim' and 'Providência no FORM 4' in respostas.get('F3-3.61', [])
        if indicadas and not e.get('acoes_rodada', e.get('acoes')):
            raise ValueError('Encaminhe a providência indicada antes de concluir a avaliação do risco.')
        e['conferencia_r17'] = exigir_r17(conferencia34(3,e), f'/forms34/{obj.id}/blocos')
        e['situacao'] = 'Avaliação concluída'
        e['concluida'] = True
        e['conclusao'] = dict(pessoa_id=pessoa.id, em=agora, versao=versao,
                             conferencia_r17=deepcopy(e['conferencia_r17']))
        e['revisao_aberta'] = False
    elif acao == 'destinar_lacuna':
        exigir(papeis, 'aal')
        if not f3:
            raise ValueError('Ato exclusivo do FORM 3.')
        from app.lacunas_form3 import listar, validar_destino
        lacuna = next((l for l in listar(e) if l['id'] == dados.get('lacuna_id')), None)
        if not lacuna:
            raise ValueError('Lacuna não está ativa nesta versão.')
        validar_destino(dados)
        e.setdefault('destinos_lacunas', {})[lacuna['id']] = dict(destino=dados['destino'], prioridade=dados['prioridade'])
    elif acao == 'encaminhar_acao':
        exigir(papeis, 'aal')
        lacuna = None
        if dados.get('lacuna_id'):
            from app.lacunas_form3 import listar
            lacuna = next((l for l in listar(e) if l['id'] == dados['lacuna_id']), None)
            if not lacuna:
                raise ValueError('Lacuna não está ativa nesta versão. Atualize a página.')
            existente = e.get('encaminhamentos_lacunas', {}).get(lacuna['id'])
            if existente:
                return fechar_comando(cmd, {'permitido': True, 'identidade_id': existente['acao_id'], 'existente': True})
            if dados.get('destino') != 'Providência no FORM 4':
                raise ValueError('Escolha Providência no FORM 4 para criar a ação.')
            if dados.get('prioridade') not in ('Imediata', 'Alta', 'Média', 'Baixa', 'A confirmar'):
                raise ValueError('Escolha a prioridade desta lacuna.')
            dados = {**dados, 'justificativa': lacuna['rotulo'], 'outra': True}
        motivo = _texto(dados, 'justificativa')
        if e.get('acoes') and dados.get('outra') is not True:
            return fechar_comando(cmd, {'permitido': True, 'identidade_id': e['acoes'][-1],
                                        'existente': True})
        # R17 exige prontidão no encaminhamento do FORM 2; não bloqueia medidas protetivas do FORM 3.
        e['conferencia_r17'] = retrato(conferencia34(3,e))
        fonte = historico(sessao, obj.id)[-1]
        chave = f'f3:{obj.id}:v{fonte.sequencia_cadeia}'
        a = _criar(sessao, cmd, conta_id, obj.registro_id, 4, 3, fonte.id, chave,
            dict(form=4, respostas={'F4-4.9':e.get('respostas',{}).get('F3-3.60','')},
                 prioridade_origem=e.get('respostas',{}).get('F3-3.60'),fornecedor_guarda_dados=e.get('fornecedor_guarda_dados',False),
                 situacao='Em preenchimento', risco_id=obj.id,
                 faixa_origem=_faixa(e), motivo=motivo, prorrogacoes=0, prazo=None,
                 executor_id=None, decisoes_pendentes={}, escopos_restritos=[]))
        if lacuna:
            ae = estado(sessao, a.id)
            ae['origem_lacuna'] = deepcopy(lacuna)
            ae['respostas'].update({'F4-4.2': lacuna['id'], 'F4-4.9': dados['prioridade']})
            ae['prioridade_origem'] = dados['prioridade']
            ae['tema_sugerido'] = lacuna.get('tema')
            from app.modelos import Tema
            tema = sessao.get(Tema, lacuna.get('tema')) if lacuna.get('tema') else None
            if tema and tema.ativo:
                ae['temas'] = {'principal': tema.codigo, 'complementares': []}
            _gravar_estado(sessao, cmd, a, 'origem_lacuna', ae)
            e.setdefault('encaminhamentos_lacunas', {})[lacuna['id']] = dict(
                acao_id=a.id, prioridade=dados['prioridade'], destino=dados['destino'])
        e.setdefault('acoes', []).append(a.id)
        e.setdefault('acoes_rodada', []).append(a.id)
        destino_id = a.id
    elif acao == 'salvar_temas':
        exigir(papeis, 'secretaria')
        if e.get('plano_aprovado'):
            raise ValueError('Plano aprovado: temas preservados. Ajustes do aprendizado geram nova versão própria.')
        from app.temas_form4 import validar as validar_temas
        e['temas']=validar_temas(sessao,dados.get('tema_principal',''),dados.get('temas_complementares',[]))
    elif acao == 'solicitar_tema':
        exigir(papeis, 'secretaria')
        e.setdefault('solicitacoes_tema',[]).append(dict(id=cmd.id,nome=_texto(dados,'nome_sugerido',200),
            justificativa=_texto(dados,'justificativa'),pessoa_id=pessoa.id,em=agora,situacao='Em análise'))
    elif acao in ('propor_residual_acao', 'confirmar_residual_acao', 'decidir_residual_acao', 'aceitar_residual_acao'):
        from app.encerramento_form4 import nota_confirmada, reducao_total
        if not e.get('verificada') or reducao_total(e):
            raise ValueError('Este ato exige verificação aprovada com risco ainda não totalmente reduzido.')
        if acao == 'propor_residual_acao':
            exigir(papeis, 'secretaria')
            if 'dpo' in papeis:raise PermissionError('A Secretaria propõe; o DPO confirma.')
            if nota_confirmada(e):raise ValueError('Nota posterior já confirmada; preserve esta decisão e reavalie o risco de origem.')
            from app.avaliacao_risco34 import pontuar
            nota = pontuar(dados.get('pr'), dados.get('ir'))
            if nota['nota'] is None:raise ValueError('Informe probabilidade e impacto após a ação.')
            e['residual_acao'] = dict(nota, justificativa=_texto(dados, 'justificativa'))
            e['residual_acao_confirmacoes'] = {'secretaria':dict(pessoa_id=pessoa.id, em=agora)}
        elif acao == 'confirmar_residual_acao':
            exigir(papeis, 'dpo')
            if nota_confirmada(e):raise ValueError('Nota posterior já confirmada.')
            _confirmar(e, 'residual_acao', pessoa.id, papeis, agora)
        else:
            nota = nota_confirmada(e)
            if not nota:raise ValueError('Aguarda nota residual confirmada pela Secretaria e pelo DPO.')
            justificativa = _texto(dados, 'justificativa')
            if acao == 'aceitar_residual_acao':
                if 'dpo' in papeis:raise PermissionError('Aceitação cabe à autoridade competente, não ao DPO.')
                exigir(papeis, 'gabinete' if nota['faixa']=='Crítico' else 'secretario')
                if 'gabinete' in papeis and nota['faixa']!='Crítico':raise PermissionError('Gabinete registra somente a decisão de risco Crítico.')
                if e.get('aceitacao_residual_acao'):raise ValueError('Aceitação posterior já registrada.')
                _pareceres(e, nota['faixa'])
                decisao = dict(pessoa_id=pessoa.id, em=agora, justificativa=justificativa, nota=deepcopy(nota))
                if nota['faixa']=='Crítico':decisao.update(decisor='Prefeito', registrador='Gabinete', documento=_texto(dados,'documento',200))
                e['aceitacao_residual_acao'] = decisao
                e.setdefault('decisao_residual_acao', dict(decisao, opcao='aceitar'))
            else:
                exigir(papeis, 'secretaria')
                if 'dpo' in papeis:raise PermissionError('A escolha de tratamento cabe à Secretaria.')
                if e.get('decisao_residual_acao'):raise ValueError('Decisão posterior já registrada.')
                opcao = dados.get('opcao')
                if opcao not in ('reavaliar','nova_providencia'):raise ValueError('Escolha reavaliar o risco ou nova providência.')
                risco = sessao.get(IdentidadeForms34, e.get('risco_id')) if e.get('risco_id') else None
                re = estado(sessao, risco.id) if risco else None
                if opcao == 'reavaliar':
                    if not risco:raise ValueError('Esta ação não tem risco de origem; use nova providência.')
                    if re.get('conclusao'):re.setdefault('conclusoes_anteriores', []).append(re.pop('conclusao'))
                    re['concluida'] = False
                    re['revisao_aberta'] = True
                    re['reavaliacao_solicitada'] = dict(acao_id=obj.id,pessoa_id=pessoa.id,em=agora,justificativa=justificativa)
                    _gravar_estado(sessao,cmd,risco,'reavaliacao_solicitada',re)
                    destino_id = risco.id
                else:
                    fonte = historico(sessao, risco.id)[-1] if risco else None
                    a = _criar(sessao,cmd,conta_id,obj.registro_id,4,3 if risco else ref.fonte_form,
                        fonte.id if fonte else ref.fonte_id, 'residual-acao:'+obj.id+':'+cmd.id,
                        dict(form=4,respostas={},situacao='Em preenchimento',risco_id=risco.id if risco else None,
                             faixa_origem=nota['faixa'],motivo=justificativa,acao_anterior_id=obj.id,
                             prorrogacoes=0,prazo=None,executor_id=None,decisoes_pendentes={},escopos_restritos=[]))
                    destino_id = a.id
                    if risco:
                        re.setdefault('acoes',[]).append(a.id)
                        re.setdefault('acoes_rodada',[]).append(a.id)
                        _gravar_estado(sessao,cmd,risco,'providencia_pos_acao',re)
                e['decisao_residual_acao'] = dict(opcao=opcao,pessoa_id=pessoa.id,em=agora,
                    justificativa=justificativa,destino_id=destino_id,nota=deepcopy(nota))
    elif acao == 'planejar':
        exigir(papeis, 'secretaria')
        if e.get('plano_aprovado'):
            raise ValueError('Plano aprovado: alterações de prazo exigem pedido próprio.')
        from app.regras_atos34 import CARGOS
        cargo=dados.get('cargo')
        if cargo not in CARGOS:raise ValueError('Escolha o cargo, função ou unidade responsável.')
        if len(_texto(dados, 'plano')) < 30:
            from app.validacao_atos34 import ErrosCampos
            raise ErrosCampos({'plano': 'Descreva o plano com pelo menos 30 caracteres.'})
        from app.temas_form4 import validar as validar_temas
        anteriores=e.get('temas',{})
        e['temas']=validar_temas(sessao,dados.get('tema_principal',anteriores.get('principal','')),
            dados.get('temas_complementares',anteriores.get('complementares',[])),obrigatorio=True)
        e.pop('executor_id',None)  # autoria anterior permanece nos eventos, não no novo cargo
        from app.prazos_plano34 import duracao_validada
        duracao = duracao_validada(e, dados.get('duracao_dias'))
        e.update(plano=_texto(dados,'plano'),cargo_responsavel=cargo,unidade_responsavel_id=uid,
                 duracao_dias=duracao, plano_registrado_em=agora, prazo=None)
    elif acao == 'aprovar_plano':
        faixa = _faixa(e)
        exigir(papeis, 'gabinete' if faixa == 'Crítico' else 'secretario')
        if 'gabinete' in papeis and faixa != 'Crítico':
            raise PermissionError('Prefeito não aprova plano fora do risco Crítico.')
        if not e.get('plano') or not (e.get('cargo_responsavel') or e.get('executor_id')) or not (e.get('duracao_dias') or e.get('prazo')):
            raise ValueError('Informe plano, executor e duração antes da aprovação.')
        if e.get('plano_aprovado'):
            raise ValueError('Plano já aprovado; conteúdo preservado.')
        if e.get('duracao_dias') is None:
            raise ValueError('Antes de aprovar, peça à Secretaria que registre a duração do plano em dias corridos. A data anterior continua no histórico.')
        e['conferencia_plano'] = exigir_r17(conferencia_etapa(e, 'plano'), f'/forms34/{obj.id}/blocos')
        from app.prazos_plano34 import vencimento_na_aprovacao
        e['prazo'] = vencimento_na_aprovacao(e, agora)
        e['plano_aprovado'] = dict(pessoa_id=pessoa.id, em=agora, justificativa=_texto(dados, 'justificativa'), prazo=e['prazo'])
        if faixa=='Crítico':e['plano_aprovado'].update(decisor='Prefeito',registrador='Gabinete',documento=_texto(dados,'documento',200))
        e['situacao'] = 'Plano aprovado'
    elif acao == 'executar_medida':
        exigir(papeis, 'executor_unidade')
        if 'dpo' in papeis:raise PermissionError('O DPO não registra execução.')
        if not e.get('plano_aprovado'):
            raise ValueError('A medida requer plano autorizado; a espera do DPO no FORM 3 não o bloqueia.')
        if len(_texto(dados, 'resumo')) < 30:
            from app.validacao_atos34 import ErrosCampos
            raise ErrosCampos({'resumo': 'Descreva o que foi feito com pelo menos 30 caracteres.'})
        if not e.get('cargo_responsavel'):
            raise ValueError('Informe o cargo ou função responsável antes de registrar a execução.')
        e['conferencia_execucao'] = exigir_r17(conferencia_etapa(e, 'execucao'), f'/forms34/{obj.id}/blocos')
        e['execucao'] = dict(evidencia=_texto(dados, 'evidencia'), resumo=_texto(dados, 'resumo'),
                            cargo_responsavel=e.get('cargo_responsavel'), unidade_responsavel_id=uid,
                            pessoa_id=pessoa.id, em=agora)
        e['situacao'] = 'Execução informada, aguardando verificação'
    elif acao == 'verificar':
        exigir(papeis, 'verificador')
        if papeis.intersection(('dpo', 'relator')) or pessoa.id == e.get('execucao',{}).get('pessoa_id') or 'executor_unidade' in papeis:
            raise PermissionError('Verificador deve ser pessoa independente, nunca executor, DPO ou Relator.')
        if not e.get('execucao'):
            raise ValueError('Aguarda evidência da execução.')
        if type(dados.get('aprovada')) is not bool:
            raise ValueError('Informe o resultado da verificação.')
        respostas_verificacao = validar_verificacao(dados)
        from app.fila_form2 import unidades
        unidade_verificador = sorted(unidades(sessao, pessoa.id, 'demo34_verificador') - {uid})[0]
        e['verificacao'] = dict(aprovada=dados['aprovada'], evidencia=_texto(dados, 'evidencia'),
                                pessoa_id=pessoa.id, unidade_id=unidade_verificador, em=agora,
                                respostas=respostas_verificacao,
                                quantidade_a_confirmar=sum(v == 'A confirmar' for v in respostas_verificacao.values()))
        e.setdefault('respostas', {}).update(respostas_verificacao)
        e['verificada'] = dados['aprovada']
        e['situacao'] = 'Verificação aprovada' if dados['aprovada'] else 'Requer ajuste na execução'
    elif acao in ('pedir_prorrogacao', 'pedir_cancelamento'):
        exigir(papeis, 'secretaria')
        tipo = acao.removeprefix('pedir_')
        if tipo in e['decisoes_pendentes']:
            raise ValueError('Já existe pedido aguardando decisão.')
        pedido = dict(justificativa=_texto(dados, 'justificativa'), pessoa_id=pessoa.id, em=agora)
        if tipo == 'prorrogacao':
            if e.get('prorrogacoes', 0) >= 2:
                raise ValueError('Mais de duas prorrogações não estão autorizadas nesta demonstração.')
            pedido['prazo'] = date.fromisoformat(dados['prazo']).isoformat()
            if not e.get('prazo') or pedido['prazo'] <= e['prazo']:
                raise ValueError('A data proposta deve ser posterior ao prazo vigente.')
            e.pop('manifestacao_comite', None)
        e['decisoes_pendentes'][tipo] = pedido
    elif acao == 'decidir_prorrogacao':
        exigir(papeis, 'secretario')
        pedido = e['decisoes_pendentes'].get('prorrogacao')
        if not pedido:
            raise ValueError('Não há pedido de prorrogação.')
        if type(dados.get('aprovar')) is not bool:
            raise ValueError('Informe aprovação ou rejeição.')
        motivo = _texto(dados, 'justificativa')
        if e['prorrogacoes'] == 1:
            m = e.get('manifestacao_comite', {})
            if m.get('finalidade') != 'prorrogacao':
                raise ValueError('A segunda prorrogação exige manifestação do Comitê.')
            if dados['aprovar'] and not m['favoravel']:
                e['ciencia_prefeito'] = dict(em=agora, motivo=motivo, automatica=True)
                _gravar(sessao, cmd, 'forms34_objeto', obj.id, obj.registro_id,
                         'f34_ciencia_prefeito', {'motivo': 'segunda prorrogação mantida contra manifestação'})
        if dados['aprovar']:
            e['prazo'] = pedido['prazo']
            e['prorrogacoes'] += 1
        del e['decisoes_pendentes']['prorrogacao']
    elif acao == 'cancelar':
        exigir(papeis, 'secretario')
        if not e['decisoes_pendentes'].get('cancelamento'):
            raise ValueError('Registre o pedido de cancelamento primeiro.')
        _pareceres(e, 'Alto' if _faixa(e) in ('Alto', 'Crítico') else _faixa(e))
        e['cancelada'] = dict(pessoa_id=pessoa.id, em=agora, justificativa=_texto(dados, 'justificativa'))
        e['decisoes_pendentes'] = {}
        e['verificada'] = False
        e['situacao'] = 'Cancelada com aprovação'
        if _faixa(e) in ('Alto', 'Crítico'):
            e['ciencia_comite'] = dict(em=agora, motivo='cancelamento')
    elif acao == 'aprender':
        exigir(papeis, 'secretaria')
        from app.encerramento_form4 import pode_encerrar
        if not pode_encerrar(e) or e.get('condicoes_abertas'):
            raise ValueError('Aprendizagem exige verificação aprovada e decisão sobre o risco que sobrou.')
        temas=deepcopy(e.get('aprendizagem',{}).get('temas',e.get('temas',{})))
        if 'tema_principal' in dados or 'temas_complementares' in dados:
            from app.temas_form4 import validar as validar_temas
            temas=validar_temas(sessao,dados.get('tema_principal',temas.get('principal','')),
                dados.get('temas_complementares',temas.get('complementares',[])),obrigatorio=bool(temas.get('principal')))
        e['aprendizagem'] = dict(contexto=_texto(dados, 'contexto'), diretriz=_texto(dados, 'diretriz'), escopo=_texto(dados, 'escopo'),
                                 temas=temas,
                                 acao_id=obj.id, verificacao=deepcopy(e['verificacao']), pessoa_id=pessoa.id, em=agora,
                                 versao=e.get('aprendizagem', {}).get('versao', 0) + 1)
        e.pop('aprendizagem_conferida', None)
        e.pop('aprendizagem_autorizada', None)
        e.pop('aprendizagem_devolvida', None)
    elif acao == 'conferir_aprendizagem':
        exigir(papeis, 'dpo')
        if not e.get('aprendizagem') or not e.get('verificada'):
            raise ValueError('Não há aprendizagem verificada para conferir.')
        if e.get('aprendizagem_devolvida'):
            raise ValueError('Aguarde a nova versão da aprendizagem pela Secretaria.')
        if type(dados.get('sem_falha_exposta')) is not bool:
            raise ValueError('Confirme se o relato não expõe falha aberta nem facilita exploração.')
        if dados.get('sem_dados_pessoais') is False or dados.get('sem_falha_exposta') is False:
            e['aprendizagem_devolvida'] = dict(pessoa_id=pessoa.id, em=agora,
                observacao=_texto(dados, 'observacao'), versao=e['aprendizagem']['versao'])
            e.pop('aprendizagem_conferida', None)
            e.pop('aprendizagem_autorizada', None)
        elif dados.get('sem_dados_pessoais') is True:
            e['aprendizagem_conferida'] = dict(pessoa_id=pessoa.id, em=agora, sem_falha_exposta=True, sem_dados_pessoais=True)
            if dados.get('observacao'):
                e['aprendizagem_conferida']['observacao'] = _texto(dados, 'observacao')
        else:
            raise ValueError('Informe Sim ou Não na conferência.')
    elif acao == 'autorizar_aprendizagem':
        exigir(papeis, 'secretaria')
        if not e.get('aprendizagem_conferida'):
            raise ValueError('Aguarda conferência do DPO.')
        e['aprendizagem_autorizada'] = dict(pessoa_id=pessoa.id, em=agora)
    else:
        raise ValueError('Ato não disponível.')
    ev = _gravar_estado(sessao, cmd, obj, acao, e)
    from app.encerramento_form4 import pode_encerrar
    if not f3 and acao not in ('salvar_bloco','abrir_detalhes','salvar_temas','solicitar_tema') and pode_encerrar(e) and not e.get('encerrada'):
        # Verificação cobra somente as respostas do verificador. Atos antigos são preservados.
        e['conferencia_r17'] = retrato(conferencia34(4,e))
        e['encerrada'] = True
        e['situacao'] = 'Concluída com verificação'
        ev = _gravar_estado(sessao, cmd, obj, 'encerramento_automatico', e)
    return fechar_comando(cmd, {'permitido': True, 'identidade_id': destino_id, 'versao': ev.sequencia_cadeia})


@_atomica
def registrar_referencia_restrita(sessao, *, conta_id, comando_id, identidade_id, versao, dados):
    from app.restrito_forms34 import pode_ler, acrescentar
    obj = sessao.get(IdentidadeForms34, identidade_id)
    if not obj:
        raise ValueError('Objeto inexistente.')
    _registro(sessao, obj.registro_id)
    e = estado(sessao, obj.id)
    if not pode_ler(sessao, conta_id, identidade_id, e):
        raise PermissionError('Referência restrita sem escopo autorizado.')
    cmd, repeticao = _abrir(sessao, comando_id, conta_id, 'f34_referencia_restrita',
        dict(identidade_id=identidade_id, versao=versao, dados=dados))
    if repeticao is not None:
        return repeticao
    if versao != e.pop('versao'):
        raise ValueError('A referência mudou; atualize a página.')
    from app.validacao_atos34 import validar
    validar('registrar_referencia',dados)
    rid = acrescentar(sessao, obj.id, cmd.ator_id, dados)
    e['referencia_restrita_id'] = rid  # só existência/estado, nunca conteúdo no livro geral
    e['juridico'] = 'referência registrada'
    ev = _gravar_estado(sessao, cmd, obj, 'referencia_registrada', e)
    return fechar_comando(cmd, {'permitido': True, 'identidade_id': obj.id, 'versao': ev.sequencia_cadeia})
