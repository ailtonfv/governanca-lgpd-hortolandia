"""Incremento 8W — piloto de ajuda contextual da Cartilha no FORM 1."""

from fastapi.testclient import TestClient

from app.ajudas_cartilha_form1 import (
    AJUDAS_CARTILHA_FORM1,
    VERSAO_CARTILHA_AJUDAS_FORM1,
)
from app.consultas_interface import carregar_registro
from app.main import app
from testes.test_bloco5_form1_integral import _rascunho_pronto


cliente = TestClient(app)
IDS_PILOTO = {"2.1", "2.11", "2.12", "4.1", "5.1", "6.1", "7.1", "9.1"}


def test_piloto_reproduz_os_oito_campos_da_matriz_sem_criar_perguntas():
    # Arrange
    ids_catalogados = set(AJUDAS_CARTILHA_FORM1)

    # Act / Assert
    assert ids_catalogados == IDS_PILOTO
    assert VERSAO_CARTILHA_AJUDAS_FORM1 == "REV30.11"
    assert all(item["texto"] for item in AJUDAS_CARTILHA_FORM1.values())
    assert all(item["secao"] for item in AJUDAS_CARTILHA_FORM1.values())
    assert all(item["limite"] for item in AJUDAS_CARTILHA_FORM1.values())


def test_projecao_associa_ajuda_somente_aos_campos_do_piloto(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F18W-PROJECAO")

    # Act
    _, projecao = carregar_registro(sessao, "CONTA-A1", registro["registro_id"])
    integral = projecao["form1_integral"]
    campos = {}
    for numero in range(1, 15):
        campos.update(integral.get(f"campos_bloco_{numero}", {}))

    # Assert
    assert {
        campo_id for campo_id, campo in campos.items()
        if campo.get("ajuda_cartilha")
    } == IDS_PILOTO
    assert campos["2.1"]["ajuda_cartilha"]["secao"].startswith("5.2 ")
    assert campos["5.1"]["ajuda_cartilha"]["versao"] == "REV30.11"


def test_interface_exibe_ajudas_sob_demanda_sem_link_inoperante(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F18W-INTERFACE")

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}?conta_id=CONTA-A1"
    )
    estilo = cliente.get("/estaticos/estilo.css")

    # Assert
    assert pagina.status_code == 200
    assert pagina.text.count("Entenda esta pergunta") == 8
    assert "Cartilha LGPD REV30.11 — seção 5.2 Operações, canais e ambientes" in pagina.text
    assert "Cartilha LGPD REV30.11 — seção 8.1 Necessidade de conhecer e acesso mínimo" in pagina.text
    assert "WhatsApp é canal de entrada, não repositório oficial" in pagina.text
    assert "Consultar Cartilha LGPD" not in pagina.text
    assert estilo.status_code == 200
    assert ".ajuda-cartilha-form1 summary:focus-visible" in estilo.text
