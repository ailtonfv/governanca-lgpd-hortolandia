"""Consulta editorial isolada: documento sintético, sem publicar a Cartilha interna."""
from copy import deepcopy
import hashlib
from html import escape, unescape
from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient
import pytest

from app import cartilha_local
from app.ajudas_cartilha_form1 import AJUDAS_CARTILHA_FORM1, SECOES_CARTILHA
from app.main import app
from app.modelos import RascunhoForm1Integral
from testes.test_bloco5_form1_integral import _rascunho_pronto
from testes.test_p1_usabilidade_form1 import Elementos

cliente = TestClient(app, client=("127.0.0.1", 50123))


@pytest.fixture
def documento_local(tmp_path, monkeypatch):
    # Arrange: seções de teste, nunca copiar conteúdo do documento interno para a suíte.
    partes = []
    for chave, titulo in SECOES_CARTILHA.items():
        partes.append(f'<w:p><w:pPr><w:pStyle w:val="Ttulo2"/></w:pPr><w:r><w:t>{escape(titulo)}</w:t></w:r></w:p>')
        partes.append(f'<w:p><w:r><w:t>Orientação fictícia {chave} &lt;script&gt; não executar.</w:t></w:r></w:p>')
        partes.append('<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Quadro fictício</w:t></w:r></w:p></w:tc></w:tr></w:tbl>')
        partes.append('<w:p><w:pPr><w:pStyle w:val="Ttulo3"/></w:pPr><w:r><w:t>Subseção fictícia preservada</w:t></w:r></w:p>')
    partes.append('<w:p><w:pPr><w:pStyle w:val="Ttulo2"/></w:pPr><w:r><w:t>99.1 Fora do mapa</w:t></w:r></w:p><w:p><w:r><w:t>NAO_EXIBIR_FORA_DA_SECAO</w:t></w:r></w:p>')
    memoria = BytesIO()
    with ZipFile(memoria, 'w') as z:
        z.writestr('word/document.xml', '<w:document xmlns:w="'+cartilha_local.NS['w']+'"><w:body>'+''.join(partes)+'</w:body></w:document>')
        z.writestr('word/_rels/document.xml.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>')
    caminho = tmp_path / 'cartilha_ficticia.docx'
    caminho.write_bytes(memoria.getvalue())
    monkeypatch.setattr(cartilha_local, 'CAMINHO_CARTILHA', caminho)
    monkeypatch.setattr(cartilha_local, 'SHA256_CARTILHA', hashlib.sha256(memoria.getvalue()).hexdigest())
    cartilha_local._ler_edicao.cache_clear()
    yield caminho
    cartilha_local._ler_edicao.cache_clear()


def test_mapa_e_leitura_preservam_edicao_secoes_subsecoes_e_quadros(documento_local):
    # Act
    secoes = cartilha_local.secoes_cartilha_disponiveis()
    # Assert
    assert set(secoes) == set(SECOES_CARTILHA)
    assert len(AJUDAS_CARTILHA_FORM1) == 22
    for ajuda in AJUDAS_CARTILHA_FORM1.values():
        assert SECOES_CARTILHA[ajuda['secao_id']] == ajuda['secao']
        assert any(b['tipo'] == 'tabela' for b in secoes[ajuda['secao_id']])
        assert any(b.get('texto') == 'Subseção fictícia preservada' for b in secoes[ajuda['secao_id']])
    assert 'NAO_EXIBIR_FORA_DA_SECAO' not in str(secoes)
    assert 'Marque o primeiro canal' not in AJUDAS_CARTILHA_FORM1['2.1']['texto']
    assert 'sem confirmação histórica' in AJUDAS_CARTILHA_FORM1['2.1']['texto']


