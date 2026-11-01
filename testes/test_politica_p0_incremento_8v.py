"""Política P0 restrita do Incremento 8V — Arrange, Act, Assert."""

from copy import deepcopy

from fastapi.testclient import TestClient

from app.form1_integral import campos_por_id
from app.main import app
from app.modelos import RascunhoForm1Integral, VersaoForm1Integral
from app.pre_validacao_form1_integral import (
    carregar_matriz_obrigatoriedade,
    metadado_visual_obrigatoriedade,
    pre_validar_form1_integral,
)
from app.rascunho_form1_integral import _lacre, _validar_respostas_catalogadas
from app.submissao_form1_integral import preparar_snapshot_form1_integral
from testes.test_bloco7_form1_integral import _rascunho


CONTROLE_MULTIPLO = "seleção múltipla (combo com marcações)"
cliente = TestClient(app)


def _campos_multiplos_com(alternativa):
    return {
        campo_id: campo
        for campo_id, campo in campos_por_id().items()
        if campo.controle == CONTROLE_MULTIPLO and alternativa in campo.alternativas
    }


def test_0_2_e_0_3_vazios_sao_nao_bloqueantes_e_somente_leitura():
    regras = carregar_matriz_obrigatoriedade()

    resultado = pre_validar_form1_integral(
        {"respostas": {}}, nome_institucional="Servidor Fictício",
        cargo_funcao=None, email_institucional=None,
    )

    assert regras["0.2"].classe == "Metadado institucional não bloqueante, somente leitura"
    assert regras["0.3"].classe == "Metadado institucional não bloqueante, somente leitura"
    assert metadado_visual_obrigatoriedade("0.2")["marcador"] == "****"
    assert metadado_visual_obrigatoriedade("0.3")["rotulo"] == "Facultativo · somente leitura"
    assert {"0.2", "0.3"}.isdisjoint(
        {item.get("campo_id") for item in resultado["regras_pendentes"]}
    )
    assert resultado["submissao_habilitada"] is False


def test_a_confirmar_e_exclusivo_em_todos_os_31_catalogos_multiplos():
    campos = _campos_multiplos_com("A confirmar")

    assert len(campos) == 31
    for campo_id, campo in campos.items():
        substantiva = next(
            item for item in campo.alternativas
            if item not in {"A confirmar", "Não se aplica", "Nenhuma das situações acima"}
        )
        problema = _validar_respostas_catalogadas(
            None, {campo_id: ["A confirmar", substantiva]}, {campo_id}
        )
        assert problema is not None, campo_id


def test_a_confirmar_tambem_e_exclusivo_nos_quatro_reusos_do_catalogo_5_1():
    catalogo = campos_por_id()["5.1"].alternativas
    substantiva = next(item for item in catalogo if item != "A confirmar")

    for campo_id in {"4.2.5.1", "6.2.2", "9.2.2", "10.4"}:
        problema = _validar_respostas_catalogadas(
            None, {campo_id: ["A confirmar", substantiva]}, {campo_id}
        )
        assert problema is not None, campo_id


def test_nao_se_aplica_e_exclusivo_somente_nos_tres_catalogos_que_o_preveem():
    campos = _campos_multiplos_com("Não se aplica")

    assert set(campos) == {"3.4.1", "13.1", "13.4"}
    for campo_id, campo in campos.items():
        substantiva = next(
            item for item in campo.alternativas
            if item not in {"A confirmar", "Não se aplica", "Nenhuma das situações acima"}
        )
        problema = _validar_respostas_catalogadas(
            None, {campo_id: ["Não se aplica", substantiva]}, {campo_id}
        )
        assert problema is not None, campo_id
        assert _validar_respostas_catalogadas(
            None, {campo_id: ["Não se aplica"]}, {campo_id}
        ) is None
    assert "catálogo REV13" in _validar_respostas_catalogadas(
        None, {"7.1": ["Não se aplica"]}, {"7.1"}
    )


def test_pre_validacao_preserva_rascunho_legado_contraditorio_sem_normalizar():
    substantiva = next(
        item for item in campos_por_id()["7.1"].alternativas if item != "A confirmar"
    )
    conteudo = {"respostas": {"7.1": ["A confirmar", substantiva]}}
    original = deepcopy(conteudo)

    resultado = pre_validar_form1_integral(
        conteudo, nome_institucional="Servidor Fictício"
    )

    assert conteudo == original
    assert resultado["submissao_habilitada"] is False


def test_api_http_recusa_combinacao_forjada_sem_criar_nova_versao(sessao):
    registro = _rascunho(sessao, "F18V-HTTP")

    resposta = cliente.post(
        f"/registros/{registro['registro_id']}/form1-integral/bloco-7/salvar",
        data={
            "conta_id": "CONTA-A1", "comando_id": "F18V-HTTP-S",
            "versao_lida": "1", "campo__7.1": ["A confirmar", "Coleta"],
        },
    )

    rascunho = sessao.get(RascunhoForm1Integral, registro["registro_id"])
    assert resposta.status_code == 200
    assert "não pode coexistir" in resposta.text
    assert rascunho.versao_rascunho == 1
    assert "7.1" not in rascunho.conteudo["respostas"]


def test_snapshot_preserva_combinacao_legada_sem_conversao(sessao):
    registro = _rascunho(sessao, "F18V-LEGADO")
    rascunho = sessao.get(RascunhoForm1Integral, registro["registro_id"])
    substantiva = next(
        item for item in campos_por_id()["7.1"].alternativas if item != "A confirmar"
    )
    conteudo = deepcopy(rascunho.conteudo)
    conteudo["respostas"]["7.1"] = ["A confirmar", substantiva]
    rascunho.conteudo = conteudo
    rascunho.lacre_conteudo = _lacre(conteudo)
    sessao.commit()

    resultado = preparar_snapshot_form1_integral(
        sessao, comando_id="F18V-LEGADO-SNAPSHOT", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
    )
    sessao.commit()

    snapshot = sessao.get(VersaoForm1Integral, resultado["snapshot_id"])
    assert resultado["permitido"] is True
    assert snapshot.conteudo["form1_integral"]["respostas"]["7.1"] == [
        "A confirmar", substantiva
    ]
    assert snapshot.conteudo["submissao_habilitada"] is False
