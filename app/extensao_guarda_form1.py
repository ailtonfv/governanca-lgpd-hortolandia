"""Procedimentos, evidências e transferência: recorte optativo versionado."""
import json
from copy import deepcopy
from dataclasses import replace
from functools import lru_cache
from pathlib import Path

from app.form1_integral import CONDICOES_BLOCO_12

VERSAO_GUARDA = "F1-C3-REV13-EXT-GUARDA-v1"
VERSAO_COMBINADA = "F1-C3-REV13-EXT-MEDIDAS-GUARDA-v1"


@lru_cache(maxsize=1)
def definicao_guarda():
    return json.loads((Path(__file__).parent / "catalogos" /
                       "form1_rev13_ext_guarda_v1.json").read_text(encoding="utf-8"))


def usa_guarda(conteudo=None):
    versao = (conteudo or {}).get("extensao_guarda", {}).get("versao")
    if versao not in (None, VERSAO_GUARDA):
        raise ValueError("versão da extensão de guarda não reconhecida")
    return versao == VERSAO_GUARDA


def estender_catalogo_guarda(base, conteudo):
    if not usa_guarda(conteudo):
        return base
    resultado = {}
    definicao = definicao_guarda()
    for campo_id, campo in base.items():
        if campo_id == "12.3":
            for item in definicao["campos"]:
                resultado[item["id"]] = replace(
                    campo, id=item["id"], pergunta=item["pergunta"],
                    controle=item["controle"], alternativas=tuple(item["alternativas"]),
                    instrucao=item["instrucao"],
                )
        elif campo_id not in definicao["ids_substituidos"]:
            resultado[campo_id] = campo
    return resultado


def estender_matriz_guarda(base, conteudo):
    if not usa_guarda(conteudo):
        return base
    resultado = {}
    definicao = definicao_guarda()
    for campo_id, regra in base.items():
        if campo_id == "12.3":
            for item in definicao["campos"]:
                condicao = " e ".join(
                    f"{dep} = {' ou '.join(valores)}" for dep, valores in item["condicoes"]
                ) or "Sempre visível; resposta independente"
                resultado[item["id"]] = replace(
                    regra, campo_id=item["id"], classe=item["classe"],
                    condicao=condicao, observacao=definicao["observacao"],
                )
        elif campo_id not in definicao["ids_substituidos"]:
            resultado[campo_id] = regra
    return resultado


def condicoes_guarda(conteudo=None):
    if not usa_guarda(conteudo):
        return CONDICOES_BLOCO_12
    resultado = {k: v for k, v in CONDICOES_BLOCO_12.items()
                 if k not in definicao_guarda()["ids_substituidos"]}
    resultado.update({item["id"]: tuple((dep, tuple(valores)) for dep, valores in item["condicoes"])
                      for item in definicao_guarda()["campos"] if item["condicoes"]})
    return resultado


def incorporar_guarda(conteudo, rascunho, snapshot, pessoa_id, momento):
    from app.extensao_medidas_form1 import catalogo_efetivo, versao_estrutura
    catalogo = catalogo_efetivo(rascunho.conteudo)
    legado = {
        "versao_estrutura": versao_estrutura(rascunho.conteudo),
        "snapshot_id": snapshot.id, "numero_snapshot": snapshot.numero,
        "lacre_snapshot": snapshot.lacre, "versao_rascunho": rascunho.versao_rascunho,
        "rascunho_salvo_por": rascunho.salvo_por,
        "rascunho_salvo_em": rascunho.salvo_em.isoformat(), "campos": [],
    }
    for campo_id in definicao_guarda()["ids_substituidos"]:
        legado["campos"].append({
            "id": campo_id, "pergunta": catalogo[campo_id].pergunta,
            "resposta": conteudo.get("respostas", {}).pop(campo_id, None),
            "respostas_inativas": conteudo.get("respostas_inativas", {}).pop(campo_id, []),
        })
    conteudo["extensao_guarda"] = {
        "versao": VERSAO_GUARDA, "matriz": definicao_guarda()["matriz_id"],
        "adotada_por": pessoa_id, "papel": "ARP", "adotada_em": momento.isoformat(),
        "legado": legado,
    }


def adotar_extensao_guarda(sessao, *, comando_id, conta_id, registro_id,
                          versao_lida, confirmar=False, momento=None):
    from app.extensao_medidas_form1 import versao_estrutura
    from app.rascunho_form1_integral import (
        _agora_utc, _ator, _negar, _preparar_alteracao, _salvar_conteudo,
    )
    from app.submissao_form1_integral import preparar_snapshot_na_transacao
    from app.eventos import registrar_auditoria
    tipo = "adotar_extensao_guarda_form1_integral"
    parametros = dict(conta_id=conta_id, registro_id=registro_id,
                      versao_lida=versao_lida, confirmar=confirmar,
                      extensao=VERSAO_GUARDA)
    registro, pessoa_id, rascunho, comando, resposta = _preparar_alteracao(
        sessao, comando_id=comando_id, tipo_comando=tipo, conta_id=conta_id,
        registro_id=registro_id, versao_lida=versao_lida, parametros=parametros,
    )
    if resposta is not None:
        return resposta
    if confirmar is not True or usa_guarda(rascunho.conteudo):
        _, _, ator_tipo, ator_id = _ator(sessao, conta_id)
        return _negar(sessao, comando, ator_tipo, ator_id, conta_id, registro_id, tipo,
                      "confirme a adoção da extensão de guarda ainda não adotada")
    momento = momento or _agora_utc()
    snapshot, evento = preparar_snapshot_na_transacao(
        sessao, comando=comando, registro=registro, rascunho=rascunho,
        pessoa_id=pessoa_id, momento=momento, reusar_existente=True,
    )
    conteudo = deepcopy(rascunho.conteudo)
    incorporar_guarda(conteudo, rascunho, snapshot, pessoa_id, momento)
    resultado = _salvar_conteudo(
        sessao, comando=comando, registro=registro, rascunho=rascunho,
        pessoa_id=pessoa_id, versao_lida=versao_lida, conteudo=conteudo,
        tipo_evento=tipo, motivo="Extensão de guarda adotada; responda separadamente por operação",
        detalhes={"snapshot_anterior_id": snapshot.id, "papel": "ARP"},
        momento=momento, ordem_no_comando=2 if evento is not None else 1,
    )
    registrar_auditoria(
        sessao, "extensao_guarda_form1_adotada", comando.ator_tipo, comando.ator_id,
        {"registro_id": registro_id, "papel": "ARP", "versao_estrutura": versao_estrutura(conteudo),
         "snapshot_anterior_id": snapshot.id, "lacre_anterior": snapshot.lacre,
         "versao_rascunho": resultado["versao_rascunho"]}, comando_id=comando.id,
    )
    return resultado
