"""Integração somente leitura dos canais históricos com a pergunta 2.1."""

from sqlalchemy import update
from fastapi.testclient import TestClient

from app.atribuicao_form1_integral import atribuir_arp_form1_integral
from app.consultas_interface import carregar_registro
from app.main import app
from app.modelos import Canal, RascunhoForm1Integral, RegistroCanal
from app.rascunho_form1_integral import (
    iniciar_rascunho_form1_integral,
    salvar_bloco_2_form1_integral,
)
from testes.apoio import CADASTRO, g1


cliente = TestClient(app)


def _registro_integral(sessao, prefixo, *, objeto="OBJ-SRV-001", contexto="CTX-TRIB-03",
                       canais=None):
    resultado = g1(
        f"{prefixo}-G1", objeto, contexto,
        titulo="Serviço multicanal fictício",
        canais_confirmados_ids=canais,
    )
    atribuir_arp_form1_integral(
        sessao, comando_id=f"{prefixo}-ARP", conta_id="CONTA-A1",
        registro_id=resultado["registro_id"], modo="proprio", versao_lida=0,
    )
    sessao.commit()
    iniciar_rascunho_form1_integral(
        sessao, comando_id=f"{prefixo}-INICIAR", conta_id="CONTA-A1",
        registro_id=resultado["registro_id"],
    )
    sessao.commit()
    return resultado


def test_arp_consulta_um_ou_varios_canais_historicos_na_pergunta_2_1(sessao):
    # Arrange
    registro = _registro_integral(
        sessao, "CMD-F1-CANAIS-VARIOS", canais=["CNL-001", "CNL-002"]
    )

    # Act
    _, resumo = carregar_registro(sessao, "CONTA-A1", registro["registro_id"])
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}?conta_id=CONTA-A1"
    )

    # Assert
    leitura = resumo["form1_integral"]["leitura_2_1"]
    assert list(resumo["form1_integral"]["campos_bloco_2"])[0] == "2.1"
    assert leitura["estado"] == "canais_confirmados"
    assert [item["id"] for item in leitura["canais"]] == ["CNL-001", "CNL-002"]
    assert leitura["somente_leitura"] is True
    assert pagina.status_code == 200
    assert 'data-canais-2-1-estado="canais_confirmados"' in pagina.text
    assert "Balcão de atendimento (fictício)" in pagina.text
    assert "Portal da Prefeitura (fictício)" in pagina.text
    assert 'name="campo__2.1"' not in pagina.text


def test_ausencia_de_canais_confirmada_e_estado_explicito(sessao):
    # Arrange
    registro = _registro_integral(
        sessao, "CMD-F1-CANAIS-ZERO", objeto="OBJ-SRV-900",
        contexto="CTX-TRIB-01", canais=[],
    )

    # Act
    _, resumo = carregar_registro(sessao, "CONTA-A1", registro["registro_id"])

    # Assert
    leitura = resumo["form1_integral"]["leitura_2_1"]
    assert leitura["estado"] == "ausencia_confirmada"
    assert leitura["canais"] == []
    assert leitura["confirmado_por"] == "Servidor Alfa (fictício)"


def test_registro_antigo_sem_confirmacao_permanece_distinto_e_compativel(sessao):
    # Arrange
    resultado = g1(
        "CMD-F1-CANAIS-LEGADO-G1", CADASTRO, "CTX-TRIB-01",
        titulo="Atividade legada fictícia",
    )
    atribuir_arp_form1_integral(
        sessao, comando_id="CMD-F1-CANAIS-LEGADO-ARP", conta_id="CONTA-A1",
        registro_id=resultado["registro_id"], modo="proprio", versao_lida=0,
    )
    sessao.commit()
    iniciar_rascunho_form1_integral(
        sessao, comando_id="CMD-F1-CANAIS-LEGADO-INICIAR", conta_id="CONTA-A1",
        registro_id=resultado["registro_id"],
    )
    sessao.commit()

    # Act
    _, resumo = carregar_registro(sessao, "CONTA-A1", resultado["registro_id"])
    pagina = cliente.get(
        f"/registros/{resultado['registro_id']}?conta_id=CONTA-A1"
    )

    # Assert
    leitura = resumo["form1_integral"]["leitura_2_1"]
    assert leitura["estado"] == "sem_confirmacao_historica"
    assert leitura["somente_leitura"] is False
    assert 'name="campo__2.1"' in pagina.text


