"""Fila provisória exclusiva do DPO; solicitar não cria entrada no catálogo."""
from sqlalchemy import select
from app.fila_form2 import pessoa_ativa, unidades
from app.modelos import IdentidadeForms34, Registro
from app.fluxo_forms34 import estado
from app.apresentacao_form2 import data_local


def consultar(sessao, conta):
    pessoa=pessoa_ativa(sessao,conta)
    if not unidades(sessao,pessoa.id,'governanca_protecao_dados'):
        raise PermissionError('Consulta exclusiva do Encarregado de Dados (DPO).')
    pedidos=[]
    for obj in sessao.scalars(select(IdentidadeForms34).where(IdentidadeForms34.tipo=='A')):
        try:e=estado(sessao,obj.id)
        except ValueError:continue
        for pedido in e.get('solicitacoes_tema',[]):
            pedidos.append(dict(**pedido,registro=sessao.get(Registro,obj.registro_id).codigo_lgpd,
                acao=obj.codigo,quando=data_local(pedido['em'])))
    return sorted(pedidos,key=lambda p:p['em'])
