"""FORM02_11: consulta legível sem mutações ou novas permissões."""
from copy import deepcopy
from html import unescape
from pathlib import Path
import re

import pytest

from app.apresentacao_form2 import apresentar_origem
from app.modelos import Pessoa, VersaoForm1Integral
from app.origem_form2 import ler_origem
from app.rotas_form2_preparacao import paginas
from testes.test_form2_preparacao import base, iniciar, salvar, cliente


@pytest.mark.parametrize("perfil,total", [("original",128),("medidas",129),("guarda",139),("ambas",140)])
def test_consulta_http_quatro_estruturas_sem_reinterpretar_origem(sessao, perfil, total):
    rid, sid = base(sessao, perfil=perfil)
    origem = ler_origem(sessao, rid, sid)
    antes = deepcopy(origem["snapshot"].conteudo), origem["snapshot"].lacre

    resposta = cliente.get(f"/registros/{rid}/form2/preparacao", params={"conta_id":"CONTA-A1", "snapshot_id":sid})

    assert resposta.status_code == 200
    html = resposta.text
    assert html.count('data-pergunta-historica=') == total
    for pergunta in origem["perguntas"]:
        assert unescape(f'{pergunta["id"]} — {pergunta["pergunta"]}') in unescape(html)
    for canal in origem["canais"]["canais"]:
        assert canal["canal_nome"] in unescape(html)
    for chave in ("extensao_medidas", "extensao_guarda"):
        if chave in origem["conteudo"]:
            legado = origem["conteudo"][chave]["legado"]
            campos = legado.get("campos", [legado])
            for campo in campos:
                assert campo["pergunta"] in unescape(html)
            assert "não convertidas para os novos campos" in html
    assert 'class="botao-primario">Designar AAL e iniciar preparação' in html
    assert 'class="botao-secundario">Consultar origem' in html
    assert '<details class="form2-tecnico"><summary>Conteúdo técnico completo' in html
    assert '"submissao_habilitada": false' in html
    sessao.expire_all()
    snap = sessao.get(VersaoForm1Integral, sid)
    assert (snap.conteudo, snap.lacre) == antes


def test_autoria_legivel_designacao_salvamento_e_apa_somente_consulta(sessao):
    rid, sid = base(sessao)
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    assert salvar(sessao, rid, pid)["permitido"]
    url = f"/registros/{rid}/form2/preparacao"
    for conta, editavel in [("CONTA-A1", False), ("CONTA-G1", True)]:
        resposta = cliente.get(url, params={"conta_id":conta,"preparacao_id":pid})
        assert resposta.status_code == 200
        html = resposta.text
        for pessoa_id in ("PESSOA-A", "PESSOA-G"):
            p = sessao.get(Pessoa, pessoa_id)
            assert f"{p.matricula} — {p.nome}" in html
        assert ('id="anotacao"' in html) is editavel
        assert ('class="botao-primario">Salvar rascunho' in html) is editavel
        assert "APA — Agente Público Autorizado (designação)" in html
        assert "AAL responsável:" in html
        assert html.index('id="proxima-acao"') < html.index('id="anotacoes"') < html.index('id="titulo-origem"')
        if editavel:
            assert 'for="anotacao"' in html and 'aria-describedby="ajuda-salvar"' in html
    assert cliente.get(url, params={"conta_id":"CONTA-B1","preparacao_id":pid}).status_code == 403


def test_proxima_acao_corresponde_a_origem_e_ao_papel(sessao):
    from app.modelos import Registro
    from app.rascunho_form1_integral import salvar_bloco_2_form1_integral
    from testes.test_snapshot_form1_integral import _snapshot

    rid, s1 = base(sessao)
    url = f"/registros/{rid}/form2/preparacao"
    contexto = {"secretaria_id": "UNID-NORTE", "instrumento": "form2"}
    def abrir(conta, **parametros):
        pagina = cliente.get(url, params={**contexto, "conta_id": conta, **parametros})
        assert pagina.status_code == 200
        return pagina.text

    inicial = abrir("CONTA-A1")
    assert 'class="botao-primario">Selecionar versão do FORM 1' in inicial
    p1 = iniciar(sessao, rid, s1)["preparacao_id"]
    assert salvar_bloco_2_form1_integral(sessao, comando_id="FICT-UX09-F1", conta_id="CONTA-A1",
        registro_id=rid, versao_lida=1, respostas={"2.3": "Unidade fictícia S2"})["permitido"]
    sessao.commit()
    s2 = _snapshot(sessao, {"registro_id": rid}, "FICT-UX09-S2", versao=2)["snapshot_id"]

    for conta, rotulo in (("CONTA-A1", "Acompanhar preparação"), ("CONTA-G1", "Retomar preparação")):
        tela = abrir(conta, snapshot_id=s1)
        assert 'id="preparador"' not in tela
        destino = unescape(re.search(rf'class="botao-link" href="([^"]+)">{rotulo}</a>', tela).group(1))
        pagina = cliente.get(destino)
        assert pagina.status_code == 200 and pagina.url.params["preparacao_id"] == p1
        assert pagina.url.params["secretaria_id"] == contexto["secretaria_id"]
        assert ('id="anotacao"' in pagina.text) is (conta == "CONTA-G1")
    assert cliente.get(url, params={"conta_id": "CONTA-G1", "snapshot_id": s2}).status_code == 403
    livre = abrir("CONTA-A1", snapshot_id=s2)
    assert livre.index("Designar AAL e iniciar preparação") < livre.index('id="titulo-origem"')
    assert iniciar(sessao, rid, s2, comando_id="FICT-UX09-D2")["permitido"]
    assert 'id="preparador"' not in abrir("CONTA-A1", snapshot_id=s2)
    assert s1 in abrir("CONTA-G1", snapshot_id=s2)

    sessao.get(Registro, rid).estado_atual = "suspenso"
    sessao.commit()
    consulta = abrir("CONTA-G1", preparacao_id=p1)
    assert '>Consultar preparação</a>' in consulta
    assert "Retomar preparação" not in consulta and 'id="anotacao"' not in consulta


