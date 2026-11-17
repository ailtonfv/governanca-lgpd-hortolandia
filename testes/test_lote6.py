import re

from fastapi.testclient import TestClient

from app.main import app
from app.respostas_form2 import estados_regua_form2
from testes.test_governanca_form2_v9 import principal


def test_p98_cartao_atual_e_grade_compacta(principal):
    cliente = TestClient(app)
    raiz = f"/form2/participacoes/{principal.id}"
    for bloco in (2, 3, 7, 14):
        pagina = cliente.get(f"{raiz}/blocos/{bloco}?conta_id=CONTA-B1")
        assert pagina.status_code == 200
        assert pagina.text.count('aria-current="page"') == 1
        assert pagina.text.count("Você está aqui") == 1
        assert "grade-form2-compacta" in pagina.text
        assert len(re.findall('data-numero="', pagina.text)) == 14
        assert 'role="img" aria-label="Aguarda homologação jurídica (D11)"' in pagina.text
    participacao = cliente.get(raiz + "?conta_id=CONTA-B1")
    assert "grade-form2-compacta" not in participacao.text


def test_p97_p99_p100_central_e_nome_da_origem(sessao, principal):
    from app.modelos import Registro
    from app.origem_form2 import nome_objeto_em_analise

    nome = nome_objeto_em_analise(sessao, principal.registro_id, principal.snapshot_id)
    registro = sessao.get(Registro, principal.registro_id)
    registro.titulo_objeto = "Título atual diferente da apresentação"
    sessao.commit()
    cliente = TestClient(app)
    central = cliente.get("/central?conta_id=CONTA-B1")
    assert "<h1>Central de Acesso</h1>" in central.text
    assert "Central de Acesso LGPD" not in central.text
    assert "Ao voltar a uma aba antiga, confira o servidor em sessão." in central.text
    assert "antes do sinal #" not in central.text
    esperado = f"{registro.codigo_lgpd} · {nome} · Abrir participação"
    assert esperado in central.text
    fila = cliente.get("/form2/filas?conta_id=CONTA-B1")
    assert esperado in fila.text


def test_p86_comentario_nao_cria_preenchimento():
    from app.form2_rev212 import RASCUNHO

    estado = estados_regua_form2({RASCUNHO: {"3": {"comentario:F2-3.1": "Anotação fictícia"}}})
    assert estado["situacao"]["3"] == "— Ainda não preenchido"
