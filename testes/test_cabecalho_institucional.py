"""Identidade compartilhada: recurso oficial local e páginas autorizadas."""
from copy import deepcopy
import hashlib
from pathlib import Path
import struct
from urllib.parse import urlparse

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.modelos import RascunhoForm1Integral, VersaoForm1Integral
from testes.test_conferencia_interna_form1_integral_8ac import _preparar, _solicitar
from testes.test_p1_usabilidade_form1 import Elementos
from testes.test_cartilha_local_form1 import documento_local

cliente = TestClient(app, client=("127.0.0.1", 50123))
SHA256_OFICIAL = "ee5f7faec20ebc645c13c6cd28bfa97e5193034e69143dcf1ff6c9c7606f52be"


def conferir_cabecalho(resposta):
    elementos = Elementos(resposta.text).elementos
    imagens = [a for t, a, _ in elementos if t == "img" and a.get("class") == "brasao-institucional"]
    assert len(imagens) == 1
    img = imagens[0]
    assert img["alt"] == "Brasão oficial do Município de Hortolândia"
    assert img["width"] == img["height"] == "64"
    assert urlparse(img["src"]).path == "/estaticos/imagens/brasao-hortolandia.png"
    assert urlparse(img["src"]).netloc == "testserver"
    assert "tabindex" not in img and "onclick" not in img
    assert resposta.text.count("Prefeitura Municipal de Hortolândia") == 1
    assert "Sistema Municipal de Governança LGPD" in resposta.text
    assert "Ambiente de demonstração — utilize exclusivamente dados fictícios." in resposta.text
    assert resposta.text.index('class="topo"') < resposta.text.index('<main')


def test_png_local_e_original_sem_dependencia_externa():
    # Arrange / Act: lê pela mesma rota estática utilizada no navegador.
    resposta = cliente.get("/estaticos/imagens/brasao-hortolandia.png")
    # Assert: bytes preservados e proporção declarada consistente com a imagem.
    assert resposta.status_code == 200
    assert resposta.headers["content-type"] == "image/png"
    assert resposta.content == Path("app/estaticos/imagens/brasao-hortolandia.png").read_bytes()
    assert hashlib.sha256(resposta.content).hexdigest() == SHA256_OFICIAL
    assert resposta.content[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", resposta.content[16:24]) == (591, 591)


@pytest.mark.parametrize("conta", [f"CONTA-{letra}1" for letra in "ABCDEFGH"])
def test_painel_dos_perfis_compartilha_identidade_sem_novo_controle(conta):
    resposta = cliente.get("/", params={"conta_id": conta})
    assert resposta.status_code == 200
    conferir_cabecalho(resposta)


def test_abertura_preenchimento_consulta_erro_e_historico_preservados(sessao):
    registro = _preparar(sessao, "BRASAO-FICT")
    rid = registro["registro_id"]
    assert _solicitar(sessao, registro, comando="BRASAO-FICT-S1")["permitido"]
    rascunho = sessao.get(RascunhoForm1Integral, rid)
    anterior = deepcopy(rascunho.conteudo), rascunho.versao_rascunho
    from sqlalchemy import select
    snapshot = sessao.scalar(select(VersaoForm1Integral).where(VersaoForm1Integral.registro_id == rid))
    historico = snapshot.conteudo_canonico, snapshot.lacre
    paginas = [
        ("/registros/novo?conta_id=CONTA-A1", 200),
        (f"/registros/{rid}?conta_id=CONTA-G1", 200),
        (f"/registros/{rid}?conta_id=CONTA-A1", 200),
        (f"/registros/{rid}?conta_id=CONTA-C1", 403),
        (f"/registros/{rid}/form1-integral/conferencia-interna?conta_id=CONTA-A1", 200),
    ]
    for destino, status in paginas:
        resposta = cliente.get(destino)
        assert resposta.status_code == status
        conferir_cabecalho(resposta)
    integral = cliente.get(paginas[1][0]).text
    assert 'id="titulo-bloco-1"' in integral and 'id="titulo-bloco-14"' in integral
    assert 'id="titulo-pre-validacao-form1"' in integral
    assert "conclusão institucional do FORM 1 ainda não está habilitada" in integral
    sessao.refresh(rascunho)
    sessao.refresh(snapshot)
    assert (rascunho.conteudo, rascunho.versao_rascunho) == anterior
    assert (snapshot.conteudo_canonico, snapshot.lacre) == historico


def test_consulta_local_de_ajuda_herda_cabecalho_sem_alterar_cartilha(sessao, documento_local):
    registro = _preparar(sessao, "BRASAO-AJUDA-FICT")
    resposta = cliente.get(f"/registros/{registro['registro_id']}/cartilha/REV30.13/levantamento?conta_id=CONTA-G1")
    assert resposta.status_code == 200
    conferir_cabecalho(resposta)
    assert "Orientação fictícia" in resposta.text
