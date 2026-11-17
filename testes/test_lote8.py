from app.confirmacoes_form2 import itens_a_confirmar
from app.form2_rev212 import RASCUNHO


def test_c1_lista_agrupada_exclui_inativas_comentarios_e_bloco14():
    conteudo = {"respostas_etapa1": {"F2-2.9": "A_CONFIRMAR"}, RASCUNHO: {
        "6": {"opcao:F2-6.1": ["A_CONFIRMAR"], "opcao:F2-6.2": ["A_CONFIRMAR"],
              "comentario:F2-6.3": "A_CONFIRMAR"},
        "14": {"opcao:F2-14.1": ["A_CONFIRMAR"]}}}
    grupos = itens_a_confirmar(conteudo)
    assert grupos == [
        {"bloco": 2, "itens": [{"item": "F2-2.9", "ancora": "F2-2.9"}]},
        {"bloco": 6, "itens": [{"item": "F2-6.1", "ancora": "F2-6.1"}]}]


from fastapi.testclient import TestClient
from app.main import app
from testes.test_governanca_form2_v9 import principal


def test_c1_lista_nas_duas_perguntas_sem_premarcacao(sessao, principal):
    principal.conteudo = {**principal.conteudo, "respostas_etapa1": {"F2-2.9": "A_CONFIRMAR"},
                         RASCUNHO: {"6": {"opcao:F2-6.1": ["A_CONFIRMAR"]}}}
    sessao.commit()
    tela = TestClient(app).get(f"/form2/participacoes/{principal.id}/blocos/14?conta_id=CONTA-B1")
    assert tela.status_code == 200
    assert tela.text.count('2 pergunta(s) ativa(s)') == 2
    assert tela.text.count('6?conta_id=CONTA-B1#F2-6.1') == 2
    campo = tela.text.split('name="opcao:F2-14.8"')[1].split('</select>')[0]
    assert 'selected' not in campo
