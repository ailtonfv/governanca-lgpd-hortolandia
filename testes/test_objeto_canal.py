"""Associação transversal de canais aos objetos do catálogo.

Os cenários usam somente identificadores e conteúdos fictícios.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.banco import motor
from app.modelos import Canal, ObjetoCanal, ObjetoCatalogo
from migracoes.objeto_canal import aplicar as aplicar_migracao


def _vinculos_vigentes(sessao, objeto_id):
    return list(sessao.scalars(
        select(ObjetoCanal)
        .where(
            ObjetoCanal.objeto_id == objeto_id,
            ObjetoCanal.vigente_ate.is_(None),
        )
        .order_by(ObjetoCanal.canal_id)
    ))


@pytest.mark.parametrize(
    ("objeto_id", "tipo_esperado"),
    [
        ("OBJ-SRV-900", "servico"),
        ("OBJ-PRC-010", "processo"),
        ("OBJ-ATV-001", "atividade"),
    ],
)
def test_objeto_admite_zero_um_e_varios_canais(sessao, objeto_id, tipo_esperado):
    # Arrange
    objeto = sessao.get(ObjetoCatalogo, objeto_id)
    assert objeto.tipo_objeto == tipo_esperado
    assert _vinculos_vigentes(sessao, objeto_id) == []

    # Act + Assert: um canal habitual
    sessao.add(ObjetoCanal(objeto_id=objeto_id, canal_id="CNL-001"))
    sessao.commit()
    assert [v.canal_id for v in _vinculos_vigentes(sessao, objeto_id)] == ["CNL-001"]

    # Act + Assert: vários canais habituais no mesmo objeto
    sessao.add(ObjetoCanal(objeto_id=objeto_id, canal_id="CNL-002"))
    sessao.commit()
    assert [v.canal_id for v in _vinculos_vigentes(sessao, objeto_id)] == [
        "CNL-001",
        "CNL-002",
    ]


def test_vinculo_de_canal_nao_e_herdado_por_outro_objeto(sessao):
    # Arrange + Act
    sessao.add(ObjetoCanal(objeto_id="OBJ-PRC-010", canal_id="CNL-003"))
    sessao.commit()

    # Assert
    assert [v.canal_id for v in _vinculos_vigentes(sessao, "OBJ-PRC-010")] == ["CNL-003"]
    assert _vinculos_vigentes(sessao, "OBJ-SRV-010") == []
    assert _vinculos_vigentes(sessao, "OBJ-ATV-001") == []


@pytest.mark.parametrize(
    ("objeto_id", "canal_id"),
    [
        ("OBJ-INEXISTENTE", "CNL-001"),
        ("OBJ-PRC-010", "CNL-INEXISTENTE"),
    ],
)
def test_rejeita_vinculo_com_referencia_invalida(sessao, objeto_id, canal_id):
    # Arrange + Act + Assert
    with pytest.raises(IntegrityError), sessao.begin_nested():
        sessao.add(ObjetoCanal(objeto_id=objeto_id, canal_id=canal_id))
        sessao.flush()


def test_rejeita_vinculo_vigente_duplicado(sessao):
    # Arrange: o vínculo já vem da carga fictícia legada.
    assert len(_vinculos_vigentes(sessao, "OBJ-SRV-001")) == 2

    # Act + Assert
    with pytest.raises(IntegrityError), sessao.begin_nested():
        sessao.add(ObjetoCanal(objeto_id="OBJ-SRV-001", canal_id="CNL-001"))
        sessao.flush()


def test_vigencia_preserva_historico_e_admite_novo_vinculo_atual(sessao):
    # Arrange
    anterior = sessao.scalar(select(ObjetoCanal).where(
        ObjetoCanal.objeto_id == "OBJ-SRV-002",
        ObjetoCanal.canal_id == "CNL-001",
        ObjetoCanal.vigente_ate.is_(None),
    ))
    encerrado_em = datetime(2026, 10, 27, 12, 0, tzinfo=timezone.utc)

    # Act
    anterior.vigente_ate = encerrado_em
    sessao.flush()
    atual = ObjetoCanal(objeto_id="OBJ-SRV-002", canal_id="CNL-001")
    sessao.add(atual)
    sessao.commit()

    # Assert
    historico = list(sessao.scalars(select(ObjetoCanal).where(
        ObjetoCanal.objeto_id == "OBJ-SRV-002",
        ObjetoCanal.canal_id == "CNL-001",
    ).order_by(ObjetoCanal.id)))
    assert len(historico) == 2
    assert historico[0].id == anterior.id
    assert historico[0].vigente_ate == encerrado_em
    assert historico[1].id == atual.id
    assert historico[1].vigente_ate is None


def test_carga_preserva_os_vinculos_de_servicos_preexistentes(sessao):
    # Arrange + Act
    pares = set(sessao.execute(
        select(ObjetoCanal.objeto_id, ObjetoCanal.canal_id)
    ).all())

    # Assert
    assert pares == {
        ("OBJ-SRV-001", "CNL-001"),
        ("OBJ-SRV-001", "CNL-002"),
        ("OBJ-SRV-002", "CNL-001"),
    }


def test_migracao_14_renomeia_sem_perder_vinculos():
    # Arrange: reproduz a estrutura e os nomes legados sobre a carga existente.
    with motor.begin() as conexao:
        antes = conexao.execute(text("""
            SELECT id, objeto_id, canal_id, vigente_de, vigente_ate, observacao
              FROM objeto_canal
             ORDER BY id
        """)).mappings().all()
        conexao.execute(text(
            "ALTER INDEX uq_objeto_canal_vigente RENAME TO uq_servico_canal_vigente"
        ))
        conexao.execute(text(
            "ALTER TABLE objeto_canal RENAME COLUMN objeto_id TO servico_id"
        ))
        conexao.execute(text(
            "ALTER TABLE objeto_canal RENAME TO servico_canal"
        ))

    # Act
    with Session(motor) as sessao, sessao.begin():
        aplicar_migracao(sessao)

    # Assert
    inspetor = inspect(motor)
    assert "objeto_canal" in inspetor.get_table_names()
    assert "servico_canal" not in inspetor.get_table_names()
    assert {c["name"] for c in inspetor.get_columns("objeto_canal")} >= {
        "id",
        "objeto_id",
        "canal_id",
        "vigente_de",
        "vigente_ate",
        "observacao",
    }
    assert "uq_objeto_canal_vigente" in {
        indice["name"] for indice in inspetor.get_indexes("objeto_canal")
    }
    with motor.connect() as conexao:
        depois = conexao.execute(text("""
            SELECT id, objeto_id, canal_id, vigente_de, vigente_ate, observacao
              FROM objeto_canal
             ORDER BY id
        """)).mappings().all()
    assert [dict(linha) for linha in depois] == [dict(linha) for linha in antes]
    assert len(depois) == 3
    assert sessao_get_canal("CNL-001") is True


def sessao_get_canal(canal_id):
    """Confirma que a migração não alterou o catálogo canônico de canais."""
    with Session(motor) as sessao:
        return sessao.get(Canal, canal_id) is not None
