"""GOV_FORMS_REV18_03: adoção, salvamento e leitura histórica no mesmo Registro."""
import re
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.eventos import verificar_cadeia, lacre
from app.extensao_guarda_form1 import adotar_extensao_guarda, VERSAO_COMBINADA, VERSAO_GUARDA
from app.extensao_medidas_form1 import (
    adotar_extensao_medidas, catalogo_efetivo, conteudo_da_estrutura,
    matriz_efetiva, versao_estrutura, VERSAO_BASE, VERSAO_EXTENSAO,
)
from app.main import app
from app.modelos import Comando, EventoAuditoria, RascunhoForm1Integral, VersaoForm1Integral
from app.origem_form2 import ler_origem
from app.pre_validacao_form1_integral import pre_validar_form1_integral
from app.rascunho_form1_integral import (
    salvar_bloco_12_form1_integral, salvar_bloco_13_form1_integral, salvar_bloco_14_form1_integral,
)
from app.rev18_form1 import adotar_rev18, POLITICA_REV18, VERSAO_REV18
from testes.test_conferencia_interna_form1_integral_8ac import _preparar, _solicitar

cliente = TestClient(app)
ARP = "CONTA-G1"
APA = "CONTA-A1"


def test_perfis_catalogo_matriz_e_politica_consultiva():
    esperados = list(catalogo_efetivo(conteudo_da_estrutura(VERSAO_COMBINADA)))
    esperados.insert(esperados.index("11.3"), "11.2.5")
    novo = conteudo_da_estrutura(VERSAO_REV18)
    catalogo = catalogo_efetivo(novo)
    assert len(esperados) == 141 and list(catalogo) == esperados
    assert list(matriz_efetiva(novo)) == esperados
    assert catalogo["11.2.5"].alternativas == ("Sim", "Não", "Em alguns casos", "A confirmar")
    for perfil, total in [(VERSAO_BASE, 128), (VERSAO_EXTENSAO, 129), (VERSAO_GUARDA, 139), (VERSAO_COMBINADA, 140)]:
        antigo = catalogo_efetivo(conteudo_da_estrutura(perfil))
        assert len(antigo) == total and "11.2.5" not in antigo
        assert antigo["14.2.1"].pergunta == "Em que etapa ocorre?"
        assert antigo["14.2.1"].alternativas == catalogo["14.2.1"].alternativas
        for chave in ("14.1", "14.2", "14.2.2"):
            assert antigo[chave].pergunta == catalogo[chave].pergunta
    assert catalogo["14.2.1"].pergunta == "Em que momento do fluxo ocorre?"
    pre = pre_validar_form1_integral({**novo, "respostas": {"11.2.5": "A confirmar"}},
                                    nome_institucional="Servidor fictício")
    assert pre["versao_politica"] == POLITICA_REV18 and not pre["submissao_habilitada"]
    assert {"0.2", "0.3", "11.2.5"}.isdisjoint(i.get("campo_id") for i in pre["incompletos"] + pre["regras_pendentes"])
    assert "11.2.5" in {i["campo_id"] for i in pre["avisos"]}
    for incompleta in ({**novo, "extensao_guarda": {}},
                       {**novo, "revisao_18": {"versao": VERSAO_REV18, "politica": "desconhecida"}}):
        with pytest.raises(ValueError, match="composição REV18"):
            catalogo_efetivo(incompleta)


