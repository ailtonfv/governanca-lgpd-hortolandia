from app.confirmacoes_form2 import itens_a_confirmar
from app.form2_rev212 import RASCUNHO
from app.form2_rev212 import condicoes_de_tela, mapa_regras
from app.contrato_form2_respostas import carregar_contrato
from app.respostas_form2 import definicao_revisao
from app.fatos_abertura_form2 import projetar_fatos_abertura


def test_d6_fatos_do_snapshot_sem_alterar_respostas():
    itens = [{'id': 'F2-4.1', 'referencias_form1': ['F1-5.1']},
             {'id': 'F2-5.1', 'referencias_form1': ['F1-2.13']}]
    origem = {'perguntas': [{'id': '5.1', 'respondida': True, 'valor': ['Categoria fictícia']}],
              'conteudo': {}}
    projetar_fatos_abertura(itens, origem)
    assert itens[0]['fatos_abertura'][0]['valor'] == 'Categoria fictícia'
    assert itens[1]['fatos_abertura'] == []
    assert all('valor' not in item for item in itens)


def test_d6_sete_aberturas_sem_premarcacao(principal):
    cliente = TestClient(app)
    for numero in (4, 5, 6, 7, 8, 9, 11):
        tela = cliente.get(f"/form2/participacoes/{principal.id}/blocos/{numero}?conta_id=CONTA-B1")
        assert tela.status_code == 200
        assert 'class="fatos-abertura-form2"' in tela.text
        campo = tela.text.split(f'name="opcao:F2-{numero}.1"')[1].split('</select>')[0]
        assert 'selected' not in campo


def test_c2_condicoes_resolvem_opcoes_de_outros_blocos():
    itens = definicao_revisao(5)['itens']
    condicoes_de_tela(itens, mapa_regras(carregar_contrato()), {}, ())
    for q in itens:
        assert 'ALT_' not in q['ajuda_condicao']
    for q in itens:
        if q['id'] in ('F2-5.4', 'F2-5.7'):
            assert 'Consentimento' in q['ajuda_condicao']


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


def test_c4_consultas_sem_rotulo_tecnico(principal):
    cliente = TestClient(app)
    for numero in (13, 14):
        tela = cliente.get(f"/form2/participacoes/{principal.id}/blocos/{numero}?conta_id=CONTA-B1")
        assert tela.status_code == 200
        assert 'Consulta automática' not in tela.text
        assert 'resposta candidata' not in tela.text
