"""Leitura dos cartões: reutiliza o escopo das páginas de destino, sem conceder acesso."""
from urllib.parse import urlencode
from sqlalchemy import select
from app.consultas_interface import carregar_painel
from app.fila_form2 import pessoa_ativa, autorizado
from app.modelos import ParticipacaoForm2, Registro, IdentidadeForms34
from app.origem_form2 import nome_objeto_em_analise
from app.fluxo_forms34 import consultar
from app.leitura_atos34 import situacao_atual


def itens_em_andamento(sessao, conta_id):
    pessoa = pessoa_ativa(sessao, conta_id)
    query = urlencode({'conta_id': conta_id})
    itens = {n: [] for n in range(1, 5)}
    painel = carregar_painel(sessao, conta_id)
    for r in (painel or {}).get('registros', []):
        if r['estado_codigo'] in ('concluido', 'cancelado'):
            continue
        itens[1].append(dict(texto=f"{r['codigo_lgpd']} · {r['titulo']} — {r['situacao_form1_integral']}",
                            href=f"/registros/{r['id']}?{query}"))
    linhas = sessao.execute(select(ParticipacaoForm2, Registro).join(Registro,
        Registro.id == ParticipacaoForm2.registro_id).where(
        ParticipacaoForm2.responsavel_id == pessoa.id,
        ParticipacaoForm2.estado == 'em_atendimento').order_by(Registro.codigo_lgpd, ParticipacaoForm2.id)).all()
    for p, r in linhas:
        if not autorizado(sessao, pessoa, p):
            continue
        tipo = {'servico': 'Serviço', 'processo': 'Processo', 'atividade': 'Atividade'}.get(r.tipo_objeto, r.tipo_objeto)
        nome = nome_objeto_em_analise(sessao, r.id, p.snapshot_id)
        itens[2].append(dict(texto=f'{r.codigo_lgpd} · {nome} ({tipo})',
                            href=f'/form2/participacoes/{p.id}?{query}'))
    for obj in sessao.scalars(select(IdentidadeForms34).order_by(IdentidadeForms34.codigo)):
        try:
            _, ref, estado, _, papeis, _ = consultar(sessao, conta_id, obj.id)
        except (PermissionError, ValueError):
            continue
        r = sessao.get(Registro, obj.registro_id)
        from app.acompanhamento_forms34 import resumo
        acompanhamento = resumo(sessao,obj,estado,papeis,pessoa.id)
        itens[ref.form].append(dict(texto=f"{r.codigo_lgpd} · {acompanhamento['titulo']} — {acompanhamento['situacao']}",
                                  pendente=acompanhamento['pendente'],
                                  href=f"/forms34/{obj.id}/blocos/{acompanhamento['bloco']}?{query}"))
    for n in (3,4):itens[n].sort(key=lambda item:not item['pendente'])
    return itens


def cartoes_em_andamento(sessao, conta_id):
    query = urlencode({'conta_id': conta_id})
    destinos = {1: f'/central/itens/1?{query}', 2: f'/form2/filas?{query}',
                3: f'/forms34?{query}&form=3', 4: f'/forms34?{query}&form=4'}
    return {n: dict(itens=lista[:3], mais=max(0, len(lista)-3),
                    lista=f'/central/itens/{n}?{query}', acesso=destinos[n])
            for n, lista in itens_em_andamento(sessao, conta_id).items()}
