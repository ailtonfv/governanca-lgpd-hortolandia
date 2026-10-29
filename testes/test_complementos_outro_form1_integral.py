"""Política uniforme dos complementos de Outro — Incremento 7C/B."""

from fastapi.testclient import TestClient

from app.form1_integral import alternativas_outro_por_campo
from app.main import app
from app.modelos import RascunhoForm1Integral
from app.pre_validacao_form1_integral import pre_validar_form1_integral
from app.rascunho_form1_integral import (
    adicionar_participante_form1_integral,
    remover_participante_form1_integral,
    salvar_cabecalho_bloco_3_form1_integral,
    salvar_bloco_6_form1_integral,
    salvar_bloco_8_form1_integral,
)
from testes.test_bloco7_form1_integral import _rascunho


cliente = TestClient(app)


def _conteudo(sessao, registro_id):
    return sessao.get(RascunhoForm1Integral, registro_id).conteudo


def test_catalogo_declara_exatamente_os_38_contextos_de_outro():
    alternativas = alternativas_outro_por_campo()

    assert len(alternativas) == 38
    assert alternativas["5.1"] == "Outro"
    assert alternativas["7.1"] == "Outra"
    assert {"4.2.5.1", "6.2.2", "9.2.2", "10.4"} <= set(alternativas)


def test_complemento_comum_e_reutilizacao_do_catalogo_sao_independentes(sessao):
    registro = _rascunho(sessao, "F1-OUTRO-COMUM")
    resultado_8 = salvar_bloco_8_form1_integral(
        sessao, comando_id="F1-OUTRO-COMUM-B8", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"8.3": ["Outro"]},
        complementos_outro={"8.3": "Meio municipal fictício"},
    )
    sessao.commit()
    resultado_6 = salvar_bloco_6_form1_integral(
        sessao, comando_id="F1-OUTRO-COMUM-B6", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=2,
        respostas={"6.2": "Sim", "6.2.2": ["Outro"]},
        complementos_outro={"6.2.2": "Categoria documental fictícia"},
    )
    sessao.commit()

    conteudo = _conteudo(sessao, registro["registro_id"])
    assert resultado_8["permitido"] and resultado_6["permitido"]
    assert conteudo["complementos"] == {
        "8.3": "Meio municipal fictício",
        "6.2.2": "Categoria documental fictícia",
    }


def test_desselecao_inativa_complemento_sem_apagar_historico(sessao):
    registro = _rascunho(sessao, "F1-OUTRO-HIST")
    salvar_bloco_8_form1_integral(
        sessao, comando_id="F1-OUTRO-HIST-1", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"8.3": ["Outro"]},
        complementos_outro={"8.3": "Meio complementar fictício"},
    )
    sessao.commit()
    resultado = salvar_bloco_8_form1_integral(
        sessao, comando_id="F1-OUTRO-HIST-2", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=2,
        respostas={"8.3": ["E-mail institucional"]},
        complementos_outro={"8.3": ""},
    )
    sessao.commit()

    conteudo = _conteudo(sessao, registro["registro_id"])
    assert resultado["permitido"] and "8.3" not in conteudo.get("complementos", {})
    assert conteudo["complementos_inativos"]["8.3"][-1]["valor"] == (
        "Meio complementar fictício"
    )


def test_complemento_recusa_excesso_e_uso_sem_outro(sessao):
    registro = _rascunho(sessao, "F1-OUTRO-INV")
    excesso = salvar_bloco_8_form1_integral(
        sessao, comando_id="F1-OUTRO-INV-1", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"8.3": ["Outro"]}, complementos_outro={"8.3": "x" * 201},
    )
    sessao.commit()
    indevido = salvar_bloco_8_form1_integral(
        sessao, comando_id="F1-OUTRO-INV-2", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"8.3": ["Telefone"]},
        complementos_outro={"8.3": "Meio complementar fictício"},
    )
    sessao.commit()

    assert not excesso["permitido"] and "até 200 caracteres" in excesso["motivo"]
    assert not indevido["permitido"] and "somente pode ser usado" in indevido["motivo"]


def test_participante_preserva_complemento_ao_ser_removido(sessao):
    registro = _rascunho(sessao, "F1-OUTRO-PART")
    salvar_cabecalho_bloco_3_form1_integral(
        sessao, comando_id="F1-OUTRO-PART-B3", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        resposta_3_1="Sim",
    )
    sessao.commit()
    adicionado = adicionar_participante_form1_integral(
        sessao, comando_id="F1-OUTRO-PART-ADD", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=2,
        respostas={"3.2": ["Outro"]},
        complementos_outro={"3.2": "Entidade pública fictícia"},
    )
    sessao.commit()
    assert adicionado["permitido"], adicionado
    remover_participante_form1_integral(
        sessao, comando_id="F1-OUTRO-PART-R", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=3,
        participante_id=adicionado["participante_id"],
    )
    sessao.commit()

    inativo = _conteudo(sessao, registro["registro_id"])["participantes_inativos"][-1]
    assert inativo["complementos"]["3.2"] == "Entidade pública fictícia"


def test_pre_validacao_aponta_complementos_comum_e_de_participante():
    resultado = pre_validar_form1_integral(
        {
            "respostas": {"3.1": "Sim", "8.3": ["Outro"]},
            "participantes": [{
                "id": "PART-FICT-OUTRO",
                "respostas": {"3.2": ["Outro"]},
                "complementos": {},
            }],
        },
        nome_institucional="Agente Fictício",
    )

    pendencias = [(item["campo_id"], item.get("ocorrencia"))
                  for item in resultado["incompletos"]]
    assert ("8.3", None) in pendencias
    assert ("3.2", 1) in pendencias


def test_interface_exibe_complementos_genericos_e_exclusividade_visual(sessao):
    registro = _rascunho(sessao, "F1-OUTRO-HTTP")

    pagina = cliente.get(f"/registros/{registro['registro_id']}?conta_id=CONTA-A1")

    assert pagina.status_code == 200
    assert 'name="complemento_outro__8.3"' in pagina.text
    assert 'name="complemento_outro__6.2.2"' in pagina.text
    assert "aplicarExclusividadeAConfirmarNoBloco5" in pagina.text
    assert "opcao.value === 'A confirmar'" in pagina.text
