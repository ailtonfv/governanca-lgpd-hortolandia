"""Links dos instrumentos e do dashboard com edição e autorizações fictícias."""
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from app.main import app
from app.mapa_cartilha import CARTILHA_DASHBOARD, FORM2_BLOCOS, FORM3_BLOCOS, FORM4_BLOCOS
from testes.apoio_entrada import ClienteAposApresentacao
from testes.test_cartilha_local_form1 import documento_integrado
from testes.test_dashboard import dados
from testes.test_lote12 import entrada, fonte, protecoes
from testes.test_p1_usabilidade_form1 import Elementos


def _links(resposta, chaves):
    assert resposta.status_code == 200
    links = [attrs for tag, attrs, _ in Elementos(resposta.text).elementos
             if tag == "a" and "data-cartilha-chave" in attrs]
    assert set(chaves) <= {a["data-cartilha-chave"] for a in links}
    for link in links:
        assert link["target"] == "_blank"
        assert set(link["rel"].split()) == {"noopener", "noreferrer"}
        assert "/cartilha/REV30.24/" + link["data-cartilha-chave"] in link["href"]
    return links


def _conta(url, conta_id):
    partes = urlsplit(url)
    consulta = parse_qs(partes.query)
    consulta["conta_id"] = [conta_id]
    return urlunsplit(partes._replace(query=urlencode(consulta, doseq=True)))


def test_links_dos_blocos_dos_forms_2_a_4(dados, entrada, documento_integrado):
    cliente = ClienteAposApresentacao(app, client=("127.0.0.1", 51518))
    por_tipo = {item["obj"].tipo: item["obj"].id for item in dados["objetos"]}
    telas = (
        (f"/form2/participacoes/{entrada.id}/blocos", FORM2_BLOCOS),
        (f"/forms34/{por_tipo['R']}/blocos", FORM3_BLOCOS),
        (f"/forms34/{por_tipo['A']}/blocos", FORM4_BLOCOS),
    )
    destinos = {}
    for prefixo, mapa in telas:
        for bloco, chaves in mapa.items():
            resposta = cliente.get(f"{prefixo}/{bloco}?conta_id=CONTA-B1")
            for link in _links(resposta, chaves):
                destinos[link["href"]] = link["data-cartilha-chave"]
    for url, chave in destinos.items():
        resposta = cliente.get(url)
        assert resposta.status_code == 200
        assert f"Tópico fictício {chave}" in resposta.text
        assert resposta.headers["Cache-Control"] == "private, no-store"
    assert cliente.get(_conta(next(iter(destinos)), "CONTA-C1")).status_code == 403


def test_links_do_dashboard_e_limites_da_rota(dados, documento_integrado):
    cliente = ClienteAposApresentacao(app, client=("127.0.0.1", 51518))
    for tela, chaves in CARTILHA_DASHBOARD.items():
        rota = "/dashboard" if tela == "abertura" else f"/dashboard/{tela}"
        resposta = cliente.get(f"{rota}?conta_id=CONTA-B1")
        for link in _links(resposta, chaves):
            destino = cliente.get(link["href"])
            assert destino.status_code == 200
            assert "Tópico fictício " + link["data-cartilha-chave"] in destino.text
    rota = "/ajuda/cartilha/REV30.24/CART-51"
    assert cliente.get(rota + "?origem=dashboard&conta_id=INEXISTENTE").status_code == 403
    assert cliente.get(rota + "?origem=central&conta_id=CONTA-B1").status_code == 404
    externo = ClienteAposApresentacao(app, client=("192.0.2.10", 51518))
    assert externo.get(rota + "?origem=dashboard&conta_id=CONTA-B1").status_code == 403