@pytest.mark.parametrize("perfil", [VERSAO_BASE, VERSAO_EXTENSAO, VERSAO_GUARDA, VERSAO_COMBINADA])
def test_adocao_de_cada_perfil_preserva_origem_autoria_e_repeticao(sessao, perfil):
    registro = _preparar(sessao, "REV18")
    rid = registro["registro_id"]
    rascunho = sessao.get(RascunhoForm1Integral, rid)
    assert salvar_bloco_14_form1_integral(
        sessao, comando_id="R18-B14", conta_id=ARP, registro_id=rid, versao_lida=1,
        respostas={"14.2": "Sim", "14.2.1": "Entrada", "14.2.2": "Fato fictício"},
    )["permitido"]
    for versoes, adotar in [((VERSAO_GUARDA, VERSAO_COMBINADA), adotar_extensao_guarda),
                            ((VERSAO_EXTENSAO, VERSAO_COMBINADA), adotar_extensao_medidas)]:
        if perfil in versoes:
            assert adotar(sessao, comando_id=adotar.__name__, conta_id=ARP, registro_id=rid,
                          versao_lida=rascunho.versao_rascunho, confirmar=True)["permitido"]
    destino = ["Entre sistemas"] if perfil in (VERSAO_GUARDA, VERSAO_COMBINADA) else "Arquivo fictício"
    assert salvar_bloco_12_form1_integral(
        sessao, comando_id="R18-GUARDA", conta_id=ARP, registro_id=rid, versao_lida=rascunho.versao_rascunho,
        estrutura_lida=perfil, respostas={"12.5": "Sim", "12.5.1": destino},
    )["permitido"]
    medidas = {"13.2": "Sempre"}
    if perfil in (VERSAO_EXTENSAO, VERSAO_COMBINADA):
        medidas["13.2.1"] = "Não"
    assert salvar_bloco_13_form1_integral(
        sessao, comando_id="R18-MEDIDAS", conta_id=ARP, registro_id=rid, versao_lida=rascunho.versao_rascunho,
        estrutura_lida=perfil, respostas=medidas,
    )["permitido"]
    sessao.commit()
    antes = deepcopy(rascunho.conteudo)
    assert versao_estrutura(antes) == perfil
    dados = dict(comando_id="REV18-ADOTAR", registro_id=rid, conta_id=ARP,
                 versao_lida=rascunho.versao_rascunho, confirmar=True)
    assert adotar_rev18(sessao, **dados)["permitido"]
    sessao.commit()
    assert adotar_rev18(sessao, **dados)["reexecutado"]
    atual = rascunho.conteudo
    assert versao_estrutura(atual) == VERSAO_REV18
    esperadas = dict(antes["respostas"])
    if "extensao_guarda" not in antes:
        esperadas.pop("12.5")
        esperadas.pop("12.5.1")
        legado = atual["extensao_guarda"]["legado"]["campos"]
        assert next(i for i in legado if i["id"] == "12.5.1")["resposta"] == destino
    if "extensao_medidas" not in antes:
        esperadas.pop("13.2")
        assert atual["extensao_medidas"]["legado"]["resposta"] == "Sempre"
    assert atual["respostas"] == esperadas
    for nome in ("extensao_medidas", "extensao_guarda"):
        if nome in antes:
            assert atual[nome] == antes[nome]
        else:
            assert atual[nome]["legado"]["versao_estrutura"] == perfil
    anterior = sessao.get(VersaoForm1Integral, atual["revisao_18"]["snapshot_anterior_id"])
    assert anterior.conteudo["form1_integral"] == antes
    assert anterior.lacre == lacre(anterior.conteudo_canonico)
    perguntas = ler_origem(sessao, rid, anterior.id)["perguntas"]
    assert next(i for i in perguntas if i["id"] == "14.2.1")["pergunta"] == "Em que etapa ocorre?"
    auditoria = sessao.scalars(select(EventoAuditoria).where(EventoAuditoria.comando_id == dados["comando_id"])).one()
    assert auditoria.conteudo["papel"] == "ARP" and auditoria.conteudo["lacre_anterior"] == anterior.lacre
    assert atual["revisao_18"]["adotada_por"] == "PESSOA-G"
    assert verificar_cadeia(sessao, registro["codigo_lgpd"])[0]


