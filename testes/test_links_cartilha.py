"""Integridade das chaves editoriais e abertura contextual da Cartilha."""
from pathlib import Path
import re

import pytest
from fastapi import Request

from app import cartilha_local, cartilha_topicos
from app.clausulas_lgpd import catalogo
from app.main import app
from app.mapa_cartilha import FORM2_CLAUSULAS, FORM4_CLAUSULAS
from app.rotas_fila_form2 import paginas
from testes.test_bloco5_form1_integral import _rascunho_pronto
from testes.test_cartilha_local_form1 import cliente, documento_integrado
from testes.test_p1_usabilidade_form1 import Elementos


def test_chaves_das_telas_resolvem_na_edicao_instalada():
    doc = cartilha_local.CAMINHO_CARTILHA_INTEGRADA
    catalogo_local = cartilha_topicos.CAMINHO_TOPICOS
    if not doc.is_file() and not catalogo_local.is_file():
        pytest.skip("Instale localmente a REV30.24 e o catálogo de tópicos para conferir os destinos reais.")
    raiz = Path(__file__).resolve().parents[1] / "app"
    chaves = {
        chave
        for arquivo in raiz.rglob("*")
        if arquivo != catalogo_local and arquivo.suffix in {".html", ".py", ".js", ".json"}
        for chave in re.findall(r"\bCART-\d+\b", arquivo.read_text(encoding="utf-8-sig"))
    }
    assert chaves == cartilha_topicos.CHAVES_CARTILHA
    topicos = cartilha_topicos.catalogo_topicos()
    ausentes = sorted(chaves - cartilha_topicos.destinos_integrados(topicos).keys())
    assert not ausentes, "Chaves sem marcador disponível na edição instalada: " + ", ".join(ausentes)


def _requisicao():
    return Request({"type": "http", "scheme": "http", "server": ("testserver", 80),
                    "headers": [], "router": app.router, "client": ("127.0.0.1", 50123)})


def test_sem_marcador_real_ou_chave_desconhecida_nao_ha_link(documento_integrado, monkeypatch):
    topicos = cartilha_topicos.catalogo_topicos()
    invalido = {**topicos, "CART-52": {**topicos["CART-52"], "ancora": "inexistente"}}
    monkeypatch.setattr(cartilha_topicos, "catalogo_topicos", lambda: invalido)
    links = cartilha_topicos.links_topicos(_requisicao(), "CONTA-A1", ("CART-28", "CART-52", "CART-99"), "registro")
    assert [link["chave"] for link in links] == ["CART-28"]


def test_links_do_quadro_de_clausulas_e_do_anexo_abrem_documento(sessao, documento_integrado):
    rid = _rascunho_pronto(sessao, "CARTILHA-CLAUSULAS")["registro_id"]
    clausulas = catalogo()
    for arquivo, chaves, condicao in (
        ("_clausulas_form2.html", FORM2_CLAUSULAS,
         {"numero": 9, "ativa": lambda *_: True, "clausulas_lgpd": clausulas, "valores": {}}),
        ("_clausulas_form4.html", FORM4_CLAUSULAS,
         {"ref": {"form": 4}, "bloco": 2, "clausulas_acao": [{"codigo": "B01"}],
          "clausulas_aviso": clausulas["aviso_fixo"], "estado": {}}),
    ):
        links_cartilha = cartilha_topicos.links_topicos(_requisicao(), "CONTA-A1", chaves, rid)
        html = paginas.get_template(arquivo).render(links_cartilha_clausulas=links_cartilha, **condicao)
        links = [attrs for tag, attrs, _ in Elementos(html).elementos if tag == "a"]
        assert tuple(link["data-cartilha-chave"] for link in links) == chaves
        for link in links:
            assert link["target"] == "_blank"
            assert set(link["rel"].split()) == {"noopener", "noreferrer"}
            resposta = cliente.get(link["href"])
            assert resposta.status_code == 200
            assert f'Tópico fictício {link["data-cartilha-chave"]}' in resposta.text
