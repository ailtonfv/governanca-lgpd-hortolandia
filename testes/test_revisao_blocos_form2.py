import re
import pytest

from app.contrato_form2_respostas import ARQUIVO
from testes.test_form2_preparacao import base, cliente, iniciar


@pytest.mark.skipif(not ARQUIVO.is_file(), reason="Matriz privada da instalação")
def test_percurso_revisao_completo(sessao):
    registro, origem = base(sessao)
    prep = iniciar(sessao, registro, origem)["preparacao_id"]
    rota = f"/registros/{registro}/form2/preparacao/{prep}/revisao"
    aal = {"conta_id": "CONTA-G1"}
    ids = []
    for bloco in range(1, 15):
        pagina = cliente.get(f"{rota}/{bloco}", params=aal)
        assert pagina.status_code == 200
        ids.extend(re.findall(r'<legend>(F2-[^ ]+) —', pagina.text))
    assert len(ids) == len(set(ids)) == 255
    assert cliente.get(f"{rota}/3", params={"conta_id": "CONTA-A1"}).status_code == 403
    for bloco, versao, campo, valor in [(3, 1, "comentario:F2-3.1", "Revisar exemplo fictício"),
                                         (14, 2, "texto:F2-14.2#2", "Ocorrência de ensaio")]:
        url = f"{rota}/{bloco}"
        dados = {"edicao": "REV21.2", "comando_id": f"REV-{bloco}", "versao_lida": str(versao), campo: valor}
        assert cliente.post(url, params=aal, data=dados, follow_redirects=False).status_code == 303
        assert valor in cliente.get(url, params=aal).text
    invalido = {"edicao": "REV21.2", "comando_id": "REV-JUR", "versao_lida": "3", "opcao:F2-3.1": "SIM"}
    assert cliente.post(f"{rota}/3", params=aal, data=invalido).status_code == 409