def test_ocorrencias_complementos_inativos_e_vazios_sao_legiveis_sem_mutacao():
    fonte = {
        "participantes":[{"id":"PART-FICT-1", "respostas":{"3.2":"Secretaria fictícia", "3.5":["Outro"]},
                          "complementos":{"3.5":"Apoio fictício"}}],
        "participantes_inativos":[{"id":"PART-FICT-ANTERIOR", "respostas":{"3.2":"Unidade anterior"}}],
        "destinatarios_10_2_1":[{"id":"DEST-FICT-1", "categoria":"Outra Secretaria", "modalidade":"identificado", "unidade_id":"UNID-FICT-1", "instrumento":"Ato fictício"}],
        "destinatarios_10_2_1_inativos":[{"id":"DEST-FICT-ANTERIOR","motivo_desativacao":"Categoria retirada"}],
        "complementos":{"5.1":"<script>fictício</script>"},
        "complementos_inativos":{"5.1":[{"valor":"Texto anterior", "motivo":"substituído"}]},
        "respostas_inativas":{"2.12.1":["Resposta anterior"]},
    }
    original = deepcopy(fonte)
    consulta = apresentar_origem({"conteudo":fonte,"perguntas":[{"id":"3.2","pergunta":"Unidade participante?"}]})
    macro = paginas.env.get_template("_consulta_historica_form2.html").module.valor
    html = "".join(str(macro(g["valor"], consulta["rotulos"], {})) for g in consulta["grupos"])
    for texto in ("PART-FICT-1", "PART-FICT-ANTERIOR", "DEST-FICT-1", "DEST-FICT-ANTERIOR", "Apoio fictício", "Ato fictício", "Texto anterior", "Resposta anterior", "3.2 — Unidade participante?"):
        assert texto in unescape(html)
    assert "Destinatário identificado" in html and "Código da unidade preservado" in html
    assert "&lt;script&gt;" in html and "<script>" not in html
    for vazio in (None, ""):
        assert "Não informado nesta versão" in str(macro(vazio, {}, {}))
    assert "não equivale a resposta negativa" in str(macro([], {}, {}))
    assert ">0</span>" in str(macro(0, {}, {}))
    assert ">False</span>" in str(macro(False, {}, {}))
    assert fonte == original


@pytest.mark.parametrize("estado,texto", [
    ("sem_confirmacao_historica", "Não significa ausência de canais"),
    ("ausencia_confirmada", "Ausência de canais expressamente confirmada"),
])
def test_canais_ausencia_explicita_distinta_de_sem_confirmacao(sessao, estado, texto):
    # Projeção sintética somente em memória; não modifica o snapshot persistido.
    from app.form2_preparacao import consultar_preparacao
    from app.apresentacao_form2 import identificar_agentes, PAPEIS
    rid, sid = base(sessao)
    dados = consultar_preparacao(sessao, conta_id="CONTA-A1", registro_id=rid, snapshot_id=sid)
    dados["origem"]["canais"] = {"estado":estado,"canais":[]}
    from starlette.requests import Request
    from app.main import app
    request = Request({"type":"http","method":"GET","path":"/","root_path":"","query_string":b"",
                       "scheme":"http","server":("testserver",80),"headers":[],"router":app.router})
    html = paginas.env.get_template("form2_preparacao.html").render(
        **dados, request=request, conta_id="CONTA-A1", contexto_navegacao={}, secretaria={"nome":"Secretaria fictícia"}, alvo=None, agentes=identificar_agentes(sessao,dados),
        consulta_historica=apresentar_origem(dados["origem"]), papeis=PAPEIS)
    assert texto in html


def test_contraste_foco_e_responsividade_sem_biblioteca_nova():
    css = Path("app/estaticos/form2_preparacao.css").read_text(encoding="utf8")
    assert ":focus-visible" in css and "prefers-reduced-motion" in css
    assert "max-width: 600px" in css and "min-width: 0" in css
    assert "min-height: 44px" in css and "overflow-wrap: anywhere" in css
    def luminancia(cor):
        partes = [int(cor[i:i+2],16)/255 for i in (0,2,4)]
        return sum(peso*(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4)
                   for peso,v in zip((.2126,.7152,.0722),partes))
    assert (luminancia("ffffff")+.05)/(luminancia("075985")+.05) >= 4.5
    assert (luminancia("edf1f4")+.05)/(luminancia("475569")+.05) >= 4.5
