"""Extensão optativa do contrato candidato 3; nunca reinterpreta a REV13."""

import json
from copy import deepcopy
from dataclasses import replace
from functools import lru_cache
from pathlib import Path

from app.form1_integral import campos_por_id
from app import rev18_form1

VERSAO_BASE = "F1-C3-REV13"
VERSAO_EXTENSAO = "F1-C3-REV13-EXT-MEDIDAS-v1"
IDS_BLOCO_13_EXTENSAO = ("13.1", "13.2", "13.2.1", "13.3", "13.4")


@lru_cache(maxsize=1)
def definicao_extensao():
    return json.loads((Path(__file__).parent / "catalogos" /
                       "form1_rev13_ext_medidas_v1.json").read_text(encoding="utf-8"))


def versao_medidas(conteudo=None):
    versao = (conteudo or {}).get("extensao_medidas", {}).get("versao", VERSAO_BASE)
    if versao not in (VERSAO_BASE, VERSAO_EXTENSAO):
        raise ValueError("versão da extensão de medidas não reconhecida")
    return versao


def versao_estrutura(conteudo=None):
    from app.extensao_guarda_form1 import usa_guarda, VERSAO_GUARDA, VERSAO_COMBINADA
    medidas = versao_medidas(conteudo)
    guarda = usa_guarda(conteudo)
    if "revisao_18" in (conteudo or {}):
        revisao = conteudo["revisao_18"]
        if (not isinstance(revisao, dict)
                or revisao.get("versao") != rev18_form1.VERSAO_REV18
                or revisao.get("politica") != rev18_form1.POLITICA_REV18
                or not guarda or medidas != VERSAO_EXTENSAO):
            raise ValueError("composição REV18 não reconhecida")
        return rev18_form1.VERSAO_REV18
    if guarda:
        return VERSAO_COMBINADA if medidas == VERSAO_EXTENSAO else VERSAO_GUARDA
    return medidas


def conteudo_da_estrutura(versao):
    """Interpreta o perfil declarado; o domínio ainda confere o perfil persistido."""
    from app.extensao_guarda_form1 import VERSAO_GUARDA, VERSAO_COMBINADA
    if versao == rev18_form1.VERSAO_REV18:
        return {**conteudo_da_estrutura(VERSAO_COMBINADA),
                "revisao_18": {"versao": versao, "politica": rev18_form1.POLITICA_REV18}}
    if versao not in (VERSAO_BASE, VERSAO_EXTENSAO, VERSAO_GUARDA, VERSAO_COMBINADA):
        raise ValueError("versão da estrutura não reconhecida")
    conteudo = {}
    if versao in (VERSAO_EXTENSAO, VERSAO_COMBINADA):
        conteudo["extensao_medidas"] = {"versao": VERSAO_EXTENSAO}
    if versao in (VERSAO_GUARDA, VERSAO_COMBINADA):
        conteudo["extensao_guarda"] = {"versao": VERSAO_GUARDA}
    return conteudo


def catalogo_efetivo(conteudo=None):
    base = campos_por_id()
    from app.extensao_guarda_form1 import estender_catalogo_guarda
    estrutura = versao_estrutura(conteudo)
    if versao_medidas(conteudo) == VERSAO_BASE:
        return estender_catalogo_guarda(base, conteudo)
    definicao = definicao_extensao()
    resultado = {}
    for campo_id, campo in base.items():
        if campo_id != "13.2":
            resultado[campo_id] = campo
            continue
        for item in definicao["campos"]:
            resultado[item["id"]] = replace(
                campo, id=item["id"], pergunta=item["pergunta"],
                alternativas=tuple(definicao["alternativas"]), instrucao="",
            )
    resultado = estender_catalogo_guarda(resultado, conteudo)
    return rev18_form1.estender_catalogo(resultado) if estrutura == rev18_form1.VERSAO_REV18 else resultado


