from app.respostas_form2 import estados_regua_form2
from app.form2_rev212 import RASCUNHO

def test_p102_progresso_proporcional():
    estado = estados_regua_form2({"respostas_etapa1": {"F2-2.9": "A_CONFIRMAR"}})
    assert estado["progresso"]["2"] == {"respondidas": 1, "ativas": 10, "percentual": 10.0}
    assert "1" not in estado["progresso"]

def test_p102_progresso_completo():
    estado = estados_regua_form2({"respostas_etapa1": {
        "F2-1.2": "CONFIRMADA", "F2-1.2.1": "Descrição fictícia", "F2-1.3": "SIM"}})
    assert estado["progresso"]["1"] == {"respondidas": 3, "ativas": 3, "percentual": 100}
    assert estado["situacao"]["1"] == "✓ Todas as perguntas ativas respondidas"

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

def test_p103_p105_p106_telas(principal):
    cliente = TestClient(app)
    central = cliente.get("/central?conta_id=CONTA-B1")
    assert 'class="central-cabecalho"' not in central.text
    tela = cliente.get(f"/form2/participacoes/{principal.id}?conta_id=CONTA-B1")
    assert 'class="central-cabecalho"' in tela.text
    assert 'data-area-tematica hidden' in tela.text
    assert 'data-destino-fixo data-dpo=' in tela.text
    dpo = cliente.get(f"/form2/participacoes/{principal.id}/orientacao?conta_id=CONTA-E1")
    assert dpo.status_code == 200
    assert "ficará no histórico e não poderá ser alterada" in dpo.text
    assert 'Cancelar e revisar as opções' in dpo.text
