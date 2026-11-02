"""Incremento 8AH — separação operacional entre os contratos 2 e 3."""

import re

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.modelos import Instrumento, RascunhoForm1Integral, RascunhoInstrumento
from testes.apoio import CADASTRO, g1


cliente = TestClient(app)


def _registro(prefixo: str):
    return g1(prefixo, CADASTRO, "CTX-TRIB-01", titulo="Atividade fictícia 8AH")


def test_registro_sem_arp_prioriza_designacao_e_nao_expoe_questionario_legado():
    # Arrange
    registro = _registro("8AH-SEM-ARP-G1")

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )

    # Assert
    assert pagina.status_code == 200
    assert "Designação do ARP" in pagina.text
    assert pagina.text.index("Designação do ARP") < pagina.text.index(
        "Informações do Registro — somente leitura"
    )
    assert "Iniciar FORM 1 Integral" not in pagina.text
    assert 'class="formulario formulario-integral"' not in pagina.text
    assert "Questionário resumido de demonstração" not in pagina.text
    assert "data-instrumento-regressao" not in pagina.text
    assert "Questionário sintético legado — recurso exclusivo de demonstração técnica" not in pagina.text
    assert "questionario-sintetico-legado" not in pagina.text


def test_designacao_confirmada_permite_ao_arp_iniciar_no_bloco_1():
    # Arrange
    registro = _registro("8AH-DESIGNAR-G1")
    designacao = cliente.post(
        f"/registros/{registro['registro_id']}/form1-integral/atribuir-arp",
        data={
            "conta_id": "CONTA-A1",
            "comando_id": "8AH-DESIGNAR-ARP",
            "modo": "outro",
            "arp_pessoa_id": "PESSOA-G",
            "versao_lida": "0",
        },
    )

    # Act
    pagina_arp = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-G1"}
    )
    inicio = cliente.post(
        f"/registros/{registro['registro_id']}/form1-integral/iniciar",
        data={"conta_id": "CONTA-G1", "comando_id": "8AH-INICIAR-INTEGRAL"},
        follow_redirects=False,
    )

    # Assert
    assert designacao.status_code == 200
    assert "Designação do ARP confirmada" in designacao.text
    assert "ARP vigente:</strong> matrícula MAT-FICT-0007 · Servidor Épsilon" in designacao.text
    assert "Iniciar FORM 1 Integral" in pagina_arp.text
    assert inicio.status_code == 303
    assert inicio.headers["location"].endswith("#titulo-bloco-1")
    destino = cliente.get(inicio.headers["location"])
    assert "FORM 1 — Levantamento Inicial do Tratamento de Dados Pessoais" in destino.text
    assert "FORM 1 — Etapa 1 de 4 — Bloco 1 de 14" in destino.text
    assert 'id="titulo-bloco-1"' in destino.text
    assert "Salvar rascunho do FORM 1" in destino.text
    assert "data-instrumento-regressao" not in destino.text


