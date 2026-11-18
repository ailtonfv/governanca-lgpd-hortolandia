from app.confirmacoes_form2 import itens_a_confirmar
from app.form2_rev212 import RASCUNHO
from app.form2_rev212 import condicoes_de_tela, mapa_regras
from app.contrato_form2_respostas import carregar_contrato
from app.respostas_form2 import definicao_revisao
from app.fatos_abertura_form2 import projetar_fatos_abertura
from app.respostas_form2 import aplicar_revisao, contagem_perguntas_ativas
import pytest


def test_n1_reatribuicao_visivel_na_fila_autorizada(sessao, principal):
    from carga_ficticia.pessoas import semear_eta
    from app.modelos import Designacao
    from app.fila_form2 import reatribuir
    semear_eta(sessao)
    sessao.add(Designacao(pessoa_id='PESSOA-A', unidade_id=principal.unidade_id, papel='gestor_fila'))
    sessao.commit()
    reatribuir(sessao, conta_id='CONTA-A1', comando_id='L8-N1', participacao_id=principal.id,
               versao=principal.versao, responsavel_id='PESSOA-I', motivo='Redistribuição fictícia')
    sessao.commit()
    for conta in ('CONTA-A1','CONTA-I1'):
        pagina = TestClient(app).get('/form2/filas?conta_id=' + conta)
        assert pagina.status_code == 200
        assert 'Reatribuído por Servidor Alfa' in pagina.text
        assert ' às ' in pagina.context['atribuidores'][principal.id]
from app.form2_rev212 import orientacoes_ao_usuario


def test_c12_ajuda_separada_da_especificacao():
    texto = 'Controle candidato • Texto curto. Até 200 caracteres. Exibição • 1.1 = Sim. Indique a referência fictícia.'
    assert orientacoes_ao_usuario(texto) == ['Indique a referência fictícia.']
    for chave in ('F2-9.6.1', 'F2-9.6.2', 'F2-9.7.2'):
        item = next(q for q in definicao_revisao(9)['itens'] if q['id'] == chave)
        assert item['ajudas_usuario']
        assert all('Controle candidato' not in ajuda and 'Exibição' not in ajuda for ajuda in item['ajudas_usuario'])


def test_c10_apoio_sem_guia_inadequado_no_bloco4():
    assert all(f['chave'] != 'ANPD-LI' for q in definicao_revisao(4)['itens'] for f in q['fontes_publicas'])
    assert any(f['chave'] == 'ANPD-LI' for q in definicao_revisao(3)['itens'] for f in q['fontes_publicas'])
from app.campos_form2 import normalizar_cnpj
from app.campos_form2 import validar_referencia_temporal, data_exata


def test_c7_data_e_referencia_temporal():
    assert validar_referencia_temporal('2026-12-15') == '2026-12-15'
    assert validar_referencia_temporal('Após deliberação fictícia') == 'Após deliberação fictícia'
    assert data_exata('2026-12-15') and not data_exata('Após deliberação fictícia')
    for valor in ('2026-02-30', 'x' * 201):
        with pytest.raises(ValueError):
            validar_referencia_temporal(valor)


def test_c6_cnpj_sintetico_e_recusas():
    assert normalizar_cnpj('00000000000191') == '00.000.000/0001-91'
    assert normalizar_cnpj('') == ''
    for invalido in ('00000000000190', '11111111111111', 'texto fictício', '123'):
        with pytest.raises(ValueError):
            normalizar_cnpj(invalido)


def test_d7_condicoes_e_contagem():
    base = {RASCUNHO: {'10': {'opcao:F2-10.2': ['NAO'], 'opcao:F2-10.9': ['SIM'],
                             'opcao:F2-10.9.6': ['NAO']}}}
    antes = contagem_perguntas_ativas(base, [10])[10][1]
    alterado, _ = aplicar_revisao(base, 10, {'opcao:F2-10.2': ['SIM'],
        'opcao:F2-10.9.6': ['SIM']}, demonstrativo=True)
    assert contagem_perguntas_ativas(alterado, [10])[10][1] >= antes + 6
    for item in ('F2-10.3','F2-10.4','F2-10.9.7','F2-10.9.8','F2-10.9.9','F2-10.9.10'):
        campo = ('texto:' if item.endswith('.7') else 'opcao:') + item
        with pytest.raises(ValueError, match='depende de resposta anterior'):
            aplicar_revisao(base, 10, {campo: ['Fictício' if campo.startswith('texto:') else 'SIM']}, demonstrativo=True)


