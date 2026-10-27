"""Condicionais REV13 de Ouvidoria e e-SIC a partir do retrato do APA."""

from fastapi.testclient import TestClient
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from app.atribuicao_form1_integral import atribuir_arp_form1_integral
from app.banco import motor
from app.consultas_interface import carregar_registro
from app.main import app
from app.modelos import (Canal, ObjetoCanal, RascunhoForm1Integral,
                         Registro, RegistroCanal)
from app.rascunho_form1_integral import (iniciar_rascunho_form1_integral,
                                         salvar_bloco_2_form1_integral)
from migracoes.classificacao_canais_form1 import aplicar as aplicar_migracao
from testes.apoio import CADASTRO, g1


cliente = TestClient(app)


def _preparar_registro(sessao, prefixo, canais, *, legado=False):
    for canal_id in set(canais or []):
        if canal_id in {"CNL-004", "CNL-005"}:
            sessao.add(ObjetoCanal(objeto_id="OBJ-SRV-001", canal_id=canal_id))
    sessao.commit()
    resultado = g1(
        f"{prefixo}-G1",
        CADASTRO if legado else "OBJ-SRV-001",
        "CTX-TRIB-01" if legado else "CTX-TRIB-03",
        titulo="Fluxo condicional fictício",
        **({} if legado else {"canais_confirmados_ids": canais}),
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


def _pagina(registro_id, conta_id="CONTA-A1"):
    return cliente.get(f"/registros/{registro_id}?conta_id={conta_id}")


def test_ouvidoria_isolada_exibe_e_persiste_somente_seu_ramo(sessao):
    # Arrange
    registro = _preparar_registro(sessao, "CMD-COND-OUV", ["CNL-004"])

    # Act
    pagina = _pagina(registro["registro_id"])
    resultado = salvar_bloco_2_form1_integral(
        sessao, comando_id="CMD-COND-OUV-SALVAR", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={
            "OUV.1": ["Solicitação"],
            "OUV.2": ["Identificado"],
            "OUV.3": "Em alguns casos",
            "OUV.4": "Depende da manifestação",
        },
    )
    sessao.commit()

    # Assert
    respostas = sessao.get(
        RascunhoForm1Integral, registro["registro_id"]
    ).conteudo["respostas"]
    assert pagina.status_code == 200
    assert 'name="campo__OUV.1"' in pagina.text
    assert 'name="campo__ESIC.1"' not in pagina.text
    assert resultado["permitido"]
    assert respostas["OUV.4"] == "Depende da manifestação"


def test_esic_isolado_exibe_e_persiste_somente_seu_ramo(sessao):
    # Arrange
    registro = _preparar_registro(sessao, "CMD-COND-ESIC", ["CNL-005"])

    # Act
    pagina = _pagina(registro["registro_id"])
    resultado = salvar_bloco_2_form1_integral(
        sessao, comando_id="CMD-COND-ESIC-SALVAR", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"ESIC.1": "Sim", "ESIC.2": "Em alguns casos"},
    )
    sessao.commit()

    # Assert
    assert 'name="campo__ESIC.1"' in pagina.text
    assert 'name="campo__OUV.1"' not in pagina.text
    assert resultado["permitido"]
    assert sessao.get(
        RascunhoForm1Integral, registro["registro_id"]
    ).conteudo["respostas"]["ESIC.2"] == "Em alguns casos"


def test_ouvidoria_e_esic_ativam_ramos_independentes_sem_duplicacao(sessao):
    # Arrange
    registro = _preparar_registro(
        sessao, "CMD-COND-AMBOS", ["CNL-004", "CNL-005"]
    )

    # Act
    pagina = _pagina(registro["registro_id"])
    resultado = salvar_bloco_2_form1_integral(
        sessao, comando_id="CMD-COND-AMBOS-SALVAR", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={
            "OUV.1": ["Reclamação"], "OUV.2": ["Anônimo"],
            "OUV.3": "Não", "OUV.4": "Nenhum dado de identificação",
            "ESIC.1": "Sim", "ESIC.2": "Sim",
        },
    )
    sessao.commit()

    # Assert
    assert pagina.text.count('name="campo__OUV.1"') == 7
    assert pagina.text.count('name="campo__ESIC.1"') == 1
    assert resultado["permitido"]
    respostas = sessao.get(
        RascunhoForm1Integral, registro["registro_id"]
    ).conteudo["respostas"]
    assert respostas["OUV.1"] == ["Reclamação"]
    assert respostas["ESIC.1"] == "Sim"


