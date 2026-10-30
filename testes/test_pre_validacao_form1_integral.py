"""Pré-validação consultiva do contrato candidato 3 — Arrange, Act, Assert."""

from copy import deepcopy

from fastapi.testclient import TestClient

from app.form1_integral import campos_por_id
from app.main import app
from app.modelos import RascunhoForm1Integral
from app.pre_validacao_form1_integral import (
    carregar_matriz_obrigatoriedade,
    pre_validar_form1_integral,
)
from testes.test_bloco7_form1_integral import _rascunho


cliente = TestClient(app)


def _ids(itens):
    return {item.get("campo_id") for item in itens}


def test_matriz_runtime_cobre_os_128_ids_sem_copia_independente():
    regras = carregar_matriz_obrigatoriedade()

    assert len(regras) == 128
    assert set(regras) == set(campos_por_id())


def test_pre_validacao_e_consultiva_e_preserva_o_conteudo():
    conteudo = {"respostas": {"1.2": "Serviço", "1.3": "Objeto fictício"}}
    original = {"respostas": dict(conteudo["respostas"])}

    resultado = pre_validar_form1_integral(conteudo, nome_institucional="Agente Fictício")

    assert resultado["consultiva"] is True
    assert resultado["submissao_habilitada"] is False
    assert conteudo == original
    assert "0.2" in _ids(resultado["regras_pendentes"])
    assert "0.3" in _ids(resultado["regras_pendentes"])


def test_pendencias_identificam_etapa_e_tipo_de_destino_sem_inventar_destino_institucional():
    resultado = pre_validar_form1_integral(
        {"respostas": {"3.1": "Sim", "10.1": "Sim", "10.2": ["Outra Secretaria"]}},
        nome_institucional="Agente Fictício",
    )
    itens = {item["campo_id"]: item for item in resultado["incompletos"]}
    institucionais = {item["campo_id"]: item for item in resultado["regras_pendentes"] if item.get("campo_id")}

    assert itens["2.2"]["etapa"] == 1 and itens["2.2"]["destino_tipo"] == "campo"
    assert itens["5.1"]["etapa"] == 2
    assert itens["9.1"]["etapa"] == 3
    assert itens["12.1"]["etapa"] == 4
    assert itens["3.2"]["destino_tipo"] == "secao"
    assert itens["10.2.1"]["destino_tipo"] == "secao"
    assert institucionais["0.2"]["destino_navegavel"] is False
    assert institucionais["0.3"]["etapa"] is None


def test_condicional_inequivoca_distingue_inativo_de_incompleto():
    inativo = pre_validar_form1_integral(
        {"respostas": {"2.4": "Sim"}}, nome_institucional="Agente Fictício"
    )
    ativo = pre_validar_form1_integral(
        {"respostas": {"2.4": "Não"}}, nome_institucional="Agente Fictício"
    )

    assert {"2.4.1", "2.4.2"} <= _ids(inativo["nao_aplicaveis"])
    assert {"2.4.1", "2.4.2"} <= _ids(ativo["incompletos"])


def test_nao_se_aplica_satisfaz_e_a_confirmar_nao_satisfaz_obrigatorio():
    conclusivo = pre_validar_form1_integral(
        {"respostas": {"5.1": ["Não se aplica"]}}, nome_institucional="Agente Fictício"
    )
    provisoria = pre_validar_form1_integral(
        {"respostas": {"5.1": ["A confirmar"]}}, nome_institucional="Agente Fictício"
    )

    assert "5.1" not in _ids(conclusivo["incompletos"])
    assert "5.1" in _ids(provisoria["incompletos"])


def test_whatsapp_corporativo_usa_condicionais_canônicas_e_10_2_1_fica_estruturada():
    resultado = pre_validar_form1_integral(
        {"respostas": {"8.3": ["WhatsApp corporativo"], "10.1": "Sim"}},
        nome_institucional="Agente Fictício",
    )

    pendentes = _ids(resultado["regras_pendentes"])
    assert "10.2.1" not in pendentes
    assert {"8.7", "8.8", "8.9"} <= _ids(resultado["incompletos"])
    assert "8.8.1" in _ids(resultado["nao_aplicaveis"])


