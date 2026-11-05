"""INSTRUÇÃO_FORMS01_03: adoção explícita, legado imutável e 129 IDs efetivos."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import threading

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.banco import motor
from app.eventos import lacre, verificar_cadeia
from app.extensao_medidas_form1 import (
    adotar_extensao_medidas, catalogo_efetivo, matriz_efetiva, versao_estrutura,
    VERSAO_BASE, VERSAO_EXTENSAO, definicao_extensao,
)
from app.form1_integral import campos_por_id
from app.main import app
from app.modelos import (RascunhoForm1Integral, VersaoForm1Integral, Evento,
                        EventoAuditoria, Comando, Registro)
from app.pre_validacao_form1_integral import pre_validar_form1_integral, carregar_matriz_obrigatoriedade
from app.rascunho_form1_integral import salvar_bloco_13_form1_integral
from app.submissao_form1_integral import preparar_snapshot_form1_integral
from testes.test_conferencia_interna_form1_integral_8ac import _preparar, _solicitar

cliente = TestClient(app)
EXT = {"extensao_medidas": {"versao": VERSAO_EXTENSAO}}


def preparar(sessao):
    registro = _preparar(sessao, "EXT13")
    rid = registro["registro_id"]
    resultado = salvar_bloco_13_form1_integral(
        sessao, comando_id="EXT13-LEGADO", conta_id="CONTA-G1", registro_id=rid,
        versao_lida=1, respostas={"13.1": ["A confirmar"], "13.2": "Às vezes", "13.3": "Não"},
    )
    sessao.commit()
    assert resultado["permitido"]
    return registro


def adotar(sessao, rid, **substituicoes):
    dados = dict(comando_id="EXT13-ADOTAR", conta_id="CONTA-G1", registro_id=rid,
                 versao_lida=2, confirmar=True)
    dados.update(substituicoes)
    resultado = adotar_extensao_medidas(sessao, **dados)
    sessao.commit()
    return resultado


def test_catalogo_matriz_legados_intactos_e_extensao_129_independente():
    base = campos_por_id()
    matriz = carregar_matriz_obrigatoriedade()
    ampliado, regras = catalogo_efetivo(EXT), matriz_efetiva(EXT)
    assert len(base) == len(matriz) == 128 and "13.2.1" not in base
    assert len(ampliado) == len(regras) == definicao_extensao()["quantidade_efetiva"] == 129
    assert [k for k in ampliado if k.startswith("13.")] == ["13.1", "13.2", "13.2.1", "13.3", "13.4"]
    for campo in base:
        if campo != "13.2":
            assert ampliado[campo] == base[campo]
            assert regras[campo] == matriz[campo]
    assert "documentos físicos" in ampliado["13.2"].pergunta
    assert "estações de trabalho" in ampliado["13.2.1"].pergunta
    assert all(regras[k].classe == "Facultativa nesta proposta" for k in ("13.2", "13.2.1"))
    assert ampliado["13.2"].alternativas == ampliado["13.2.1"].alternativas == base["13.2"].alternativas


def test_adocao_preserva_snapshot_enunciado_original_e_demais_respostas(sessao):
    registro = preparar(sessao)
    rid = registro["registro_id"]
    anterior = deepcopy(sessao.get(RascunhoForm1Integral, rid).conteudo)
    estado = sessao.get(Registro, rid).estado_atual

    resultado = adotar(sessao, rid)

    assert resultado["permitido"]
    rascunho = sessao.get(RascunhoForm1Integral, rid)
    legado = rascunho.conteudo["extensao_medidas"]["legado"]
    snapshot = sessao.get(VersaoForm1Integral, legado["snapshot_id"])
    assert snapshot.conteudo["form1_integral"] == anterior
    assert snapshot.lacre == lacre(snapshot.conteudo_canonico) == legado["lacre_snapshot"]
    assert legado["pergunta"] == campos_por_id()["13.2"].pergunta
    assert legado["resposta"] == "Às vezes"
    assert legado["rascunho_salvo_por"] == "PESSOA-G"
    assert versao_estrutura(snapshot.conteudo["form1_integral"]) == VERSAO_BASE
    assert versao_estrutura(rascunho.conteudo) == VERSAO_EXTENSAO
    assert "13.2" not in rascunho.conteudo["respostas"] and "13.2.1" not in rascunho.conteudo["respostas"]
    assert rascunho.conteudo["respostas"] == {k:v for k,v in anterior["respostas"].items() if k != "13.2"}
    assert rascunho.versao_rascunho == 3
    assert sessao.get(Registro, rid).estado_atual == estado
    assert snapshot.conteudo["submissao_habilitada"] is False
    assert verificar_cadeia(sessao, registro["codigo_lgpd"])[0]
    eventos = sessao.scalars(select(Evento).where(Evento.comando_id == "EXT13-ADOTAR").order_by(Evento.ordem_no_comando)).all()
    assert [e.ordem_no_comando for e in eventos] == [1, 2]
    assert eventos[-1].conteudo["versao_estrutura"] == VERSAO_EXTENSAO
    auditoria = sessao.scalar(select(EventoAuditoria).where(EventoAuditoria.comando_id == "EXT13-ADOTAR"))
    assert auditoria.conteudo["papel"] == "ARP"


def test_adocao_idempotente_e_recusa_reuso_ou_segunda_adocao(sessao):
    rid = preparar(sessao)["registro_id"]
    assert adotar(sessao, rid)["permitido"]
    assert adotar(sessao, rid)["reexecutado"]
    assert not adotar(sessao, rid, versao_lida=3)["permitido"]
    assert not adotar(sessao, rid, comando_id="EXT13-NOVA", versao_lida=3)["permitido"]
    assert sessao.scalar(select(func.count()).select_from(VersaoForm1Integral)) == 1
    assert sessao.get(RascunhoForm1Integral, rid).versao_rascunho == 3


@pytest.mark.parametrize("alteracao", [{"conta_id":"CONTA-A1"}, {"conta_id":"CONTA-B1"},
                                     {"confirmar":False}, {"versao_lida":1}])
def test_adocao_exige_arp_autorizado_confirmacao_e_versao_atual(sessao, alteracao):
    rid = preparar(sessao)["registro_id"]
    anterior = deepcopy(sessao.get(RascunhoForm1Integral, rid).conteudo)
    assert not adotar(sessao, rid, **alteracao)["permitido"]
    assert sessao.get(RascunhoForm1Integral, rid).conteudo == anterior
    assert sessao.scalar(select(func.count()).select_from(VersaoForm1Integral)) == 0


def test_respostas_independentes_recuperadas_e_facultativas(sessao):
    rid = preparar(sessao)["registro_id"]
    assert adotar(sessao, rid)["permitido"]
    for n, respostas in enumerate(({"13.2":"Sempre", "13.2.1":"Não"},
                                   {"13.2":"A confirmar", "13.2.1":"Não se aplica"}, {}), start=3):
        resultado = salvar_bloco_13_form1_integral(
            sessao, comando_id=f"EXT13-SALVAR-{n}", conta_id="CONTA-G1", registro_id=rid,
            versao_lida=n, respostas=respostas, estrutura_lida=VERSAO_EXTENSAO)
        sessao.commit()
        sessao.expire_all()
        assert resultado["permitido"]
        conteudo = sessao.get(RascunhoForm1Integral, rid).conteudo
        for campo in ("13.2", "13.2.1"):
            assert conteudo["respostas"].get(campo) == respostas.get(campo)
        pre = pre_validar_form1_integral(conteudo, nome_institucional="Servidor fictício")
        assert not pre["submissao_habilitada"]
        assert not any(i["campo_id"] in ("13.2", "13.2.1") for i in pre["incompletos"])
        assert len(pre["avisos"]) == (1 if n == 4 else 0)
        assert conteudo["extensao_medidas"]["legado"]["resposta"] == "Às vezes"


@pytest.mark.parametrize("estrutura,respostas", [(None,{"13.2":"Sempre"}),
    ("VERSAO-FORJADA",{"13.2":"Sempre"}), (VERSAO_EXTENSAO,{"13.2.1":"opção forjada"}),
    (VERSAO_EXTENSAO,{"13.2.2":"Sempre"})])
def test_extensao_recusa_aba_legada_versao_ou_respostas_invalidas(sessao, estrutura, respostas):
    rid = preparar(sessao)["registro_id"]
    assert adotar(sessao, rid)["permitido"]
    anterior = deepcopy(sessao.get(RascunhoForm1Integral, rid).conteudo)
    resultado = salvar_bloco_13_form1_integral(
        sessao, comando_id="EXT13-INVALIDO", conta_id="CONTA-G1", registro_id=rid,
        versao_lida=3, respostas=respostas, estrutura_lida=estrutura)
    sessao.commit()
    assert not resultado["permitido"]
    assert sessao.get(RascunhoForm1Integral, rid).conteudo == anterior


def test_legado_recusa_novo_campo_sem_adocao(sessao):
    rid = preparar(sessao)["registro_id"]
    for indice, estrutura in enumerate((None, VERSAO_EXTENSAO)):
        resultado = salvar_bloco_13_form1_integral(
            sessao, comando_id=f"EXT13-SEM-ADOCAO-{indice}", conta_id="CONTA-G1",
            registro_id=rid, versao_lida=2, respostas={"13.2.1":"Sempre"}, estrutura_lida=estrutura)
        sessao.commit()
        assert not resultado["permitido"]
    assert versao_estrutura(sessao.get(RascunhoForm1Integral, rid).conteudo) == VERSAO_BASE


def test_snapshot_preexistente_reutilizado_sem_reescrita(sessao, monkeypatch):
    registro = preparar(sessao)
    rid = registro["registro_id"]
    # Simula envelope anterior à extensão, sem discriminador adicional.
    from app import submissao_form1_integral as snapshots
    envelope_atual = snapshots._envelope_snapshot
    def envelope_legado(*args):
        envelope = envelope_atual(*args)
        envelope["contrato"].pop("versao_estrutura")
        return envelope
    with monkeypatch.context() as legado:
        legado.setattr(snapshots, "_envelope_snapshot", envelope_legado)
        assert _solicitar(sessao, registro, versao=2)["permitido"]
    snapshot = sessao.scalar(select(VersaoForm1Integral))
    anterior = (deepcopy(snapshot.conteudo), snapshot.conteudo_canonico, snapshot.lacre)
    assert adotar(sessao, rid)["permitido"]
    sessao.refresh(snapshot)
    assert anterior == (snapshot.conteudo, snapshot.conteudo_canonico, snapshot.lacre)
    assert sessao.scalar(select(func.count()).select_from(VersaoForm1Integral)) == 1
    pagina = cliente.get(f"/registros/{rid}/form1-integral/conferencia-interna?conta_id=CONTA-A1")
    assert pagina.status_code == 200
    assert campos_por_id()["13.2"].pergunta in pagina.text
    assert catalogo_efetivo(EXT)["13.2.1"].pergunta not in pagina.text


def test_rollback_na_adocao_reverte_snapshot_eventos_rascunho(sessao, monkeypatch):
    rid = preparar(sessao)["registro_id"]
    anterior = deepcopy(sessao.get(RascunhoForm1Integral, rid).conteudo)
    def falhar(*args, **kwargs):
        raise RuntimeError("falha fictícia na auditoria")
    monkeypatch.setattr("app.eventos.registrar_auditoria", falhar)
    with pytest.raises(RuntimeError, match="falha fictícia"):
        adotar_extensao_medidas(sessao, comando_id="EXT13-ROLLBACK", conta_id="CONTA-G1",
                               registro_id=rid, versao_lida=2, confirmar=True)
    sessao.rollback()
    assert sessao.get(RascunhoForm1Integral, rid).conteudo == anterior
    assert sessao.scalar(select(func.count()).select_from(VersaoForm1Integral)) == 0
    assert sessao.get(Comando, "EXT13-ROLLBACK") is None
    assert sessao.scalar(select(func.count()).select_from(Evento).where(Evento.comando_id=="EXT13-ROLLBACK")) == 0


def test_adocoes_concorrentes_preservam_um_snapshot_e_uma_alteracao(sessao):
    rid = preparar(sessao)["registro_id"]
    barreira = threading.Barrier(2)
    def executar(indice):
        with Session(motor) as outra, outra.begin():
            barreira.wait(timeout=10)
            return adotar_extensao_medidas(outra, comando_id=f"EXT13-CONC-{indice}", conta_id="CONTA-G1",
                                          registro_id=rid, versao_lida=2, confirmar=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        resultados = list(pool.map(executar, (1, 2)))
    assert sorted(r["permitido"] for r in resultados) == [False, True]
    sessao.expire_all()
    assert sessao.get(RascunhoForm1Integral, rid).versao_rascunho == 3
    assert sessao.scalar(select(func.count()).select_from(VersaoForm1Integral)) == 1


def test_http_adocao_salvamento_consulta_e_snapshot_ampliado(sessao):
    registro = preparar(sessao)
    rid = registro["registro_id"]
    url = f"/registros/{rid}"
    legado = cliente.get(url + "?conta_id=CONTA-G1")
    assert campos_por_id()["13.2"].pergunta in legado.text
    assert 'name="campo__13.2.1"' not in legado.text
    assert 'data-adotar-medidas' in legado.text
    consulta = cliente.get(url + "?conta_id=CONTA-A1")
    assert 'data-adotar-medidas' not in consulta.text

    resposta = cliente.post(url + "/form1-integral/bloco-13/adotar-extensao", data={
        "conta_id":"CONTA-G1", "comando_id":"EXT13-HTTP-A", "versao_lida":"2", "confirmar":"sim"})
    assert resposta.status_code == 200 and resposta.url.fragment == "titulo-bloco-13"
    assert 'name="campo__13.2.1"' in resposta.text
    assert 'data-adotar-medidas' not in resposta.text
    assert campos_por_id()["13.2"].pergunta in resposta.text  # Arquivo legado consultável.
    assert 'id="ajuda-cartilha-13.1"' in resposta.text
    salvo = cliente.post(url + "/form1-integral/bloco-13/salvar", data={
        "conta_id":"CONTA-G1", "comando_id":"EXT13-HTTP-S", "versao_lida":"3",
        "estrutura_lida":VERSAO_EXTENSAO, "campo__13.2":"Sempre", "campo__13.2.1":"Não",
        "acao_pos_salvar":"proximo"})
    assert salvo.status_code == 200 and "titulo-bloco-14" in str(salvo.url)
    recarga = cliente.get(url + "?conta_id=CONTA-G1")
    assert '<option value="Não" selected>' in recarga.text
    consulta = cliente.get(url + "?conta_id=CONTA-A1")
    assert 'name="campo__13.2.1"' not in consulta.text
    assert catalogo_efetivo(EXT)["13.2.1"].pergunta in consulta.text
    assert _solicitar(sessao, registro, versao=4)["permitido"]
    consulta_snapshot = cliente.get(url + "/form1-integral/conferencia-interna?conta_id=CONTA-A1")
    assert VERSAO_EXTENSAO in consulta_snapshot.text
    assert catalogo_efetivo(EXT)["13.2.1"].pergunta in consulta_snapshot.text
    sessao.expire_all()
    snapshots = sessao.scalars(select(VersaoForm1Integral).order_by(VersaoForm1Integral.numero)).all()
    assert [s.conteudo["contrato"]["versao_estrutura"] for s in snapshots] == [VERSAO_BASE, VERSAO_EXTENSAO]
    assert all(not s.conteudo["submissao_habilitada"] for s in snapshots)
    painel = cliente.get("/?conta_id=CONTA-G1")
    assert painel.status_code == 200


def test_outro_bloco_preserva_extensao_e_navegacao_12_13_14(sessao):
    rid = preparar(sessao)["registro_id"]
    assert adotar(sessao, rid)["permitido"]
    conteudo = deepcopy(sessao.get(RascunhoForm1Integral, rid).conteudo)
    anterior = cliente.post(f"/registros/{rid}/form1-integral/bloco-12/salvar", data={
        "conta_id":"CONTA-G1", "comando_id":"EXT13-B12", "versao_lida":"3",
        "acao_pos_salvar":"proximo"}, follow_redirects=False)
    assert anterior.headers["location"].endswith("#titulo-bloco-13")
    ultimo = cliente.post(f"/registros/{rid}/form1-integral/bloco-14/salvar", data={
        "conta_id":"CONTA-G1", "comando_id":"EXT13-B14", "versao_lida":"4",
        "acao_pos_salvar":"proximo"}, follow_redirects=False)
    assert ultimo.headers["location"].endswith("#titulo-pre-validacao-form1")
    sessao.expire_all()
    atual = sessao.get(RascunhoForm1Integral, rid).conteudo
    assert atual["extensao_medidas"] == conteudo["extensao_medidas"]
    assert atual["respostas"]["13.1"] == conteudo["respostas"]["13.1"]
    assert "13.2" not in atual["respostas"]


def test_adocao_e_recuperacao_local_nao_convertem_respostas():
    from pathlib import Path
    import shutil
    import subprocess
    node = shutil.which("node")
    if not node:
        pytest.skip("Node indisponível; aceitação visual permanece separada")
    raiz = Path(__file__).resolve().parents[1]
    resultado = subprocess.run([node, str(raiz / "testes/apoio_extensao_medidas_form1.cjs")],
                               cwd=raiz, capture_output=True, text=True)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
