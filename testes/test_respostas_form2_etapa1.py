"""Respostas estruturadas da unidade de guarda, sempre com massa fictícia."""

from copy import deepcopy

import pytest

from app import apresentacao_form2, respostas_form2
from app.catalogo_form2_rev18 import VERSAO as VERSAO_CATALOGO
from app.form2_preparacao import salvar_preparacao, salvar_respostas_bloco
from app.modelos import PreparacaoForm2
from app.respostas_form2 import ENVELOPE_V2, aplicar_bloco
from testes.test_form2_preparacao import base, cliente, iniciar


IDS = ("F2-2.9", "F2-2.9.1", "F2-2.9.2", "F2-2.9.3")


def _fontes():
    escolhas = {
        "F2-2.9": ("unica", [("SIM", "Sim"), ("NAO", "Não"),
                               ("A_CONFIRMAR", "A CONFIRMAR"), ("ANALISE", "Requer análise")]),
        "F2-2.9.1": ("multipla", [("ALT_01", "Norma fictícia"), ("ALT_05", "Outro"),
                                     ("A_CONFIRMAR", "A CONFIRMAR")]),
        "F2-2.9.2": ("unica", [("SIM", "Sim"), ("NAO", "Não"),
                                 ("A_CONFIRMAR", "A CONFIRMAR")]),
        "F2-2.9.3": ("unica", [("ALT_01", "Avaliar medida fictícia"),
                                 ("ALT_04", "Requer análise adicional"),
                                 ("A_CONFIRMAR", "A CONFIRMAR")]),
    }
    itens, alternativas, editoriais = [], [], []
    for item_id in IDS:
        modo, opcoes = escolhas[item_id]
        itens.append({"id": item_id, "etapa": 1, "bloco": 2, "edicao": "habilitada",
                      "referencias_anpd": [], "controle": "Seleção", "fonte_controle": "TESTE"})
        editoriais.append({"id": item_id, "enunciado": f"Pergunta fictícia {item_id}",
                           "escolha_documental": {"modo": modo,
                               "alternativas": [rotulo for _, rotulo in opcoes]}})
        for codigo, rotulo in opcoes:
            alternativas.append({"id": item_id, "codigo": codigo, "rotulo": rotulo,
                "fonte": "TESTE", "tratamento": "Análise especializada" if codigo in {"ANALISE", "ALT_04"} else
                "Factual a confirmar" if codigo == "A_CONFIRMAR" else "Opção substantiva",
                "complemento": "Texto condicionado (R13)" if codigo == "ALT_05" else "—"})
    itens.append({"id": "F2-3.1", "etapa": 1, "bloco": 3, "edicao": "bloqueada_d11",
                  "referencias_anpd": ["ANPD-PP", "ANPD-LI"], "controle": "Seleção", "fonte_controle": "TESTE"})
    editoriais.append({"id": "F2-3.1", "enunciado": "Pergunta jurídica fictícia"})
    condicoes = [
        {"alvo": "F2-2.9", "combinar": "SIMPLES", "origem": "—", "operador": "SEMPRE", "codigo_valor": "—"},
        {"alvo": "F2-2.9.1", "combinar": "SIMPLES", "origem": "F2-2.9", "operador": "IGUAL", "codigo_valor": "SIM"},
        {"alvo": "F2-2.9.2", "combinar": "SIMPLES", "origem": "—", "operador": "SEMPRE", "codigo_valor": "—"},
        {"alvo": "F2-2.9.3", "combinar": "SIMPLES", "origem": "F2-2.9.2", "operador": "IGUAL", "codigo_valor": "SIM"},
    ]
    contrato = {"versao": "F2-REV18-CONTROLES-CANDIDATA-v2", "itens": itens,
                "alternativas": alternativas, "condicoes": condicoes}
    catalogo = {"versao": VERSAO_CATALOGO, "blocos": [
        {"numero": 2, "itens": editoriais[:4], "notas_documentais": []},
        {"numero": 3, "itens": editoriais[4:]},
    ]}
    return contrato, catalogo


@pytest.fixture(autouse=True)
def contrato_sintetico(monkeypatch):
    contrato, catalogo = _fontes()
    monkeypatch.setattr(respostas_form2, "carregar_contrato", lambda: deepcopy(contrato))
    monkeypatch.setattr(respostas_form2, "carregar_catalogo", lambda: deepcopy(catalogo))
    monkeypatch.setattr(apresentacao_form2, "carregar_catalogo", lambda: deepcopy(catalogo))
    monkeypatch.setattr(apresentacao_form2, "projetar_bloco", respostas_form2.projetar_bloco)


