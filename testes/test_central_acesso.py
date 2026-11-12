"""Entrada demonstrativa e recorte de navegação por vínculo vigente."""
from datetime import datetime, timedelta, timezone
from html import unescape
import re

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select

from app.main import app
from app.modelos import Conta, Designacao, Unidade
from testes.apoio import CADASTRO, LANCAMENTO, g1


def test_entrada_sem_listagem_identifica_apa_e_reserva_planejados():
    cliente = TestClient(app)
    pagina = cliente.get("/")
    assert pagina.url.path == "/central"
    assert pagina.status_code == 200
    assert pagina.text.index("Secretaria de atuação") < pagina.text.index("Servidor em sessão") < pagina.text.index("APA em exercício")
    assert 'MAT-FICT-0001 — Servidor Alfa (titular)' in pagina.text
    assert 'name="secretaria_id" value="UNID-NORTE"' in pagina.text
    assert "Registros disponíveis" not in pagina.text and "Resumo do painel" not in pagina.text
    assert 'name="arp_id"' not in pagina.text and 'name="apa_id"' not in pagina.text
    assert '<label for="conta_id">Selecionar servidor por matrícula</label>' in pagina.text
    assert 'type="submit">Selecionar servidor e entrar</button>' in pagina.text
    assert 'A troca de servidor fictício é exclusiva da demonstração.' in pagina.text
    alterada = cliente.get("/central?conta_id=CONTA-G1&administracao_ti_autorizada=true&apa_id=PESSOA-G")
    assert 'Servidor Épsilon — MAT-FICT-0007</dd>' in alterada.text
    assert 'MAT-FICT-0001 — Servidor Alfa (titular)' in alterada.text
    assert 'Administração Central — TI' in alterada.text
    assert '<a ' not in alterada.text.split('id="titulo-gestao"', 1)[1]


def test_cartoes_explicam_disponibilidade_sem_oferecer_acesso_direto():
    pagina = TestClient(app).get("/central").text
    cartoes = re.findall(r'<li class="cartao-central [^"]+">(.*?)</li>', pagina, re.S)
    esperados = [
        ("FORM 1", "Levantamento do tratamento", "Como esse processo", "Disponível conforme autorização do Registro"),
        ("FORM 2", "Validação jurídica e institucional", "Por que e em que condições", "Análise jurídica completa ainda não implementada"),
        ("FORM 3", "Avaliação de riscos e controles", "Que riscos o tratamento", "Planejado"),
        ("FORM 4", "Plano de ação, monitoramento e aprendizagem institucional", "O que precisa ser feito", "Planejado"),
        ("Dashboard LGPD", "Indicadores consolidados", "Planejado"),
        ("Administração Central — TI", "18 Secretarias", "Planejada", "habilitação específica"),
    ]
    assert len(cartoes) == len(esperados)
    for numero, (cartao, textos) in enumerate(zip(cartoes, esperados), 1):
        assert all(texto in cartao for texto in textos)
        assert 'aria-hidden="true" focusable="false"' in cartao
        if numero != 2:
            assert '<a ' not in cartao
        if numero == 2:
            assert '>Acessar FORM 2</a>' in cartao
            assert '/form2/filas?conta_id=' in cartao
            assert 'form="abrir-painel"' not in cartao
        elif numero == 1:
            assert f'>Acessar FORM {numero}</button>' in cartao
            assert f'form="abrir-painel" name="instrumento" value="form{numero}"' in cartao
        elif numero in (3, 4):
            assert f'type="button" disabled>Acessar FORM {numero}</button>' in cartao
            assert 'form="abrir-painel"' not in cartao
        else:
            rotulo = 'Acessar Dashboard' if numero == 5 else 'Acessar Administração Central'
            assert f'type="button" disabled>{rotulo}</button>' in cartao
            assert 'form="abrir-painel"' not in cartao


