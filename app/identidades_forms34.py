"""Reserva técnica Rnn/Ann, sem avaliação ou plano institucional."""
from uuid import uuid4
from sqlalchemy import select, func
from app.modelos import (ReferenciaParticipacaoForms34 as Referencia,
    IdentidadeForms34 as Identidade)
from app.comandos import fechar_comando
from app.eventos import agora_utc
from app.infra_forms34 import _atomica, _abrir, _registro, _gravar


@_atomica
def reservar_identidade(sessao, *, comando_id, conta_id, participacao_id, tipo, chave_origem):
    """Reserva Rnn/Ann; não cria avaliação ou plano de ação institucional."""
    if tipo not in ('R', 'A') or not isinstance(chave_origem, str) or not 1 <= len(chave_origem.strip()) <= 100:
        raise ValueError("Tipo ou chave de origem inválidos.")
    dados = dict(participacao_id=participacao_id, tipo=tipo, chave_origem=chave_origem)
    comando, resposta = _abrir(sessao, comando_id, conta_id, 'base34_reservar_identidade', dados)
    if resposta is not None:
        return resposta
    ref = sessao.get(Referencia, participacao_id)
    if not ref or ref.form != {'R': 3, 'A': 4}[tipo]:
        raise ValueError("Participação técnica incompatível com a identidade.")
    registro = _registro(sessao, ref.registro_id)
    existente = sessao.scalar(select(Identidade).where(
        Identidade.registro_id == registro.id, Identidade.tipo == tipo,
        Identidade.chave_origem == chave_origem))
    if existente:
        if existente.participacao_id != participacao_id:
            raise ValueError("A chave de origem já pertence a outra participação.")
        return fechar_comando(comando, {'permitido': True, 'identidade_id': existente.id,
                                      'codigo': existente.codigo, 'existente': True})
    numero = 1 + (sessao.scalar(select(func.max(Identidade.numero)).where(
        Identidade.registro_id == registro.id, Identidade.tipo == tipo)) or 0)
    obj = Identidade(id=str(uuid4()), registro_id=registro.id, participacao_id=ref.id,
                    tipo=tipo, numero=numero, codigo=f'{registro.codigo_lgpd}-{tipo}{numero:02}',
                    chave_origem=chave_origem, criado_em=agora_utc())
    sessao.add(obj)
    sessao.flush()
    ev = _gravar(sessao, comando, 'forms34_objeto', obj.id, registro.id,
                 'base34_identidade_reservada', dict(dados, codigo=obj.codigo,
                    referencia_id=ref.id, fonte_lacre=ref.fonte_lacre))
    return fechar_comando(comando, {'permitido': True, 'identidade_id': obj.id,
                                  'codigo': obj.codigo, 'evento_id': ev.id, 'existente': False})
