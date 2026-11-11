import pytest

from app.contrato_form2_respostas import ARQUIVO
from app.respostas_form2 import aplicar_bloco
from testes.test_form2_preparacao import base, iniciar, cliente


pytestmark = pytest.mark.skipif(not ARQUIVO.is_file(), reason="Contrato local da REV18")


def test_identificacao_http(sessao):
    rid, sid = base(sessao)
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    url = f"/registros/{rid}/form2/preparacao"
    contexto = {"conta_id": "CONTA-G1", "preparacao_id": pid}
    assert 'id="form2-bloco-1"' in cliente.get(url, params=contexto).text
    rota = f"{url}/{pid}/blocos/1/salvar"
    dados = {"conta_id": "CONTA-G1", "versao_lida": "1", "comando_id": "B1-TESTE",
             "resposta_F2-1.2": "DIVERGENTE", "resposta_F2-1.3": "SIM",
             "resposta_F2-1.3.1": "Exemplo fictício para conferência"}
    salvo = cliente.post(rota, data=dados, follow_redirects=False)
    assert salvo.status_code == 303 and salvo.headers["location"].endswith("#identificacao")
    assert dados["resposta_F2-1.3.1"] in cliente.get(url, params=contexto).text
    assert cliente.post(rota, data={**dados, "resposta_F2-1.5": "indevido"}).status_code == 400


def test_identificacao_condicoes_e_preservacao():
    for secretaria in (None, "CONFIRMADA", "DIVERGENTE"):
        for suficiente in (None, "SIM", "NAO", "PARCIAL", "A_CONFIRMAR"):
            valores = {"F2-1.2": secretaria, "F2-1.3": suficiente, "F2-1.3.1": "Texto fictício"}
            if secretaria == "DIVERGENTE" or suficiente in ("NAO", "PARCIAL"):
                novo, _ = aplicar_bloco({}, bloco=1, alteracoes=valores, proxima_versao=2)
                fechado, _ = aplicar_bloco(novo, bloco=1, alteracoes={"F2-1.2": "CONFIRMADA", "F2-1.3": "SIM"}, proxima_versao=3)
                assert fechado["respostas_inativas_etapa1"]["F2-1.3.1"]["valor"] == "Texto fictício"
                aberto, _ = aplicar_bloco(fechado, bloco=1, alteracoes={"F2-1.2": "DIVERGENTE", "F2-1.3.1": None}, proxima_versao=4)
                restaurado, _ = aplicar_bloco(aberto, bloco=1, alteracoes={}, reativar={"F2-1.3.1"}, proxima_versao=5)
                assert restaurado["respostas_etapa1"]["F2-1.3.1"] == "Texto fictício"
            else:
                with pytest.raises(ValueError, match="inativo"):
                    aplicar_bloco({}, bloco=1, alteracoes=valores, proxima_versao=2)
