"""Canais do catálogo geral declarados pelo APA na abertura G1 (8AA)."""

from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select, text
from sqlalchemy.orm import Session

from app.banco import motor
from app.main import app
from app.modelos import (
    ConfirmacaoCanaisRegistro,
    Evento,
    ObjetoCanal,
    Registro,
    RegistroCanal,
)
from app.workflow import criar_registro
from migracoes.canais_declarados_apa import aplicar as aplicar_migracao_18
from migracoes.canais_declarados_apa import reverter as reverter_migracao_18


cliente = TestClient(app)


def _abrir_sem_vinculos(**alteracoes):
    dados = {
        "conta_id": "CONTA-A1",
        "comando_id": "CMD-8AA-CANAIS-GERAIS",
        "unidade_id": "UNID-NORTE",
        "tipo_objeto": "servico",
        "objeto_principal_id": "OBJ-SRV-900",
        "contexto_id": "CTX-TRIB-01",
        "situacao_canais": "identificados",
        "canais_ids": ["CNL-001", "CNL-003", "CNL-007"],
    }
    dados.update(alteracoes)
    return cliente.post("/registros", data=dados)


def test_objeto_sem_vinculos_aceita_varios_canais_do_catalogo_geral(sessao):
    # Arrange
    vinculos_antes = sessao.scalar(select(func.count()).select_from(ObjetoCanal))

    # Act
    resposta = _abrir_sem_vinculos()

    # Assert
    assert resposta.status_code == 200
    registro = sessao.scalars(select(Registro)).one()
    itens = sessao.scalars(
        select(RegistroCanal)
        .where(RegistroCanal.registro_id == registro.id)
        .order_by(RegistroCanal.canal_id_snapshot)
    ).all()
    assert [item.canal_id_snapshot for item in itens] == ["CNL-001", "CNL-003", "CNL-007"]
    assert {item.origem_confirmacao for item in itens} == {"DECLARACAO_APA"}
    assert all(item.objeto_canal_id is None for item in itens)
    assert sessao.scalar(select(func.count()).select_from(ObjetoCanal)) == vinculos_antes


def test_declaracao_preserva_autoria_estado_versao_e_evento(sessao):
    # Arrange + Act
    _abrir_sem_vinculos(comando_id="CMD-8AA-AUTORIA")
    registro = sessao.scalars(select(Registro)).one()

    # Assert
    confirmacao = sessao.get(ConfirmacaoCanaisRegistro, registro.id)
    evento = sessao.scalars(
        select(Evento).where(Evento.registro_id == registro.id, Evento.codigo_evento == "G1")
    ).one()
    assert confirmacao.confirmado_por_id == "PESSOA-A"
    assert confirmacao.confirmado_em is not None
    assert confirmacao.situacao == "identificados"
    assert confirmacao.versao_contrato_g1 == 4
    assert evento.versao_esquema_evento == 4
    assert evento.conteudo["situacao_canais"] == "identificados"
    assert evento.conteudo["versao_contrato_g1"] == 4
    assert {item["origem_confirmacao"] for item in evento.conteudo[
        "canais_habituais_confirmados"
    ]} == {"DECLARACAO_APA"}


def test_declaracao_direta_repetida_e_idempotente(sessao):
    # Arrange + Act
    primeira = _abrir_sem_vinculos(comando_id="CMD-8AA-IDEMPOTENCIA")
    repetida = _abrir_sem_vinculos(comando_id="CMD-8AA-IDEMPOTENCIA")

    # Assert
    assert primeira.status_code == 200
    assert repetida.status_code == 200
    assert sessao.scalar(select(func.count()).select_from(Registro)) == 1
    assert sessao.scalar(select(func.count()).select_from(RegistroCanal)) == 3
    assert sessao.scalar(
        select(func.count()).select_from(Evento).where(Evento.codigo_evento == "G1")
    ) == 1


def test_consulta_recupera_canais_declarados_sem_confundir_com_catalogo(sessao):
    # Arrange
    resposta_abertura = _abrir_sem_vinculos(comando_id="CMD-8AA-CONSULTA")
    registro = sessao.scalars(select(Registro)).one()

    # Act
    pagina = cliente.get(f"/registros/{registro.id}", params={"conta_id": "CONTA-A1"})

    # Assert
    assert resposta_abertura.status_code == 200
    assert pagina.status_code == 200
    assert "Presencial / balcão de atendimento" in pagina.text
    assert "Telefone" in pagina.text
    assert "WhatsApp corporativo" in pagina.text
    assert pagina.text.count("informado pelo APA para este Registro") == 3