def test_painel_do_arp_inicia_form1_integral_diretamente_no_bloco_1():
    # Arrange
    registro = _registro("8AH-PAINEL-INICIAR-G1")
    cliente.post(
        f"/registros/{registro['registro_id']}/form1-integral/atribuir-arp",
        data={
            "conta_id": "CONTA-A1",
            "comando_id": "8AH-PAINEL-ATRIBUIR-ARP",
            "modo": "outro",
            "arp_pessoa_id": "PESSOA-G",
            "versao_lida": "0",
        },
    )
    painel = cliente.get("/", params={"conta_id": "CONTA-G1"})
    formulario = re.search(
        rf'<form class="acao-iniciar-form1-integral"[^>]*'
        rf'action="((?:http://testserver)?/registros/{registro["registro_id"]}/form1-integral/iniciar)"'
        rf'[^>]*>(.*?)</form>',
        painel.text,
        re.DOTALL,
    )

    # Act
    assert formulario is not None
    comando = re.search(
        r'name="comando_id" value="([^"]+)"', formulario.group(2)
    )
    inicio = cliente.post(
        formulario.group(1),
        data={"conta_id": "CONTA-G1", "comando_id": comando.group(1)},
        follow_redirects=False,
    )

    # Assert
    assert painel.status_code == 200
    assert ">Iniciar FORM 1 Integral</button>" in formulario.group(2)
    assert (
        f'/registros/{registro["registro_id"]}?conta_id=CONTA-G1'
        '#titulo-form1-integral'
    ) not in painel.text
    assert inicio.status_code == 303
    assert inicio.headers["location"].endswith("#titulo-bloco-1")
    assert "questionario-sintetico-legado" not in inicio.headers["location"]
    destino = cliente.get(inicio.headers["location"])
    assert destino.status_code == 200
    assert "FORM 1 — Etapa 1 de 4 — Bloco 1 de 14" in destino.text
    assert 'id="titulo-bloco-1"' in destino.text
    assert "Iniciar FORM 1 Integral" not in destino.text
    assert "data-instrumento-regressao" not in destino.text
    assert "questionario-sintetico-legado" not in destino.text


def test_salvar_e_avancar_preserva_resposta_sem_abrir_instrumento_legado(sessao):
    # Arrange
    registro = _registro("8AH-AVANCAR-G1")
    cliente.post(
        f"/registros/{registro['registro_id']}/form1-integral/atribuir-arp",
        data={
            "conta_id": "CONTA-A1", "comando_id": "8AH-AVANCAR-ARP",
            "modo": "proprio", "versao_lida": "0",
        },
    )
    cliente.post(
        f"/registros/{registro['registro_id']}/form1-integral/iniciar",
        data={"conta_id": "CONTA-A1", "comando_id": "8AH-AVANCAR-INICIAR"},
    )

    # Act
    resposta = cliente.post(
        f"/registros/{registro['registro_id']}/form1-integral/bloco-1/salvar",
        data={
            "conta_id": "CONTA-A1", "comando_id": "8AH-AVANCAR-B1",
            "versao_lida": "1", "acao_pos_salvar": "proximo",
            "referencia_existente": "Não", "referencia_institucional": "",
            "fluxo_recorrente": "Sim",
        },
        follow_redirects=False,
    )

    # Assert
    assert resposta.status_code == 303
    assert resposta.headers["location"].endswith("#titulo-bloco-2")
    retomada = cliente.get(resposta.headers["location"])
    assert "Bloco 1 atualizado" in retomada.text
    assert 'value="Sim" selected' in retomada.text
    assert "data-instrumento-regressao" not in retomada.text
    rascunho = sessao.get(RascunhoForm1Integral, registro["registro_id"])
    assert rascunho.conteudo["respostas"]["1.4"] == "Sim"


def test_questionario_legado_permanece_controlado_e_independente(sessao):
    # Arrange
    registro = _registro("8AH-LEGADO-G1")
    normal = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )

    # Act
    legado = cliente.get(
        f"/registros/{registro['registro_id']}/questionario-sintetico-legado",
        params={"conta_id": "CONTA-A1"},
    )
    inicio_legado = cliente.post(
        f"/registros/{registro['registro_id']}/form1/iniciar",
        data={"conta_id": "CONTA-A1", "comando_id": "8AH-LEGADO-I1"},
    )

    # Assert
    assert "data-instrumento-regressao" not in normal.text
    assert "questionario-sintetico-legado" not in normal.text
    assert legado.status_code == 200
    assert "Questionário sintético legado — recurso exclusivo de demonstração técnica" in legado.text
    assert "Iniciar preenchimento" not in legado.text
    assert "FORM 1 — Levantamento Inicial do Tratamento de Dados Pessoais" not in legado.text
    assert "Questionário sintético legado iniciado" in inicio_legado.text
    instrumento = sessao.scalars(
        select(Instrumento).where(Instrumento.registro_id == registro["registro_id"])
    ).one()
    assert sessao.get(RascunhoInstrumento, instrumento.id) is not None
    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]) is None
