"""Consolidação das modalidades institucionais do catálogo geral no 8AA."""

from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.banco import motor
from app.main import app
from app.modelos import Canal, ObjetoCanal, RegistroCanal
from migracoes.catalogo_canais_institucionais import aplicar as aplicar_migracao_19


cliente = TestClient(app)

CANAIS_ESPERADOS = [
    ("CNL-001", "Presencial / balcão de atendimento"),
    ("CNL-002", "Portal da Prefeitura"),
    ("CNL-003", "Telefone"),
    ("CNL-004", "Ouvidoria"),
    ("CNL-005", "e-SIC"),
    ("CNL-006", "Central 156"),
    ("CNL-007", "WhatsApp corporativo"),
    ("CNL-008", "E-mail institucional"),
]


def test_catalogo_geral_contem_oito_modalidades_sem_criar_vinculos(sessao):
    # Arrange + Act
    canais = sessao.execute(
        select(Canal.id, Canal.nome_canonico).order_by(Canal.id)
    ).all()

    # Assert
    assert canais == CANAIS_ESPERADOS
    assert sessao.scalar(select(func.count()).select_from(ObjetoCanal)) == 3
    assert sessao.scalar(
        select(func.count()).select_from(ObjetoCanal).where(
            ObjetoCanal.canal_id.in_({"CNL-006", "CNL-007", "CNL-008"})
        )
    ) == 0


def test_abertura_exibe_nomes_institucionais_sem_sufixo_ficticio():
    # Arrange + Act
    pagina = cliente.get("/registros/novo", params={"conta_id": "CONTA-A1"})

    # Assert
    assert pagina.status_code == 200
    for _, nome in CANAIS_ESPERADOS:
        assert nome in pagina.text
    assert "Ouvidoria (fictícia)" not in pagina.text
    assert "(fictício)" not in pagina.text.split('id="catalogo-canais-geral"', 1)[1].split(
        'id="canais-sem-vinculo"', 1
    )[0]


def test_migracao_19_preserva_snapshot_e_nao_cria_vinculos(sessao):
    # Arrange: simula o catálogo anterior e cria um retrato histórico com seu nome antigo.
    sessao.execute(update(Canal).where(Canal.id == "CNL-001").values(
        nome_canonico="Balcão de atendimento (fictício)"
    ))
    sessao.execute(delete(Canal).where(Canal.id.in_({"CNL-006", "CNL-007", "CNL-008"})))
    sessao.commit()
    resposta = cliente.post("/registros", data={
        "conta_id": "CONTA-A1",
        "comando_id": "CMD-8AA-MIGRACAO-CATALOGO",
        "unidade_id": "UNID-NORTE",
        "tipo_objeto": "servico",
        "objeto_principal_id": "OBJ-SRV-002",
        "contexto_id": "CTX-TRIB-03",
        "situacao_canais": "identificados",
        "canais_ids": "CNL-001",
    })
    assert resposta.status_code == 200

    # Act
    with Session(motor) as migracao, migracao.begin():
        aplicar_migracao_19(migracao)

    # Assert
    with Session(motor) as verificacao:
        assert verificacao.get(Canal, "CNL-001").nome_canonico == (
            "Presencial / balcão de atendimento"
        )
        assert [verificacao.get(Canal, canal_id).nome_canonico
                for canal_id in ("CNL-006", "CNL-007", "CNL-008")] == [
            "Central 156", "WhatsApp corporativo", "E-mail institucional",
        ]
        assert verificacao.scalars(select(RegistroCanal)).one().canal_nome_snapshot == (
            "Balcão de atendimento (fictício)"
        )
        assert verificacao.scalar(
            select(func.count()).select_from(ObjetoCanal).where(
                ObjetoCanal.canal_id.in_({"CNL-006", "CNL-007", "CNL-008"})
            )
        ) == 0
