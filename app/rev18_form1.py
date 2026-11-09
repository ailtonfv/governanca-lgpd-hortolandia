"""Composição optativa REV18 do contrato candidato 3, sobre GUARDA e MEDIDAS."""
from copy import deepcopy
from dataclasses import replace

VERSAO_REV18 = "F1-C3-REV18-v1"
POLITICA_REV18 = "MATRIZ-F1-REV18-v1"
TITULO_BLOCO_14 = "Pendências e situações observadas"


def estender_catalogo(base):
    resultado = {}
    for chave, campo in base.items():
        if chave.startswith("14."):
            campo = replace(campo, bloco=f"BLOCO 14 — {TITULO_BLOCO_14.upper()}")
        if chave == "14.2.1":
            campo = replace(campo, pergunta="Em que momento do fluxo ocorre?")
        elif chave == "14.1":
            campo = replace(campo, instrucao="Consulte as pendências já listadas. Ao preencher este item, registre apenas informação adicional que ainda precise de confirmação.")
        resultado[chave] = campo
        if chave == "11.2.4":
            resultado["11.2.5"] = replace(
                campo, id="11.2.5", controle="seleção única (combo)",
                pergunta="Os dados ficam armazenados, são processados ou recebem suporte técnico fora do Brasil?",
                alternativas=("Sim", "Não", "Em alguns casos", "A confirmar"),
                instrucao="Registre somente o fato. A resposta não determina, por si só, a existência ou a licitude de transferência internacional de dados.",
            )
    return resultado


def estender_matriz(base):
    from app.pre_validacao_form1_integral import CLASSE_FACULTATIVA_PROPOSTA
    resultado = {}
    for chave, regra in base.items():
        resultado[chave] = regra
        if chave == "11.2.4":
            resultado["11.2.5"] = replace(
                regra, campo_id="11.2.5", classe=CLASSE_FACULTATIVA_PROPOSTA,
                condicao="Sempre visível", observacao="Levantamento factual sem exigência de resposta aprovada.",
            )
    return resultado


def adotar_rev18(sessao, *, comando_id, conta_id, registro_id, versao_lida, confirmar, momento=None):
    from app.extensao_guarda_form1 import incorporar_guarda, usa_guarda
    from app.extensao_medidas_form1 import incorporar_medidas, versao_estrutura, versao_medidas, VERSAO_BASE
    from app.rascunho_form1_integral import _agora_utc, _negar, _preparar_alteracao, _salvar_conteudo
    from app.submissao_form1_integral import preparar_snapshot_na_transacao
    from app.eventos import registrar_auditoria

    tipo = "adotar_rev18_form1_integral"
    parametros = dict(conta_id=conta_id, registro_id=registro_id, versao_lida=versao_lida,
                      confirmar=confirmar, versao_estrutura=VERSAO_REV18)
    registro, pessoa, rascunho, comando, resposta = _preparar_alteracao(
        sessao, comando_id=comando_id, tipo_comando=tipo, conta_id=conta_id,
        registro_id=registro_id, versao_lida=versao_lida, parametros=parametros,
    )
    if resposta is not None:
        return resposta
    anterior = versao_estrutura(rascunho.conteudo)
    if confirmar is not True or anterior == VERSAO_REV18:
        return _negar(sessao, comando, comando.ator_tipo, comando.ator_id, conta_id,
                      registro_id, tipo, "A adoção exige confirmação e um rascunho anterior à REV18.")
    momento = momento or _agora_utc()
    snapshot, evento = preparar_snapshot_na_transacao(
        sessao, comando=comando, registro=registro, rascunho=rascunho,
        pessoa_id=pessoa, momento=momento, reusar_existente=True,
    )
    conteudo = deepcopy(rascunho.conteudo)
    if not usa_guarda(conteudo):
        incorporar_guarda(conteudo, rascunho, snapshot, pessoa, momento)
    if versao_medidas(conteudo) == VERSAO_BASE:
        incorporar_medidas(conteudo, rascunho, snapshot, pessoa, momento)
    detalhes = {"versao_anterior_estrutura": anterior, "snapshot_anterior_id": snapshot.id,
                "lacre_anterior": snapshot.lacre, "papel": "ARP", "politica": POLITICA_REV18}
    conteudo["revisao_18"] = {**detalhes, "versao": VERSAO_REV18,
                              "adotada_por": pessoa, "adotada_em": momento.isoformat()}
    resultado = _salvar_conteudo(
        sessao, comando=comando, registro=registro, rascunho=rascunho, pessoa_id=pessoa,
        versao_lida=versao_lida, conteudo=conteudo, tipo_evento=tipo,
        motivo="REV18 adotada no rascunho", detalhes=detalhes, momento=momento,
        ordem_no_comando=2 if evento is not None else 1,
    )
    registrar_auditoria(sessao, tipo, comando.ator_tipo, comando.ator_id,
                        {**detalhes, "registro_id": registro_id, "versao_estrutura": VERSAO_REV18,
                         "versao_rascunho": resultado["versao_rascunho"]}, comando_id=comando.id)
    return resultado
