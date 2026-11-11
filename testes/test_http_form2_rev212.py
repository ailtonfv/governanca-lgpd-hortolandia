from types import SimpleNamespace
import re
import pytest

from starlette.requests import Request
from fastapi import HTTPException
from urllib.parse import urlencode
from app.main import app
from app import rotas_form2_preparacao as rotas
from app.respostas_form2 import aplicar_revisao


def test_percurso_rascunho_http(monkeypatch):
    prep = SimpleNamespace(id="FICTICIO-P", versao_rascunho=1, conteudo={
        "revisao_blocos_rev20": {"13": {"texto:F2-13.12": "Local fictício da REV20"}}
    })
    origem = {"perguntas": [], "conteudo": {"respostas": {}}}
    def consultar(sessao, conta_id, **kwargs):
        autorizado = conta_id == "FICTICIO-AAL"
        return {"permitido": autorizado, "pode_editar": autorizado, "preparacao": prep,
                "registro": SimpleNamespace(id="FICTICIO-R", codigo_lgpd="Fictício"), "origem": origem}

    def salvar(sessao, *, bloco, versao_lida, alteracoes, **kwargs):
        if versao_lida != prep.versao_rascunho:
            return {"permitido": False, "motivo": "Versão desatualizada"}
        try:
            prep.conteudo, _ = aplicar_revisao(prep.conteudo, bloco, alteracoes)
        except ValueError as erro:
            return {"permitido": False, "motivo": str(erro)}
        prep.versao_rascunho += 1
        return {"permitido": True}

    monkeypatch.setattr(rotas, "consultar_preparacao", consultar)
    monkeypatch.setattr(rotas, "salvar_respostas_bloco", salvar)
    def abrir(n, conta="FICTICIO-AAL", dados=None):
        corpo = urlencode(dados or {}).encode()
        async def receber():
            return {"type": "http.request", "body": corpo, "more_body": False}
        request = Request({"type": "http", "method": "POST" if dados is not None else "GET",
                           "scheme": "http", "server": ("testserver",80), "root_path": "",
                           "path": f"/registros/FICTICIO-R/form2/preparacao/FICTICIO-P/revisao/{n}",
                           "query_string": urlencode({"conta_id": conta}).encode(),
                           "headers": [(b"content-type", b"application/x-www-form-urlencoded")],
                           "router": app.router}, receber)
        tarefa = rotas.revisao_form2(request, "FICTICIO-R", "FICTICIO-P", n, conta,
                                     SimpleNamespace(commit=lambda: None))
        # A sessão em memória e o corpo do formulário estão disponíveis imediatamente.
        try:
            tarefa.send(None)
        except StopIteration as resultado:
            return resultado.value
        finally:
            tarefa.close()
        raise AssertionError("A rota esperava uma dependência externa.")
    ids = []
    for n in range(1, 15):
        pagina = abrir(n)
        assert pagina.status_code == 200
        ids.extend(re.findall(r"<legend>(F2-[^ ]+) —", pagina.body.decode()))
    assert len(ids) == len(set(ids)) == 255
    with pytest.raises(HTTPException) as erro:
        abrir(3, conta="FICTICIO-OUTRA")
    assert erro.value.status_code == 403
    dados = {"comando_id": "FICTICIO-1", "versao_lida": "1", "opcao:F2-13.12": "SIM"}
    with pytest.raises(HTTPException) as erro:
        abrir(13, dados=dados)
    assert erro.value.status_code == 409
    dados["edicao"] = "REV21.2"
    assert abrir(13, dados=dados).status_code == 303
    dados.update(comando_id="FICTICIO-2", versao_lida="2")
    dados["texto:F2-13.12.1"] = "Local fictício da REV21.2"
    assert abrir(13, dados=dados).status_code == 303
    pagina = abrir(13).body.decode()
    assert dados["texto:F2-13.12.1"] in pagina and "Local fictício da REV20" in pagina
