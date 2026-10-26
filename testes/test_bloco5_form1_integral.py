"""Incremento isolado do Bloco 5 do FORM 1 integral — REV13."""

import pytest
from fastapi.testclient import TestClient

from app.atribuicao_form1_integral import atribuir_arp_form1_integral
from app.eventos import verificar_cadeia
from app.main import app
from app.modelos import RascunhoForm1Integral
from app.rascunho_form1_integral import (
    iniciar_rascunho_form1_integral,
    problemas_submissao_bloco_5,
    salvar_bloco_4_form1_integral,
    salvar_bloco_5_form1_integral,
)
from testes.apoio import CADASTRO, g1


cliente = TestClient(app)


def _rascunho_pronto(sessao, prefixo):
    registro = g1(
        f"{prefixo}-G1", CADASTRO, "CTX-TRIB-01",
        titulo="Atividade tributária fictícia",
    )
    atribuir_arp_form1_integral(
        sessao, comando_id=f"{prefixo}-ARP", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], modo="proprio", versao_lida=0,
    )
    sessao.commit()
    iniciar_rascunho_form1_integral(
        sessao, comando_id=f"{prefixo}-INICIAR", conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
    )
    sessao.commit()
    return registro


def test_bloco_5_salva_catalogo_e_complemento_sem_copiar_bloco_4(sessao):
    registro = _rascunho_pronto(sessao, "CMD-F15-SALVAR")
    salvar_bloco_4_form1_integral(
        sessao, comando_id="CMD-F15-SALVAR-B4", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"4.2": "Sim", "4.2.5": "Sim", "4.2.5.1": ["Telefone"]},
    )
    sessao.commit()

    resultado = salvar_bloco_5_form1_integral(
        sessao, comando_id="CMD-F15-SALVAR-B5", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=2,
        respostas={"5.1": ["Nome", "Outro"]},
        complemento_outro="Identificador municipal complementar",
    )
    sessao.commit()

    conteudo = sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo
    assert resultado["permitido"] and resultado["versao_rascunho"] == 3
    assert conteudo["respostas"]["5.1"] == ["Nome", "Outro"]
    assert conteudo["complementos"]["5.1"] == "Identificador municipal complementar"
    assert conteudo["respostas"]["4.2.5.1"] == ["Telefone"]
    assert "Telefone" not in conteudo["respostas"]["5.1"]
    assert verificar_cadeia(sessao, registro["codigo_lgpd"])[0]

    atualizado = salvar_bloco_5_form1_integral(
        sessao, comando_id="CMD-F15-SALVAR-SEM-OUTRO", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=3,
        respostas={"5.1": ["Nome"]}, complemento_outro="",
    )
    sessao.commit()
    conteudo = sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo
    assert atualizado["permitido"] and "complementos" not in conteudo
    assert conteudo["complementos_inativos"]["5.1"][-1]["valor"] == (
        "Identificador municipal complementar"
    )


def test_bloco_5_aceita_rascunho_vazio_e_a_confirmar_isolado(sessao):
    registro = _rascunho_pronto(sessao, "CMD-F15-PARCIAL")
    vazio = salvar_bloco_5_form1_integral(
        sessao, comando_id="CMD-F15-PARCIAL-VAZIO", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1, respostas={},
    )
    sessao.commit()
    pendente = salvar_bloco_5_form1_integral(
        sessao, comando_id="CMD-F15-PARCIAL-CONF", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=2,
        respostas={"5.1": ["A confirmar"]},
    )
    sessao.commit()

    conteudo = sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo
    assert vazio["permitido"] and pendente["permitido"]
    assert conteudo["respostas"]["5.1"] == ["A confirmar"]


@pytest.mark.parametrize(
    ("respostas", "complemento", "trecho"),
    (
        ({"5.1": ["Categoria inexistente"]}, "", "catálogo REV13"),
        ({"5.1": ["Nome", "Nome"]}, "", "opção repetida"),
        ({"5.1": ["A confirmar", "Nome"]}, "", "não pode coexistir"),
        ({"5.1": ["Nome"]}, "Categoria adicional", "somente pode ser usado"),
        ({"5.1": ["Outro"]}, "x" * 201, "até 200 caracteres"),
        ({"5.1": ["Outro"]}, "CPF: 12345678901", "identificador concreto"),
    ),
)
def test_bloco_5_recusa_entradas_invalidas(sessao, respostas, complemento, trecho):
    registro = _rascunho_pronto(sessao, "CMD-F15-INVALIDO")

    resultado = salvar_bloco_5_form1_integral(
        sessao, comando_id=f"CMD-F15-INVALIDO-{trecho}", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas=respostas, complemento_outro=complemento,
    )
    sessao.commit()

    assert not resultado["permitido"] and trecho in resultado["motivo"]
    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]).versao_rascunho == 1