def test_nenhum_canal_ou_canal_generico_nao_ativa_ramos(sessao):
    # Arrange
    registro = _preparar_registro(sessao, "CMD-COND-NENHUM", ["CNL-001"])

    # Act
    pagina = _pagina(registro["registro_id"])
    forjado = salvar_bloco_2_form1_integral(
        sessao, comando_id="CMD-COND-NENHUM-FORJADO", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"OUV.1": ["Solicitação"]},
    )
    sessao.commit()

    # Assert
    assert 'name="campo__OUV.1"' not in pagina.text
    assert 'name="campo__ESIC.1"' not in pagina.text
    assert not forjado["permitido"]
    assert "campo condicional inativo" in forjado["motivo"]


def test_registro_antigo_preserva_resposta_e_condicional_legadas(sessao):
    # Arrange
    registro = _preparar_registro(sessao, "CMD-COND-LEGADO", [], legado=True)

    # Act
    resultado = salvar_bloco_2_form1_integral(
        sessao, comando_id="CMD-COND-LEGADO-SALVAR", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"2.1": "Ouvidoria", "OUV.1": ["Sugestão"]},
    )
    sessao.commit()
    pagina = _pagina(registro["registro_id"])

    # Assert
    assert resultado["permitido"]
    assert 'name="campo__2.1"' in pagina.text
    assert 'name="campo__OUV.1"' in pagina.text
    assert "Sugestão" in sessao.get(
        RascunhoForm1Integral, registro["registro_id"]
    ).conteudo["respostas"]["OUV.1"]


def test_classificacao_historica_nao_depende_de_mudanca_posterior_no_canal(sessao):
    # Arrange
    registro = _preparar_registro(sessao, "CMD-COND-SNAPSHOT", ["CNL-004"])
    sessao.get(Canal, "CNL-004").classificacao_form1 = None
    sessao.commit()

    # Act
    _, resumo = carregar_registro(sessao, "CONTA-A1", registro["registro_id"])
    resultado = salvar_bloco_2_form1_integral(
        sessao, comando_id="CMD-COND-SNAPSHOT-SALVAR", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"OUV.3": "Sim"},
    )
    sessao.commit()

    # Assert
    assert resumo["form1_integral"]["campos_bloco_2"]["OUV.3"][
        "condicao_canal_ativa"
    ] is True
    assert resultado["permitido"]


def test_somente_arp_atual_pode_salvar_condicional(sessao):
    # Arrange
    registro = _preparar_registro(sessao, "CMD-COND-AUTORIZACAO", ["CNL-005"])

    # Act
    resultado = salvar_bloco_2_form1_integral(
        sessao, comando_id="CMD-COND-AUTORIZACAO-SALVAR", conta_id="CONTA-B1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"ESIC.1": "Sim"},
    )
    sessao.commit()

    # Assert
    assert not resultado["permitido"]
    assert "somente o ARP atual" in resultado["motivo"]
    assert sessao.get(
        RascunhoForm1Integral, registro["registro_id"]
    ).versao_rascunho == 1


def test_migracao_16_adiciona_classificacoes_sem_reinterpretar_historico(sessao):
    # Arrange: mantém um Registro histórico genérico e simula o esquema da versão 15.
    registro = _preparar_registro(sessao, "CMD-COND-MIGRACAO", ["CNL-001"])
    with motor.begin() as conexao:
        conexao.execute(text(
            "ALTER TABLE registro_canal DROP CONSTRAINT IF EXISTS "
            "ck_registro_canal_classificacao_form1"
        ))
        conexao.execute(text(
            "ALTER TABLE canal DROP CONSTRAINT IF EXISTS ck_canal_classificacao_form1"
        ))
        conexao.execute(text(
            "ALTER TABLE registro_canal DROP COLUMN classificacao_form1_snapshot"
        ))
        conexao.execute(text("ALTER TABLE canal DROP COLUMN classificacao_form1"))

    # Act
    with Session(motor) as sessao_migracao, sessao_migracao.begin():
        aplicar_migracao(sessao_migracao)

    # Assert
    inspetor = inspect(motor)
    assert "classificacao_form1" in {
        item["name"] for item in inspetor.get_columns("canal")
    }
    assert "classificacao_form1_snapshot" in {
        item["name"] for item in inspetor.get_columns("registro_canal")
    }
    with Session(motor) as verificacao:
        assert verificacao.get(Registro, registro["registro_id"]) is not None
        retrato = verificacao.scalar(select(RegistroCanal).where(
            RegistroCanal.registro_id == registro["registro_id"]
        ))
        assert retrato.classificacao_form1_snapshot is None
