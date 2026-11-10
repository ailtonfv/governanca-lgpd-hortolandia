"""Unidade consultiva, com origens e preparações fictícias."""
from copy import deepcopy
import re

import pytest

from app import apresentacao_form2, catalogo_form2_rev18
from app.eventos import verificar_cadeia
from app.modelos import PreparacaoForm2, VersaoForm1Integral
from app.rascunho_form1_integral import salvar_bloco_12_form1_integral
from testes.test_form2_preparacao import base, cliente, iniciar
from testes.test_snapshot_form1_integral import _snapshot


def test_unidade_isola_origens_e_reutiliza_anotacao(sessao, monkeypatch):
    # A instalação pública pode executar este cenário sem material editorial local.
    itens = [{"id": id_, "enunciado": f"Enunciado fictício {id_}"} for id_ in
             ("F2-2.9", "F2-2.9.1", "F2-2.9.2", "F2-2.9.3")]
    itens[0]["escolha_documental"] = {"modo": "unica", "alternativas": ["Alternativa sintética"]}
    for filha, pai in ((1, 0), (3, 2)):
        itens[filha]["condicao_documental"] = {"origem": itens[pai]["id"], "resposta": "Sim"}
    monkeypatch.setattr(apresentacao_form2, "carregar_catalogo",
                        lambda: {"versao": "TESTE", "blocos": [{"numero": 2, "itens": itens}]})
    rid, s1 = base(sessao)
    url = f"/registros/{rid}/form2/preparacao"
    aal = {"conta_id": "CONTA-G1"}
    assert cliente.get(url, params={**aal, "snapshot_id": s1}).status_code == 403
    p1 = iniciar(sessao, rid, s1)["preparacao_id"]
    respostas = {"12.1": "Sim", "12.1.1": "37", "12.1.2": "Anos", "12.1.3": ["Outro"]}
    assert salvar_bloco_12_form1_integral(
        sessao, comando_id="GUARDA-S2", registro_id=rid, conta_id="CONTA-A1", versao_lida=1,
        respostas=respostas, complementos_outro={"12.1.3": "Referência fictícia de guarda"},
    )["permitido"]
    sessao.commit()
    s2 = _snapshot(sessao, {"registro_id": rid}, "GUARDA-ORIGEM-2", versao=2)["snapshot_id"]

    def retrato(sid):
        snapshot = sessao.get(VersaoForm1Integral, sid)
        return snapshot.lacre, deepcopy(snapshot.conteudo)

    antes = [retrato(s) for s in (s1, s2)]
    assert cliente.get(url, params={**aal, "preparacao_id": p1, "snapshot_id": s2}).status_code == 403
    apa = cliente.get(url, params={"conta_id": "CONTA-A1", "preparacao_id": p1})
    assert apa.status_code == 200 and 'id="unidade-guarda"' not in apa.text
    p2 = iniciar(sessao, rid, s2, comando_id="GUARDA-DESIGNAR-2")["preparacao_id"]
    for pid, numero in ((p1, 1), (p2, 2)):
        pagina = cliente.get(url, params={**aal, "preparacao_id": pid})
        assert pagina.status_code == 200
        unidade = pagina.text.split('id="unidade-guarda"', 1)[1].split('id="anotacoes"', 1)[0]
        assert pagina.text.count('href="#unidade-guarda"') == 1
        assert pagina.text.index('id="mapa-etapas"') < pagina.text.index('href="#unidade-guarda"')
        mapa = pagina.text.split('<ol class="mapa-form2">', 1)[1].split('</ol>', 1)[0]
        etapas = re.findall(r'<ul aria-label="Blocos da etapa [1-4]">(.*?)</ul>', mapa, re.S)
        assert [re.findall(r'Bloco (\d+)', e) for e in etapas] == [
            ["1", "2", "3", "4"], ["5", "6", "7", "13"], ["8", "9", "10", "11", "12"], ["14"]]
        assert mapa.count("<a ") == mapa.count('aria-current="step"') == 1
        assert 'href="#unidade-guarda"' not in apa.text
        assert "Alternativa sintética" in unidade
        assert ("Não há prazo de guarda informado" in unidade) == (numero == 1)
        assert unidade.count('class="fato-guarda"') == unidade.count("data-fato-guarda=") == 21
        assert "Mostrar também as não informadas" in pagina.text
        assert f"Versão histórica nº {numero} " in unidade
        assert "F1-12.1.3" in unidade and "<input" not in unidade and "<textarea" not in unidade
        prazo = unidade.split('data-fato-guarda="12.1.1"', 1)[1].split("</dd>", 1)[0]
        assert ("Sem resposta nesta versão" in prazo) == (numero == 1)
        assert "Pergunta inexistente nesta versão" in unidade.split('data-fato-guarda="12.5.2"', 1)[1].split("</dd>", 1)[0]
        assert ("Referência fictícia de guarda" in unidade) == (numero == 2)
        assert ('>37</span>' in unidade) == (numero == 2)
        for item in itens:
            assert item["enunciado"] in unidade
        for id_ in ("F2-2.9", "F2-2.9.2"):
            assert f"Aplicável se {id_} receber a resposta “Sim”." in unidade
        assert pagina.text.count('name="anotacao_preparatoria"') == 1

    dados = {**aal, "comando_id": "GUARDA-ANOTAR", "versao_lida": "1",
             "anotacao_preparatoria": "Conferir a referência fictícia."}
    salvar = url + f"/{p2}/salvar"
    assert cliente.post(salvar, data=dados).status_code == 200
    assert cliente.post(salvar, data={**dados, "comando_id": "GUARDA-OBSOLETA"}).status_code == 409
    sessao.expire_all()
    preparacao = sessao.get(PreparacaoForm2, p2)
    assert preparacao.conteudo == {"anotacao_preparatoria": dados["anotacao_preparatoria"]}
    assert (preparacao.salvo_por, preparacao.versao_rascunho) == ("PESSOA-G", 2)
    assert sessao.get(PreparacaoForm2, p1).versao_rascunho == 1
    assert verificar_cadeia(sessao, p2)[0] and antes == [retrato(s) for s in (s1, s2)]


