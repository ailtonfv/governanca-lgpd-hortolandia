"""FORMS01_04: extensão de guarda factual, versionada e optativa (AAA)."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import threading
from pathlib import Path
import json
import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.banco import motor
from app.eventos import lacre, verificar_cadeia
from app.extensao_guarda_form1 import (
    adotar_extensao_guarda, definicao_guarda, VERSAO_GUARDA, VERSAO_COMBINADA,
)
from app.extensao_medidas_form1 import (
    adotar_extensao_medidas, catalogo_efetivo, matriz_efetiva, versao_estrutura,
    conteudo_da_estrutura, VERSAO_BASE, VERSAO_EXTENSAO,
)
from app.form1_integral import campos_por_id
from app.main import app
from app.modelos import RascunhoForm1Integral, VersaoForm1Integral, Evento, EventoAuditoria, Registro, Comando
from app.pre_validacao_form1_integral import pre_validar_form1_integral, perguntas_para_localizacao
from app.rascunho_form1_integral import salvar_bloco_12_form1_integral, salvar_bloco_13_form1_integral
from testes.test_conferencia_interna_form1_integral_8ac import _preparar, _solicitar

cliente = TestClient(app)
LEGADO = {"12.1":"Sim", "12.1.1":"5", "12.1.2":"Anos", "12.1.3":["Tabela de temporalidade"],
          "12.2":"Guarda permanente", "12.3":"Sim", "12.4":"Em alguns casos",
          "12.4.1":"Referência documental fictícia", "12.5":"Sim", "12.5.1":"Arquivo fictício"}
NOVO = {"12.3":"Sim", "12.3.1":"Não", "12.3.2":"Não se aplica", "12.3.3":"A confirmar",
        "12.4":"Não", "12.4.2":"Sim", "12.4.2.1":"Livro de eliminação fictício",
        "12.4.3":"Não se aplica", "12.4.4":"Em alguns casos", "12.4.4.1":"Registro de remessa fictício",
        "12.5":"Sim", "12.5.1":["Entre sistemas", "De custódia", "Outra situação"],
        "12.5.1.1":"Modalidade fictícia", "12.5.2":"Destino institucional fictício"}


def preparar(sessao, medidas=False):
    registro = _preparar(sessao, "GUARDA")
    rid = registro["registro_id"]
    assert salvar_bloco_12_form1_integral(sessao, comando_id="GUARDA-LEGADO", conta_id="CONTA-G1",
        registro_id=rid, versao_lida=1, respostas=LEGADO)["permitido"]
    sessao.commit()
    if medidas:
        assert adotar_extensao_medidas(sessao, comando_id="GUARDA-MEDIDAS", conta_id="CONTA-G1",
            registro_id=rid, versao_lida=2, confirmar=True)["permitido"]
        assert salvar_bloco_13_form1_integral(sessao, comando_id="GUARDA-MEDIDAS-S", conta_id="CONTA-G1",
            registro_id=rid, versao_lida=3, estrutura_lida=VERSAO_EXTENSAO,
            respostas={"13.2":"Sempre", "13.2.1":"Não"})["permitido"]
        sessao.commit()
    return registro


def adotar(sessao, rid, **alteracoes):
    dados = dict(comando_id="GUARDA-ADOTAR", conta_id="CONTA-G1", registro_id=rid,
                 versao_lida=sessao.get(RascunhoForm1Integral, rid).versao_rascunho, confirmar=True)
    dados.update(alteracoes)
    resultado = adotar_extensao_guarda(sessao, **dados)
    sessao.commit()
    return resultado


def salvar(sessao, rid, respostas, comando="GUARDA-S", **alteracoes):
    rascunho = sessao.get(RascunhoForm1Integral, rid)
    dados = dict(comando_id=comando, conta_id="CONTA-G1", registro_id=rid,
                 versao_lida=rascunho.versao_rascunho, estrutura_lida=versao_estrutura(rascunho.conteudo),
                 respostas=respostas)
    dados.update(alteracoes)
    resultado = salvar_bloco_12_form1_integral(sessao, **dados)
    sessao.commit()
    return resultado


def test_quatro_perfis_preservam_128_129_e_acrescentam_somente_bloco12():
    alterados = set(definicao_guarda()["ids_substituidos"])
    for versao, total in ((VERSAO_BASE,128),(VERSAO_EXTENSAO,129),(VERSAO_GUARDA,139),(VERSAO_COMBINADA,140)):
        conteudo = conteudo_da_estrutura(versao)
        catalogo, matriz = catalogo_efetivo(conteudo), matriz_efetiva(conteudo)
        assert len(catalogo) == len(matriz) == total
        assert versao_estrutura(conteudo) == versao
        if versao in (VERSAO_GUARDA,VERSAO_COMBINADA):
            anterior = catalogo_efetivo(conteudo_da_estrutura(VERSAO_EXTENSAO if versao==VERSAO_COMBINADA else VERSAO_BASE))
            for k in set(anterior)-alterados:
                assert catalogo[k] == anterior[k]
            ids = [k for k in catalogo if k.startswith("12.")]
            assert ids == sorted(ids, key=lambda i: tuple(map(int,i.split('.'))))
            assert set(catalogo) == set(matriz)
    assert "12.3.1" not in campos_por_id()


@pytest.mark.parametrize("medidas", [False, True])
def test_adocao_preserva_legado_completo_e_nao_adota_bloco13_automaticamente(sessao, medidas):
    registro = preparar(sessao, medidas)
    rid = registro["registro_id"]
    rascunho = sessao.get(RascunhoForm1Integral,rid)
    antes = deepcopy(rascunho.conteudo)
    estado = sessao.get(Registro,rid).estado_atual
    assert adotar(sessao,rid)["permitido"]
    conteudo = rascunho.conteudo
    legado = conteudo["extensao_guarda"]["legado"]
    snapshot = sessao.get(VersaoForm1Integral,legado["snapshot_id"])
    assert snapshot.conteudo["form1_integral"] == antes
    assert snapshot.lacre == lacre(snapshot.conteudo_canonico) == legado["lacre_snapshot"]
    assert legado["versao_estrutura"] == versao_estrutura(antes)
    for item in legado["campos"]:
        assert item["pergunta"] == campos_por_id()[item["id"]].pergunta
        assert item["resposta"] == LEGADO[item["id"]]
    assert all(c["id"] not in conteudo["respostas"] for c in definicao_guarda()["campos"])
    assert conteudo["respostas"] == {k:v for k,v in antes["respostas"].items() if k not in definicao_guarda()["ids_substituidos"]}
    assert conteudo.get("extensao_medidas") == antes.get("extensao_medidas")
    assert sessao.get(Registro,rid).estado_atual == estado
    assert verificar_cadeia(sessao, registro["codigo_lgpd"])[0]
    auditoria = sessao.scalar(select(EventoAuditoria).where(EventoAuditoria.comando_id=="GUARDA-ADOTAR"))
    assert auditoria.conteudo["papel"] == "ARP"
    assert auditoria.conteudo["versao_estrutura"] == versao_estrutura(conteudo)


def test_adoção_em_ordem_inversa_preserva_respostas_guarda(sessao):
    rid = preparar(sessao)["registro_id"]
    assert adotar(sessao,rid)["permitido"]
    assert salvar(sessao,rid,NOVO)["permitido"]
    antes = deepcopy(sessao.get(RascunhoForm1Integral,rid).conteudo)
    resultado = adotar_extensao_medidas(sessao, comando_id="GUARDA-DEPOIS-MED", conta_id="CONTA-G1",
        registro_id=rid, versao_lida=4, confirmar=True)
    sessao.commit()
    assert resultado["permitido"]
    depois = sessao.get(RascunhoForm1Integral,rid).conteudo
    assert versao_estrutura(depois) == VERSAO_COMBINADA
    assert depois["extensao_guarda"] == antes["extensao_guarda"]
    assert depois["respostas"] == antes["respostas"]
    assert depois["extensao_medidas"]["legado"]["versao_estrutura"] == VERSAO_GUARDA


def test_respostas_independentes_e_inativas_preservadas(sessao):
    rid = preparar(sessao)["registro_id"]
    assert adotar(sessao,rid)["permitido"]
    assert salvar(sessao,rid,NOVO)["permitido"]
    sessao.expire_all()
    conteudo = sessao.get(RascunhoForm1Integral,rid).conteudo
    for k,v in NOVO.items():
        assert conteudo["respostas"][k] == v
    assert conteudo["respostas"]["12.3.1"] == "Não" and conteudo["respostas"]["12.4.2"] == "Sim"
    resposta = {**NOVO,"12.4.2":"Não se aplica","12.4.4":"A confirmar","12.5":"Não"}
    for k in ("12.4.2.1","12.4.4.1","12.5.1","12.5.1.1","12.5.2"):
        resposta.pop(k)
    assert salvar(sessao,rid,resposta,comando="GUARDA-INATIVAS")["permitido"]
    conteudo = sessao.get(RascunhoForm1Integral,rid).conteudo
    for k in ("12.4.2.1","12.4.4.1","12.5.1","12.5.1.1","12.5.2"):
        assert k not in conteudo["respostas"]
        assert conteudo["respostas_inativas"][k][-1]["valor"] == NOVO[k]
    assert conteudo["extensao_guarda"]["legado"]["campos"][0]["resposta"] == "Sim"


def test_pre_validacao_facultativos_nao_aplicaveis_avisos_e_ordem():
    conteudo = {**conteudo_da_estrutura(VERSAO_COMBINADA),"respostas":{
        "12.3":"A confirmar","12.3.1":"Não","12.3.2":"Não se aplica",
        "12.4":"Sim","12.4.2":"Não se aplica","12.4.3":"Em alguns casos",
        "12.4.4":"A confirmar","12.5":"Sim","12.5.1":["Outra situação"]}}
    pre = pre_validar_form1_integral(conteudo,nome_institucional="Servidor fictício")
    faltam = [i["campo_id"] for i in pre["incompletos"] if i["campo_id"].startswith("12.")]
    assert faltam == ["12.1","12.2","12.4.1","12.4.3.1","12.5.1.1","12.5.2"]
    assert [i["campo_id"] for i in pre["avisos"]] == ["12.3","12.4.4"]
    assert "12.4.2.1" in [i["campo_id"] for i in pre["nao_aplicaveis"]]
    assert not pre["submissao_habilitada"]
    assert all("irregular" not in i["detalhe"] for i in pre["incompletos"])
    assert "12.4.3.1" in {i["campo_id"] for i in perguntas_para_localizacao(conteudo)}
    vazio = pre_validar_form1_integral(conteudo_da_estrutura(VERSAO_GUARDA),nome_institucional="Servidor fictício")
    assert not any(i["campo_id"] in {c["id"] for c in definicao_guarda()["campos"]} for i in vazio["incompletos"])


@pytest.mark.parametrize("alteracao", [{"conta_id":"CONTA-A1"},{"conta_id":"CONTA-B1"},{"confirmar":False},{"versao_lida":1}])
def test_adocao_negada_preserva_rascunho(sessao,alteracao):
    rid = preparar(sessao)["registro_id"]
    antes=deepcopy(sessao.get(RascunhoForm1Integral,rid).conteudo)
    assert not adotar(sessao,rid,**alteracao)["permitido"]
    assert sessao.get(RascunhoForm1Integral,rid).conteudo == antes
    assert sessao.scalar(select(func.count()).select_from(VersaoForm1Integral)) == 0


def test_idempotencia_e_reuso_de_chave(sessao):
    rid=preparar(sessao)["registro_id"]
    assert adotar(sessao,rid,versao_lida=2)["permitido"]
    assert adotar(sessao,rid,versao_lida=2)["reexecutado"]
    assert not adotar(sessao,rid,versao_lida=3)["permitido"]
    assert not adotar(sessao,rid,comando_id="GUARDA-JA-ADOTADA")["permitido"]
    assert sessao.scalar(select(func.count()).select_from(VersaoForm1Integral)) == 1


@pytest.mark.parametrize("respostas", [
    {"12.3.1":"Opção forjada"}, {"12.4.2":"Não","12.4.2.1":"Indevido"},
    {"12.5":"Sim","12.5.1":["Entre sistemas","Entre sistemas"]},
    {"12.5":"Sim","12.5.1":["Desconhecido"]},
    {"12.5":"Sim","12.5.1":"Entre sistemas"},
    {"12.5":"Sim","12.5.1":["Outra situação"],"12.5.1.1":"x"*201},
    {"12.5":"Não","12.5.2":"Destino indevido"}, {"12.3.99":"Sim"},
])
def test_entradas_invalidas_nao_persistem(sessao,respostas):
    rid=preparar(sessao)["registro_id"]
    assert adotar(sessao,rid)["permitido"]
    antes=deepcopy(sessao.get(RascunhoForm1Integral,rid).conteudo)
    assert not salvar(sessao,rid,respostas)["permitido"]
    assert sessao.get(RascunhoForm1Integral,rid).conteudo == antes


def test_aba_antiga_ou_sem_adocao_nao_muda_semantica(sessao):
    rid=preparar(sessao)["registro_id"]
    assert not salvar(sessao,rid,{"12.3.1":"Sim"},estrutura_lida=VERSAO_GUARDA)["permitido"]
    assert adotar(sessao,rid)["permitido"]
    for n,estrutura in enumerate((None,VERSAO_BASE,"FORJADA")):
        assert not salvar(sessao,rid,LEGADO,comando=f"GUARDA-ABA-{n}",estrutura_lida=estrutura)["permitido"]
    assert "12.3" not in sessao.get(RascunhoForm1Integral,rid).conteudo["respostas"]


def test_rollback_da_auditoria_desfaz_adocao_completa(sessao,monkeypatch):
    rid=preparar(sessao)["registro_id"]
    antes=deepcopy(sessao.get(RascunhoForm1Integral,rid).conteudo)
    def falhar(*args,**kwargs): raise RuntimeError("falha fictícia")
    monkeypatch.setattr("app.eventos.registrar_auditoria",falhar)
    with pytest.raises(RuntimeError,match="falha fictícia"):
        adotar_extensao_guarda(sessao,comando_id="GUARDA-RB",conta_id="CONTA-G1",registro_id=rid,versao_lida=2,confirmar=True)
    sessao.rollback()
    assert sessao.get(RascunhoForm1Integral,rid).conteudo == antes
    assert sessao.get(Comando,"GUARDA-RB") is None
    assert sessao.scalar(select(func.count()).select_from(VersaoForm1Integral)) == 0
    assert sessao.scalar(select(func.count()).select_from(Evento).where(Evento.comando_id=="GUARDA-RB")) == 0


def test_adocoes_concorrentes_nao_duplicam_snapshot(sessao):
    rid=preparar(sessao)["registro_id"]
    barreira=threading.Barrier(2)
    def executar(n):
        with Session(motor) as outra,outra.begin():
            barreira.wait(timeout=10)
            return adotar_extensao_guarda(outra,comando_id=f"GUARDA-CONC-{n}",conta_id="CONTA-G1",registro_id=rid,versao_lida=2,confirmar=True)
    with ThreadPoolExecutor(max_workers=2) as pool: resultados=list(pool.map(executar,(1,2)))
    assert sorted(r["permitido"] for r in resultados)==[False,True]
    assert sessao.scalar(select(func.count()).select_from(VersaoForm1Integral))==1


def test_snapshot_previo_consultavel_com_enunciados_originais(sessao):
    registro=preparar(sessao,medidas=True)
    rid=registro["registro_id"]
    assert _solicitar(sessao,registro,comando="GUARDA-S1",versao=4)["permitido"]
    snapshots=sessao.scalars(select(VersaoForm1Integral)).all()
    antes={s.id:(s.conteudo_canonico,s.lacre) for s in snapshots}
    assert adotar(sessao,rid)["permitido"]
    assert salvar(sessao,rid,NOVO)["permitido"]
    for snap in snapshots:
        sessao.refresh(snap)
        assert (snap.conteudo_canonico,snap.lacre)==antes[snap.id]
    pagina=cliente.get(f"/registros/{rid}/form1-integral/conferencia-interna?conta_id=CONTA-A1")
    assert pagina.status_code==200
    for campo_id in definicao_guarda()["ids_substituidos"]:
        assert campos_por_id()[campo_id].pergunta in pagina.text
    assert "Arquivo fictício" in pagina.text
    assert VERSAO_EXTENSAO in pagina.text
    assert VERSAO_COMBINADA not in pagina.text


def test_http_matriz_compacta_consulta_salvamento_e_navegacao(sessao):
    registro=preparar(sessao)
    rid=registro["registro_id"]
    url=f"/registros/{rid}"
    assert 'data-adotar-guarda' not in cliente.get(url+'?conta_id=CONTA-A1').text
    nao=cliente.post(url+'/form1-integral/bloco-12/adotar-extensao',data={
        'conta_id':'CONTA-G1','comando_id':'GUARDA-HTTP-NAO','versao_lida':'2'})
    assert nao.url.params['erro']=='1'
    pagina=cliente.post(url+'/form1-integral/bloco-12/adotar-extensao',data={
        'conta_id':'CONTA-G1','comando_id':'GUARDA-HTTP-SIM','versao_lida':'2','confirmar':'sim'})
    assert pagina.url.fragment=='titulo-bloco-12'
    assert pagina.text.count('class="operacao-guarda-form1"')==4
    assert 'name="campo__12.4.2.1"' in pagina.text
    for item in definicao_guarda()['campos']:
        campo_id=item['id']
        if item['controle']!='seleção múltipla (combo com marcações)':
            assert pagina.text.count(f'name="campo__{campo_id}"')==1
            assert f'aria-labelledby="rotulo-integral-{campo_id}"' in pagina.text
    dados={f'campo__{k}':v for k,v in NOVO.items()}
    resposta=cliente.post(url+'/form1-integral/bloco-12/salvar',data={
        **dados,'conta_id':'CONTA-G1','comando_id':'GUARDA-HTTP-S','versao_lida':'3',
        'estrutura_lida':VERSAO_GUARDA,'acao_pos_salvar':'proximo'})
    assert resposta.url.params['erro']=='0' and resposta.url.fragment=='titulo-bloco-13'
    recarga=cliente.get(url+'?conta_id=CONTA-G1')
    assert 'Livro de eliminação fictício' in recarga.text
    consulta=cliente.get(url+'?conta_id=CONTA-A1')
    assert 'name="campo__12.4.2.1"' not in consulta.text
    assert 'Livro de eliminação fictício' in consulta.text
    assert _solicitar(sessao,registro,comando='GUARDA-S2',versao=4)['permitido']
    snapshot=cliente.get(url+'/form1-integral/conferencia-interna?conta_id=CONTA-A1')
    assert VERSAO_GUARDA in snapshot.text
    assert catalogo_efetivo(conteudo_da_estrutura(VERSAO_GUARDA))['12.4.2'].pergunta in snapshot.text
    assert 'Arquivo fictício' in snapshot.text # Consulta de legado separado.
    assert cliente.get('/?conta_id=CONTA-G1').status_code==200
    assert cliente.get('/?conta_id=CONTA-A1').status_code==200


def test_salvar_11_13_14_preserva_extensao_e_submissao_bloqueada(sessao):
    registro=preparar(sessao,medidas=True)
    rid=registro['registro_id']
    assert adotar(sessao,rid)['permitido']
    assert salvar(sessao,rid,NOVO)['permitido']
    antes=deepcopy(sessao.get(RascunhoForm1Integral,rid).conteudo)
    for n,bloco in enumerate((11,13,14),start=6):
        dados={'conta_id':'CONTA-G1','comando_id':f'GUARDA-OUTRO-{bloco}','versao_lida':str(n),'acao_pos_salvar':'proximo'}
        if bloco==13:dados.update(estrutura_lida=VERSAO_COMBINADA,**{'campo__13.2':'Não','campo__13.2.1':'Sempre'})
        pagina=cliente.post(f'/registros/{rid}/form1-integral/bloco-{bloco}/salvar',data=dados)
        assert pagina.url.params['erro']=='0'
    sessao.expire_all()
    conteudo=sessao.get(RascunhoForm1Integral,rid).conteudo
    assert conteudo['extensao_guarda']==antes['extensao_guarda']
    for k,v in NOVO.items():assert conteudo['respostas'][k]==v
    assert not pre_validar_form1_integral(conteudo,nome_institucional='Servidor fictício')['submissao_habilitada']


def test_respostas_legadas_inativas_nao_sao_reinterpretadas(sessao):
    rid=preparar(sessao)['registro_id']
    assert salvar(sessao,rid,{'12.4':'Não','12.5':'Não'})['permitido']
    antes=deepcopy(sessao.get(RascunhoForm1Integral,rid).conteudo)
    assert adotar(sessao,rid)['permitido']
    conteudo=sessao.get(RascunhoForm1Integral,rid).conteudo
    for k in ('12.4.1','12.5.1'):
        assert k not in conteudo.get('respostas_inativas',{})
        item=next(i for i in conteudo['extensao_guarda']['legado']['campos'] if i['id']==k)
        assert item['respostas_inativas']==antes['respostas_inativas'][k]


def test_estilo_compacto_responsivo_sem_dependencia_de_cor():
    css=Path('app/estaticos/estilo.css').read_text(encoding='utf-8')
    assert 'grid-template-columns: repeat(3, minmax(0, 1fr))' in css
    assert '@media (max-width: 800px) { .grade-operacao-guarda { grid-template-columns: minmax(0, 1fr); } }' in css
    template=Path('app/paginas/_operacoes_guarda_form1.html').read_text(encoding='utf-8')
    assert '<fieldset' in template and '<legend>' in template
    assert 'required' not in template # Rascunhos incompletos continuam permitidos.


def test_javascript_adocao_e_condicionais_independentes():
    import shutil
    import subprocess
    node=shutil.which('node')
    if not node: pytest.skip('Node indisponível; aceitação visual permanece separada.')
    raiz=Path(__file__).resolve().parents[1]
    resultado=subprocess.run([node,str(raiz/'testes/apoio_extensao_guarda_form1.cjs')],cwd=raiz,capture_output=True,text=True)
    assert resultado.returncode==0,resultado.stdout+resultado.stderr