def test_bloco_5_somente_arp_atual_pode_salvar(sessao):
    registro = _rascunho_pronto(sessao, "CMD-F15-PERMISSAO")

    resultado = salvar_bloco_5_form1_integral(
        sessao, comando_id="CMD-F15-PERMISSAO-NEGADO", conta_id="CONTA-G1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"5.1": ["Nome"]},
    )
    sessao.commit()

    assert not resultado["permitido"] and "somente o ARP atual" in resultado["motivo"]
    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]).versao_rascunho == 1


def test_bloco_5_e_idempotente_e_recusa_versao_antiga(sessao):
    registro = _rascunho_pronto(sessao, "CMD-F15-IDEM")
    parametros = dict(
        comando_id="CMD-F15-IDEM-SALVAR", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"5.1": ["Nome"]},
    )
    primeiro = salvar_bloco_5_form1_integral(sessao, **parametros)
    sessao.commit()
    repetido = salvar_bloco_5_form1_integral(sessao, **parametros)
    antigo = salvar_bloco_5_form1_integral(
        sessao, comando_id="CMD-F15-IDEM-ANTIGO", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"5.1": ["Telefone"]},
    )
    sessao.commit()

    assert primeiro["permitido"] and repetido["reexecutado"] is True
    assert not antigo["permitido"] and "desatualizado" in antigo["motivo"]
    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]).versao_rascunho == 2


def test_falha_no_evento_desfaz_salvamento_do_bloco_5(sessao, monkeypatch):
    registro = _rascunho_pronto(sessao, "CMD-F15-ROLLBACK")

    def falhar(*args, **kwargs):
        raise RuntimeError("falha fictícia controlada")

    monkeypatch.setattr("app.rascunho_form1_integral.registrar_evento", falhar)
    with pytest.raises(RuntimeError, match="falha fictícia"):
        salvar_bloco_5_form1_integral(
            sessao, comando_id="CMD-F15-ROLLBACK-SALVAR", conta_id="CONTA-A1",
            registro_id=registro["registro_id"], versao_lida=1,
            respostas={"5.1": ["Nome"]},
        )
        sessao.commit()
    sessao.rollback()

    conteudo = sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo
    assert "5.1" not in conteudo["respostas"]


def test_interface_exibe_35_alternativas_e_salva_bloco_5(sessao):
    registro = _rascunho_pronto(sessao, "CMD-F15-HTTP")
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}?conta_id=CONTA-A1"
    )
    salvamento = cliente.post(
        f"/registros/{registro['registro_id']}/form1-integral/bloco-5/salvar",
        data={
            "conta_id": "CONTA-A1",
            "comando_id": "CMD-F15-HTTP-SALVAR",
            "versao_lida": "1",
            "campo__5.1": ["Nome", "Outro"],
            "complemento_outro_5_1": "Categoria municipal complementar",
        },
    )

    assert pagina.status_code == 200
    assert pagina.text.count('name="campo__5.1"') == 35
    assert "Esta orientação reduz o risco" in pagina.text
    assert salvamento.status_code == 200
    assert "Bloco 5 do FORM 1 integral salvo com segurança" in salvamento.text


def test_regras_preparadas_para_submissao_nao_sao_ativadas_no_rascunho():
    assert problemas_submissao_bloco_5({"respostas": {}}) == [
        "5.1: informe ao menos uma categoria de dado"
    ]
    assert problemas_submissao_bloco_5({"respostas": {"5.1": ["A confirmar"]}}) == [
        "5.1: A confirmar não satisfaz a submissão integral"
    ]
    assert problemas_submissao_bloco_5({"respostas": {"5.1": ["Outro"]}}) == [
        "5.1: informe o complemento descritivo de Outro"
    ]
    assert problemas_submissao_bloco_5({
        "respostas": {"5.1": ["Outro"]},
        "complementos": {"5.1": "Categoria municipal complementar"},
    }) == []
