"""FORM02_12: navegação usa permissões existentes, sem produzir atos."""
from datetime import timedelta
from html import unescape
from pathlib import Path
import re

import pytest
from sqlalchemy import select, func

from app.form2_preparacao import projetar_navegacao_preparacao, agora
from app.modelos import HabilitacaoForm2Preparacao, EventoAuditoria, Evento, Comando, Conta, Pessoa, Registro
from testes.test_form2_preparacao import base, iniciar, cliente, habilitar, salvar


def artigo(html, numero):
    return re.search(rf'<li data-instrumento="FORM{numero}">(.*?)</li>', html, re.S).group(1)


def destino_form2(html):
    return unescape(re.search(r'data-acesso-form2 href="([^"]+)"', html).group(1))


def contagens(sessao):
    return tuple(sessao.scalar(select(func.count()).select_from(modelo))
                 for modelo in (Evento, EventoAuditoria, Comando))


def test_painel_registro_form2_retorno_apa_e_preparador(sessao):
    rid, sid = base(sessao)
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    for conta, texto, editavel in [("CONTA-A1", "Acompanhar preparação", False),
                                   ("CONTA-G1", "Iniciar preparação", True)]:
        central = cliente.get("/central", params={"conta_id": conta})
        destino_painel = re.search(r'<form action="([^"]+/painel)"', central.text).group(1)
        painel = cliente.get(destino_painel,
                            params={"conta_id": conta, "secretaria_id": "UNID-NORTE"})
        assert painel.status_code == 200 and "Voltar à Central de Acesso" in painel.text
        caminho = f"/registros/{rid}?conta_id={conta}#instrumentos-registro"
        assert caminho in painel.text
        antes = contagens(sessao)
        pagina = cliente.get(caminho)
        assert pagina.status_code == 200
        assert contagens(sessao) == antes  # exibir link não registra consulta ao FORM 2
        assert texto in artigo(pagina.text, 2)
        assert 'href="#titulo-form1-integral"' in artigo(pagina.text, 1)
        assert 'id="titulo-form1-integral" tabindex="-1"' in pagina.text
        destino = destino_form2(pagina.text)
        assert f"/registros/{rid}/form2/preparacao?conta_id={conta}" in destino
        assert f"preparacao_id={pid}" in destino and "#" not in destino
        form2 = cliente.get(destino)
        assert form2.status_code == 200
        assert ('id="anotacao"' in form2.text) is editavel
        assert caminho in form2.text and "Voltar ao Registro" in form2.text
        assert f'/painel?conta_id={conta}&amp;instrumento=form2' in form2.text
        for numero in (3,4):
            planejado = artigo(pagina.text, numero)
            assert "Planejado" in planejado and "<a " not in planejado and "<button" not in planejado


@pytest.mark.parametrize("situacao", ["ausente", "expirada", "futura", "inativa", "politica", "conta_inativa", "pessoa_inativa"])
def test_sem_autorizacao_efetiva_nao_oferece_form2(sessao, situacao):
    rid, sid = base(sessao)
    hab = sessao.scalar(select(HabilitacaoForm2Preparacao).where(
        HabilitacaoForm2Preparacao.registro_id==rid, HabilitacaoForm2Preparacao.pessoa_id=="PESSOA-A"))
    if situacao == "ausente": sessao.delete(hab)
    elif situacao == "expirada": hab.vigente_ate = agora()-timedelta(seconds=1)
    elif situacao == "futura": hab.vigente_de = agora()+timedelta(hours=1)
    elif situacao == "inativa": hab.ativa = False
    elif situacao == "politica": hab.versao_politica = "POLITICA-FICT-NAO-VIGENTE"
    elif situacao == "conta_inativa": sessao.get(Conta,"CONTA-A1").ativa = False
    else: sessao.get(Pessoa,"PESSOA-A").ativa = False
    sessao.commit()
    antes = contagens(sessao)
    assert projetar_navegacao_preparacao(sessao, conta_id="CONTA-A1", registro_id=rid) is None
    assert contagens(sessao) == antes
    pagina = cliente.get(f"/registros/{rid}", params={"conta_id":"CONTA-A1"})
    assert "data-acesso-form2" not in pagina.text
    assert cliente.get(f"/registros/{rid}/form2/preparacao", params={"conta_id":"CONTA-A1"}).status_code == 403


