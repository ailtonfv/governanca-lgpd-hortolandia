"""Bloco 7 do FORM 1 integral — operações de tratamento."""

from fastapi.testclient import TestClient

from app.atribuicao_form1_integral import atribuir_arp_form1_integral
from app.main import app
from app.modelos import RascunhoForm1Integral
from app.rascunho_form1_integral import iniciar_rascunho_form1_integral, salvar_bloco_7_form1_integral
from testes.apoio import CADASTRO, g1

cliente = TestClient(app)


def _rascunho(sessao, prefixo):
    registro = g1(f"{prefixo}-G1", CADASTRO, "CTX-TRIB-01", titulo="Processo fictício")
    atribuir_arp_form1_integral(sessao, comando_id=f"{prefixo}-A", conta_id="CONTA-A1",
                               registro_id=registro["registro_id"], modo="proprio", versao_lida=0)
    sessao.commit()
    iniciar_rascunho_form1_integral(sessao, comando_id=f"{prefixo}-I", conta_id="CONTA-A1",
                                    registro_id=registro["registro_id"])
    sessao.commit()
    return registro


def test_bloco_7_salva_operacoes_e_e_idempotente(sessao):
    registro = _rascunho(sessao, "F17-OK")
    parametros = dict(comando_id="F17-OK-S", conta_id="CONTA-A1",
                      registro_id=registro["registro_id"], versao_lida=1,
                      respostas={"7.1": ["Coleta", "Armazenamento", "Eliminação"]})
    resultado = salvar_bloco_7_form1_integral(sessao, **parametros)
    sessao.commit()
    repetido = salvar_bloco_7_form1_integral(sessao, **parametros)
    assert resultado["permitido"] and repetido["reexecutado"]
    assert sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo["respostas"]["7.1"] == ["Coleta", "Armazenamento", "Eliminação"]


def test_bloco_7_aceita_parcial_e_recusa_catalogo_forjado(sessao):
    registro = _rascunho(sessao, "F17-INV")
    parcial = salvar_bloco_7_form1_integral(sessao, comando_id="F17-P", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1, respostas={"7.1": ["A confirmar"]})
    sessao.commit()
    invalido = salvar_bloco_7_form1_integral(sessao, comando_id="F17-X", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=2, respostas={"7.1": ["Operação forjada"]})
    sessao.commit()
    assert parcial["permitido"]
    assert not invalido["permitido"] and "catálogo REV13" in invalido["motivo"]


def test_bloco_7_somente_arp_e_versao_atual(sessao):
    registro = _rascunho(sessao, "F17-SEG")
    negado = salvar_bloco_7_form1_integral(sessao, comando_id="F17-N", conta_id="CONTA-G1",
        registro_id=registro["registro_id"], versao_lida=1, respostas={})
    sessao.commit()
    assert not negado["permitido"] and "ARP atual" in negado["motivo"]


def test_interface_exibe_23_operacoes_e_salva_bloco_7(sessao):
    registro = _rascunho(sessao, "F17-HTTP")
    pagina = cliente.get(f"/registros/{registro['registro_id']}?conta_id=CONTA-A1")
    resposta = cliente.post(f"/registros/{registro['registro_id']}/form1-integral/bloco-7/salvar",
        data={"conta_id": "CONTA-A1", "comando_id": "F17-HTTP-S", "versao_lida": "1",
              "campo__7.1": ["Coleta", "Acesso"]})
    assert pagina.text.count('name="campo__7.1"') == 23
    assert resposta.status_code == 200 and "Bloco 7" in resposta.text
