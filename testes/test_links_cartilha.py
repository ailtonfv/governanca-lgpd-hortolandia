"""Referências CART de tela; a edição instalada permanece fora do Git."""
from html import unescape
from pathlib import Path
import re

import pytest
from fastapi import Request

from app import cartilha_local
from app.clausulas_lgpd import catalogo
from app.main import app
from app.rotas_fila_form2 import paginas
from testes.test_bloco5_form1_integral import _rascunho_pronto
from testes.test_cartilha_local_form1 import cliente, documento_local
from testes.test_p1_usabilidade_form1 import Elementos


@pytest.fixture
def destinos_instalados():
    if not cartilha_local.CAMINHO_CARTILHA.is_file():
        pytest.skip("Instale localmente a Cartilha REV30.13 para conferir os destinos reais.")
    secoes = cartilha_local.secoes_cartilha_disponiveis()
    assert secoes, "Edição instalada indisponível ou diferente da edição conferida."
    return cartilha_local.destinos_cartilha_clausulas(catalogo()["links"], secoes)


def test_todas_as_chaves_cart_resolvem_exceto_as_pendencias_conhecidas(destinos_instalados):
    raiz = Path(__file__).resolve().parents[1] / "app"
    chaves = {
        chave
        for arquivo in raiz.rglob("*")
        if arquivo.suffix in {".html", ".py", ".js", ".json"}
        for chave in re.findall(r"\bCART-\d+\b", arquivo.read_text(encoding="utf-8-sig"))
    }
    assert chaves
    ausentes = sorted(chaves - destinos_instalados.keys() - {"CART-28", "CART-52"})
    assert not ausentes, "Chaves sem destino na Cartilha instalada: " + ", ".join(ausentes)


@pytest.mark.parametrize("chave", [
    pytest.param("CART-28", marks=pytest.mark.xfail(strict=True,
        reason="O tópico sobre contratos, terceiros, OSCs e Cultura não tem destino na REV30.13.")),
    pytest.param("CART-52", marks=pytest.mark.xfail(strict=True,
        reason="O Anexo E consta como proposta e não tem destino na REV30.13.")),
])
def test_pendencias_editoriais_da_cartilha(chave, destinos_instalados):
    assert chave in destinos_instalados, f"{chave} sem destino na Cartilha instalada"


def test_link_de_clausulas_abre_apenas_para_registro_visivel_no_ambiente_local(sessao, documento_local):
    registro = _rascunho_pronto(sessao, "CARTILHA-CLAUSULAS")
    rid = registro["registro_id"]
    escopo = {
        "type": "http", "scheme": "http", "server": ("testserver", 80), "headers": [],
        "router": app.router, "client": ("127.0.0.1", 50123),
    }
    clausulas = catalogo()
    links = clausulas["links"]
    disponiveis = cartilha_local.links_cartilha_clausulas(Request(escopo), sessao, "CONTA-A1", rid, links)
    assert [link["chave"] for link in disponiveis] == ["CART-11"]
    for arquivo, condicao in (
        ("_clausulas_form2.html", {"numero": 9, "ativa": lambda *_: True, "clausulas_lgpd": clausulas, "valores": {}}),
        ("_clausulas_form4.html", {"ref": {"form": 4}, "bloco": 2, "clausulas_acao": [{"codigo": "B01"}],
                                  "clausulas_aviso": clausulas["aviso_fixo"], "estado": {}}),
    ):
        html = paginas.get_template(arquivo).render(links_cartilha_clausulas=disponiveis, **condicao)
        [link] = [attrs for tag, attrs, _ in Elementos(html).elementos if tag == "a"]
        assert link["data-cartilha-chave"] == "CART-11"
        assert link["target"] == "_blank" and set(link["rel"].split()) == {"noopener", "noreferrer"}
        resposta = cliente.get(link["href"])
        assert resposta.status_code == 200
        assert "Operador, terceiros, OSCs e entidades parceiras" in unescape(resposta.text)

    assert not cartilha_local.links_cartilha_clausulas(Request(escopo), sessao, "INEXISTENTE", rid, links)
    remoto = Request({**escopo, "client": ("192.0.2.10", 50123)})
    assert not cartilha_local.links_cartilha_clausulas(remoto, sessao, "CONTA-A1", rid, links)