def test_d7_post_bloqueado_sem_gravar(sessao, principal):
    cliente = TestClient(app)
    for n, item in enumerate(('F2-10.3','F2-10.4','F2-10.9.7','F2-10.9.8','F2-10.9.9','F2-10.9.10')):
        campo = ('texto:' if item.endswith('.7') else 'opcao:') + item
        retorno = cliente.post(f'/form2/participacoes/{principal.id}/blocos/10', data={
            'conta_id': 'CONTA-B1', 'comando_id': f'L8-D7-{n}', 'versao': principal.versao,
            campo: 'Fictício' if campo.startswith('texto:') else 'SIM'})
        assert retorno.status_code == 409
    sessao.refresh(principal)
    assert not principal.conteudo.get(RASCUNHO, {}).get('10')


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
    assert tela.text.count('2 perguntas ativas') == 2
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


def test_p108_etiquetas_legiveis(principal):
    pagina = TestClient(app).get(f'/form2/participacoes/{principal.id}/blocos/3?conta_id=CONTA-B1')
    assert '[D11]' in pagina.text
    assert '[Guarda]' in pagina.text
    assert 'title="Aguarda homologação jurídica (D11)"' in pagina.text
    assert '⚖' not in pagina.text and '🗄' not in pagina.text


def test_c3_condicoes_de_fluxos_em_linguagem_comum():
    itens = definicao_revisao(11)['itens']
    condicoes_de_tela(itens, mapa_regras(carregar_contrato()), {}, ())
    ajudas = ' '.join(q['ajuda_condicao'] for q in itens)
    assert 'fluxo de Ouvidoria' in ajudas and 'fluxo de e-SIC' in ajudas
    assert 'ramo OUV' not in ajudas and 'ramo ESIC' not in ajudas


def test_c6_post_cnpj_invalido_nao_grava(sessao, principal):
    cliente = TestClient(app)
    url = f'/form2/participacoes/{principal.id}/blocos/10'
    dados = {'conta_id':'CONTA-B1', 'comando_id':'L8-CNPJ-INVALIDO', 'versao':principal.versao,
             'opcao:F2-10.2':'SIM', 'opcao:F2-10.2.2':'SIM', 'texto:F2-10.2.3':'00000000000190'}
    assert cliente.post(url, data=dados).status_code == 409
    sessao.refresh(principal)
    assert not principal.conteudo.get(RASCUNHO, {}).get('10')
    dados.update(comando_id='L8-CNPJ-VALIDO')
    dados['texto:F2-10.2.3'] = '00000000000191'
    assert cliente.post(url, data=dados).status_code == 200
    sessao.refresh(principal)
    assert principal.conteudo[RASCUNHO]['10']['texto:F2-10.2.3'] == '00.000.000/0001-91'


def test_c7_envio_direto_data_e_texto():
    base = {RASCUNHO: {'14': {'opcao:F2-14.4': ['SIM'], 'opcao:F2-14.4.2': ['SIM']}}}
    for valor in ('2026-12-15', 'Após a deliberação fictícia'):
        novo, _ = aplicar_revisao(base, 14, {'texto:F2-14.4.3':[valor]}, demonstrativo=True)
        assert novo[RASCUNHO]['14']['texto:F2-14.4.3'] == valor
    with pytest.raises(ValueError, match='data válida'):
        aplicar_revisao(base, 14, {'texto:F2-14.4.3':['2026-02-30']}, demonstrativo=True)


def test_c9_limites_unificados_preservam_excecao_explicita():
    from app.respostas_form2 import limite_texto_revisao
    assert limite_texto_revisao({'controle': 'Texto curto'}) == 200
    assert limite_texto_revisao({'controle': 'Texto longo'}) == 1000
    assert limite_texto_revisao({'controle': 'Texto curto', 'dominio': 'Até 500 caracteres'}) == 500
    for numero, chave in [(11,'F2-11.4.1'), (13,'F2-13.12.1'), (14,'F2-14.3'), (14,'F2-14.4.3')]:
        q = next(q for q in definicao_revisao(numero)['itens'] if q['id'] == chave)
        assert limite_texto_revisao(q) == 200
