"""Infraestrutura transacional interna, sem política de competências."""
from functools import wraps
from uuid import UUID
from sqlalchemy import select
from app.modelos import Registro, Pessoa, Conta, Evento
from app.comandos import abrir_comando
from app.eventos import registrar_evento, registrar_auditoria


def _atomica(fn):
    @wraps(fn)
    def executar(sessao, **kwargs):
        with sessao.begin_nested():
            return fn(sessao, **kwargs)
    return executar


def _uuid(valor):
    if not isinstance(valor, str) or str(UUID(valor)) != valor:
        raise ValueError("Identificador técnico inválido.")
    return valor


def _ator(sessao, conta_id):
    conta = sessao.get(Conta, conta_id)
    pessoa = sessao.get(Pessoa, conta.pessoa_id) if conta and conta.ativa else None
    if not pessoa or not pessoa.ativa:
        raise PermissionError("Autoria indisponível.")
    return pessoa.id


def _abrir(sessao, comando_id, conta_id, tipo, dados):
    ator = _ator(sessao, conta_id)
    return abrir_comando(sessao, comando_id, tipo, dict(dados, conta_id=conta_id,
                        ator_id=ator), 'pessoa', ator, conta_id)


def _registro(sessao, registro_id):
    registro = sessao.scalar(select(Registro).where(Registro.id == registro_id)
                            .with_for_update().execution_options(populate_existing=True))
    if not registro:
        raise ValueError("Registro de origem inexistente.")
    return registro


def _gravar(sessao, comando, cadeia_tipo, cadeia_id, registro_id, tipo, dados):
    ev = registrar_evento(sessao, comando, cadeia_tipo, cadeia_id, tipo, dados,
                         registro_id=registro_id, versao_regra='FORMS34-BASE-v1')
    registrar_auditoria(sessao, tipo, comando.ator_tipo, comando.ator_id,
                       {'registro_id': registro_id, 'objeto_id': cadeia_id}, comando_id=comando.id)
    return ev


def historico(sessao, identidade_id):
    """Somente fatos internos; camada chamadora deverá aplicar escopo de acesso."""
    return sessao.scalars(select(Evento).where(
        Evento.cadeia_tipo == 'forms34_objeto', Evento.cadeia_id == identidade_id)
        .order_by(Evento.sequencia_cadeia)).all()
