"""Correções focalizadas da abertura e do painel de Registros (8Z)."""

import re

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.banco import motor
from app.main import app
from app.modelos import Registro
from testes.apoio import CADASTRO, g1


cliente = TestClient(app)


def _dados_abertura(**alteracoes):
    dados = {
        "conta_id": "CONTA-A1",
        "comando_id": "CMD-8Z-ABERTURA",
        "unidade_id": "UNID-NORTE",
        "tipo_objeto": "atividade",
        "objeto_principal_id": CADASTRO,
        "contexto_id": "CTX-TRIB-01",
        "situacao_canais": "nenhum",
    }
    dados.update(alteracoes)
    return dados


def test_painel_alfa_apresenta_varios_registros_em_cartoes_sem_tabela_cortada():
    # Arrange
    registros = [
        g1("CMD-8Z-PAINEL-1", "OBJ-SRV-001", "CTX-TRIB-03"),
        g1("CMD-8Z-PAINEL-2", "OBJ-SRV-002", "CTX-TRIB-03"),
    ]

    # Act
    pagina = cliente.get("/?conta_id=CONTA-A1")

    # Assert
    assert pagina.status_code == 200
    assert pagina.text.count('class="cartao-mapeamento"') == 2
    assert "<table>" not in pagina.text
    assert pagina.text.count("Ver detalhes do Registro</a>") == 2
    for registro in registros:
        assert registro["codigo_lgpd"] in pagina.text
        assert f'/registros/{registro["registro_id"]}?conta_id=CONTA-A1' in pagina.text


def test_contexto_invalido_e_limpo_sem_aparecer_selecionado():
    # Arrange + Act
    pagina = cliente.get(
        "/registros/novo",
        params={
            "conta_id": "CONTA-A1",
            "unidade_id": "UNID-NORTE",
            "tipo_objeto": "servico",
            "objeto_principal_id": "OBJ-SRV-002",
            "contexto_id": "CTX-URB-01",
            "campos_erro": "contexto_id",
        },
    )

    # Assert
    assert pagina.status_code == 200
    assert 'value="OBJ-SRV-002"' in pagina.text
    assert re.search(r'<option value="CTX-URB-01"[^>]*selected', pagina.text) is None
    assert "A seleção anterior foi removida" in pagina.text
    assert "Selecione um contexto permitido" in pagina.text


def test_api_recusa_contexto_invalido_e_nao_cria_registro(sessao):
    # Arrange + Act
    resposta = cliente.post(
        "/registros",
        data=_dados_abertura(
            comando_id="CMD-8Z-CONTEXTO-INVALIDO",
            contexto_id="CTX-SAU-01",
        ),
    )

    # Assert
    assert resposta.status_code == 200
    assert "contexto de atuação não permitido" in resposta.text
    assert "A seleção anterior foi removida" in resposta.text
    assert sessao.scalar(select(func.count()).select_from(Registro)) == 0


def test_duplicidade_identifica_registro_acessivel_e_oferece_consulta():
    # Arrange
    existente = g1(
        "CMD-8Z-DUPLICIDADE-EXISTENTE",
        CADASTRO,
        "CTX-TRIB-01",
        titulo="Cadastro territorial fictício",
    )

    # Act
    resposta = cliente.post(
        "/registros",
        data=_dados_abertura(comando_id="CMD-8Z-DUPLICIDADE-NOVA"),
    )

    # Assert
    assert resposta.status_code == 200
    assert "Registro já existente" in resposta.text
    assert existente["codigo_lgpd"] in resposta.text
    assert "Cadastro territorial fictício" in resposta.text
    assert "Planejamento Urbano e Gestão Estratégica" in resposta.text
    assert "Gestão cadastral tributária (CTX-TRIB-01)" in resposta.text
    assert "Em andamento" in resposta.text
    assert f'/registros/{existente["registro_id"]}?conta_id=CONTA-A1' in resposta.text
    assert "Consultar este Registro" in resposta.text


def test_duplicidade_de_outra_secretaria_nao_divulga_detalhes():
    # Arrange
    existente = g1(
        "CMD-8Z-DUPLICIDADE-RESTRITA",
        CADASTRO,
        "CTX-TRIB-01",
        titulo="Mapeamento restrito fictício",
    )

    # Act
    resposta = cliente.post(
        "/registros",
        data={
            "conta_id": "CONTA-C1",
            "comando_id": "CMD-8Z-DUPLICIDADE-FORA",
            "unidade_id": "UNID-SUL",
            "tipo_objeto": "atividade",
            "objeto_principal_id": CADASTRO,
            "contexto_id": "CTX-TRIB-01",
            "situacao_canais": "nenhum",
        },
    )

    # Assert
    assert resposta.status_code == 200
    assert "seu perfil não possui acesso aos detalhes" in resposta.text
    assert existente["codigo_lgpd"] not in resposta.text
    assert "Mapeamento restrito fictício" not in resposta.text
    assert "Consultar este Registro" not in resposta.text


def test_css_preserva_60_40_e_empilha_cartoes_em_largura_reduzida():
    # Arrange + Act
    estilo = cliente.get("/estaticos/estilo.css")

    # Assert
    assert estilo.status_code == 200
    assert "minmax(0, 3fr) minmax(18rem, 2fr)" in estilo.text
    assert ".cartao-mapeamento" in estilo.text
    assert "@media (max-width: 950px)" in estilo.text
    assert 'grid-template-areas: "atencao" "mapeamentos"' in estilo.text
    assert "overflow-x: auto" not in estilo.text.split(".lista-mapeamentos-painel", 1)[1].split(".grade-alertas", 1)[0]