def test_todos_links_abrem_secao_correta_sem_alterar_rascunho(sessao, documento_local):
    # Arrange
    registro = _rascunho_pronto(sessao, 'CARTILHA-LINKS')
    rid = registro['registro_id']
    rascunho = sessao.get(RascunhoForm1Integral, rid)
    antes = deepcopy(rascunho.conteudo), rascunho.versao_rascunho
    # Act
    pagina = cliente.get(f'/registros/{rid}?conta_id=CONTA-A1')
    elementos = Elementos(pagina.text).elementos
    # Assert
    assert pagina.status_code == 200
    for campo_id, ajuda in AJUDAS_CARTILHA_FORM1.items():
        link = next(attrs for tag, attrs, pais in elementos if tag == 'a'
                    and any(a.get('id') == f'ajuda-cartilha-{campo_id}' for _, a in pais))
        assert link and link['target'] == '_blank' and 'noopener' in link['rel']
        assert 'abre em outra aba' in pagina.text
        destino = cliente.get(link['href'])
        assert destino.status_code == 200
        assert f'<h1 id="titulo-cartilha">{ajuda["secao"]}</h1>' in unescape(destino.text)
        assert f'Orientação fictícia {ajuda["secao_id"]}' in destino.text
        assert 'Volte àquela aba' in destino.text
        assert not any(t in {'script', 'form'} for t, _, _ in Elementos(destino.text).elementos)
        assert 'private, no-store' == destino.headers['cache-control']
    sessao.expire_all()
    depois = sessao.get(RascunhoForm1Integral, rid)
    assert (depois.conteudo, depois.versao_rascunho) == antes


def test_ausencia_edicao_divergente_e_secao_invalida_sem_link_falso(sessao, documento_local):
    # Arrange
    registro = _rascunho_pronto(sessao, 'CARTILHA-AUSENTE')
    url = f'/registros/{registro["registro_id"]}'
    # Act / Assert
    assert cliente.get(url+'/cartilha/REV30.11/conceitos?conta_id=CONTA-A1').status_code == 404
    assert cliente.get(url+'/cartilha/REV30.13/inexistente?conta_id=CONTA-A1').status_code == 404
    for dados in (b'arquivo divergente', None):
        if dados is None:
            documento_local.unlink()
        else:
            documento_local.write_bytes(dados)
        pagina = cliente.get(url+'?conta_id=CONTA-A1')
        assert 'Entenda esta pergunta' in pagina.text
        assert 'Consulta da Cartilha indisponível' in pagina.text
        assert 'Consultar este item da Cartilha' not in pagina.text
        assert cliente.get(url+'/cartilha/REV30.13/conceitos?conta_id=CONTA-A1').status_code == 404


def test_consulta_exige_acesso_ao_registro_e_conexao_local(sessao, documento_local):
    # Arrange
    registro = _rascunho_pronto(sessao, 'CARTILHA-ACESSO')
    url = f'/registros/{registro["registro_id"]}/cartilha/REV30.13/conceitos'
    # Act / Assert
    for conta in ('CONTA-INEXISTENTE', 'CONTA-C1'):
        resposta = cliente.get(url+f'?conta_id={conta}')
        assert resposta.status_code == 403
        assert 'Orientação fictícia' not in resposta.text
    externo = TestClient(app, client=('192.0.2.10', 50000))
    assert externo.get(url+'?conta_id=CONTA-A1', headers={'X-Forwarded-For':'127.0.0.1'}).status_code == 403
    assert cliente.post(url+'?conta_id=CONTA-A1').status_code == 405
    assert cliente.get('/estaticos/cartilha/'+documento_local.name).status_code == 404


def test_ajudas_respeitam_condicionais_e_semantica_acessivel(sessao, documento_local):
    # Arrange
    registro = _rascunho_pronto(sessao, 'CARTILHA-CONDICOES')
    # Act
    html = cliente.get(f'/registros/{registro["registro_id"]}?conta_id=CONTA-A1').text
    elementos = Elementos(html).elementos
    # Assert
    for campo_id in ('2.13.1', '8.7', '8.8', '8.9', '10.8', '10.8.1'):
        tag, _, pais = next(e for e in elementos if e[1].get('id') == f'ajuda-cartilha-{campo_id}')
        assert tag == 'details' and '<summary>Entenda esta pergunta</summary>' in html
        assert any('campo-condicional' in a.get('class', '') for _, a in pais)
    for campo_id in ('3.2', '3.3', '3.4', '3.4.1', '3.5'):
        _, _, pais = next(e for e in elementos if e[1].get('id') == f'ajuda-cartilha-{campo_id}')
        assert any(a.get('id') == 'participantes-integral' for _, a in pais)
