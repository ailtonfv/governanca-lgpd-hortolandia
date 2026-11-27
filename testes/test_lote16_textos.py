from pathlib import Path
from app.rev22_form1 import definicoes


def test_textos_aprovados_e_catalogo_local_sem_mudar_codigo_docs():
    raiz=Path(__file__).parents[1]
    texto=(raiz/'app/paginas/apoio_como-funciona.html').read_text(encoding='utf8')
    for trecho in ('se o risco foi totalmente reduzido','nem falha ainda aberta','por todos os servidores',
                   'prazo máximo é de 30 dias','Aceitação com condições gera uma providência',
                   'a Secretaria propõe a nota do risco que sobrou e o DPO confirma',
                   'Não vê o conteúdo dos Registros.'):
        assert trecho in texto
    novo=(raiz/'app/paginas/novo_registro.html').read_text(encoding='utf8')
    assert 'Nenhum canal: o trabalho não começa por pedido de alguém' in novo
    q=definicoes()['8.2']
    assert 'Processo administrativo eletrônico municipal' not in q['options']
    assert 'DOCS' in q['options']
    assert q['option_labels']['DOCS']=='DOCS (inclui aprovações on-line)'


def test_g11_dicas_compartilhadas():
    from fastapi.testclient import TestClient
    from app.main import app

    resposta = TestClient(app).get('/como-funciona?conta_id=CONTA-A1')
    assert resposta.status_code == 200
    assert 'Dicas para usar o sistema' in resposta.text and 'F3-3.28' in resposta.text
    assert 'A Cartilha abre em outra aba' in resposta.text
