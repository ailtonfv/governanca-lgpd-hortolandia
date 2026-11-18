"""Decisões do Lote 10: identificadores, dados fictícios e testes no _teste."""
from copy import deepcopy
import re
from fastapi.testclient import TestClient
from app.main import app
from app.respostas_form2 import definicao_bloco, definicao_revisao
from app.contrato_form2_respostas import carregar_contrato
from testes.test_governanca_form2_v9 import principal


def test_d9_treze_rotulos_codigos_e_destinos(principal):
    # Arrange: decisões explícitas e códigos do contrato anterior.
    tecnicas = ('F2-2.5','F2-2.6','F2-2.8','F2-2.9','F2-2.9.3',
                'F2-8.4','F2-8.5','F2-11S.8','F2-14.5')
    juridicas = ('F2-4.5','F2-6.6','F2-7.4.2.1','F2-11.7')
    contrato = carregar_contrato()
    cliente = TestClient(app)
    paginas = {}
    for ids, tipo, destino, contrario in ((tecnicas,'técnica','tematica','juridico'),
                                         (juridicas,'jurídica','juridico','tematica')):
        for chave in ids:
            bloco = int(re.match(r'F2-(\d+)', chave).group(1))
            # Act: mesma definição consumida pela tela, sem alterar respostas salvas.
            itens = (definicao_bloco(bloco) if bloco <= 2 else definicao_revisao(bloco))['itens']
            q = next(i for i in itens if i['id'] == chave)
            anteriores = [a for a in contrato['alternativas'] if a['id'] == chave]
            codigos = [a['codigo'] for a in anteriores if a['rotulo'].startswith('Requer análise')]
            # Assert: todos os códigos anteriores preservados e atalhos corretos.
            assert codigos
            assert {a['codigo'] for a in anteriores} <= {a['codigo'] for a in q['alternativas']}
            for codigo in codigos:
                assert next(a['rotulo'] for a in q['alternativas'] if a['codigo']==codigo) == 'Requer análise '+tipo
            if bloco not in paginas:
                resp=cliente.get(f'/form2/participacoes/{principal.id}/blocos/{bloco}?conta_id=CONTA-B1')
                assert resp.status_code == 200
                paginas[bloco]=resp.text
            trecho=paginas[bloco].split('data-item="'+chave+'"',1)[1].split('</aside>',1)[0]
            assert 'consulta_tipo='+destino in trecho
            assert 'consulta_tipo=dpo' in trecho
            assert 'consulta_tipo='+contrario not in trecho
            assert 'consulta_item='+chave in trecho or 'consulta_item='+chave.replace('.','%2E') in trecho


def test_d9_rotulo_nao_reescreve_valor_salvo():
    from app.classificacao_analise_form2 import classificar
    # Arrange: resposta histórica e opção sintética.
    resposta = {'opcao:F2-2.5': ['ANALISE_LEGADA']}
    antes = deepcopy(resposta)
    q={'id':'F2-2.5','alternativas':[{'codigo':'ANALISE_LEGADA','rotulo':'Requer análise'}]}
    # Act / Assert: apenas a apresentação é transformada.
    classificar(q)
    assert resposta == antes
    assert q['alternativas'][0]['codigo']=='ANALISE_LEGADA'
    assert q['alternativas'][0]['rotulo']=='Requer análise técnica'


def test_d10_orienta_sem_identificar_pessoa(principal):
    # Arrange / Act: renderização real da pergunta, sem escrever respostas.
    q=next(q for q in definicao_revisao(10)['itens'] if q['id']=='F2-10.2.1')
    tela=TestClient(app).get(f'/form2/participacoes/{principal.id}/blocos/10?conta_id=CONTA-B1')
    # Assert: texto aprovado e ajuda visíveis, campo preservado.
    assert tela.status_code == 200
    trecho=tela.text.split('id="F2-10.2.1"',1)[1].split('</fieldset>',1)[0]
    assert q['enunciado'] in trecho
    assert q['enunciado'].endswith('(sem nome).')
    assert 'Não informe nome de pessoa física.' in trecho
    assert 'texto:F2-10.2.1' in trecho


def test_d12_apoio_somente_nos_tres_blocos(principal):
    from app.contrato_form2_respostas import REFERENCIAS_ANPD
    # Arrange: três fontes, sem substituir as demais referências já existentes.
    destinos={6:'ANPD-CA', 9:'ANPD-TI', 13:'ANPD-DT'}
    cliente=TestClient(app)
    for numero in range(1,15):
        # Act: percorrer todas as páginas, inclusive as que não devem receber links.
        resp=cliente.get(f'/form2/participacoes/{principal.id}/blocos/{numero}?conta_id=CONTA-B1')
        assert resp.status_code==200
        for bloco,chave in destinos.items():
            fonte=REFERENCIAS_ANPD[chave]
            # Assert: link só no destino aprovado; quadro existente reaproveitado.
            assert (fonte['url'] in resp.text) is (numero==bloco)
            if numero==bloco:
                assert 'id="apoio-anpd"' in resp.text
                assert fonte['titulo'] in resp.text
