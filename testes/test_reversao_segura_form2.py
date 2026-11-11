"""Reversão de esquema somente vazio, preservando dados e dependências."""
import pytest
from sqlalchemy import inspect, select, func, text
from app.modelos import ParticipacaoForm2, VersaoForm1Integral, ResumoDpo
from migracoes.fila_form2 import aplicar, reverter
from migracoes.versao_form1_integral import reverter as reverter_origem
from testes.test_filas_form2_rev22 import origem

TABELAS={'participacao_form2','complemento_form2','aviso_dpo','resumo_dpo'}

def existentes(sessao):
    return set(inspect(sessao.connection()).get_table_names())

def test_reversao_fila_vazia_e_reaplicacao(sessao):
    reverter(sessao)
    assert not TABELAS & existentes(sessao)
    assert 'versao_form1_integral' in existentes(sessao)
    reverter(sessao)  # idempotência em infraestrutura já revertida
    aplicar(sessao)
    assert TABELAS <= existentes(sessao)
    sessao.commit()

def test_reversao_fila_com_dados_recusada_sem_perda(sessao):
    origem(sessao)
    ids=list(sessao.scalars(select(ParticipacaoForm2.id)))
    snapshots=list(sessao.scalars(select(VersaoForm1Integral.id)))
    with pytest.raises(RuntimeError,match='contém snapshots ou outros dados'):
        reverter(sessao)
    assert TABELAS <= existentes(sessao)
    assert list(sessao.scalars(select(ParticipacaoForm2.id)))==ids
    assert list(sessao.scalars(select(VersaoForm1Integral.id)))==snapshots
    sessao.rollback()

def test_reversao_preserva_resumo_dpo_mesmo_sem_participacoes(sessao):
    sessao.add(ResumoDpo(periodo='2026-11-1',estado='pendente'));sessao.commit()
    with pytest.raises(RuntimeError,match='resumo_dpo'):
        reverter(sessao)
    assert TABELAS <= existentes(sessao)
    assert sessao.get(ResumoDpo,'2026-11-1') is not None
    sessao.rollback()

def test_reversao_origem_recusa_dependencias_instaladas_antes_do_ddl(sessao):
    with pytest.raises(RuntimeError,match='migrações dependentes'):
        reverter_origem(sessao)
    assert TABELAS <= existentes(sessao)
    assert 'versao_form1_integral' in existentes(sessao)
    # A recusa é da aplicação; a transação continua utilizável.
    assert sessao.scalar(select(func.count()).select_from(VersaoForm1Integral))==0
    sessao.rollback()

def test_reversao_recusa_dependente_externo_sem_cascade(sessao):
    sessao.execute(text('CREATE TABLE dependencia_sintetica (id text REFERENCES participacao_form2(id))'))
    with pytest.raises(RuntimeError,match='dependencia_sintetica'):
        reverter(sessao)
    assert TABELAS <= existentes(sessao)
    sessao.rollback()

def test_reversao_ddl_desfeita_por_rollback_da_transacao(sessao):
    reverter(sessao)
    assert not TABELAS & existentes(sessao)
    sessao.rollback()
    assert TABELAS <= existentes(sessao)