def test_preparador_sem_designacao_nao_recebe_link_listagem_ou_origem(sessao):
    rid, sid = base(sessao)
    url = f"/registros/{rid}/form2/preparacao"
    preparador = {"conta_id": "CONTA-G1"}
    pagina = cliente.get(f"/registros/{rid}", params=preparador)
    assert 'data-acesso-form2' not in artigo(pagina.text, 2)
    assert "designação pelo APA" in artigo(pagina.text, 2)
    painel = cliente.get("/painel", params={**preparador, "secretaria_id": "UNID-NORTE", "instrumento": "form2"})
    assert painel.status_code == 200 and rid not in painel.text
    antes = contagens(sessao)
    for parametros in (preparador, {**preparador, "snapshot_id": sid}):
        resposta = cliente.get(url, params=parametros)
        assert resposta.status_code == 403
        assert sid not in resposta.text and 'id="snapshot-origem"' not in resposta.text
    eventos, auditorias, comandos = antes
    assert contagens(sessao) == (eventos, auditorias + 2, comandos)
    autorizado = cliente.get(url, params={"conta_id": "CONTA-A1", "snapshot_id": sid})
    assert autorizado.status_code == 200 and "Designar AAL e iniciar preparação" in autorizado.text


def test_inicio_e_retomada_seguem_o_historico_do_aal(sessao):
    from app.apresentacao_form2 import data_local
    from app.modelos import VersaoForm1Integral
    rid, sid = base(sessao)
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    origem_em = sessao.get(VersaoForm1Integral, sid).preparado_em
    params = {"conta_id": "CONTA-G1", "secretaria_id": "UNID-NORTE", "instrumento": "form2"}
    for versao, texto, iniciada in [(1, " ", False), (2, "Observação fictícia.", True), (3, "", True)]:
        momento = agora() + timedelta(minutes=versao * 10)
        assert salvar(sessao, rid, pid, versao_lida=versao, comando_id=f"FICT-UX07-{versao}",
                      momento=momento, conteudo={"anotacao_preparatoria": texto})["permitido"]
        lista = cliente.get("/painel", params=params)
        assert "#" not in destino_form2(lista.text)
        assert ("Retomar preparação" in lista.text) is iniciada
        assert ("Designada ao AAL — ainda não iniciada" in lista.text) is not iniciada
        for resposta in (lista, cliente.get(destino_form2(lista.text))):
            assert resposta.status_code == 200
            assert f"versão histórica nº 1, registrada em {data_local(origem_em)}" in resposta.text
            assert f"Último salvamento em {data_local(momento)}" in resposta.text
            assert "Servidor Épsilon (fictício) (AAL)" in resposta.text


def test_paginas_form2_com_contexto_anterior(sessao, monkeypatch):
    import app.main as principal
    import app.rotas_form2_preparacao as rotas

    rid, sid = base(sessao)
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    consulta_atual = rotas.consultar_preparacao
    projecao_atual = principal.projetar_navegacao_preparacao

    def consulta_anterior(*args, **kwargs):
        dados = consulta_atual(*args, **kwargs)
        dados.pop("trabalho_aal", None)
        return dados

    def projecao_anterior(*args, **kwargs):
        dados = projecao_atual(*args, **kwargs)
        if dados:
            dados.pop("resumo")
        return dados

    monkeypatch.setattr(rotas, "consultar_preparacao", consulta_anterior)
    monkeypatch.setattr(principal, "projetar_navegacao_preparacao", projecao_anterior)
    rota = f"/registros/{rid}/form2/preparacao"
    for salva in (False, True):
        if salva:
            assert salvar(sessao, rid, pid)["permitido"]
        for conta in ("CONTA-A1", "CONTA-G1"):
            params = {"conta_id": conta, "secretaria_id": "UNID-NORTE", "instrumento": "form2"}
            lista = cliente.get("/painel", params=params)
            assert lista.status_code == 200 and "Situação da preparação indisponível" in lista.text
            assert "Ainda sem designação" not in lista.text
            destino = destino_form2(lista.text)
            assert "#" not in destino
            pagina = cliente.get(destino)
            assert pagina.status_code == 200
            assert ("Em preparação pelo AAL" if salva else "Designada ao AAL — ainda não iniciada") in pagina.text
            assert ('id="anotacao"' in pagina.text) == (conta == "CONTA-G1")
            contexto = dict(pagina.context)
            contexto.pop("trabalho_aal")
            html = pagina.template.render(contexto)
            assert "Situação da preparação indisponível" in html
            assert "Designada ao AAL — ainda não iniciada" not in html and "Em preparação pelo AAL" not in html
    assert cliente.get(rota, params={"conta_id": "CONTA-B1", "preparacao_id": pid}).status_code == 403


def test_acao_de_inicio_depende_do_estado_real(sessao):
    rid, sid = base(sessao)
    params = {"conta_id": "CONTA-A1", "secretaria_id": "UNID-NORTE", "instrumento": "form2"}
    assert "Selecionar versão do FORM 1" in cliente.get("/painel", params=params).text
    sessao.get(Registro, rid).estado_atual = "suspenso"
    sessao.commit()
    lista = cliente.get("/painel", params=params)
    assert "Consultar disponibilidade" in lista.text and "Selecionar versão do FORM 1" not in lista.text
    origem = cliente.get(f"/registros/{rid}/form2/preparacao", params={**params, "snapshot_id": sid})
    assert origem.status_code == 200 and 'id="preparador"' not in origem.text