def _salvar(sessao, rid, pid, comando, versao, alteracoes, **extra):
    return salvar_respostas_bloco(
        sessao, comando_id=comando, conta_id="CONTA-G1", registro_id=rid,
        preparacao_id=pid, bloco=2, versao_lida=versao, alteracoes=alteracoes, **extra)


def test_salva_codigos_e_anotacao_continua_independente(sessao):
    rid, sid = base(sessao)
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    resposta = _salvar(sessao, rid, pid, "F2-B2-1", 1, {
        "F2-2.9": "SIM", "F2-2.9.1": ["ALT_01"], "F2-2.9.2": "A_CONFIRMAR"})
    assert resposta["permitido"] and resposta["versao"] == 2
    repetida = _salvar(sessao, rid, pid, "F2-B2-1", 1, {
        "F2-2.9": "SIM", "F2-2.9.1": ["ALT_01"], "F2-2.9.2": "A_CONFIRMAR"})
    assert repetida["reexecutado"]
    prep = sessao.get(PreparacaoForm2, pid)
    assert prep.versao_envelope == ENVELOPE_V2
    assert prep.conteudo["respostas_etapa1"]["F2-2.9.1"] == ["ALT_01"]
    assert prep.conteudo["sinalizadores_etapa1"] == [
        {"item_id": "F2-2.9.2", "classe": "factual", "efeito": "relacionar_no_bloco_14"}]

    anotacao = salvar_preparacao(sessao, comando_id="F2-ANOTAR-2", conta_id="CONTA-G1",
        registro_id=rid, preparacao_id=pid, versao_lida=2,
        conteudo={"anotacao_preparatoria": "Observação fictícia preservada."})
    assert anotacao["permitido"]
    assert prep.conteudo["respostas_etapa1"]["F2-2.9"] == "SIM"


def test_inativacao_preserva_e_reativacao_exige_ato_explicito(sessao):
    rid, sid = base(sessao)
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    assert _salvar(sessao, rid, pid, "F2-ATIVA", 1,
                   {"F2-2.9": "SIM", "F2-2.9.1": ["ALT_01"]})["permitido"]
    assert _salvar(sessao, rid, pid, "F2-INATIVA", 2, {"F2-2.9": "NAO"})["permitido"]
    prep = sessao.get(PreparacaoForm2, pid)
    assert "F2-2.9.1" not in prep.conteudo["respostas_etapa1"]
    assert prep.conteudo["respostas_inativas_etapa1"]["F2-2.9.1"]["valor"] == ["ALT_01"]
    assert _salvar(sessao, rid, pid, "F2-REATIVA", 3, {"F2-2.9": "SIM"},
                   reativar={"F2-2.9.1"})["permitido"]
    assert prep.conteudo["respostas_etapa1"]["F2-2.9.1"] == ["ALT_01"]


def test_recusa_combinacao_invalida_e_bloco_juridico(sessao):
    rid, sid = base(sessao)
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    invalida = _salvar(sessao, rid, pid, "F2-INVALIDA", 1,
        {"F2-2.9": "SIM", "F2-2.9.1": ["ALT_01", "A_CONFIRMAR"]})
    assert not invalida["permitido"]
    assert sessao.get(PreparacaoForm2, pid).versao_rascunho == 1
    with pytest.raises(PermissionError, match="sem controles homologados"):
        aplicar_bloco({"anotacao_preparatoria": ""}, bloco=3,
                      alteracoes={"F2-3.1": "QUALQUER"}, proxima_versao=2)


def test_outro_exige_complemento_e_nao_aceita_complemento_solto():
    with pytest.raises(ValueError, match="exige complemento"):
        aplicar_bloco({}, bloco=2,
                      alteracoes={"F2-2.9": "SIM", "F2-2.9.1": ["ALT_05"]},
                      proxima_versao=2)
    with pytest.raises(ValueError, match="não selecionada"):
        aplicar_bloco({}, bloco=2,
                      alteracoes={"F2-2.9": "SIM", "F2-2.9.1": ["ALT_01"]},
                      complementos={"F2-2.9.1": {"ALT_05": "Descrição fictícia"}},
                      proxima_versao=2)
    novo, _ = aplicar_bloco({}, bloco=2,
                            alteracoes={"F2-2.9": "SIM", "F2-2.9.1": ["ALT_05"]},
                            complementos={"F2-2.9.1": {"ALT_05": "Descrição fictícia"}},
                            proxima_versao=2)
    assert novo["complementos_etapa1"]["F2-2.9.1"]["ALT_05"] == "Descrição fictícia"


