"""Isolamento da migração 3/4; alterações destrutivas só na cópia _teste."""
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.banco import motor
from app.modelos import Evento, ParticipacaoForm2
from app.eventos import verificar_cadeia
from migracoes.base_forms34 import aplicar
from testes.test_filas_form2_rev22 import origem
from testes.test_lote11 import referencia, identidade


@pytest.fixture(scope='module', autouse=True)
def migracao_explicita(esquema):
    aplicar(motor)


@pytest.mark.parametrize('cadeia', ['registro', 'participacao_form2'])
@pytest.mark.parametrize('operacao', ['UPDATE', 'DELETE'])
def test_sql_legado_sem_nova_restricao(sessao, cadeia, operacao):
    # Arrange: eventos genuínos dos fluxos F1/F2 na massa fictícia.
    r = origem(sessao)
    sessao.commit()
    ev = sessao.scalar(select(Evento).where(
        Evento.registro_id == r['registro_id'], Evento.cadeia_tipo == cadeia))
    assert ev is not None
    eid, cid = ev.id, ev.cadeia_id
    # Act: SQL deliberadamente direto; rollback restaura inclusive o lacre.
    transacao = sessao.begin_nested()
    try:
        sql = ('UPDATE evento SET tipo_evento=tipo_evento WHERE id=:id'
               if operacao == 'UPDATE' else 'DELETE FROM evento WHERE id=:id')
        assert sessao.execute(text(sql), {'id': eid}).rowcount == 1
    finally:
        transacao.rollback()
    # Assert: não é permissão do domínio; só prova que o trigger não interfere.
    sessao.expire_all()
    assert sessao.get(Evento, eid) is not None
    assert verificar_cadeia(sessao, cid)[0]


@pytest.mark.parametrize('form', [3, 4])
@pytest.mark.parametrize('cadeia', ['forms34_contexto', 'forms34_objeto'])
@pytest.mark.parametrize('operacao', ['UPDATE', 'DELETE', 'DISFARCAR'])
def test_evento_forms34_nao_pode_ser_alterado_ou_disfarcado(sessao, form, cadeia, operacao):
    # Arrange: contexto e identidade via domínio, ambos F3 e F4.
    r = origem(sessao)
    p = sessao.scalar(select(ParticipacaoForm2).where(
        ParticipacaoForm2.registro_id == r['registro_id']))
    ev = sessao.scalar(select(Evento).where(Evento.cadeia_id == p.id).order_by(Evento.id.desc()))
    fonte = dict(registro_id=r['registro_id'], fonte_form=2, fonte_id=str(ev.id))
    sessao.commit()
    pid = referencia(sessao, fonte, form=form)
    obj = identidade(sessao, pid, tipo='R' if form == 3 else 'A')
    cid = pid if cadeia == 'forms34_contexto' else obj['identidade_id']
    alvo = sessao.scalar(select(Evento).where(Evento.cadeia_id == cid))
    # Act / Assert: mesmo mudar cadeia_tipo é recusado pelo predicado OLD.
    sql = {'UPDATE': 'UPDATE evento SET tipo_evento=tipo_evento WHERE id=:id',
           'DELETE': 'DELETE FROM evento WHERE id=:id',
           'DISFARCAR': "UPDATE evento SET cadeia_tipo='registro' WHERE id=:id"}[operacao]
    with pytest.raises(IntegrityError):
        with sessao.begin_nested():
            sessao.execute(text(sql), {'id': alvo.id})
    assert verificar_cadeia(sessao, cid)[0]
