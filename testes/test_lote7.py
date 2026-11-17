from app.respostas_form2 import estados_regua_form2
from app.form2_rev212 import RASCUNHO

def test_p102_progresso_proporcional():
    estado = estados_regua_form2({RASCUNHO: {"2": {"opcao:F2-2.9": ["A_CONFIRMAR"]}}})
    assert estado["progresso"]["2"] == {"respondidas": 1, "ativas": 10, "percentual": 10.0}
    assert "1" not in estado["progresso"]

def test_p102_progresso_completo(monkeypatch):
    import app.respostas_form2 as dominio
    monkeypatch.setattr(dominio, "contagem_perguntas_ativas", lambda *a, **k: {2: (10, 10)})
    estado = dominio.estados_regua_form2({})
    assert estado["progresso"]["2"]["percentual"] == 100
    assert estado["situacao"]["2"] == "✓ Todas as perguntas ativas respondidas"

from fastapi.testclient import TestClient
from app.main import app
from testes.test_governanca_form2_v9 import principal

def test_p101_salvar_para_continuar_preserva_validacao(sessao, principal):
    cliente = TestClient(app)
    url = f"/form2/participacoes/{principal.id}/blocos/3"
    pagina = cliente.get(url + "?conta_id=CONTA-B1")
    assert 'id="saida-bloco-form2"' in pagina.text
    assert 'Salvar e continuar' in pagina.text
    dados = {"conta_id": "CONTA-B1", "versao": principal.versao,
             "comando_id": "L7-RECUSADO", "opcao:F2-3.1": ["ALT_09", "A_CONFIRMAR"]}
    recusa = cliente.post(url, data=dados, headers={"X-Salvar-Bloco": "1"})
    assert recusa.status_code == 409
    sessao.refresh(principal)
    assert not principal.conteudo.get(RASCUNHO, {}).get("3")
    dados.update(comando_id="L7-SALVO")
    dados["opcao:F2-3.1"] = ["ALT_09", "ANALISE_JURIDICA"]
    salvo = cliente.post(url, data=dados, headers={"X-Salvar-Bloco": "1"})
    assert salvo.status_code == 200
    assert salvo.json()["salvo"] is True
    sessao.refresh(principal)
    assert principal.conteudo[RASCUNHO]["3"]["opcao:F2-3.1"] == ["ALT_09", "ANALISE_JURIDICA"]
    assert "/blocos/3?" in salvo.json()["destino"]
