"""Sobras da vistoria: testes direcionados, dados exclusivamente fictícios."""
import re
from html import unescape
from pathlib import Path
import pytest
from testes.test_lote15b import abrir
from testes.test_cartilha_local_form1 import documento_local
from testes.test_lote11 import fonte
from testes.apoio_entrada import ClienteAposApresentacao as TestClient
from app.main import app


def test_c217_cartilha_presente_nos_14_blocos(sessao,documento_local):
    reg,c,url=abrir(sessao)
    for bloco in range(1,15):
        html=c.get(url+f'?conta_id=CONTA-G1&bloco={bloco}').text
        link=re.search(r'<a[^>]+href="([^"]*/cartilha/[^"]+)"[^>]*>Na Cartilha:',html)
        assert link,bloco
        assert '(abre em outra aba)' in html
        assert c.get(unescape(link[1])).status_code==200


def test_c217_montagem_recusa_documento_ausente_e_confere_copia(tmp_path,documento_local,monkeypatch):
    from scripts import preparar_cartilha_entrega as montagem
    from app import cartilha_local
    import shutil
    origem=tmp_path/'origem'; destino=tmp_path/'entrega'
    with pytest.raises(ValueError,match='ausente'):montagem.preparar(origem,destino)
    relativo=Path('documentos_locais/cartilha')/montagem.ARQUIVO_CARTILHA
    (origem/relativo).parent.mkdir(parents=True)
    shutil.copy2(cartilha_local.CAMINHO_CARTILHA,origem/relativo)
    monkeypatch.setattr(montagem,'SHA256_CARTILHA',cartilha_local.SHA256_CARTILHA)
    alvo=montagem.preparar(origem,destino)
    assert alvo.read_bytes()==(origem/relativo).read_bytes()
    assert montagem.preparar(origem,destino)==alvo


def test_c213_c214_c215_confirmado_e_permissoes(sessao,fonte):
    from app.modelos import ParticipacaoForm2,Designacao
    p=sessao.get(ParticipacaoForm2,fonte['form2_id'])
    sessao.add(Designacao(pessoa_id='PESSOA-B',unidade_id=p.unidade_id,papel='aal_form2',ativa=True))
    p.responsavel_id='PESSOA-B';sessao.commit()
    c=TestClient(app)
    for conta,permitido in [('CONTA-A1',False),('CONTA-B1',True),('CONTA-G1',False)]:
        html=c.get('/registros/'+fonte['registro_id']+'?conta_id='+conta).text
        assert 'Versão de trabalho:' in html and 'salvamentos.' in html
        assert 'Você pode salvar e continuar depois' not in html
        assert 'Quando terminar, apresente ao APA' not in html
        assert not re.search(r'<span class="estado">Rascunho \d',html)
        cartoes=html[html.index('id="instrumentos-registro"'):]
        assert 'Consultar FORM 1' in cartoes and 'Ir ao preenchimento' not in cartoes
        f2=re.search(r'<li data-instrumento="FORM2">.*?</li>',cartoes,re.S)[0]
        if permitido:
            link=re.search(r'href="([^"]+)"',f2)[1]
            assert '/form2/participacoes/'+p.id in link and 'Consultar FORM 2' in f2
            assert c.get(unescape(link)).status_code==200
        else:
            assert 'O FORM 2 está com o AAL.' in f2 and '<a ' not in f2


def test_c216_sem_titulo_de_gestao_vazio(sessao):
    c=TestClient(app)
    assert 'Áreas de Gestão' not in c.get('/central?conta_id=CONTA-G1').text
    assert 'Áreas de Gestão' in c.get('/central?conta_id=CONTA-A1').text


def test_c218_grupos_abaixo_da_origem_e_canais_nomeados(sessao):
    reg,c,url=abrir(sessao)
    for bloco,origem,canal in [(8,'8.3','WhatsApp'),(2,'2.1','Ouvidoria'),(10,'10.1',None)]:
        html=c.get(url+f'?conta_id=CONTA-G1&bloco={bloco}').text
        trecho=html[html.index('id="pergunta-'+origem+'"'):]
        fim=trecho.index('</fieldset>')
        aviso=trecho.index('data-condicao-grupo=')
        assert fim < aviso
        if canal:assert canal+' for marcado em F1-'+origem in trecho
