from app.identificacao_registro import identificar
"""Leitura dos cartões: reutiliza o escopo das páginas de destino, sem conceder acesso."""
from urllib.parse import urlencode
from datetime import timezone
from sqlalchemy import select, or_
from app.consultas_interface import carregar_painel
from app.fila_form2 import pessoa_ativa, autorizado
from app.modelos import ParticipacaoForm2, Registro, IdentidadeForms34, ComplementoForm2, AtribuicaoForm1Integral
from app.providencias import classificar
from app.continuidade_apa import unidades_em_que_e_apa_atual
from app.origem_form2 import nome_objeto_em_analise
from app.fluxo_forms34 import consultar
from app.leitura_atos34 import situacao_atual


def itens_em_andamento(sessao, conta_id):
    from app.modelos import ContextoAtuacao
    contextos={c.id:c.nome for c in sessao.scalars(select(ContextoAtuacao))}
    pessoa = pessoa_ativa(sessao, conta_id)
    query = urlencode({'conta_id': conta_id})
    itens = {n: [] for n in range(1, 5)}
    painel = carregar_painel(sessao, conta_id)
    unidades_apa = unidades_em_que_e_apa_atual(sessao, pessoa.id)
    for r in (painel or {}).get('registros', []):
        if r['estado_codigo'] in ('concluido', 'cancelado'):
            continue
        registro = sessao.get(Registro, r['id'])
        estado = {**r, 'designar_arp': r['unidade_id'] in unidades_apa and not sessao.get(AtribuicaoForm1Integral, r['id'])}
        proxima = classificar(1, estado)
        itens[1].append(dict(contexto=r.get('contexto_nome',''),desde=registro.criado_em.astimezone(timezone.utc).isoformat(), **proxima, texto=f"{identificar(r)} — {r['situacao_form1_integral']}",
                            href=(f"/registros/{r['id']}/form1-integral/conferencia-interna?{query}"
                                  if proxima['ato'] == 'conferir' else
                                  f"/registros/{r['id']}/form1-rev22?{query}" if proxima['pendente'] and proxima['etapa'] == 'f1-levanta' else
                                  f"/registros/{r['id']}?{query}")))
    linhas = sessao.execute(select(ParticipacaoForm2, Registro).join(Registro,
        Registro.id == ParticipacaoForm2.registro_id).where(
        or_(ParticipacaoForm2.responsavel_id == pessoa.id,
            (ParticipacaoForm2.tipo == 'dpo') & ParticipacaoForm2.responsavel_id.is_(None)),
        ParticipacaoForm2.estado.in_(['aguardando', 'em_atendimento'])).order_by(Registro.codigo_lgpd, ParticipacaoForm2.id)).all()
    for p, r in linhas:
        if not autorizado(sessao, pessoa, p):
            continue
        tipo = {'servico': 'Serviço', 'processo': 'Processo', 'atividade': 'Atividade'}.get(r.tipo_objeto, r.tipo_objeto)
        nome = nome_objeto_em_analise(sessao, r.id, p.snapshot_id)
        complemento = sessao.scalar(select(ComplementoForm2).where(ComplementoForm2.participacao_id == p.id))
        abertas = list(sessao.scalars(select(ParticipacaoForm2.id).where(ParticipacaoForm2.origem_id == p.id, ParticipacaoForm2.estado != 'concluida')))
        proxima = classificar(2, dict(tipo=p.tipo, estado=p.estado, complemento=complemento.estado if complemento else None, consultas_abertas=bool(abertas)))
        itens[2].append(dict(contexto=contextos.get(r.contexto_atuacao_id,''),desde=p.entrada_em.astimezone(timezone.utc).isoformat(), **proxima, texto=f'{identificar(r,nome)}',
                            href=f'/form2/participacoes/{p.id}?{query}'))
    for obj in sessao.scalars(select(IdentidadeForms34).order_by(IdentidadeForms34.codigo)):
        try:
            _, ref, estado, _, papeis, _ = consultar(sessao, conta_id, obj.id)
        except (PermissionError, ValueError):
            continue
        r = sessao.get(Registro, obj.registro_id)
        from app.acompanhamento_forms34 import resumo
        acompanhamento = resumo(sessao,obj,estado,papeis,pessoa.id)
        itens[ref.form].append(dict(contexto=contextos.get(r.contexto_atuacao_id,''),texto=f"{identificar(r)} · {acompanhamento['titulo']} — {acompanhamento['situacao']}",
                                  **{k: acompanhamento[k] for k in ('pendente','etapa','ato','botao','pendencia')},
                                  desde=obj.criado_em.astimezone(timezone.utc).isoformat(),
                                  href=f"/forms34/{obj.id}/blocos/{acompanhamento['bloco']}?{query}"))
    for lista in itens.values():
        lista.sort(key=lambda item:(not item['pendente'], item['desde'], item['href']))
    return itens


def cartoes_em_andamento(sessao, conta_id, listas=None):
    query = urlencode({'conta_id': conta_id})
    destinos = {1: f'/central/itens/1?{query}', 2: f'/form2/filas?{query}',
                3: f'/forms34?{query}&form=3', 4: f'/forms34?{query}&form=4'}
    return {n: dict(itens=lista[:3], mais=max(0, len(lista)-3),
                    pendencias=[i for i in lista if i.get('pendente')][:3],
                    total_pendencias=sum(bool(i.get('pendente')) for i in lista),
                    acompanhamento=[i for i in lista if not i.get('pendente')],
                    lista=f'/central/itens/{n}?{query}', acesso=destinos[n])
            for n, lista in (listas if listas is not None else itens_em_andamento(sessao, conta_id)).items()}