def test_apa_tambem_preparador_e_estado_sem_edicao(sessao):
    rid, sid = base(sessao)
    habilitar(sessao,rid,"PESSOA-A","preparar")
    pid = iniciar(sessao,rid,sid,preparador_id="PESSOA-A")["preparacao_id"]
    proj = projetar_navegacao_preparacao(sessao,conta_id="CONTA-A1",registro_id=rid)
    assert proj["preparacao_id"] == pid and proj["pode_editar"] and proj["e_apa"]
    assert proj["resumo"]["origem"] == proj["resumo"]["rascunho"] == 1
    assert "MAT-FICT-0001" in proj["resumo"]["autor"]
    sessao.get(Registro,rid).estado_atual = "suspenso"
    sessao.commit()
    proj = projetar_navegacao_preparacao(sessao,conta_id="CONTA-A1",registro_id=rid)
    assert not proj["pode_editar"]
    pagina = cliente.get(f"/registros/{rid}",params={"conta_id":"CONTA-A1"})
    assert "Retomar preparação" not in artigo(pagina.text,2)
    assert 'id="anotacao"' not in cliente.get(destino_form2(pagina.text)).text


def test_infraestrutura_ausente_nao_quebra_detalhes(sessao,monkeypatch):
    import app.form2_preparacao as modulo
    rid, sid = base(sessao)
    class SemTabelas:
        def has_table(self,nome): return False
    monkeypatch.setattr(modulo,"inspect",lambda conexao:SemTabelas())
    pagina = cliente.get(f"/registros/{rid}",params={"conta_id":"CONTA-A1"})
    assert pagina.status_code == 200 and "data-acesso-form2" not in pagina.text


def test_retorno_nao_amplia_visibilidade_do_registro(sessao,monkeypatch):
    import app.consultas_interface as consultas
    rid,sid = base(sessao)
    pid = iniciar(sessao,rid,sid)["preparacao_id"]
    monkeypatch.setattr(consultas,"_ids_visiveis",lambda sessao, identidade:set())
    pagina = cliente.get(f"/registros/{rid}/form2/preparacao",params={"conta_id":"CONTA-G1","preparacao_id":pid})
    assert pagina.status_code == 200 and "Voltar ao Registro" not in pagina.text
    assert "Voltar à lista de Registros do FORM 2" in pagina.text


def test_links_nativos_foco_e_layout_sem_dependencia_nova():
    template = Path("app/paginas/_instrumentos_registro.html").read_text(encoding="utf8")
    assert 'id="instrumentos-registro" tabindex="-1"' in template
    assert 'onclick=' not in template and 'tabindex="0"' not in template
    assert 'href=' in template  # links nativos ativáveis por Enter
    css = Path("app/estaticos/instrumentos_registro.css").read_text(encoding="utf8")
    assert ":focus-visible" in css and "minmax(0, 1fr)" in css
    assert "max-width: 650px" in css and "scroll-margin-top" in css
    assert "flex-wrap: wrap" in css


def test_dashboard_e_reserva_estatica_sem_rotas_ou_acoes(sessao):
    from app.main import app
    rid,sid = base(sessao)
    painel = cliente.get("/painel?conta_id=CONTA-A1")
    assert painel.status_code == 200 and "Dashboard LGPD" not in painel.text
    urls = [f"/registros/{rid}?conta_id=CONTA-A1",
            f"/registros/{rid}/form2/preparacao?conta_id=CONTA-A1"]
    for url in urls:
        pagina = cliente.get(url)
        assert pagina.status_code == 200 and "Dashboard LGPD" not in pagina.text
    assert "Dashboard LGPD" in cliente.get("/central").text
    assert not any("dashboard" in caminho.lower() for caminho in app.openapi()["paths"])


def test_habilitacao_de_um_registro_nao_oferece_link_em_outro(sessao):
    from testes.test_snapshot_form1_integral import _preparar
    base(sessao)
    outro = _preparar(sessao,"F2-NAV-OUTRO")["registro_id"]
    pagina = cliente.get(f"/registros/{outro}",params={"conta_id":"CONTA-A1"})
    assert pagina.status_code == 200 and "data-acesso-form2" not in pagina.text


def test_destino_dos_instrumentos_preserva_ancora_e_foco():
    import shutil
    import subprocess
    node = shutil.which("node")
    assert node, "Node necessário para o teste local de navegação"
    resultado = subprocess.run([node,"testes/apoio_navegacao_instrumentos.cjs"],capture_output=True,text=True)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
