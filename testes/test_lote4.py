import pytest
from testes.apoio_entrada import ClienteAposApresentacao as TestClient
from sqlalchemy import select

from app.main import app
from app.fila_form2 import manifestar_de_oficio
from app.modelos import Designacao, ParticipacaoForm2
from app.conferencia_interna_form1_integral import (
    solicitar_conferencia_interna_form1_integral, confirmar_conferencia_interna_form1_integral,
    devolver_conferencia_interna_form1_integral,
)
from app.respostas_form2 import aplicar_bloco, aguarda_temporalidade, GUARDA_INSTITUCIONAL
from carga_ficticia.pessoas import semear_eta
from testes.test_form2_preparacao import base
from testes.test_governanca_form2_v9 import principal


def test_temporalidade_e_falta_factual():
    for codigo in (GUARDA_INSTITUCIONAL, "A_CONFIRMAR"):
        dados, _ = aplicar_bloco({}, bloco=2, proxima_versao=1, alteracoes={"F2-2.9": codigo})
        assert aguarda_temporalidade(dados) == (codigo == GUARDA_INSTITUCIONAL)
        assert bool(dados["sinalizadores_etapa1"]) == (codigo == "A_CONFIRMAR")


def test_eta_idempotente(sessao):
    semear_eta(sessao)
    semear_eta(sessao)
    sessao.flush()
    assert len(sessao.scalars(select(Designacao).where(
        Designacao.pessoa_id == "PESSOA-I", Designacao.papel == "aal_form2")).all()) == 1


def test_oficio_resposta_sem_modificar_principal(sessao, principal):
    p = principal
    estado = (p.snapshot_id, p.estado, p.versao)
    c = TestClient(app)
    url = f"/form2/participacoes/{p.id}/orientacao"
    assert c.get(url, params={"conta_id":"CONTA-E1"}).status_code == 200
    assert c.get(url, params={"conta_id":"CONTA-B1"}).status_code == 403
    proibida = c.post(url.replace("/orientacao","/blocos/2"), data={
        "conta_id":"CONTA-E1", "versao":p.versao, "comando_id":"L4-DPO-BLOCO",
        "resposta_F2-2.9":GUARDA_INSTITUCIONAL})
    assert proibida.status_code in (403, 409)
    ato = dict(conta_id="CONTA-E1", participacao_id=p.id, comando_id="L4-DPO", texto="Rever a finalidade.")
    r = manifestar_de_oficio(sessao, **ato)
    sessao.commit()
    assert manifestar_de_oficio(sessao, **ato) == {**r, "reexecutado": True}
    sessao.commit()
    cid = r["participacao_id"]
    assert "Rever a finalidade." in c.get(url.removesuffix("/orientacao"), params={"conta_id":"CONTA-B1"}).text
    assert c.post(f"/form2/participacoes/{cid}/orientacao",
        data={"conta_id":"CONTA-B1","comando_id":"L4-DEC","texto":"Incluída na análise.","decisao":"Acolhida"}).status_code == 200
    sessao.expire_all()
    assert sessao.get(ParticipacaoForm2,cid).conteudo["resposta"]["decisao"] == "Acolhida"
    assert (p.snapshot_id,p.estado,p.versao) == estado


@pytest.mark.parametrize("suplente", [True, False])
def test_segregacao_e_ausencia_de_conferente(sessao,suplente):
    rid, _ = base(sessao)
    if not suplente:
        sessao.scalar(select(Designacao).where(Designacao.unidade_id=="UNID-NORTE",
            Designacao.tipo_apa=="suplente")).ativa=False
        sessao.commit()
    args=dict(registro_id=rid,versao_lida=1)
    assert solicitar_conferencia_interna_form1_integral(sessao,**args,conta_id="CONTA-A1",comando_id="L4-SOL")["permitido"]
    sessao.commit()
    assert not devolver_conferencia_interna_form1_integral(sessao,**args,conta_id="CONTA-A1",
        comando_id="L4-DEV",justificativa="Revisar")["permitido"]
    assert not confirmar_conferencia_interna_form1_integral(sessao,**args,conta_id="CONTA-A1",comando_id="L4-A")["permitido"]
    sessao.commit()
    cliente = TestClient(app)
    consulta = f"/registros/{rid}/form1-integral/conferencia-interna"
    assert (consulta in cliente.get("/central?conta_id=CONTA-F1").text) == suplente
    assert consulta not in cliente.get("/central?conta_id=CONTA-A1").text
    assert cliente.get(consulta, params={"conta_id":"CONTA-A1"}).status_code == 403
    assert cliente.get(consulta, params={"conta_id":"CONTA-F1"}).status_code == (200 if suplente else 403)
    if not suplente:
        painel=TestClient(app).get("/form2/filas?conta_id=CONTA-E1")
        assert "Aguardando definição de quem fará a conferência" in painel.text
    assert confirmar_conferencia_interna_form1_integral(sessao,**args,conta_id="CONTA-F1",comando_id="L4-F")["permitido"] == suplente


def test_guarda_no_bloco_fila_e_painel(sessao,principal):
    p=principal
    c=TestClient(app)
    resposta=c.post(f"/form2/participacoes/{p.id}/blocos/2", data={
        "conta_id":"CONTA-B1","comando_id":"L4-GUARDA","versao":p.versao,
        "resposta_F2-2.9":GUARDA_INSTITUCIONAL})
    selo="Guarda em definição"
    assert resposta.status_code==200 and selo in resposta.text
    assert selo in c.get("/form2/filas?conta_id=CONTA-B1").text
    painel=c.get("/form2/filas?conta_id=CONTA-E1")
    assert painel.context["aguardando_guarda"]==1
    assert "Registros aguardando definição de temporalidade: 1" in painel.text


def test_reatribuicao_de_beta_para_eta(sessao,principal):
    p=principal
    semear_eta(sessao)
    sessao.add(Designacao(pessoa_id="PESSOA-A", unidade_id=p.unidade_id, papel="gestor_fila"))
    sessao.commit()
    c=TestClient(app)
    fila=c.get("/form2/filas?conta_id=CONTA-A1")
    assert {agente.id for agente in fila.context["agentes"][p.id]}=={"PESSOA-I"}
    r=c.post(f"/form2/participacoes/{p.id}/reatribuir",data={
        "conta_id":"CONTA-A1","comando_id":"L4-ETA","versao":p.versao,
        "responsavel_id":"PESSOA-I","motivo":"Distribuição das oficinas fictícias."})
    assert r.status_code==200 and "Servidor Eta" in r.context["mensagem_atribuicao"]
    sessao.refresh(p)
    assert p.responsavel_id=="PESSOA-I"