def test_guarda_usa_enunciado_da_extensao_e_respostas_vazias(sessao, monkeypatch):
    monkeypatch.setattr(apresentacao_form2, "carregar_catalogo",
                        lambda: {"versao": "TESTE", "blocos": [{"numero": 2, "itens": []}]})
    rid, sid = base(sessao, perfil="ambas")
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    pagina = cliente.get(f"/registros/{rid}/form2/preparacao",
                         params={"conta_id": "CONTA-G1", "preparacao_id": pid})
    assert pagina.status_code == 200
    unidade = pagina.text.split('id="unidade-guarda"', 1)[1].split('id="anotacoes"', 1)[0]
    for id_ in ("12.3", "12.4", "12.5", "12.5.2"):
        item = unidade.split(f'data-fato-guarda="{id_}"', 1)[1].split("</dd>", 1)[0]
        assert f"F1-{id_} — " in item and "Sem resposta nesta versão." in item
    assert unidade.count("data-fato-guarda=") == 21
    assert pagina.text.count("Detalhes técnicos (auditoria)") == 1


@pytest.mark.parametrize("invalido", [False, True])
def test_catalogo_local_indisponivel_preserva_preparacao(sessao, tmp_path, monkeypatch, invalido):
    arquivo = tmp_path / "catalogo.json"
    if invalido:
        arquivo.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(catalogo_form2_rev18, "ARQUIVO", arquivo)
    rid, sid = base(sessao)
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    pagina = cliente.get(f"/registros/{rid}/form2/preparacao",
                         params={"conta_id": "CONTA-G1", "preparacao_id": pid})
    assert pagina.status_code == 200 and 'id="unidade-guarda"' in pagina.text
    assert "A anotação geral continua disponível" in pagina.text and 'id="anotacao"' in pagina.text
    assert 'id="orientacoes-guarda"' not in pagina.text


@pytest.mark.skipif(not catalogo_form2_rev18.ARQUIVO.is_file(), reason="Catálogo institucional de uso local")
def test_edicao_local_renderiza_enunciados_validados(sessao):
    rid, sid = base(sessao)
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    pagina = cliente.get(f"/registros/{rid}/form2/preparacao",
                         params={"conta_id": "CONTA-G1", "preparacao_id": pid})
    assert pagina.status_code == 200
    bloco = next(b for b in catalogo_form2_rev18.carregar_catalogo()["blocos"] if b["numero"] == 2)
    perguntas = [q for q in bloco["itens"] if q["id"] == "F2-2.9" or q["id"].startswith("F2-2.9.")]
    assert len(perguntas) == 4 and all(q["enunciado"] in pagina.text for q in perguntas)
    for questao in perguntas:
        for alternativa in questao["escolha_documental"]["alternativas"]:
            assert alternativa in pagina.text
    assert "Lei nº 8.159/1991" in pagina.text
