"""Atos demonstrativos dos FORMs 3/4. Decisões 18/11 + complemento 11-B.

Estado derivado exclusivamente de eventos; transação e bloqueio por Registro.
Nenhum ato é concedido por um campo enviado pelo navegador.
"""
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
    dados['versao'] = eventos[-1].sequencia_cadeia
    return dados


def consultar(sessao, conta_id, identidade_id):
    obj = sessao.get(IdentidadeForms34, identidade_id)
    if not obj:
        raise ValueError('Objeto inexistente.')
    ref = sessao.get(Referencia, obj.participacao_id)
    pessoa, papeis, uid = contexto(sessao, conta_id, ref)
    exigir(papeis, 'secretaria', 'dpo', 'secretario', 'prefeito', 'verificador', 'relator')
    return obj, ref, estado(sessao, obj.id), pessoa, papeis, uid


def _gravar_estado(sessao, comando, obj, acao, e):
    ev = _gravar(sessao, comando, 'forms34_objeto', obj.id, obj.registro_id,
                 'f34_' + acao, {'estado': deepcopy(e)})
    return ev


def _criar(sessao, comando, conta_id, registro_id, form, fonte_form, fonte_id, chave, inicial):
    refid = str(uuid5(NAMESPACE_URL, f'forms34/{registro_id}/{form}/{chave}'))
    fixar_referencia(sessao, comando_id=_subchave(comando.id, 'ref'), conta_id=conta_id,
                     participacao_id=refid, registro_id=registro_id, form=form,
                     fonte_form=fonte_form, fonte_id=str(fonte_id))
    reservado = reservar_identidade(sessao, comando_id=_subchave(comando.id, 'identidade'),
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
            p.estado != 'em_atendimento' or not autorizado(sessao, pessoa, p)):
        raise PermissionError('Somente o AAL responsável encaminha pelos itens F2-14.5/14.6.')
    dados = dict(participacao_id=p.id, versao=versao, form=form, justificativa=justificativa)
    cmd, repeticao = _abrir(sessao, comando_id, conta_id, 'f34_ingressar', dados)
    if repeticao is not None:
        return repeticao
    if type(form) is not int or form not in (3, 4) or p.versao != versao:
        raise ValueError('Instrumento ou versão inválida. Atualize a página.')
    from app.form2_rev212 import indice_valores
    respostas = indice_valores(p.conteudo or {})
    item = 'F2-14.5' if form == 3 else 'F2-14.6'
    if not any(v in ('Sim', 'SIM') for v in respostas.get('opcao:' + item, [])):
        raise ValueError(f'Confirme {item} no FORM 2 antes deste ato.')
    sinais = sinais_form2(p.conteudo or {})
    from app.gatilhos_juridicos34 import motivos
    gatilhos = motivos(p.conteudo or {})
    if form == 4 and sinais and not any(v in ('Sim', 'SIM') for v in respostas.get('opcao:F2-14.5', [])):
        _texto({'justificativa': justificativa}, 'justificativa')
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
        dict(form=form, respostas={}, sinais=sinais, origem_form2_id=p.id, situacao_form2=p.estado,
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
    confirmacoes[lado] = dict(pessoa_id=pessoa_id, em=agora)


def _faixa(e):
    a = e.get('avaliacao')
    return a['residual']['faixa'] if a and _consenso(e, 'avaliacao') else e.get('faixa_origem', 'Não avaliado')


def _pareceres(e, faixa):
    if faixa in ('Alto', 'Crítico') and not e.get('manifestacao_dpo'):
        raise ValueError('Aguarda manifestação prévia do DPO.')
    if faixa == 'Crítico' and e.get('manifestacao_comite',{}).get('finalidade') != 'residual':
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
    cmd, repeticao = _abrir(sessao, comando_id, conta_id, 'f34_ato',
        dict(identidade_id=obj.id, versao=versao, acao=acao, dados=dados))
    if repeticao is not None:
        return repeticao
    if type(versao) is not int or versao != e.pop('versao'):
        raise ValueError('O Registro mudou. Atualize antes de confirmar.')
    if not isinstance(dados, dict):
        raise ValueError('Dados inválidos.')
    agora = agora_utc().isoformat()
    f3 = e['form'] == 3
    if 'dpo' in papeis and acao in ('aceitar_residual','aprovar_plano','decidir_prorrogacao','cancelar','executar_medida','verificar'):
        raise PermissionError('O DPO não exerce estes atos de autoridade, execução ou verificação.')
    if acao in ('propor_avaliacao', 'confirmar_avaliacao', 'propor_triagem', 'confirmar_triagem',
                'sem_consenso', 'aceitar_residual', 'concluir_avaliacao', 'encaminhar_acao') and not f3:
        raise ValueError('Ato exclusivo do FORM 3.')
    if acao in ('planejar', 'aprovar_plano', 'executar_medida', 'verificar', 'pedir_prorrogacao',
                'decidir_prorrogacao', 'pedir_cancelamento', 'cancelar', 'aprender',
                'conferir_aprendizagem', 'autorizar_aprendizagem') and f3:
        raise ValueError('Ato exclusivo do FORM 4.')
    if e.get('cancelada') or e.get('encerrada'):
        if acao not in ('aprender', 'conferir_aprendizagem', 'autorizar_aprendizagem'):
            raise ValueError('Ação encerrada; seu histórico permanece preservado.')
    destino_id = obj.id
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
        _gravar_estado(sessao,cmd,novo,'ingresso',inicial)
        destino_id=novo.id
    elif acao == 'salvar_bloco':
        exigir(papeis, 'secretaria', 'dpo')
        from app.questionario_forms34 import salvar
        e['respostas'] = salvar(e['form'], e.get('respostas', {}), dados, e)
        if f3:
            e['sinais'] = sorted(set(e.get('sinais', [])) | ({'F3-3.10'} if e['respostas'].get('F3-3.10') else set()) |
                ({'F3-3.54'} if e['respostas'].get('F3-3.54') in ('Sim','Requer análise','A confirmar') else set()))
    elif acao == 'abrir_detalhes':
        exigir(papeis, 'secretaria', 'dpo')
        bloco = dados.get('bloco')
        if type(bloco) is not int or not 1 <= bloco <= (16 if f3 else 9):
            raise ValueError('Bloco inválido.')
        e.setdefault('aberturas', {})[str(bloco)] = _texto(dados, 'motivo', 300)
    elif acao == 'propor_avaliacao':
        if e.get('avaliacao_sem_consenso'):
            raise ValueError('Sem consenso: aguarda deliberação do Comitê antes de reapresentar.')
        lado = _lado(papeis)
        e['evento'] = _texto(dados, 'evento')
        e['causa'] = _texto(dados, 'causa')
        e['consequencia'] = _texto(dados, 'consequencia')
        e['avaliacao'] = propor_avaliacao(dados)
        e['avaliacao_confirmacoes'] = {lado: dict(pessoa_id=pessoa.id, em=agora)}
        e['avaliacao_sem_consenso'] = False
        for k in ('aceitacao', 'manifestacao_dpo', 'manifestacao_comite', 'triagem'):
            e.pop(k, None)
        e['triagem_confirmacoes'] = {}
        e['situacao'] = 'Aguardando DPO' if lado == 'secretaria' else 'Aguardando Secretaria'
    elif acao in ('confirmar_avaliacao', 'confirmar_triagem'):
        campo = acao.removeprefix('confirmar_')
        _confirmar(e, campo, pessoa.id, papeis, agora)
        e['situacao'] = 'Avaliação conjunta registrada' if _consenso(e, campo) else 'Aguardando confirmação'
    elif acao == 'sem_consenso':
        campo = dados.get('campo')
        if campo not in ('avaliacao', 'triagem') or not e.get(campo):
            raise ValueError('Indique a proposta em discussão.')
        lado = _lado(papeis)
        e.setdefault(campo + '_posicoes', {})[lado] = _texto(dados, 'posicao', 300)
        e[campo + '_sem_consenso'] = True
        e[campo + '_confirmacoes'] = {}
        e['situacao'] = 'Sem consenso — encaminhado ao Comitê'
    elif acao == 'manifestar_comite':
        exigir(papeis, 'relator')
        if papeis.intersection(('verificador', 'dpo')):
            raise PermissionError('Relator distinto do verificador e do DPO.')
        finalidade = dados.get('finalidade')
        if finalidade not in ('avaliacao', 'triagem', 'residual', 'prorrogacao', 'cancelamento'):
            raise ValueError('Finalidade da manifestação inválida.')
        m = dict(ata=_texto(dados, 'ata', 200), texto=_texto(dados, 'texto'),
                 favoravel=dados.get('favoravel') is True, finalidade=finalidade,
                 pessoa_id=pessoa.id, em=agora)
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
        exigir(alvo_papeis, 'secretario', 'prefeito')
        _texto(dados, 'necessidade', 300)
        e['escopos_restritos'] = sorted(set(e.get('escopos_restritos', [])) | {alvo_conta.pessoa_id})
    elif acao == 'propor_triagem':
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
    elif acao == 'aceitar_residual':
        if not _consenso(e, 'avaliacao'):
            raise ValueError('A nota ainda não tem as duas confirmações.')
        faixa = _faixa(e)
        if faixa == 'Não avaliado':
            raise ValueError('Risco não avaliado não pode ser aceito.')
        exigir(papeis, 'prefeito' if faixa == 'Crítico' else 'secretario')
        if 'prefeito' in papeis and faixa != 'Crítico':
            raise PermissionError('Prefeito atua somente no risco Crítico.')
        _pareceres(e, faixa)
        e['aceitacao'] = dict(pessoa_id=pessoa.id, em=agora, justificativa=_texto(dados, 'justificativa'))
        if faixa in ('Alto', 'Crítico'):
            e['ciencia_comite'] = dict(em=agora, motivo='aceitação residual')
    elif acao == 'concluir_avaliacao':
        exigir(papeis, 'secretaria', 'dpo')
        if not _consenso(e, 'avaliacao'):
            raise ValueError('Aguardando confirmação conjunta; medidas de proteção continuam disponíveis.')
        if exige_triagem(e['avaliacao'], e.get('sinais')) and not _consenso(e, 'triagem'):
            raise ValueError('A triagem exige confirmação conjunta.')
        if not e.get('aceitacao'):
            raise ValueError('Pendente de autoridade competente.')
        e['situacao'] = 'Avaliação concluída'
    elif acao == 'encaminhar_acao':
        exigir(papeis, 'aal')
        motivo = _texto(dados, 'justificativa')
        if e.get('acoes'):
            return fechar_comando(cmd, {'permitido': True, 'identidade_id': e['acoes'][-1],
                                        'existente': True})
        fonte = historico(sessao, obj.id)[-1]
        chave = f'f3:{obj.id}:v{fonte.sequencia_cadeia}'
        a = _criar(sessao, cmd, conta_id, obj.registro_id, 4, 3, fonte.id, chave,
            dict(form=4, respostas={'F4-4.9':e.get('respostas',{}).get('F3-3.60','')},
                 prioridade_origem=e.get('respostas',{}).get('F3-3.60'),
                 situacao='Em preenchimento', risco_id=obj.id,
                 faixa_origem=_faixa(e), motivo=motivo, prorrogacoes=0, prazo=None,
                 executor_id=None, decisoes_pendentes={}, escopos_restritos=[]))
        e.setdefault('acoes', []).append(a.id)
        destino_id = a.id
    elif acao == 'planejar':
        exigir(papeis, 'secretaria')
        if e.get('plano_aprovado'):
            raise ValueError('Plano aprovado: alterações de prazo exigem pedido próprio.')
        executor = sessao.get(Pessoa, dados.get('executor_id'))
        from app.fila_form2 import unidades
        if (not executor or not executor.ativa or
                unidades(sessao, executor.id, 'governanca_protecao_dados') or
                uid not in unidades(sessao, executor.id, 'preenchedor') | unidades(sessao, executor.id, 'aal_form2')):
            raise PermissionError('Executor deve participar da unidade; o DPO não executa.')
        e.update(plano=_texto(dados, 'plano'), executor_id=executor.id,
                 prazo=date.fromisoformat(dados['prazo']).isoformat())
    elif acao == 'aprovar_plano':
        faixa = _faixa(e)
        exigir(papeis, 'prefeito' if faixa == 'Crítico' else 'secretario')
        if 'prefeito' in papeis and faixa != 'Crítico':
            raise PermissionError('Prefeito não aprova plano fora do risco Crítico.')
        if not e.get('plano') or not e.get('executor_id') or not e.get('prazo'):
            raise ValueError('Informe plano, executor e prazo antes da aprovação.')
        e['plano_aprovado'] = dict(pessoa_id=pessoa.id, em=agora, justificativa=_texto(dados, 'justificativa'))
        e['situacao'] = 'Plano aprovado'
    elif acao == 'executar_medida':
        exigir(papeis, 'secretaria')
        if 'dpo' in papeis or pessoa.id != e.get('executor_id'):
            raise PermissionError('Somente o executor indicado, nunca o DPO, registra execução.')
        if not e.get('plano_aprovado'):
            raise ValueError('A medida requer plano autorizado; a espera do DPO no FORM 3 não o bloqueia.')
        e['execucao'] = dict(evidencia=_texto(dados, 'evidencia'), pessoa_id=pessoa.id, em=agora)
        e['situacao'] = 'Execução informada, aguardando verificação'
    elif acao == 'verificar':
        exigir(papeis, 'verificador')
        if papeis.intersection(('dpo', 'relator')) or pessoa.id == e.get('executor_id'):
            raise PermissionError('Verificador deve ser pessoa independente, nunca executor, DPO ou Relator.')
        if not e.get('execucao'):
            raise ValueError('Aguarda evidência da execução.')
        if type(dados.get('aprovada')) is not bool:
            raise ValueError('Informe o resultado da verificação.')
        e['verificacao'] = dict(aprovada=dados['aprovada'], evidencia=_texto(dados, 'evidencia'),
                                pessoa_id=pessoa.id, em=agora)
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
        if not e.get('verificada') or e.get('cancelada'):
            raise ValueError('Aprendizagem somente após verificação aprovada.')
        e['aprendizagem'] = dict(diretriz=_texto(dados, 'diretriz'), escopo=_texto(dados, 'escopo'),
                                 versao=e.get('aprendizagem', {}).get('versao', 0) + 1)
        e.pop('aprendizagem_conferida', None)
        e.pop('aprendizagem_autorizada', None)
    elif acao == 'conferir_aprendizagem':
        exigir(papeis, 'dpo')
        if not e.get('aprendizagem') or not e.get('verificada'):
            raise ValueError('Não há aprendizagem verificada para conferir.')
        if dados.get('sem_dados_pessoais') is not True:
            raise ValueError('Confirme a ausência de dados pessoais antes de disponibilizar.')
        e['aprendizagem_conferida'] = dict(pessoa_id=pessoa.id, em=agora)
    elif acao == 'autorizar_aprendizagem':
        exigir(papeis, 'secretaria')
        if not e.get('aprendizagem_conferida'):
            raise ValueError('Aguarda conferência do DPO.')
        e['aprendizagem_autorizada'] = dict(pessoa_id=pessoa.id, em=agora)
    else:
        raise ValueError('Ato não disponível.')
    ev = _gravar_estado(sessao, cmd, obj, acao, e)
    if not f3 and e.get('verificada') and _sem_pendencia(e) and not e.get('encerrada'):
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
    rid = acrescentar(sessao, obj.id, cmd.ator_id, dados)
    e['referencia_restrita_id'] = rid  # só existência/estado, nunca conteúdo no livro geral
    e['juridico'] = 'referência registrada'
    ev = _gravar_estado(sessao, cmd, obj, 'referencia_registrada', e)
    return fechar_comando(cmd, {'permitido': True, 'identidade_id': obj.id, 'versao': ev.sequencia_cadeia})
