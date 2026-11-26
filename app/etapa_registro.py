"""Etapa de leitura do Registro; não conclui atos nem concede acesso."""
from urllib.parse import urlencode
from sqlalchemy import select
from app.modelos import Registro, ParticipacaoForm2, IdentidadeForms34, Pessoa, Conta
from app.providencias import classificar


def decidir_etapa(form1, participacoes, objetos):
    """Uma regra para Painel e detalhes. Entradas são fatos, nunca inferência de resposta."""
    acoes = [o for o in objetos if o['form'] == 4]
    if acoes and all(o['estado'].get('verificada') and o['estado'].get('aprendizagem_autorizada') for o in acoes):
        return dict(form='Ciclo completo', situacao='Ciclo completo', desde=max(
            o['estado']['aprendizagem_autorizada']['em'] for o in acoes), responsavel=None, itens=[])
    if participacoes and not objetos and all(p['estado'] == 'concluida' for p in participacoes):
        return dict(form='Ciclo completo', situacao='Ciclo completo', desde=max(
            (p['concluida_em'] for p in participacoes if p['concluida_em']), default=None), responsavel=None, itens=[])
    if objetos:
        abertos = [o for o in objetos if not (o['estado'].get('concluida') if o['form'] == 3 else
                    o['estado'].get('verificada') and o['estado'].get('aprendizagem_autorizada'))]
        itens = abertos or objetos
        form = max(o['form'] for o in itens)
        itens = [o for o in itens if o['form'] == form]
        return dict(form=form, situacao='; '.join(dict.fromkeys(o['situacao'] for o in itens)),
                    desde=min(o['desde'] for o in itens), itens=itens,
                    responsavel='; '.join(dict.fromkeys(p for o in itens for p in o['responsaveis'])) or None)
    if participacoes:
        p = participacoes[-1]
        return dict(form=2, situacao=('Em análise pelo AAL' if p['responsavel'] else
                    'Aguardando atribuição de AAL pelo gestor da fila (APA)'),
                    desde=p['assumida_em'] or p['entrada_em'], responsavel=p['responsavel'] or 'Gestor da fila (APA)', itens=[])
    return dict(form=1, situacao=form1['estado'], desde=form1['desde'], responsavel=form1['responsavel'], itens=[])


def etapa_atual(sessao, registro, conta_id, fluxo):
    """Chamado somente após a autorização de consulta ao Registro."""
    from app.fluxo_forms34 import estado, consultar
    from app.infra_forms34 import historico
    from app.leitura_atos34 import situacao_atual
    from app.fila_form2 import autorizado, pessoa_ativa
    from app.identidade_demonstrativa import identidade_demonstrativa as rotulo
    query = urlencode({'conta_id': conta_id})
    pessoa = pessoa_ativa(sessao, conta_id)
    ps = list(sessao.scalars(select(ParticipacaoForm2).where(ParticipacaoForm2.registro_id == registro.id,
        ParticipacaoForm2.tipo == 'principal').order_by(ParticipacaoForm2.entrada_em)))
    participacoes = []
    instrumentos = {1: [], 2: [], 3: [], 4: []}
    minhas = []
    for p in ps:
        responsavel = sessao.get(Pessoa, p.responsavel_id) if p.responsavel_id else None
        participacoes.append(dict(estado=p.estado, entrada_em=p.entrada_em, assumida_em=p.assumida_em,
            concluida_em=p.concluida_em, responsavel=(rotulo(responsavel.nome)+' (AAL)') if responsavel else None))
        href = f'/form2/participacoes/{p.id}?{query}' if autorizado(sessao,pessoa,p) and (not p.responsavel_id or p.responsavel_id == pessoa.id) else None
        instrumentos[2].append(dict(situacao='Análise concluída' if p.estado=='concluida' else 'Em análise' if responsavel else 'Aguardando AAL',
                                    desde=p.concluida_em or p.assumida_em or p.entrada_em, href=href))
        if href and p.responsavel_id == pessoa.id and p.estado != 'concluida':
            from app.modelos import ComplementoForm2
            complemento = sessao.scalar(select(ComplementoForm2).where(ComplementoForm2.participacao_id==p.id))
            consultas = sessao.scalar(select(ParticipacaoForm2.id).where(ParticipacaoForm2.origem_id==p.id, ParticipacaoForm2.estado!='concluida').limit(1))
            c = classificar(2,dict(tipo=p.tipo,estado=p.estado,complemento=complemento.estado if complemento else None,consultas_abertas=bool(consultas)))
            if c['pendente']: minhas.append(dict(rotulo=c['botao'],href=href))
    objetos=[]
    for obj in sessao.scalars(select(IdentidadeForms34).where(IdentidadeForms34.registro_id==registro.id).order_by(IdentidadeForms34.criado_em)):
        try: e=estado(sessao,obj.id)
        except ValueError: continue  # Reserva técnica sem ingresso não é etapa.
        eventos=historico(sessao,obj.id)
        ultimo=next((ev for ev in reversed(eventos) if ev.tipo_evento.startswith('f34_') and ev.tipo_evento not in ('f34_salvar_bloco','f34_abrir_detalhes')),eventos[-1])
        responsaveis=[]
        for conta in sessao.scalars(select(Conta).where(Conta.ativa.is_(True))):
            try: _,_,_,ator,papeis,_=consultar(sessao,conta.id,obj.id)
            except (ValueError,PermissionError): continue
            c=classificar(e['form'],e,papeis,ator.id)
            if c['pendente']:
                responsaveis.append(rotulo(ator.nome)+' — '+c['botao'])
                if conta.id==conta_id: minhas.append(dict(rotulo=c['botao'],href=f'/forms34/{obj.id}/blocos/{c["bloco"]}?{query}'))
        item=dict(form=e['form'],estado=e,situacao=situacao_atual(e),desde=ultimo.ocorrido_em,responsaveis=responsaveis)
        objetos.append(item)
        try:
            consultar(sessao,conta_id,obj.id)
            instrumentos[e['form']].append(dict(situacao=item['situacao'],desde=item['desde'],href=f'/forms34/{obj.id}/blocos/1?{query}'))
        except (ValueError,PermissionError):
            instrumentos[e['form']].append(dict(situacao='Consulta restrita ao perfil autorizado',desde=None,href=None))
    f1=dict(estado=fluxo['estado'],responsavel=fluxo['responsavel'],desde=fluxo['ultima_atividade'][0] if fluxo['ultima_atividade'] else registro.criado_em)
    resultado=decidir_etapa(f1,participacoes,objetos)
    resultado.update(instrumentos=instrumentos, minhas=minhas, form1_confirmado=fluxo['atual']=='confirmar')
    if resultado['form']=='Ciclo completo': resultado['minhas']=[]
    return resultado