def test_informacao_pendente_cria_retrato_distinto_de_nenhum(sessao):
    # Arrange + Act
    resposta = _abrir_sem_vinculos(
        comando_id="CMD-8AA-PENDENTE",
        situacao_canais="informacao_insuficiente",
        canais_ids=[],
    )

    # Assert
    registro = sessao.scalars(select(Registro)).one()
    confirmacao = sessao.get(ConfirmacaoCanaisRegistro, registro.id)
    assert resposta.status_code == 200
    assert confirmacao.situacao == "informacao_insuficiente"
    assert sessao.scalar(select(func.count()).select_from(RegistroCanal)) == 0
    pagina = cliente.get(f"/registros/{registro.id}", params={"conta_id": "CONTA-A1"})
    assert "confirmação dos canais permanece pendente" in pagina.text
    assert "Isso não significa que nenhum canal se aplica" in pagina.text


def test_api_rejeita_pendente_com_canal_e_nao_cria_registro(sessao):
    # Arrange + Act
    resultado = criar_registro(
        sessao,
        comando_id="CMD-8AA-CONTRADICAO",
        conta_id="CONTA-A1",
        unidade_id="UNID-NORTE",
        contexto_id="CTX-TRIB-01",
        titulo_objeto="Serviço de atendimento fictício",
        objeto_principal_id="OBJ-SRV-900",
        canais_confirmados_ids=["CNL-003"],
        situacao_canais="informacao_insuficiente",
    )

    # Assert
    assert not resultado["permitido"]
    assert "informação pendente" in resultado["motivo"]
    assert sessao.scalar(select(func.count()).select_from(Registro)) == 0


def test_agente_sem_exercicio_apa_nao_declara_canal_geral(sessao):
    # Arrange + Act
    resultado = criar_registro(
        sessao,
        comando_id="CMD-8AA-SEM-APA",
        conta_id="CONTA-B1",
        unidade_id="UNID-NORTE",
        contexto_id="CTX-TRIB-01",
        titulo_objeto="Atividade cadastral fictícia",
        objeto_principal_id="OBJ-ATV-020",
        canais_confirmados_ids=["CNL-003"],
        situacao_canais="identificados",
    )

    # Assert
    assert not resultado["permitido"]
    assert "Agente Público Autorizado" in resultado["motivo"]
    assert sessao.scalar(select(func.count()).select_from(Registro)) == 0


def test_migracao_18_preserva_retrato_anterior_e_e_reversivel_sem_dados_v4(sessao):
    # Arrange: um retrato criado pela versão anterior e a estrutura equivalente à migração 17.
    resposta = cliente.post(
        "/registros",
        data={
            "conta_id": "CONTA-A1",
            "comando_id": "CMD-8AA-MIGRACAO",
            "unidade_id": "UNID-NORTE",
            "tipo_objeto": "servico",
            "objeto_principal_id": "OBJ-SRV-002",
            "contexto_id": "CTX-TRIB-03",
            "situacao_canais": "identificados",
            "canais_ids": "CNL-001",
        },
    )
    assert resposta.status_code == 200
    with motor.begin() as conexao:
        conexao.execute(text("ALTER TABLE registro_canal DROP CONSTRAINT ck_registro_canal_origem"))
        conexao.execute(text("ALTER TABLE registro_canal DROP COLUMN origem_confirmacao"))
        conexao.execute(text("ALTER TABLE registro_canal DROP COLUMN canal_id_catalogo CASCADE"))
        conexao.execute(text("ALTER TABLE registro_canal ALTER COLUMN objeto_canal_id SET NOT NULL"))
        conexao.execute(text(
            "ALTER TABLE confirmacao_canais_registro "
            "DROP CONSTRAINT ck_confirmacao_canais_situacao"
        ))
        conexao.execute(text("ALTER TABLE confirmacao_canais_registro DROP COLUMN situacao"))
        conexao.execute(text(
            "ALTER TABLE confirmacao_canais_registro DROP COLUMN versao_contrato_g1"
        ))

    # Act
    with Session(motor) as sessao_migracao, sessao_migracao.begin():
        aplicar_migracao_18(sessao_migracao)

    # Assert
    with Session(motor) as verificacao:
        confirmacao = verificacao.scalars(select(ConfirmacaoCanaisRegistro)).one()
        item = verificacao.scalars(select(RegistroCanal)).one()
        assert confirmacao.situacao == "identificados"
        assert confirmacao.versao_contrato_g1 == 3
        assert item.canal_id_catalogo == "CNL-001"
        assert item.origem_confirmacao == "VINCULO_OBJETO"
    with Session(motor) as sessao_reversao, sessao_reversao.begin():
        reverter_migracao_18(sessao_reversao)
    assert "situacao" not in {item["name"] for item in inspect(motor).get_columns(
        "confirmacao_canais_registro"
    )}
    with Session(motor) as sessao_restauracao, sessao_restauracao.begin():
        aplicar_migracao_18(sessao_restauracao)
