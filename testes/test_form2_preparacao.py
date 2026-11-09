"""FORM02_05 — aceite demonstrativo com dados fictícios, padrão AAA."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import timedelta
import threading
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func, inspect
from sqlalchemy.orm import Session

from app.banco import motor
from app.main import app
from app.modelos import (PreparacaoForm2, HabilitacaoForm2Preparacao, VersaoForm1Integral,
                        Registro, RascunhoForm1Integral, Instrumento, Evento, EventoAuditoria, Conta, Pessoa, Comando)
from app.form2_preparacao import (agora, registrar_habilitacao_controlada, iniciar_preparacao,
                                salvar_preparacao, consultar_preparacao)
from app.origem_form2 import ler_origem
from app.extensao_medidas_form1 import adotar_extensao_medidas
from app.extensao_guarda_form1 import adotar_extensao_guarda
from app.rascunho_form1_integral import salvar_bloco_2_form1_integral
from app.eventos import verificar_cadeia
from testes.test_snapshot_form1_integral import _preparar, _snapshot
from migracoes.preparacao_form2 import aplicar, reverter

cliente = TestClient(app)


def habilitar(s, rid, pessoa="PESSOA-G", finalidade="preparar", **extra):
    args = dict(comando_id=str(uuid.uuid4()), registro_id=rid, pessoa_id=pessoa,
        finalidade=finalidade, vigente_de=agora()-timedelta(days=1),
        vigente_ate=agora()+timedelta(days=1), aprovacao_referencia="ACEITE-FICT-FORM02-05",
        fundamento="Ensaio isolado com identidades fictícias")
    args.update(extra)
    out = registrar_habilitacao_controlada(s, **args)
    s.commit()
    return out


def base(s, *, habilitado=True, perfil="original"):
    r = _preparar(s, "F2-DEMO", canais=["CNL-001", "CNL-002"])
    rid = r["registro_id"]
    for adotar in ([adotar_extensao_medidas] if perfil == "medidas" else
                   [adotar_extensao_guarda] if perfil == "guarda" else
                   [adotar_extensao_medidas, adotar_extensao_guarda] if perfil == "ambas" else []):
        atual = s.get(RascunhoForm1Integral, rid)
        resultado = adotar(s, comando_id=str(uuid.uuid4()), conta_id="CONTA-A1",
                           registro_id=rid, versao_lida=atual.versao_rascunho, confirmar=True)
        assert resultado["permitido"]
        s.commit()
        s.expire_all()
    snap = _snapshot(s, r, "F2-ORIGEM", versao=s.get(RascunhoForm1Integral, rid).versao_rascunho)
    assert snap["permitido"]
    if habilitado:
        habilitar(s, rid)
        habilitar(s, rid, "PESSOA-A", "acompanhar")
    return rid, snap["snapshot_id"]


def iniciar(s, rid, sid, **extra):
    args = dict(comando_id="F2-INICIAR", conta_id="CONTA-A1", registro_id=rid,
                snapshot_id=sid, preparador_id="PESSOA-G")
    args.update(extra)
    out = iniciar_preparacao(s, **args)
    s.commit()
    return out


def salvar(s, rid, pid, **extra):
    args = dict(comando_id="F2-SALVAR", conta_id="CONTA-G1", registro_id=rid,
                preparacao_id=pid, versao_lida=1,
                conteudo={"anotacao_preparatoria": "Rever a evidência institucional fictícia."})
    args.update(extra)
    out = salvar_preparacao(s, **args)
    s.commit()
    return out


@pytest.mark.parametrize("perfil,total", [("original",128),("medidas",129),("guarda",139),("ambas",140)])
def test_t01_origem_historica_quatro_perfis(sessao, perfil, total):
    # Arrange / Act
    rid, sid = base(sessao, perfil=perfil)
    leitura = consultar_preparacao(sessao, conta_id="CONTA-A1", registro_id=rid, snapshot_id=sid)
    sessao.commit()
    # Assert
    assert leitura["permitido"]
    origem = leitura["origem"]
    assert len(origem["perguntas"]) == total
    assert len(origem["canais"]["canais"]) == 2
    assert origem["conteudo"] == sessao.get(VersaoForm1Integral, sid).conteudo["form1_integral"]
    p13 = next(p for p in origem["perguntas"] if p["id"] == "13.2")
    assert ("estações" not in p13["pergunta"]) if perfil in {"medidas", "ambas"} else True
    assert sessao.scalar(select(func.count()).select_from(PreparacaoForm2)) == 0


@pytest.mark.parametrize("falha", ["inexistente", "outro_registro", "lacre", "evento", "perfil"])
def test_t02_recusa_origem_invalida_sem_reparo(sessao, falha):
    rid, sid = base(sessao)
    snap = sessao.get(VersaoForm1Integral, sid)
    if falha == "inexistente": sid = str(uuid.uuid4())
    if falha == "outro_registro": rid = str(uuid.uuid4())
    if falha == "lacre": snap.lacre = "0" * 64
    if falha == "evento":
        sessao.get(Evento, snap.evento_preparacao_id).hash = "f" * 64
    if falha == "perfil":
        from app.origem_form2 import canonico
        from app.eventos import lacre
        pacote = deepcopy(snap.conteudo)
        pacote["form1_integral"]["extensao_medidas"] = {"versao": "inexistente"}
        snap.conteudo, snap.conteudo_canonico = pacote, canonico(pacote)
        snap.lacre = lacre(snap.conteudo_canonico)
    with pytest.raises(ValueError):
        ler_origem(sessao, rid, sid)
    sessao.rollback()
    assert sessao.scalar(select(func.count()).select_from(PreparacaoForm2)) == 0


def test_t03_snapshot_incompleto_e_sem_conferencia_nao_vira_aprovacao(sessao):
    rid, sid = base(sessao)
    out = iniciar(sessao, rid, sid)
    assert out["permitido"]
    assert sessao.get(VersaoForm1Integral, sid).conteudo["submissao_habilitada"] is False
    assert set(sessao.get(PreparacaoForm2, out["preparacao_id"]).conteudo) == {"anotacao_preparatoria"}


def test_t04_habilitacao_indicacao_e_papel_nao_concedem_edicao(sessao):
    rid, sid = base(sessao, habilitado=False)
    assert not iniciar(sessao, rid, sid)["permitido"]  # APA sem autorização específica
    habilitar(sessao, rid, "PESSOA-A", "acompanhar")
    assert not iniciar(sessao, rid, sid)["permitido"]  # indicação sem habilitação
    habilitar(sessao, rid)
    assert not iniciar(sessao, rid, sid, conta_id="CONTA-G1")["permitido"]  # não é APA
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    assert not salvar(sessao, rid, pid, conta_id="CONTA-A1")["permitido"]
    habilitar(sessao, rid, "PESSOA-B")
    assert not salvar(sessao, rid, pid, conta_id="CONTA-B1")["permitido"]
    assert salvar(sessao, rid, pid)["permitido"]


@pytest.mark.parametrize("falha", ["conta", "pessoa", "revogada", "expirada", "outro_registro"])
def test_t05_acesso_negado_no_servidor(sessao, falha):
    rid, sid = base(sessao)
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    if falha == "conta": sessao.get(Conta, "CONTA-G1").ativa = False
    if falha == "pessoa": sessao.get(Pessoa, "PESSOA-G").ativa = False
    if falha == "revogada": habilitar(sessao, rid, ativa=False)
    if falha == "expirada": habilitar(sessao, rid, vigente_de=agora()-timedelta(days=3), vigente_ate=agora()-timedelta(days=1))
    sessao.commit()
    alvo = str(uuid.uuid4()) if falha == "outro_registro" else rid
    assert not salvar(sessao, alvo, pid)["permitido"]
    assert not consultar_preparacao(sessao, conta_id="CONTA-G1", registro_id=alvo, preparacao_id=pid)["permitido"]
    assert not consultar_preparacao(sessao, conta_id="CONTA-G1", registro_id=alvo, snapshot_id=sid)["permitido"]
    sessao.commit()
    assert sessao.get(PreparacaoForm2, pid).versao_rascunho == 1


@pytest.mark.parametrize("valor", ["", "Parcial fictício", "a"*2000])
def test_t06_salvar_e_retomar_rascunho_parcial(sessao, valor):
    rid, sid = base(sessao)
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    assert salvar(sessao, rid, pid, conteudo={"anotacao_preparatoria": valor})["permitido"]
    sessao.expire_all()
    consulta = consultar_preparacao(sessao, conta_id="CONTA-G1", registro_id=rid, preparacao_id=pid)
    assert consulta["preparacao"].conteudo["anotacao_preparatoria"] == valor
    assert consulta["preparacao"].snapshot_id == sid
    assert consulta["preparacao"].salvo_por == "PESSOA-G"
    sessao.commit()


@pytest.mark.parametrize("conteudo", [{}, {"anotacao_preparatoria": "a"*2001},
    {"anotacao_preparatoria": 1}, {"anotacao_preparatoria": "\x00"},
    {"anotacao_preparatoria": "", "snapshot_id": "forjado"}])
def test_t06_entradas_invalidas_nao_alteram_dados(sessao, conteudo):
    rid, sid = base(sessao)
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    assert not salvar(sessao, rid, pid, conteudo=conteudo)["permitido"]
    assert sessao.get(PreparacaoForm2, pid).versao_rascunho == 1


def test_t07_idempotencia_estrita_e_revogacao_antes_repeticao(sessao):
    rid, sid = base(sessao)
    p = iniciar(sessao, rid, sid)
    assert iniciar(sessao, rid, sid)["reexecutado"]
    assert not iniciar(sessao, rid, sid, preparador_id="PESSOA-A")["permitido"]
    assert salvar(sessao, rid, p["preparacao_id"])["permitido"]
    assert salvar(sessao, rid, p["preparacao_id"])["reexecutado"]
    assert not salvar(sessao, rid, p["preparacao_id"], conteudo={"anotacao_preparatoria": "Diferente"})["permitido"]
    habilitar(sessao, rid, ativa=False)
    assert not salvar(sessao, rid, p["preparacao_id"])["permitido"]
    assert sessao.get(PreparacaoForm2, p["preparacao_id"]).versao_rascunho == 2


@pytest.mark.parametrize("operacao", ["iniciar", "salvar"])
def test_t07_t08_concorrencia_sem_duplicacao_ou_sobrescrita(sessao, operacao):
    rid, sid = base(sessao)
    pid = iniciar(sessao, rid, sid)["preparacao_id"] if operacao == "salvar" else None
    barreira = threading.Barrier(2)
    def executar(i):
        with Session(motor) as s, s.begin():
            barreira.wait(timeout=10)
            if operacao == "iniciar":
                return iniciar_preparacao(s, comando_id=f"PAR-{i}", conta_id="CONTA-A1",
                    registro_id=rid, snapshot_id=sid, preparador_id="PESSOA-G")
            return salvar_preparacao(s, comando_id=f"PAR-{i}", conta_id="CONTA-G1",
                registro_id=rid, preparacao_id=pid, versao_lida=1,
                conteudo={"anotacao_preparatoria": f"Fictício {i}"})
    with ThreadPoolExecutor(max_workers=2) as pool:
        resultados = list(pool.map(executar, range(2)))
    sessao.expire_all()
    assert sessao.scalar(select(func.count()).select_from(PreparacaoForm2)) == 1
    if operacao == "salvar":
        assert sum(r["permitido"] for r in resultados) == 1
        assert sessao.get(PreparacaoForm2, pid).versao_rascunho == 2
    else:
        assert len({r["preparacao_id"] for r in resultados}) == 1


def test_t09_falha_reverte_toda_a_transacao(sessao, monkeypatch):
    from app import form2_preparacao as dominio
    rid, sid = base(sessao)
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    def falhar(*a, **k): raise RuntimeError("falha induzida fictícia")
    monkeypatch.setattr(dominio, "_auditar", falhar)
    with pytest.raises(RuntimeError), sessao.begin():
        salvar_preparacao(sessao, comando_id="ROLLBACK-F2", conta_id="CONTA-G1", registro_id=rid,
            preparacao_id=pid, versao_lida=1, conteudo={"anotacao_preparatoria": "Não persistir"})
    assert sessao.get(PreparacaoForm2, pid).versao_rascunho == 1
    assert sessao.get(Comando, "ROLLBACK-F2") is None
    assert sessao.scalar(select(func.count()).select_from(Evento).where(Evento.comando_id == "ROLLBACK-F2")) == 0


def test_t10_t11_t12_duas_origens_e_historico_preservado(sessao):
    rid, sid = base(sessao)
    p1 = iniciar(sessao, rid, sid)["preparacao_id"]
    salvar(sessao, rid, p1)
    s1 = sessao.get(VersaoForm1Integral, sid)
    original = (deepcopy(s1.conteudo), s1.lacre, s1.conteudo_canonico)
    out = salvar_bloco_2_form1_integral(sessao, comando_id="F1-NOVO", conta_id="CONTA-A1",
                                       registro_id=rid, versao_lida=1, respostas={"2.3": "Nova unidade fictícia"})
    assert out["permitido"], out
    sessao.commit()
    s2 = _snapshot(sessao, {"registro_id":rid}, "SNAP-2", versao=2)["snapshot_id"]
    p2 = iniciar(sessao, rid, s2, comando_id="INICIO-2")["preparacao_id"]
    assert p1 != p2
    assert sessao.get(PreparacaoForm2, p2).conteudo == {"anotacao_preparatoria": ""}
    consulta = consultar_preparacao(sessao, conta_id="CONTA-A1", registro_id=rid, preparacao_id=p1)
    assert not consulta["pode_editar"] and consulta["origem"]["snapshot"].id == sid
    assert [e.conteudo["versao_rascunho"] for e in consulta["historico"]] == [1, 2]
    assert consulta["historico"][-1].conteudo["conteudo"] == sessao.get(PreparacaoForm2, p1).conteudo
    sessao.commit()
    sessao.refresh(s1)
    assert (s1.conteudo, s1.lacre, s1.conteudo_canonico) == original
    assert verificar_cadeia(sessao, p1)[0]


@pytest.mark.parametrize("segundo_preparador", ["PESSOA-G", "PESSOA-B"])
def test_consulta_direta_e_lista_respeitam_cada_designacao(sessao, segundo_preparador):
    rid, s1 = base(sessao)
    p1 = iniciar(sessao, rid, s1)["preparacao_id"]
    alteracao = salvar_bloco_2_form1_integral(
        sessao, comando_id="F1-S2", conta_id="CONTA-A1", registro_id=rid,
        versao_lida=1, respostas={"2.3": "Unidade fictícia da segunda origem"})
    assert alteracao["permitido"]
    sessao.commit()
    s2 = _snapshot(sessao, {"registro_id": rid}, "F2-S2", versao=2)["snapshot_id"]
    url = f"/registros/{rid}/form2/preparacao"
    conta = {"conta_id": "CONTA-G1"}

    leitura = cliente.get(url, params={**conta, "snapshot_id": s1})
    assert leitura.status_code == 200 and s1 in leitura.text and s2 not in leitura.text
    assert cliente.get(url, params={**conta, "snapshot_id": s2}).status_code == 403
    assert cliente.get(url, params={**conta, "preparacao_id": p1, "snapshot_id": s2}).status_code == 403
    apa = cliente.get(url, params={"conta_id": "CONTA-A1", "snapshot_id": s2})
    assert apa.status_code == 200 and s1 in apa.text and s2 in apa.text

    if segundo_preparador != "PESSOA-G":
        habilitar(sessao, rid, segundo_preparador)
    p2 = iniciar(sessao, rid, s2, preparador_id=segundo_preparador, comando_id="DESIGNAR-S2")["preparacao_id"]
    lista = cliente.get(url, params=conta)
    atribuida = segundo_preparador == "PESSOA-G"
    assert lista.status_code == 200 and s1 in lista.text and p1 in lista.text
    assert (s2 in lista.text) == atribuida and (p2 in lista.text) == atribuida
    for seletor in ({"snapshot_id": s2}, {"preparacao_id": p2}):
        resposta = cliente.get(url, params={**conta, **seletor})
        assert resposta.status_code == (200 if atribuida else 403)
        assert ("Unidade fictícia da segunda origem" in resposta.text) == atribuida


def test_substituicao_apa_preserva_finalidades_e_designacoes_pessoais(sessao):
    from testes.test_continuidade_apa import _iniciar

    rid, sid = base(sessao)
    habilitar(sessao, rid, "PESSOA-A", "preparar")
    habilitar(sessao, rid, "PESSOA-F", "acompanhar")
    # Como APA em exercício, Alfa pode selecionar a origem antes de se designar.
    url = f"/registros/{rid}/form2/preparacao"
    def consultar(conta):
        return cliente.get(url, params={"conta_id": conta, "snapshot_id": sid})

    assert consultar("CONTA-A1").status_code == 200
    assert consultar("CONTA-F1").status_code == 403
    pid = iniciar(sessao, rid, sid, preparador_id="PESSOA-A")["preparacao_id"]
    momento = agora()
    troca = _iniciar(sessao, momento=momento, inicio_em=momento-timedelta(minutes=1),
                     fim_previsto_em=momento+timedelta(hours=1))
    assert troca["permitido"]
    sessao.commit()

    substituto = consultar("CONTA-F1")
    assert substituto.status_code == 200 and "Acompanhar preparação" in substituto.text
    assert "Designar AAL e iniciar preparação" not in substituto.text
    designado = consultar("CONTA-A1")
    assert designado.status_code == 200 and "Iniciar preparação" in designado.text
    assert "Designar AAL e iniciar preparação" not in designado.text
    assert salvar(sessao, rid, pid, conta_id="CONTA-A1")["permitido"]
    assert not salvar(sessao, rid, pid, conta_id="CONTA-F1", comando_id="SUPLENTE")["permitido"]


def test_designacao_nao_autoriza_snapshot_de_outro_registro(sessao):
    rid, s1 = base(sessao)
    iniciar(sessao, rid, s1)
    outro = _preparar(sessao, "F2-OUTRO")
    s2 = _snapshot(sessao, outro, "ORIGEM-OUTRO")["snapshot_id"]
    url = f"/registros/{rid}/form2/preparacao"
    for conta in ("CONTA-A1", "CONTA-G1"):
        negada = cliente.get(url, params={"conta_id": conta, "snapshot_id": s2})
        assert negada.status_code == 403 and s2 not in negada.text
    outra_url = f"/registros/{outro['registro_id']}/form2/preparacao"
    assert cliente.get(outra_url, params={"conta_id": "CONTA-G1", "snapshot_id": s2}).status_code == 403


def test_t13_preparacao_nao_muda_nucleo_ou_form1(sessao):
    rid, sid = base(sessao)
    registro = sessao.get(Registro, rid)
    f1 = sessao.get(RascunhoForm1Integral, rid)
    original = (registro.estado_atual, registro.sequencia_atual, deepcopy(f1.conteudo), f1.lacre_conteudo)
    instrumentos = [(x.id,x.estado_instrumento,x.versao_vigente_id) for x in sessao.scalars(select(Instrumento))]
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    salvar(sessao, rid, pid)
    sessao.refresh(registro); sessao.refresh(f1)
    assert original == (registro.estado_atual, registro.sequencia_atual, f1.conteudo, f1.lacre_conteudo)
    assert instrumentos == [(x.id,x.estado_instrumento,x.versao_vigente_id) for x in sessao.scalars(select(Instrumento))]


def test_t15_migracao_aditiva_idempotente_reversao_protegida(sessao):
    reverter(sessao); sessao.commit()
    assert "preparacao_form2" not in inspect(motor).get_table_names()
    aplicar(sessao); aplicar(sessao); sessao.commit()
    rid, sid = base(sessao)
    snap = sessao.get(VersaoForm1Integral, sid).lacre
    aplicar(sessao); sessao.commit()
    with pytest.raises(RuntimeError, match="recusada"):
        reverter(sessao)
    sessao.rollback()
    assert sessao.get(VersaoForm1Integral, sid).lacre == snap
    assert iniciar(sessao, rid, sid)["permitido"]


def test_t14_t16_http_acesso_salvamento_erros_e_ausencia_de_submissao(sessao):
    rid, sid = base(sessao)
    url = f"/registros/{rid}/form2/preparacao"
    assert cliente.get(url, params={"conta_id":"CONTA-B1"}).status_code == 403
    consulta = cliente.get(url, params={"conta_id":"CONTA-A1", "snapshot_id":sid})
    assert consulta.status_code == 200 and "Designar AAL e iniciar preparação" in consulta.text
    resposta = cliente.post(url+"/iniciar", data={"conta_id":"CONTA-A1", "comando_id":"HTTP-I",
                            "snapshot_id":sid, "preparador_id":"PESSOA-G"}, follow_redirects=False)
    assert resposta.status_code == 303 and "#" not in resposta.headers["location"]
    sessao.expire_all()
    pid = sessao.scalar(select(PreparacaoForm2.id))
    consulta = cliente.get(url, params={"conta_id":"CONTA-G1", "preparacao_id":pid})
    assert 'id="anotacao"' in consulta.text and 'for="anotacao"' in consulta.text
    assert 'aria-describedby="ajuda-salvar"' in consulta.text
    dados = {"conta_id":"CONTA-G1", "comando_id":"HTTP-S", "versao_lida":"1",
             "anotacao_preparatoria":"<script>fictício</script>"}
    salvo = cliente.post(url+f"/{pid}/salvar", data=dados)
    assert salvo.status_code == 200 and "&lt;script&gt;" in salvo.text
    assert '<script>fictício</script>' not in salvo.text
    assert cliente.get(url, params={"conta_id":"CONTA-A1", "preparacao_id":pid}).text.count('id="anotacao"') == 0
    erro = cliente.post(url+f"/{pid}/salvar", data={**dados,"comando_id":"HTTP-OLD","anotacao_preparatoria":"Texto não perdido"})
    assert erro.status_code == 409 and "Texto não perdido" in erro.text and 'role="alert"' in erro.text
    for acao in ("submeter","validar","decidir","habilitar"):
        assert cliente.post(url+"/"+acao, data=dados).status_code == 404
    forjado = cliente.post(url+f"/{pid}/salvar", data={**dados,"snapshot_id":"forjado"})
    assert forjado.status_code == 400
    sessao.expire_all()
    assert sessao.get(PreparacaoForm2, pid).versao_rascunho == 2


def test_apa_tambem_preparador_requer_designacao_explicita(sessao):
    rid, sid = base(sessao)
    habilitar(sessao, rid, "PESSOA-A", "preparar")
    assert sessao.scalar(select(func.count()).select_from(PreparacaoForm2)) == 0
    pid = iniciar(sessao, rid, sid, preparador_id="PESSOA-A")["preparacao_id"]
    assert salvar(sessao, rid, pid, conta_id="CONTA-A1")["permitido"]
    atos = list(sessao.scalars(select(Evento).where(Evento.cadeia_id==pid).order_by(Evento.sequencia_cadeia)))
    assert [a.conteudo["papel_exercido"] for a in atos] == ["APA_designante", "preparador_demonstrativo"]


@pytest.mark.parametrize("decisao", ["devolver", "confirmar"])
def test_t03_conferencia_nao_e_gate_institucional_form2(sessao, decisao):
    from app.conferencia_interna_form1_integral import (solicitar_conferencia_interna_form1_integral,
        devolver_conferencia_interna_form1_integral, confirmar_conferencia_interna_form1_integral)
    rid, sid = base(sessao)
    solicitado = solicitar_conferencia_interna_form1_integral(sessao, comando_id="F2-CONF-I",
        conta_id="CONTA-A1", registro_id=rid, versao_lida=1)
    assert solicitado["permitido"]
    sessao.commit()
    args = dict(comando_id="F2-CONF-D", conta_id="CONTA-A1", registro_id=rid, versao_lida=1)
    if decisao == "devolver":
        out = devolver_conferencia_interna_form1_integral(sessao, **args, justificativa="Rever informação fictícia")
    else:
        out = confirmar_conferencia_interna_form1_integral(sessao, **args)
    assert out["permitido"], out
    sessao.commit()
    assert iniciar(sessao, rid, sid)["permitido"]
    assert sessao.get(VersaoForm1Integral, sid).conteudo["submissao_habilitada"] is False


def test_t03_registro_sem_snapshot_nao_cria_origem(sessao):
    r = _preparar(sessao, "F2-SEM-SNAPSHOT")
    rid = r["registro_id"]
    habilitar(sessao, rid, "PESSOA-A", "acompanhar")
    pagina = cliente.get(f"/registros/{rid}/form2/preparacao", params={"conta_id":"CONTA-A1"})
    assert pagina.status_code == 200 and "Nenhuma versão do FORM 1 disponível" in pagina.text
    assert sessao.scalar(select(func.count()).select_from(VersaoForm1Integral)) == 0
    assert sessao.scalar(select(func.count()).select_from(PreparacaoForm2)) == 0


def test_t08_revogacao_serializada_com_salvamento(sessao):
    rid, sid = base(sessao)
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    trava = threading.Event()
    liberar = threading.Event()
    def revogar():
        with Session(motor) as s, s.begin():
            registrar_habilitacao_controlada(s, comando_id="REVOGAR-CONC", registro_id=rid,
                pessoa_id="PESSOA-G", finalidade="preparar", ativa=False,
                vigente_de=agora()-timedelta(days=1), vigente_ate=agora()+timedelta(days=1),
                aprovacao_referencia="ACEITE-FICT", fundamento="Revogação sintética")
            trava.set()
            assert liberar.wait(10)
    def gravar():
        assert trava.wait(10)
        liberar.set()
        with Session(motor) as s, s.begin():
            return salvar_preparacao(s, comando_id="SAVE-REVOG", conta_id="CONTA-G1", registro_id=rid,
                preparacao_id=pid, versao_lida=1, conteudo={"anotacao_preparatoria":"Não deve salvar"})
    with ThreadPoolExecutor(max_workers=2) as pool:
        a, b = pool.submit(revogar), pool.submit(gravar)
        a.result(timeout=15)
        assert not b.result(timeout=15)["permitido"]
    sessao.expire_all()
    assert sessao.get(PreparacaoForm2, pid).versao_rascunho == 1


def test_t14_comando_nuclear_nao_recebe_preparacao(sessao):
    from app.instrumentos import iniciar_preenchimento
    rid, sid = base(sessao)
    pid = iniciar(sessao, rid, sid)["preparacao_id"]
    out = iniciar_preenchimento(sessao, comando_id="F2-FORJADO-NUCLEAR", conta_id="CONTA-A1", instrumento_id=pid)
    assert not out["permitido"]
    sessao.commit()


def test_executor_rejeita_manifesto_invalido_sem_conectar(tmp_path):
    import json
    from demonstracoes.form2_preparacao import ler_manifesto
    p = tmp_path / "manifesto.json"
    p.write_text(json.dumps({"politica":"institucional", "somente_dados_ficticios":True,"habilitacoes":[]}), encoding="utf-8")
    with pytest.raises(ValueError): ler_manifesto(p)


def test_t16_navegacao_e_saida_segura_javascript():
    import shutil, subprocess
    node = shutil.which("node")
    assert node, "Node necessário para ensaio local da proteção de saída"
    subprocess.run([node, "testes/apoio_form2_preparacao.cjs"], check=True, capture_output=True, text=True)
