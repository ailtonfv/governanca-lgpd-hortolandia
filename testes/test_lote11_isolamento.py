"""Isolamento da migração 3/4; alterações destrutivas só na cópia _teste."""
import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.banco import motor
from app.modelos import Base, Evento, ParticipacaoForm2
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
    # Act: comparar antes/depois, preservando recusas anteriores por FK.
    # DROP TRIGGER também é revertido pelo savepoint, apenas neste _teste.
    def resultado(com_trigger):
        transacao = sessao.begin_nested()
        try:
            if not com_trigger:
                sessao.execute(text('DROP TRIGGER proteger_evento_forms34 ON evento'))
            sql = ('UPDATE evento SET tipo_evento=tipo_evento WHERE id=:id'
                   if operacao == 'UPDATE' else 'DELETE FROM evento WHERE id=:id')
            try:
                return ('permitido', sessao.execute(text(sql), {'id': eid}).rowcount)
            except IntegrityError as erro:
                return ('recusado', erro.orig.sqlstate, erro.orig.diag.constraint_name)
        finally:
            transacao.rollback()
    antes, depois = resultado(False), resultado(True)
    # Assert: mesmas permissões E mesmas recusas, não um relaxamento da FK.
    assert antes == depois
    assert 'forms34_imutavel' not in depois
    sessao.expire_all()
    assert sessao.get(Evento, eid) is not None
    assert verificar_cadeia(sessao, cid)[0]


def test_create_all_nao_instala_protecoes():
    # Arrange: remover apenas triggers do lote, dentro da cópia _teste.
    assert motor.url.database.endswith('_teste')
    with motor.begin() as c:
        for tabela, trigger in [('evento', 'proteger_evento_forms34'),
                                ('identidade_forms34', 'proteger_forms34'),
                                ('referencia_participacao_forms34', 'proteger_forms34')]:
            c.execute(text(f'DROP TRIGGER IF EXISTS {trigger} ON {tabela}'))
    try:
        # Act: create_all sobre banco com tabelas existentes também não instala.
        Base.metadata.create_all(motor)
        # Assert: só a migração explícita reinstala os três triggers.
        with motor.connect() as c:
            assert c.scalar(text("SELECT count(*) FROM pg_trigger WHERE tgname IN "
                "('proteger_evento_forms34','proteger_forms34')")) == 0
        aplicar(motor)
        with motor.connect() as c:
            assert c.scalar(text("SELECT count(*) FROM pg_trigger WHERE tgname IN "
                "('proteger_evento_forms34','proteger_forms34')")) == 3
    finally:
        aplicar(motor)


@pytest.mark.parametrize('banco', [None, 'demonstracao', 'lgpd_lote9_ficticio',
                                  'lgpd_lote11_ficticio', 'teste_nao_sufixo'])
def test_migracao_recusa_banco_sem_sufixo_antes_de_conectar(banco):
    from types import SimpleNamespace
    # begin() falha se a guarda tentar abrir conexão no banco proibido.
    def conexao_proibida():
        raise AssertionError('Não pode conectar')
    falso = SimpleNamespace(url=SimpleNamespace(database=banco), begin=conexao_proibida)
    with pytest.raises(RuntimeError, match='_teste'):
        aplicar(falso)


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
