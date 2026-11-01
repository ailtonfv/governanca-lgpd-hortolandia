"""Abertura orientada do Registro LGPD e passagem explícita ao ARP (8X)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.banco import motor
from app.main import app
from app.modelos import ConfirmacaoCanaisRegistro, Registro, RegistroCanal
from app.workflow import criar_registro


cliente = TestClient(app)


def _dados_abertura(**alteracoes):
    dados = {
        "conta_id": "CONTA-A1",
        "comando_id": "CMD-8X-ABERTURA",
        "unidade_id": "UNID-NORTE",
        "tipo_objeto": "servico",
        "objeto_principal_id": "OBJ-SRV-002",
        "contexto_id": "CTX-TRIB-03",
        "situacao_canais": "identificados",
        "canais_ids": "CNL-001",
    }
    dados.update(alteracoes)
    return dados


def test_campos_essenciais_sao_sinalizados_e_escolhas_permanecem_apos_erro():
    # Arrange + Act: falta somente a confirmação dos canais.
    dados = _dados_abertura()
    dados.pop("situacao_canais")
    resposta = cliente.post("/registros", data=dados)

    # Assert
    assert resposta.status_code == 200
    assert "Revise os campos obrigatórios destacados" in resposta.text
    assert 'value="UNID-NORTE" selected' in resposta.text
    assert 'value="servico" required checked' in resposta.text
    assert 'value="OBJ-SRV-002"' in resposta.text
    assert 'value="CTX-TRIB-03"' in resposta.text
    assert 'id="canais-habituais"' in resposta.text
    assert 'aria-invalid="true"' in resposta.text


@pytest.mark.parametrize(
    ("campo", "trecho_erro"),
    [
        ("unidade_id", "Selecione uma Secretaria em que você seja o APA"),
        ("tipo_objeto", "Escolha Serviço, Processo ou Atividade"),
        ("objeto_principal_id", "Selecione um item cadastrado para a Secretaria"),
        ("contexto_id", "Selecione um contexto permitido"),
    ],
)
def test_api_nao_cria_registro_quando_campo_essencial_esta_ausente(
    sessao, campo, trecho_erro,
):
    dados = _dados_abertura(comando_id=f"CMD-8X-AUSENTE-{campo}")
    dados.pop(campo)

    resposta = cliente.post("/registros", data=dados)

    assert resposta.status_code == 200
    assert trecho_erro in resposta.text
    assert sessao.scalar(select(func.count()).select_from(Registro)) == 0


def test_ausencia_de_catalogo_nao_e_interpretada_como_nenhum_canal(sessao):
    # Arrange + Act
    resposta = cliente.post(
        "/registros",
        data=_dados_abertura(
            comando_id="CMD-8X-CATALOGO-INSUFICIENTE",
            objeto_principal_id="OBJ-SRV-900",
            contexto_id="CTX-TRIB-01",
            situacao_canais="informacao_insuficiente",
            canais_ids=[],
        ),
    )

    # Assert
    assert resposta.status_code == 200
    assert "não permite confirmar os canais habituais" in resposta.text
    assert sessao.scalar(select(func.count()).select_from(Registro)) == 0


def test_confirmacao_de_canais_identificados_exige_ao_menos_um_canal(sessao):
    resposta = cliente.post(
        "/registros",
        data=_dados_abertura(
            comando_id="CMD-8X-SEM-CANAL-SELECIONADO",
            canais_ids=[],
        ),
    )

    assert resposta.status_code == 200
    assert "selecione ao menos um canal habitual identificado" in resposta.text
    assert sessao.scalar(select(func.count()).select_from(Registro)) == 0


def test_confirmacao_expressa_de_nenhum_canal_cria_retrato_vazio(sessao):
    resposta = cliente.post(
        "/registros",
        data=_dados_abertura(
            comando_id="CMD-8X-NENHUM-CANAL",
            situacao_canais="nenhum",
            canais_ids=[],
        ),
    )

    assert resposta.status_code == 200
    registro = sessao.scalars(select(Registro)).one()
    assert sessao.get(ConfirmacaoCanaisRegistro, registro.id) is not None
    assert sessao.scalar(select(func.count()).select_from(RegistroCanal)) == 0


def test_criacao_conduz_a_escolha_explicita_do_arp_sem_atribuicao_automatica(sessao):
    resposta = cliente.post(
        "/registros",
        data=_dados_abertura(comando_id="CMD-8X-PASSAGEM-ARP"),
    )

    assert resposta.status_code == 200
    assert "Agora confirme quem será o responsável pelo preenchimento" in resposta.text
    assert 'id="titulo-atribuicao-arp"' in resposta.text
    assert "Ainda não atribuído" in resposta.text
    assert "Eu mesmo, APA atual" in resposta.text
    assert "Designar outro agente público autorizado" in resposta.text
    assert "Pendência de atribuição" in resposta.text
    assert "Matrícula MAT-FICT-0007" in resposta.text


def test_dominio_recusa_contradicao_entre_nenhum_e_canal_selecionado(sessao):
    resultado = criar_registro(
        sessao,
        comando_id="CMD-8X-CANAIS-CONTRADITORIOS",
        conta_id="CONTA-A1",
        unidade_id="UNID-NORTE",
        contexto_id="CTX-TRIB-03",
        titulo_objeto="Certidão fictícia",
        objeto_principal_id="OBJ-SRV-002",
        canais_confirmados_ids=["CNL-001"],
        situacao_canais="nenhum",
    )

    assert not resultado["permitido"]
    assert "não aceita canais selecionados" in resultado["motivo"]
    assert sessao.scalar(select(func.count()).select_from(Registro)) == 0