def test_arp_nao_pode_sobrescrever_confirmacao_historica_em_2_1(sessao):
    # Arrange
    registro = _registro_integral(
        sessao, "CMD-F1-CANAIS-IMUTAVEL", canais=["CNL-001"]
    )

    # Act
    resultado = salvar_bloco_2_form1_integral(
        sessao, comando_id="CMD-F1-CANAIS-IMUTAVEL-SALVAR", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"2.1": "Telefone"},
    )
    sessao.commit()

    # Assert
    rascunho = sessao.get(RascunhoForm1Integral, registro["registro_id"])
    canais = sessao.query(RegistroCanal).filter_by(
        registro_id=registro["registro_id"]
    ).all()
    assert not resultado["permitido"]
    assert "somente para consulta" in resultado["motivo"]
    assert rascunho.versao_rascunho == 1
    assert "2.1" not in rascunho.conteudo["respostas"]
    assert [item.canal_id_snapshot for item in canais] == ["CNL-001"]


def test_arp_nao_pode_acrescentar_complemento_a_2_1_somente_leitura(sessao):
    registro = _registro_integral(
        sessao, "CMD-F1-CANAIS-COMPLEMENTO", canais=["CNL-001"]
    )

    resultado = salvar_bloco_2_form1_integral(
        sessao, comando_id="CMD-F1-CANAIS-COMPLEMENTO-SALVAR",
        conta_id="CONTA-A1", registro_id=registro["registro_id"],
        versao_lida=1, respostas={"2.2": "Unidade fictícia"},
        complementos_outro={"2.1": "Canal complementar fictício"},
    )
    sessao.commit()

    rascunho = sessao.get(RascunhoForm1Integral, registro["registro_id"])
    assert not resultado["permitido"]
    assert "somente pode ser usado" in resultado["motivo"]
    assert "2.1" not in rascunho.conteudo.get("complementos", {})


def test_leitura_2_1_usa_snapshot_e_nao_nome_posterior_do_catalogo(sessao):
    # Arrange
    registro = _registro_integral(
        sessao, "CMD-F1-CANAIS-SNAPSHOT", canais=["CNL-001"]
    )
    sessao.execute(
        update(Canal).where(Canal.id == "CNL-001").values(
            nome_canonico="Nome posterior fictício"
        )
    )
    sessao.commit()

    # Act
    _, resumo = carregar_registro(sessao, "CONTA-A1", registro["registro_id"])

    # Assert
    assert resumo["form1_integral"]["leitura_2_1"]["canais"] == [{
        "id": "CNL-001", "nome": "Balcão de atendimento (fictício)"
    }]


def test_outro_agente_pode_consultar_mas_nao_alterar_o_rascunho(sessao):
    # Arrange
    registro = _registro_integral(
        sessao, "CMD-F1-CANAIS-PERMISSAO", canais=["CNL-001"]
    )

    # Act
    _, resumo = carregar_registro(sessao, "CONTA-B1", registro["registro_id"])
    resultado = salvar_bloco_2_form1_integral(
        sessao, comando_id="CMD-F1-CANAIS-PERMISSAO-SALVAR", conta_id="CONTA-B1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"2.2": "UNID-NORTE"},
    )
    sessao.commit()

    # Assert
    assert resumo["form1_integral"]["leitura_2_1"]["estado"] == "canais_confirmados"
    assert resumo["form1_integral"]["pode_editar"] is False
    assert not resultado["permitido"]
    assert "somente o ARP atual" in resultado["motivo"]
