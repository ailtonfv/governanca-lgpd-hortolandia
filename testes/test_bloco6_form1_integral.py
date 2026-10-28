"""Bloco 6 do FORM 1 integral — origem dos dados (REV13)."""

import pytest
from fastapi.testclient import TestClient

from app.atribuicao_form1_integral import atribuir_arp_form1_integral
from app.main import app
from app.modelos import RascunhoForm1Integral
from app.rascunho_form1_integral import (
    iniciar_rascunho_form1_integral,
    salvar_bloco_6_form1_integral,
)
from testes.apoio import CADASTRO, g1


cliente = TestClient(app)


def _rascunho(sessao, prefixo):
    registro = g1(f"{prefixo}-G1", CADASTRO, "CTX-TRIB-01", titulo="Serviço fictício")
    atribuir_arp_form1_integral(
        sessao, comando_id=f"{prefixo}-ARP", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], modo="proprio", versao_lida=0,
    )
    sessao.commit()
    iniciar_rascunho_form1_integral(
        sessao, comando_id=f"{prefixo}-INI", conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
    )
    sessao.commit()
    return registro


def test_bloco_6_salva_catalogos_condicionais_e_preserva_rascunho(sessao):
    registro = _rascunho(sessao, "F16-OK")
    resultado = salvar_bloco_6_form1_integral(
        sessao, comando_id="F16-OK-S", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={
            "6.1": ["Do próprio titular", "Produzidos pela própria unidade"],
            "6.1.1": "Base municipal fictícia", "6.2": "Sim",
            "6.2.1": "Sistema fictício", "6.2.2": ["Nome", "Telefone"],
        },
    )
    sessao.commit()
    conteudo = sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo
    assert resultado["permitido"] and resultado["versao_rascunho"] == 2
    assert conteudo["respostas"]["6.2.2"] == ["Nome", "Telefone"]


@pytest.mark.parametrize("respostas,trecho", (
    ({"6.1": ["Fonte forjada"]}, "catálogo REV13"),
    ({"6.1": ["Do próprio titular", "Do próprio titular"]}, "opção repetida"),
    ({"6.2": "Não", "6.2.1": "Fonte fictícia"}, "condicional inativo"),
    ({"6.2": "Não", "6.2.2": ["Nome"]}, "condicional inativo"),
))
def test_bloco_6_recusa_entrada_invalida(sessao, respostas, trecho):
    registro = _rascunho(sessao, "F16-INV")
    resultado = salvar_bloco_6_form1_integral(
        sessao, comando_id=f"F16-INV-{trecho}", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1, respostas=respostas,
    )
    sessao.commit()
    assert not resultado["permitido"] and trecho in resultado["motivo"]


def test_bloco_6_autorizacao_idempotencia_e_concorrencia(sessao):
    registro = _rascunho(sessao, "F16-SEG")
    negado = salvar_bloco_6_form1_integral(
        sessao, comando_id="F16-SEG-N", conta_id="CONTA-G1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"6.1": ["A confirmar"]},
    )
    sessao.commit()
    parametros = dict(
        comando_id="F16-SEG-S", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"6.1": ["A confirmar"]},
    )
    primeiro = salvar_bloco_6_form1_integral(sessao, **parametros)
    sessao.commit()
    repetido = salvar_bloco_6_form1_integral(sessao, **parametros)
    antigo = salvar_bloco_6_form1_integral(
        sessao, comando_id="F16-SEG-V", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1, respostas={},
    )
    sessao.commit()
    assert not negado["permitido"]
    assert primeiro["permitido"] and repetido["reexecutado"]
    assert not antigo["permitido"] and "desatualizado" in antigo["motivo"]


def test_interface_exibe_e_salva_bloco_6(sessao):
    registro = _rascunho(sessao, "F16-HTTP")
    pagina = cliente.get(f"/registros/{registro['registro_id']}?conta_id=CONTA-A1")
    resposta = cliente.post(
        f"/registros/{registro['registro_id']}/form1-integral/bloco-6/salvar",
        data={"conta_id": "CONTA-A1", "comando_id": "F16-HTTP-S",
              "versao_lida": "1", "campo__6.1": ["A confirmar"]},
    )
    assert pagina.status_code == 200 and "6.2.2" in pagina.text
    assert resposta.status_code == 200 and "Bloco 6" in resposta.text


def test_falha_no_evento_reverte_bloco_6(sessao, monkeypatch):
    registro = _rascunho(sessao, "F16-RB")
    monkeypatch.setattr(
        "app.rascunho_form1_integral.registrar_evento",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("falha fictícia")),
    )
    with pytest.raises(RuntimeError, match="falha fictícia"):
        salvar_bloco_6_form1_integral(
            sessao, comando_id="F16-RB-S", conta_id="CONTA-A1",
            registro_id=registro["registro_id"], versao_lida=1,
            respostas={"6.1": ["A confirmar"]},
        )
        sessao.commit()
    sessao.rollback()
    assert "6.1" not in sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo["respostas"]