def test_retrato_historico_de_canais_satisfaz_2_1_sem_alterar_rascunho():
    conteudo = {"respostas": {"OUV.1": ["Recepção"]}}

    resultado = pre_validar_form1_integral(
        conteudo,
        nome_institucional="Agente Fictício",
        respostas_somente_leitura={"2.1": ["Ouvidoria"]},
    )

    assert "2.1" not in _ids(resultado["incompletos"])
    assert "OUV.2" in _ids(resultado["incompletos"])
    assert conteudo == {"respostas": {"OUV.1": ["Recepção"]}}


def test_ausencia_historica_confirmada_satisfaz_2_1():
    resultado = pre_validar_form1_integral(
        {"respostas": {}},
        nome_institucional="Agente Fictício",
        respostas_somente_leitura={"2.1": []},
    )

    assert "2.1" not in _ids(resultado["incompletos"])
    assert {"OUV.1", "OUV.2", "OUV.3", "OUV.4", "ESIC.1", "ESIC.2"} <= _ids(resultado["nao_aplicaveis"])


def test_outro_em_5_1_sem_complemento_e_apontado_sem_bloquear_rascunho():
    resultado = pre_validar_form1_integral(
        {"respostas": {"5.1": ["Outro"]}, "complementos": {}},
        nome_institucional="Agente Fictício",
    )

    assert "5.1" in _ids(resultado["incompletos"])
    assert resultado["submissao_habilitada"] is False


def test_participante_e_validado_por_ocorrencia_sem_alterar_rascunho():
    conteudo = {
        "respostas": {"3.1": "Sim"},
        "participantes": [{"id": "PART-FICT-1", "respostas": {"3.2": ["Outra Secretaria"]}}],
    }

    resultado = pre_validar_form1_integral(conteudo, nome_institucional="Agente Fictício")

    ocorrencias = [item for item in resultado["incompletos"] if item.get("ocorrencia") == 1]
    assert {"3.3", "3.4", "3.4.1", "3.5"} <= _ids(ocorrencias)


def test_interface_apresenta_resumo_consultivo_sem_acao_de_submissao(sessao):
    registro = _rascunho(sessao, "F1-PRE-HTTP")

    pagina = cliente.get(f"/registros/{registro['registro_id']}?conta_id=CONTA-A1")

    assert pagina.status_code == 200
    assert "Pendências antes da futura submissão" in pagina.text
    assert "não submete o formulário" in pagina.text
    assert "0.2" in pagina.text and "0.3" in pagina.text
    assert "Submeter FORM 1 integral" not in pagina.text


def test_interface_oferece_navegacao_assistida_sem_alterar_rascunho(sessao):
    registro = _rascunho(sessao, "F1-PRE-NAVEGACAO")
    rascunho = sessao.get(RascunhoForm1Integral, registro["registro_id"])
    conteudo_antes = deepcopy(rascunho.conteudo)
    versao_antes = rascunho.versao_rascunho

    pagina = cliente.get(f"/registros/{registro['registro_id']}?conta_id=CONTA-A1")

    assert pagina.status_code == 200
    assert 'type="button" class="botao-pendencia-form1"' in pagina.text
    assert 'data-pendencia-campo="2.2"' in pagina.text
    assert 'data-pendencia-etapa="1"' in pagina.text
    assert 'data-pendencia-campo="12.1"' in pagina.text
    assert 'data-pendencia-etapa="4"' in pagina.text
    assert 'data-pendencia-campo="0.2"' not in pagina.text
    assert "Sem destino editável neste formulário" in pagina.text
    assert "focarPendencia(botao)" in pagina.text
    assert "data-condicional-oculta" in pagina.text
    assert "/form1-integral/submeter" not in pagina.text
    sessao.refresh(rascunho)
    assert rascunho.conteudo == conteudo_antes
    assert rascunho.versao_rascunho == versao_antes