def test_bloco11_http_adocao_navegacao_recarga_e_conferencia(sessao):
    registro = _preparar(sessao, "R18-HTTP")
    rid = registro["registro_id"]
    url = f"/registros/{rid}"
    adocao = url + "/form1-integral/adotar-rev18"
    pagina = cliente.get(url, params={"conta_id": ARP})
    assert 'data-adotar-rev18' in pagina.text and 'name="campo__11.2.5"' not in pagina.text
    assert 'data-adotar-rev18' not in cliente.get(url, params={"conta_id": APA}).text
    dados = dict(conta_id=ARP, versao_lida=1, confirmar="sim")
    for indice, ajustes in enumerate([{"conta_id": APA}, {"confirmar": ""}, {"versao_lida": 2}]):
        ret = cliente.post(adocao, data={**dados, **ajustes, "comando_id": f"R18-NEG-{indice}"})
        assert ret.url.params["erro"] == "1"
    assert not sessao.scalars(select(VersaoForm1Integral)).all()
    pagina = cliente.post(adocao, data={**dados, "comando_id": "R18-ADOCAO"})
    assert pagina.url.fragment == "titulo-bloco-11" and pagina.url.params["erro"] == "0"
    assert "Pendências e situações observadas" in pagina.text
    assert 'data-adotar-rev18' not in pagina.text
    controle = r'<div class="campo-integral"\s*>\s*<div id="rotulo-integral-11\.2\.5"'
    assert re.search(controle, pagina.text)
    salvar = url + "/form1-integral/bloco-11/salvar"
    dados = {"conta_id": ARP, "estrutura_lida": VERSAO_REV18, "acao_pos_salvar": "proximo"}
    versao = 2
    for indice, op in enumerate((None, "Infraestrutura da Prefeitura", "Infraestrutura de terceiro", "Ambas", "A confirmar")):
        resposta = ("A confirmar", "Sim", "Não", "Em alguns casos", "Sim")[indice]
        post = {**dados, "versao_lida": versao, "comando_id": f"R18-S-{indice}", "campo__11.2.5": resposta}
        if op:
            post["campo__11.2"] = op
        pagina = cliente.post(salvar, data=post)
        assert pagina.url.params["erro"] == "0" and pagina.url.fragment == "titulo-bloco-12"
        recarga = cliente.get(url, params={"conta_id": ARP}).text
        assert re.search(controle, recarga)
        seletor = recarga.split('name="campo__11.2.5"', 1)[1].split("</select>", 1)[0]
        assert f'value="{resposta}" selected' in seletor
        versao += 1
    for indice, ajuste in enumerate([{"estrutura_lida": VERSAO_BASE}, {"campo__11.2.5": "Inválida"},
                                      {"conta_id": APA}]):
        negada = cliente.post(salvar, data={**post, "versao_lida": versao, **ajuste, "comando_id": f"R18-F-{indice}"})
        assert negada.url.params["erro"] == "1"
    sessao.expire_all()
    assert sessao.get(RascunhoForm1Integral, rid).versao_rascunho == versao
    assert _solicitar(sessao, registro, comando="R18-CONF", versao=versao)["permitido"]
    snapshot = cliente.get(url + "/form1-integral/conferencia-interna", params={"conta_id": APA})
    assert VERSAO_REV18 in snapshot.text and catalogo_efetivo(conteudo_da_estrutura(VERSAO_REV18))["11.2.5"].pergunta in snapshot.text
    consulta = cliente.get(url, params={"conta_id": APA}).text
    assert 'name="campo__11.2.5"' not in consulta


def test_falha_auditoria_reverte_adocao_e_snapshot(sessao, monkeypatch):
    registro = _preparar(sessao, "REV18-RB")
    rid = registro["registro_id"]
    antes = deepcopy(sessao.get(RascunhoForm1Integral, rid).conteudo)

    def falhar(*args, **kwargs):
        raise RuntimeError("falha fictícia de auditoria")

    monkeypatch.setattr("app.eventos.registrar_auditoria", falhar)
    with pytest.raises(RuntimeError, match="falha fictícia"):
        adotar_rev18(sessao, comando_id="R18-RB", conta_id=ARP, registro_id=rid, versao_lida=1, confirmar=True)
    sessao.rollback()
    assert sessao.get(RascunhoForm1Integral, rid).conteudo == antes
    assert sessao.get(Comando, "R18-RB") is None
    assert not sessao.scalars(select(VersaoForm1Integral)).all()