def matriz_efetiva(conteudo=None):
    # Importação local evita ciclo; a matriz REV13 original permanece intacta.
    from app.pre_validacao_form1_integral import carregar_matriz_obrigatoriedade
    base = carregar_matriz_obrigatoriedade()
    from app.extensao_guarda_form1 import estender_matriz_guarda
    estrutura = versao_estrutura(conteudo)
    if versao_medidas(conteudo) == VERSAO_BASE:
        return estender_matriz_guarda(base, conteudo)
    resultado = {}
    for campo_id, regra in base.items():
        if campo_id != "13.2":
            resultado[campo_id] = regra
            continue
        for item in definicao_extensao()["campos"]:
            resultado[item["id"]] = replace(
                regra, campo_id=item["id"], classe=item["classe"],
                condicao=item["condicao"], observacao=definicao_extensao()["observacao"],
            )
    resultado = estender_matriz_guarda(resultado, conteudo)
    return rev18_form1.estender_matriz(resultado) if estrutura == rev18_form1.VERSAO_REV18 else resultado


def incorporar_medidas(conteudo, rascunho, snapshot, pessoa_id, momento):
    estrutura_anterior = versao_estrutura(rascunho.conteudo)
    anterior = conteudo.get("respostas", {}).pop("13.2", None)
    conteudo["extensao_medidas"] = {
        "versao": VERSAO_EXTENSAO,
        "matriz": definicao_extensao()["matriz_id"],
        "adotada_por": pessoa_id, "papel": "ARP", "adotada_em": momento.isoformat(),
        "legado": {
            "versao_estrutura": estrutura_anterior,
            "campo_id": "13.2", "pergunta": campos_por_id()["13.2"].pergunta,
            "resposta": anterior, "snapshot_id": snapshot.id,
            "numero_snapshot": snapshot.numero, "lacre_snapshot": snapshot.lacre,
            "versao_rascunho": rascunho.versao_rascunho,
            "rascunho_salvo_por": rascunho.salvo_por,
            "rascunho_salvo_em": rascunho.salvo_em.isoformat(),
        },
    }


def adotar_extensao_medidas(sessao, *, comando_id, conta_id, registro_id,
                           versao_lida, confirmar=False, momento=None):
    """Adoção explícita, snapshot anterior e novo rascunho na mesma transação."""
    from app.rascunho_form1_integral import (
        _agora_utc, _ator, _negar, _preparar_alteracao, _salvar_conteudo,
    )
    from app.submissao_form1_integral import preparar_snapshot_na_transacao
    from app.eventos import registrar_auditoria
    tipo = "adotar_extensao_medidas_form1_integral"
    parametros = dict(conta_id=conta_id, registro_id=registro_id,
                      versao_lida=versao_lida, confirmar=confirmar,
                      versao_estrutura=VERSAO_EXTENSAO)
    registro, pessoa_id, rascunho, comando, resposta = _preparar_alteracao(
        sessao, comando_id=comando_id, tipo_comando=tipo, conta_id=conta_id,
        registro_id=registro_id, versao_lida=versao_lida, parametros=parametros,
    )
    if resposta is not None:
        return resposta
    problema = None
    if confirmar is not True:
        problema = "confirme expressamente a adoção da extensão antes de continuar"
    elif versao_medidas(rascunho.conteudo) != VERSAO_BASE:
        problema = "a extensão de medidas já foi adotada neste rascunho"
    if problema:
        _, _, ator_tipo, ator_id = _ator(sessao, conta_id)
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id,
                      registro_id, tipo, problema)
    momento = momento or _agora_utc()
    snapshot, evento = preparar_snapshot_na_transacao(
        sessao, comando=comando, registro=registro, rascunho=rascunho,
        pessoa_id=pessoa_id, momento=momento, reusar_existente=True,
    )
    conteudo = deepcopy(rascunho.conteudo)
    incorporar_medidas(conteudo, rascunho, snapshot, pessoa_id, momento)
    resultado = _salvar_conteudo(
        sessao, comando=comando, registro=registro, rascunho=rascunho,
        pessoa_id=pessoa_id, versao_lida=versao_lida, conteudo=conteudo,
        tipo_evento=tipo, motivo="Extensão adotada; responda separadamente 13.2 e 13.2.1",
        detalhes={"snapshot_anterior_id": snapshot.id, "papel": "ARP"},
        momento=momento, ordem_no_comando=2 if evento is not None else 1,
    )
    registrar_auditoria(
        sessao, "extensao_medidas_form1_adotada", comando.ator_tipo, comando.ator_id,
        {"registro_id": registro_id, "papel": "ARP", "versao_estrutura": versao_estrutura(conteudo),
         "snapshot_anterior_id": snapshot.id, "lacre_anterior": snapshot.lacre,
         "versao_rascunho": resultado["versao_rascunho"]}, comando_id=comando.id,
    )
    return resultado