@pytest.mark.parametrize("conta,rotulo", [
    ("CONTA-A1", "Acompanhar preparação"),
    ("CONTA-G1", "Iniciar preparação"),
])
def test_escolha_explicita_filtra_form2_e_retorna_ao_contexto(sessao, conta, rotulo):
    from testes.test_form2_preparacao import base, iniciar
    from testes.test_snapshot_form1_integral import _preparar
    from testes.test_navegacao_instrumentos import contagens, destino_form2

    rid, sid = base(sessao)
    iniciar(sessao, rid, sid)
    outro = _preparar(sessao, "FICT-CENTRAL-03")["registro_id"]
    cliente = TestClient(app)
    contexto = {"conta_id": conta, "secretaria_id": "UNID-NORTE"}
    antes = contagens(sessao)
    geral = cliente.get("/painel", params=contexto)
    form1 = cliente.get("/painel", params={**contexto, "instrumento": "form1"})
    form2 = cliente.get("/painel", params={**contexto, "instrumento": "form2"})
    assert "<h1>Painel de Registros</h1>" in geral.text
    assert "<h1>Meus levantamentos</h1>" in form1.text
    assert "<h1>Minhas preparações</h1>" in form2.text
    for pagina in (geral, form1):
        assert rid in pagina.text and outro in pagina.text
        for indicador in ("Registros disponíveis", "Providências de conferência", "Campos obrigatórios pendentes"):
            assert indicador in pagina.text and indicador not in form2.text
        assert "Dashboard LGPD" not in pagina.text
    assert "Dashboard LGPD" not in form2.text and "Situação do FORM 1" not in form2.text
    assert "<small>1 Registro disponível</small>" in form2.text
    assert ("designado como AAL" if conta == "CONTA-G1" else "acompanhar esta preparação como APA") in form2.text
    assert "APA responsável:" not in form2.text.split("<article", 1)[0]
    assert "APA responsável:" in form2.text.split("<article", 1)[1]
    assert "Última atividade:" in form1.text
    assert outro not in form2.text and rotulo in form2.text
    assert form2.url.path == "/painel" and contagens(sessao) == antes
    cartao = form1.text.split(f'id="cartao-registro-{rid}"', 1)[1].split("</article>", 1)[0]
    principais = re.findall(r'<a class="botao-link"[^>]*href="([^"]+)"', cartao)
    assert len(principais) == 1
    link1 = unescape(principais[0])
    assert 'Abrir FORM 1 para preenchimento' not in cartao
    assert ('>Continuar FORM 1</a>' in cartao) == (conta == "CONTA-A1")
    for lista in (form1, form2):
        assert "Escolha um Registro</h2>" not in lista.text
        assert lista.text.count(">Voltar ao Painel geral de Registros</a>") == 1
    if conta == "CONTA-A1":  # Nesta massa, Alfa é o ARP do FORM 1 e Épsilon é o AAL do FORM 2.
        retomadas = re.findall(r'href="([^"]+/registros/' + re.escape(rid) + r'\?[^"]+#titulo-bloco-\d+)"', form1.text)
        assert retomadas and all("instrumento=form1" in href and "secretaria_id=UNID-NORTE" in href for href in retomadas)
    for tela, destino, filtro in [(form1, link1, "form1"), (form2, destino_form2(form2.text), "form2")]:
        resumo = re.search(r'class="botao-link-secundario" href="([^"]+)">Voltar ao Painel geral de Registros', tela.text).group(1)
        assert cliente.get(unescape(resumo)).url == geral.url
        assert 'id="conta_id"' not in tela.text and "Selecionar servidor por matrícula" not in tela.text
        pagina = cliente.get(destino)
        assert pagina.status_code == 200
        identidade = "Servidor Alfa — MAT-FICT-0001" if conta == "CONTA-A1" else "Servidor Épsilon — MAT-FICT-0007"
        assert f"Servidor em sessão:</strong> {identidade}" in pagina.text
        if filtro == "form2":
            assert "APA responsável:" in pagina.text and "Função nesta atividade:" in pagina.text
            assert "versão histórica nº 1" in tela.text and "Designação em" in tela.text
        assert f"Voltar à lista de Registros do FORM {filtro[-1]}" in pagina.text
        volta = unescape(re.search(r'href="([^"]+/painel\?[^"]+)"', pagina.text).group(1))
        assert dict(cliente.get(volta).url.params) == {**contexto, "instrumento": filtro}
        if filtro == "form2":
            registro = unescape(re.search(r'href="([^"]+)">Voltar ao Registro', pagina.text).group(1))
            detalhes = cliente.get(registro)
            assert detalhes.url.path == f"/registros/{rid}" and detalhes.status_code == 200
            assert dict(detalhes.url.params) == {**contexto, "instrumento": filtro}
            assert volta.replace("&", "&amp;") in detalhes.text
            assert 'name="instrumento" value="form2"' in pagina.text
            if conta == "CONTA-G1":
                salvar = unescape(re.search(r'id="form2-rascunho" method="post" action="([^"]+)"', pagina.text).group(1))
                salvo = cliente.post(salvar, data={"conta_id": conta, "comando_id": "FICT-NAV-F2",
                    "versao_lida": "1", "anotacao_preparatoria": "Anotação fictícia de navegação."})
                assert salvo.status_code == 200 and "Anotação fictícia de navegação." in salvo.text
                assert salvo.url.params["instrumento"] == filtro
                assert salvo.url.params["secretaria_id"] == contexto["secretaria_id"]


def test_form2_sem_habilitacao_e_filtro_invalido():
    cliente = TestClient(app)
    registro = g1("FICT-CENTRAL-03-SEM", CADASTRO, "CTX-TRIB-01")
    contexto = {"conta_id": "CONTA-A1", "secretaria_id": "UNID-NORTE"}
    pagina = cliente.get("/painel", params={**contexto, "instrumento": "form2"})
    assert pagina.status_code == 200 and "Nenhum Registro acessível" in pagina.text
    assert "<small>0 Registros disponíveis</small>" in pagina.text
    assert "habilitação vigente e de designação pelo APA" in pagina.text
    assert registro["registro_id"] not in pagina.text and "data-acesso-form2" not in pagina.text
    assert cliente.get("/painel", params={**contexto, "instrumento": "form3"}).status_code == 422
    assert cliente.get("/painel", params={**contexto, "instrumento": "form1", "secretaria_id": "UNID-SUL"}).status_code == 403


