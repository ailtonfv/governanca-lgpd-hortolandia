"""Correções da avaliação visual da abertura e da designação do ARP (8Y)."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


cliente = TestClient(app)
RAIZ = Path(__file__).resolve().parents[1]


def _abrir_registro(comando_id="CMD-8Y-ABERTURA"):
    return cliente.post(
        "/registros",
        data={
            "conta_id": "CONTA-A1",
            "comando_id": comando_id,
            "unidade_id": "UNID-NORTE",
            "tipo_objeto": "servico",
            "objeto_principal_id": "OBJ-SRV-002",
            "contexto_id": "CTX-TRIB-03",
            "situacao_canais": "identificados",
            "canais_ids": "CNL-001",
        },
    )


def test_abertura_explica_catalogo_demonstrativo_e_tres_situacoes_de_canais():
    # Arrange + Act
    pagina = cliente.get("/registros/novo", params={"conta_id": "CONTA-A1"})

    # Assert
    assert pagina.status_code == 200
    assert "Item do catálogo da demonstração" in pagina.text
    assert "não representam inventário municipal homologado" in pagina.text
    assert "Por quais canais as demandas chegam habitualmente?" in pagina.text
    assert "Conheço os canais utilizados" in pagina.text
    assert "Nenhum canal de entrada se aplica ao objeto" in pagina.text
    assert "Ainda preciso confirmar os canais" in pagina.text
    assert "não significa ausência de canais" in pagina.text
    assert "não informe um contexto livre" in pagina.text


def test_designacao_arp_distingue_selecao_confirmacao_e_responsavel_atual():
    # Arrange + Act
    pagina = _abrir_registro()

    # Assert
    assert pagina.status_code == 200
    assert "ARP atual" in pagina.text
    assert "ARP selecionado para designação" in pagina.text
    assert "Confirmar designação do ARP" in pagina.text
    assert "Selecionar uma pessoa não confirma a designação" in pagina.text
    assert "A confirmação também não concede acesso" in pagina.text


def test_jornada_operacional_nao_expoe_rotulos_tecnicos_dos_contratos():
    # Arrange + Act
    pagina = _abrir_registro("CMD-8Y-ROTULOS")

    # Assert
    for rotulo_tecnico in (
        "PoC nuclear",
        "PoC ampliada",
        "Instrumento sintético",
        "contrato 2",
        "contrato 3",
        "Separação entre instrumentos",
        "Iniciar preenchimento (I1)",
        "Salvar rascunho (I2)",
    ):
        assert rotulo_tecnico not in pagina.text
    assert "Outros recursos do ambiente de demonstração" in pagina.text
    assert "Questionário resumido de demonstração" in pagina.text


def test_layout_preserva_paineis_60_40_e_adapta_designacao_arp():
    # Arrange + Act
    css = (RAIZ / "app" / "estaticos" / "estilo.css").read_text(encoding="utf-8")

    # Assert
    assert "minmax(0, 3fr) minmax(18rem, 2fr)" in css
    assert ".controle-designacao-arp" in css
    assert "grid-template-columns: 1fr" in css
