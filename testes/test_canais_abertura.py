"""Confirmação histórica dos canais habituais durante a abertura do Registro."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select, text, update
from sqlalchemy.orm import Session

from app.banco import motor
from app.eventos import verificar_cadeia
from app.main import app
from app.modelos import (
    Canal,
    Comando,
    ConfirmacaoCanaisRegistro,
    Evento,
    EventoAuditoria,
    ObjetoCanal,
    Registro,
    RegistroCanal,
)
from app.workflow import criar_registro
from migracoes.canais_registro import aplicar as aplicar_migracao
from testes.apoio import evento_g1, g1, sem_reexecucao


cliente = TestClient(app)


def _canais_do_registro(sessao, registro_id):
    return list(sessao.scalars(
        select(RegistroCanal)
        .where(RegistroCanal.registro_id == registro_id)
        .order_by(RegistroCanal.canal_id_snapshot)
    ))


def test_apa_confirma_nenhum_canal_e_a_decisao_fica_explicita(sessao):
    # Arrange + Act
    resultado = g1(
        "CMD-CANAL-ZERO", "OBJ-SRV-900", "CTX-TRIB-01",
        canais_confirmados_ids=[],
    )

    # Assert
    confirmacao = sessao.get(ConfirmacaoCanaisRegistro, resultado["registro_id"])
    assert resultado["permitido"]
    assert resultado["canais_confirmados"] == []
    assert confirmacao.objeto_id == "OBJ-SRV-900"
    assert confirmacao.confirmado_por_id == "PESSOA-A"
    assert _canais_do_registro(sessao, resultado["registro_id"]) == []
    evento = evento_g1(resultado["codigo_lgpd"])
    assert evento.versao_esquema_evento == 3
    assert evento.conteudo["canais_habituais_confirmados"] == []


def test_apa_confirma_um_canal_habitual(sessao):
    # Arrange + Act
    resultado = g1(
        "CMD-CANAL-UM", "OBJ-SRV-002", "CTX-TRIB-03",
        canais_confirmados_ids=["CNL-001"],
    )

    # Assert
    canais = _canais_do_registro(sessao, resultado["registro_id"])
    assert resultado["canais_confirmados"] == ["CNL-001"]
    assert len(canais) == 1
    assert canais[0].canal_id_snapshot == "CNL-001"
    assert canais[0].canal_nome_snapshot == "Balcão de atendimento (fictício)"


def test_apa_confirma_varios_canais_sem_criar_varios_registros(sessao):
    # Arrange + Act
    resultado = g1(
        "CMD-CANAL-VARIOS", "OBJ-SRV-001", "CTX-TRIB-03",
        canais_confirmados_ids=["CNL-002", "CNL-001"],
    )

    # Assert
    assert sessao.scalar(select(func.count()).select_from(Registro)) == 1
    assert [item.canal_id_snapshot for item in _canais_do_registro(
        sessao, resultado["registro_id"]
    )] == ["CNL-001", "CNL-002"]
    assert resultado["canais_confirmados"] == ["CNL-001", "CNL-002"]


@pytest.mark.parametrize("canais", [["CNL-003"], ["CNL-INEXISTENTE"]])
def test_rejeita_canal_nao_vinculado_ou_forjado(sessao, canais):
    # Arrange + Act
    resultado = g1(
        f"CMD-CANAL-INVALIDO-{canais[0]}", "OBJ-SRV-002", "CTX-TRIB-03",
        canais_confirmados_ids=canais,
    )

    # Assert
    assert not resultado["permitido"]
    assert "fora dos vínculos habituais vigentes" in resultado["motivo"]
    assert sessao.scalar(select(func.count()).select_from(Registro)) == 0
    assert sessao.scalar(select(func.count()).select_from(ConfirmacaoCanaisRegistro)) == 0
    auditoria = sessao.scalars(select(EventoAuditoria)).one()
    assert auditoria.conteudo["acao_tentada"] == "criar_registro"


def test_rejeita_canal_repetido(sessao):
    resultado = g1(
        "CMD-CANAL-REPETIDO", "OBJ-SRV-002", "CTX-TRIB-03",
        canais_confirmados_ids=["CNL-001", "CNL-001"],
    )

    assert not resultado["permitido"]
    assert "mais de uma vez" in resultado["motivo"]
    assert sessao.scalar(select(func.count()).select_from(Registro)) == 0


@pytest.mark.parametrize("situacao", ["canal_inativo", "vinculo_encerrado"])
def test_rejeita_canal_inativo_ou_com_vigencia_encerrada(sessao, situacao):
    # Arrange
    if situacao == "canal_inativo":
        sessao.execute(update(Canal).where(Canal.id == "CNL-001").values(ativo=False))
    else:
        sessao.execute(
            update(ObjetoCanal)
            .where(
                ObjetoCanal.objeto_id == "OBJ-SRV-002",
                ObjetoCanal.canal_id == "CNL-001",
            )
            .values(vigente_ate=datetime.now(timezone.utc) - timedelta(seconds=1))
        )
    sessao.commit()

    # Act
    resultado = g1(
        "CMD-CANAL-INATIVO", "OBJ-SRV-002", "CTX-TRIB-03",
        canais_confirmados_ids=["CNL-001"],
    )

    # Assert
    assert not resultado["permitido"]
    assert sessao.scalar(select(func.count()).select_from(Registro)) == 0


def test_somente_apa_em_exercicio_pode_confirmar_canais(sessao):
    resultado = g1(
        "CMD-CANAL-SEM-APA", "OBJ-ATV-020", "CTX-TRIB-01",
        conta="CONTA-B1", canais_confirmados_ids=[],
    )

    assert not resultado["permitido"]
    assert "Agente Público Autorizado" in resultado["motivo"]
    assert sessao.scalar(select(func.count()).select_from(ConfirmacaoCanaisRegistro)) == 0


def test_confirmacao_de_canais_e_idempotente_e_detecta_reuso_da_chave(sessao):
    original = g1(
        "CMD-CANAL-IDEM", "OBJ-SRV-001", "CTX-TRIB-03",
        canais_confirmados_ids=["CNL-001", "CNL-002"],
    )
    repetido = g1(
        "CMD-CANAL-IDEM", "OBJ-SRV-001", "CTX-TRIB-03",
        canais_confirmados_ids=["CNL-002", "CNL-001"],
    )
    alterado = g1(
        "CMD-CANAL-IDEM", "OBJ-SRV-001", "CTX-TRIB-03",
        canais_confirmados_ids=["CNL-001"],
    )

    assert original["permitido"]
    assert repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(original)
    assert not alterado["permitido"]
    assert "reutilização indevida" in alterado["motivo"]
    assert sessao.scalar(select(func.count()).select_from(Registro)) == 1
    assert sessao.scalar(select(func.count()).select_from(RegistroCanal)) == 2


def test_evento_g1_audita_retrato_e_mantem_cadeia_integra(sessao):
    resultado = g1(
        "CMD-CANAL-EVENTO", "OBJ-SRV-002", "CTX-TRIB-03",
        canais_confirmados_ids=["CNL-001"],
    )

    evento = evento_g1(resultado["codigo_lgpd"])
    retrato = evento.conteudo["canais_habituais_confirmados"]
    assert retrato == [{
        "objeto_canal_id": retrato[0]["objeto_canal_id"],
        "objeto_id": "OBJ-SRV-002",
        "canal_id": "CNL-001",
        "canal_nome_snapshot": "Balcão de atendimento (fictício)",
    }]
    assert verificar_cadeia(sessao, resultado["codigo_lgpd"])[0]


def test_catalogo_futuro_nao_altera_retrato_do_registro(sessao):
    # Arrange
    resultado = g1(
        "CMD-CANAL-SNAPSHOT", "OBJ-SRV-002", "CTX-TRIB-03",
        canais_confirmados_ids=["CNL-001"],
    )
    registro_antes = sessao.get(Registro, resultado["registro_id"])
    codigo_antes = registro_antes.codigo_lgpd

    # Act: a curadoria evolui depois da abertura.
    sessao.get(Canal, "CNL-001").nome_canonico = "Canal renomeado (fictício)"
    vinculo = sessao.scalars(select(ObjetoCanal).where(
        ObjetoCanal.objeto_id == "OBJ-SRV-002",
        ObjetoCanal.canal_id == "CNL-001",
        ObjetoCanal.vigente_ate.is_(None),
    )).one()
    vinculo.vigente_ate = func.now()
    sessao.commit()

    # Assert
    retrato = _canais_do_registro(sessao, resultado["registro_id"])[0]
    assert retrato.canal_nome_snapshot == "Balcão de atendimento (fictício)"
    assert retrato.objeto_id_snapshot == "OBJ-SRV-002"
    assert sessao.get(Registro, resultado["registro_id"]).codigo_lgpd == codigo_antes


def test_dois_pedidos_simultaneos_criam_um_registro_e_um_retrato():
    def abrir():
        return g1(
            "CMD-CANAL-CONCORRENTE", "OBJ-SRV-001", "CTX-TRIB-03",
            canais_confirmados_ids=["CNL-001", "CNL-002"],
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados = list(executor.map(lambda _: abrir(), range(2)))

    assert sum(item["reexecutado"] is False for item in resultados) == 1
    assert sum(item["reexecutado"] is True for item in resultados) == 1
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Registro)) == 1
        assert sessao.scalar(select(func.count()).select_from(ConfirmacaoCanaisRegistro)) == 1
        assert sessao.scalar(select(func.count()).select_from(RegistroCanal)) == 2


def test_falha_no_evento_desfaz_registro_confirmacao_e_comando(monkeypatch):
    def falhar(*args, **kwargs):
        raise RuntimeError("falha fictícia ao registrar evento")

    monkeypatch.setattr("app.workflow.registrar_evento", falhar)
    with pytest.raises(RuntimeError):
        with Session(motor) as sessao, sessao.begin():
            criar_registro(
                sessao,
                comando_id="CMD-CANAL-ROLLBACK",
                conta_id="CONTA-A1",
                unidade_id="UNID-NORTE",
                contexto_id="CTX-TRIB-03",
                titulo_objeto="Certidão fictícia",
                objeto_principal_id="OBJ-SRV-002",
                canais_confirmados_ids=["CNL-001"],
            )

    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Registro)) == 0
        assert sessao.scalar(select(func.count()).select_from(ConfirmacaoCanaisRegistro)) == 0
        assert sessao.scalar(select(func.count()).select_from(RegistroCanal)) == 0
        assert sessao.get(Comando, "CMD-CANAL-ROLLBACK") is None


def test_percurso_nuclear_permanece_sem_projecao_e_com_evento_2(sessao):
    resultado = g1("CMD-CANAL-LEGADO", "OBJ-SRV-002", "CTX-TRIB-03")

    assert resultado["permitido"]
    assert "canais_confirmados" not in resultado
    assert sessao.get(ConfirmacaoCanaisRegistro, resultado["registro_id"]) is None
    assert evento_g1(resultado["codigo_lgpd"]).versao_esquema_evento == 2


def test_tela_apresenta_canais_habituais_depois_do_objeto():
    resposta = cliente.get("/registros/novo", params={"conta_id": "CONTA-A1"})

    assert resposta.status_code == 200
    assert resposta.text.index("3. Item do catálogo oficial") < resposta.text.index(
        "4. Canais habituais aplicáveis"
    )
    assert "Balcão de atendimento (fictício)" in resposta.text
    assert "Portal da Prefeitura (fictício)" in resposta.text
    assert 'data-objeto-canais="OBJ-SRV-001"' in resposta.text
    assert "Desmarcar todas as opções confirma que nenhum canal se aplica" in resposta.text
    assert "cidadãos, telefonemas nem protocolos individuais" in resposta.text


def test_tela_confirma_canal_e_exibe_retrato_no_registro(sessao):
    resposta = cliente.post(
        "/registros",
        data={
            "conta_id": "CONTA-A1",
            "comando_id": "CMD-CANAL-UI",
            "tipo_objeto": "servico",
            "objeto_principal_id": "OBJ-SRV-002",
            "unidade_id": "UNID-NORTE",
            "contexto_id": "CTX-TRIB-03",
            "canais_ids": "CNL-001",
        },
    )

    assert resposta.status_code == 200
    assert "Canais habituais confirmados na abertura" in resposta.text
    assert "Balcão de atendimento (fictício)" in resposta.text
    registro = sessao.scalars(select(Registro).where(
        Registro.titulo_objeto == "Certidão de débitos (fictício)"
    )).one()
    assert [item.canal_id_snapshot for item in _canais_do_registro(
        sessao, registro.id
    )] == ["CNL-001"]


def test_tela_nao_aceita_canal_forjado(sessao):
    resposta = cliente.post(
        "/registros",
        data={
            "conta_id": "CONTA-A1",
            "comando_id": "CMD-CANAL-UI-FORJADO",
            "tipo_objeto": "servico",
            "objeto_principal_id": "OBJ-SRV-002",
            "unidade_id": "UNID-NORTE",
            "contexto_id": "CTX-TRIB-03",
            "canais_ids": "CNL-003",
        },
    )

    assert resposta.status_code == 200
    assert "canal fora dos vínculos habituais vigentes" in resposta.text
    assert sessao.scalar(select(func.count()).select_from(Registro)) == 0


def test_migracao_15_cria_projecoes_sem_alterar_registro_existente(sessao):
    # Arrange: simula o esquema da versão 14 e cria um Registro pelo contrato nuclear.
    with motor.begin() as conexao:
        conexao.execute(text("DROP TABLE registro_canal"))
        conexao.execute(text("DROP TABLE confirmacao_canais_registro"))
    legado = g1("CMD-CANAL-MIGRACAO", "OBJ-SRV-002", "CTX-TRIB-03")

    # Act
    with Session(motor) as sessao_migracao, sessao_migracao.begin():
        aplicar_migracao(sessao_migracao)

    # Assert
    inspetor = inspect(motor)
    assert "confirmacao_canais_registro" in inspetor.get_table_names()
    assert "registro_canal" in inspetor.get_table_names()
    assert {fk["referred_table"] for fk in inspetor.get_foreign_keys("registro_canal")} == {
        "confirmacao_canais_registro", "objeto_canal", "pessoa",
    }
    with Session(motor) as verificacao:
        registro = verificacao.get(Registro, legado["registro_id"])
        assert registro.codigo_lgpd == legado["codigo_lgpd"]
        assert verificacao.get(ConfirmacaoCanaisRegistro, legado["registro_id"]) is None
        assert verificacao.scalar(select(func.count()).select_from(Evento)) == 1