def test_http_exibe_referencias_e_salva_sem_submeter(sessao):
    rid, sid = base(sessao)
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    url = f"/registros/{rid}/form2/preparacao"
    pagina = cliente.get(url, params={"conta_id": "CONTA-G1", "preparacao_id": pid})
    assert pagina.status_code == 200
    assert 'id="form2-bloco-2"' in pagina.text
    assert "Guia Orientativo: Tratamento de Dados Pessoais pelo Poder Público" in pagina.text
    dados = {"conta_id": "CONTA-G1", "comando_id": "F2-HTTP-B2", "versao_lida": "1",
             "resposta_F2-2.9": "SIM", "resposta_F2-2.9.1": "ALT_01",
             "resposta_F2-2.9.2": "NAO", "resposta_F2-2.9.3": ""}
    salvo = cliente.post(url + f"/{pid}/blocos/2/salvar", data=dados, follow_redirects=False)
    assert salvo.status_code == 303 and salvo.headers["location"].endswith("#unidade-guarda")
    prep = sessao.get(PreparacaoForm2, pid)
    assert prep.versao_rascunho == 2
    assert "submissao_habilitada" not in prep.conteudo


def test_http_preserva_tentativa_rejeitada_para_correcao(sessao):
    rid, sid = base(sessao)
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    url = f"/registros/{rid}/form2/preparacao/{pid}/blocos/2/salvar"
    dados = {"conta_id": "CONTA-G1", "comando_id": "F2-HTTP-INVALIDO", "versao_lida": "1",
             "resposta_F2-2.9": "SIM", "resposta_F2-2.9.1": ["", "ALT_01", "A_CONFIRMAR"],
             "resposta_F2-2.9.2": "SIM", "resposta_F2-2.9.3": "A_CONFIRMAR",
             "complemento_F2-2.9.1_ALT_05": ""}
    resposta = cliente.post(url, data=dados)
    assert resposta.status_code == 409
    assert "A confirmar deve ser exclusiva" in resposta.text
    assert 'value="SIM" selected' in resposta.text
    assert 'value="ALT_01" checked' in resposta.text
    assert 'value="A_CONFIRMAR" checked' in resposta.text
    assert resposta.text.count('fieldset class="resposta-form2"') == 4
    assert sessao.get(PreparacaoForm2, pid).versao_rascunho == 1


def test_http_reativacao_explicita_prevalece_sobre_controle_vazio(sessao):
    rid, sid = base(sessao)
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    url = f"/registros/{rid}/form2/preparacao/{pid}/blocos/2/salvar"
    base_form = {"conta_id": "CONTA-G1"}
    ativa = {**base_form, "comando_id": "F2-HTTP-REATIVA-1", "versao_lida": "1",
             "resposta_F2-2.9": "SIM", "resposta_F2-2.9.1": ["", "ALT_01"],
             "resposta_F2-2.9.2": "SIM", "resposta_F2-2.9.3": "ALT_01"}
    assert cliente.post(url, data=ativa, follow_redirects=False).status_code == 303
    inativa = {**base_form, "comando_id": "F2-HTTP-REATIVA-2", "versao_lida": "2",
               "resposta_F2-2.9": "NAO", "resposta_F2-2.9.2": "NAO"}
    assert cliente.post(url, data=inativa, follow_redirects=False).status_code == 303
    reativa = {**base_form, "comando_id": "F2-HTTP-REATIVA-3", "versao_lida": "3",
               "resposta_F2-2.9": "SIM", "resposta_F2-2.9.1": "",
               "resposta_F2-2.9.2": "SIM", "resposta_F2-2.9.3": "",
               "reativar_F2-2.9.1": "1", "reativar_F2-2.9.3": "1"}
    assert cliente.post(url, data=reativa, follow_redirects=False).status_code == 303
    prep = sessao.get(PreparacaoForm2, pid)
    assert prep.conteudo["respostas_etapa1"]["F2-2.9.1"] == ["ALT_01"]
    assert prep.conteudo["respostas_etapa1"]["F2-2.9.3"] == "ALT_01"
    assert prep.conteudo["respostas_inativas_etapa1"] == {}
