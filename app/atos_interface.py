"""Metadados de atos reais, sem confiar em autoria/data recebidas pela URL."""
from sqlalchemy import select
from app.modelos import Comando, Evento, Pessoa
from app.apresentacao_form2 import data_local


def ato_registrado(sessao, comando_id, conta_id, registro_id=None, participacao_id=None):
    comando = sessao.get(Comando, comando_id) if comando_id else None
    if not comando or comando.conta_id != conta_id or not (comando.resultado or {}).get('permitido'):
        return None
    busca = select(Evento).where(Evento.comando_id == comando.id, Evento.ator_id == comando.ator_id)
    if registro_id:
        busca = busca.where(Evento.registro_id == registro_id)
    if participacao_id:
        busca = busca.where(Evento.cadeia_id == participacao_id)
    evento = sessao.scalar(busca.order_by(Evento.ordem_no_comando.desc()).limit(1))
    pessoa = sessao.get(Pessoa, comando.ator_id)
    if not evento or not pessoa:
        return None
    return {'autor': pessoa.nome, 'quando': data_local(evento.ocorrido_em)}