def test_central_indica_quem_exerce_substituicao_vigente(sessao):
    from testes.test_continuidade_apa import _iniciar

    agora = datetime.now(timezone.utc)
    assert _iniciar(sessao, inicio_em=agora - timedelta(hours=1),
                    fim_previsto_em=agora + timedelta(days=1), momento=agora)["permitido"]
    sessao.commit()
    pagina = TestClient(app).get("/central?conta_id=CONTA-G1")
    assert "MAT-FICT-0006 — Servidor Delta (em substituição temporária)" in pagina.text


def test_selecao_recorta_cartoes_contadores_e_comando_de_abertura(sessao):
    cliente = TestClient(app)
    norte = g1("FICT-CENTRAL-N", CADASTRO, "CTX-TRIB-01")
    sul = g1("FICT-CENTRAL-S", LANCAMENTO, "CTX-TRIB-02", conta="CONTA-C1", unidade="UNID-SUL")
    sessao.add(Designacao(pessoa_id="PESSOA-A", unidade_id="UNID-SUL", papel="analista"))
    sessao.commit()
    entrada = cliente.get("/?conta_id=CONTA-A1")
    assert entrada.url.path == "/central"
    assert entrada.text.count('type="radio"') == 2
    assert 'for="secretaria-1"' in entrada.text and 'id="secretaria-1"' in entrada.text
    for unidade, presente, ausente, pode_abrir in [
        ("UNID-NORTE", norte, sul, True), ("UNID-SUL", sul, norte, False)
    ]:
        painel = cliente.get("/painel", params={"conta_id": "CONTA-A1", "secretaria_id": unidade})
        assert painel.status_code == 200
        assert presente["codigo_lgpd"] in painel.text and ausente["codigo_lgpd"] not in painel.text
        assert 'aria-label="1 Registro(s) disponível(is)"' in painel.text
        assert ("Criar novo Registro LGPD" in painel.text) is pode_abrir
        assert 'name="secretaria_id"' not in painel.text and "Selecionar servidor por matrícula" not in painel.text
        retorno = cliente.get("/?conta_id=CONTA-A1")
        assert retorno.url.path == "/painel" and presente["codigo_lgpd"] in retorno.text
        trocar = re.search(r'href="([^"]+)">Trocar Secretaria', painel.text).group(1).replace("&amp;", "&")
        assert cliente.get(trocar).url.path == "/central"


@pytest.mark.parametrize("caminho", ["/central", "/painel", "/"])
def test_contexto_explicito_fora_do_escopo_e_negado(caminho):
    resposta = TestClient(app).get(caminho, params={"conta_id": "CONTA-G1", "secretaria_id": "UNID-SUL"})
    assert resposta.status_code == 403 and "Secretaria indisponível" in resposta.text


@pytest.mark.parametrize("situacao", ["expirada", "futura", "revogada", "unidade_inativa"])
def test_preferencia_salva_nao_concede_acesso_apos_perda_do_vinculo(sessao, situacao):
    cliente = TestClient(app)
    vinculo = Designacao(pessoa_id="PESSOA-G", unidade_id="UNID-SUL", papel="analista")
    sessao.add(vinculo)
    sessao.commit()
    destino = "/painel?conta_id=CONTA-G1&secretaria_id=UNID-SUL"
    assert cliente.get(destino).status_code == 200
    agora = datetime.now(timezone.utc)
    if situacao == "expirada":
        vinculo.vigente_ate = agora - timedelta(days=1)
    elif situacao == "futura":
        vinculo.vigente_de = agora + timedelta(days=1)
    elif situacao == "revogada":
        vinculo.ativa = False
    else:
        sessao.get(Unidade, "UNID-SUL").ativa = False
    sessao.commit()
    assert cliente.get(destino).status_code == 403
    assert cliente.get("/?conta_id=CONTA-G1").context["secretaria"]["id"] == "UNID-NORTE"


def test_sem_vinculo_sem_entrada_e_conta_inativa_sem_consulta(sessao):
    cliente = TestClient(app)
    for vinculo in sessao.scalars(select(Designacao).where(Designacao.pessoa_id == "PESSOA-G")):
        vinculo.ativa = False
    sessao.commit()
    resposta = cliente.get("/painel?conta_id=CONTA-G1")
    assert resposta.url.path == "/central"
    assert "Nenhuma Secretaria com vínculo vigente" in resposta.text
    assert "Abrir Painel de Registros" not in resposta.text
    sessao.get(Conta, "CONTA-G1").ativa = False
    sessao.commit()
    assert cliente.get("/central?conta_id=CONTA-G1").status_code == 404
