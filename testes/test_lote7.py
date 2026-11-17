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
