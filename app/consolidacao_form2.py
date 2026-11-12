"""Conferência demonstrativa versionada; não encerra nem homologa o FORM 2."""
from copy import deepcopy
import json
import re
from sqlalchemy import select
from app.modelos import ParticipacaoForm2, ComplementoForm2, Registro, Evento
from app.fila_form2 import pessoa_ativa, autorizado, agora, evento
from app.comandos import abrir_comando, fechar_comando
from app.eventos import lacre
from app.respostas_form2 import estados_regua_form2, definicao_revisao
from app.form2_rev212 import RASCUNHO, indice_valores, aplicavel, conjunto_da_chave, mapa_regras, ramos_origem
from app.contrato_form2_respostas import carregar_contrato

CHAVE = "consolidacao_demonstrativa_v1"


def _principal(sessao, conta_id, participacao_id, bloquear=False):
    pessoa = pessoa_ativa(sessao, conta_id)
    if bloquear:
        from app.segregacao_form2_v9 import bloquear_registro
        bloquear_registro(sessao, sessao.get(ParticipacaoForm2, participacao_id))
    consulta = select(ParticipacaoForm2).where(ParticipacaoForm2.id == participacao_id)
    if bloquear:
        consulta = consulta.with_for_update().execution_options(populate_existing=True)
    p = sessao.scalar(consulta)
    if (not p or p.tipo != "principal" or p.responsavel_id != pessoa.id
            or not autorizado(sessao, pessoa, p)):
        raise PermissionError("Somente o AAL responsável acessa a consolidação desta participação.")
    return pessoa, p


def _fontes(sessao, p, bloquear=False):
    from app.origem_form2 import ler_origem
    from app.governanca_form2_v9 import estado
    origem = ler_origem(sessao, p.registro_id, p.snapshot_id)
    conteudo = deepcopy(p.conteudo or {})
    conteudo.pop(CHAVE, None)
    consulta = select(ParticipacaoForm2).where(
        ParticipacaoForm2.origem_id == p.id).order_by(ParticipacaoForm2.id)
    if bloquear:
        consulta = consulta.with_for_update().execution_options(populate_existing=True)
    consultas = sessao.scalars(consulta).all()
    complementos = sessao.scalars(select(ComplementoForm2).where(
        ComplementoForm2.participacao_id == p.id).order_by(ComplementoForm2.id)).all()
    return {
        "registro_id": p.registro_id, "snapshot_id": p.snapshot_id,
        "lacre_origem": origem["snapshot"].lacre,
        "ramos_origem": sorted(ramos_origem(origem)), "regras": mapa_regras(carregar_contrato()),
        "responsavel_id": p.responsavel_id, "estado": p.estado,
        "conteudo": conteudo, "manifestacao_principal": p.manifestacao,
        "governanca_v9": estado(sessao, p),
        "alternativas_bloco14": {q["id"]: {a["codigo"]: a["rotulo"] for a in q["alternativas"]}
            for q in definicao_revisao(14)["itens"]},
        "consultas": [{"id": c.id, "tipo": c.tipo, "unidade_id": c.unidade_id,
            "snapshot_id": c.snapshot_id, "contexto_form2": c.conteudo or {},
            "responsavel_id": c.responsavel_id, "estado": c.estado, "versao": c.versao,
            "questao": c.questao, "manifestacao": c.manifestacao,
            "concluida_em": c.concluida_em.isoformat() if c.concluida_em else None}
            for c in consultas],
        "complementos": [{"id": c.id, "estado": c.estado, "solicitacao": c.solicitacao,
            "snapshot_origem_id": c.snapshot_origem_id,
            "snapshot_resposta_id": c.snapshot_resposta_id} for c in complementos],
    }


def _hash(fontes):
    return lacre(json.dumps(fontes, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def montar_resumo(fontes):
    """Sinais observáveis, sem inventar obrigatoriedade ou classificação impeditiva."""
    conteudo = deepcopy(fontes["conteudo"])
    valores = indice_valores(conteudo)
    for campos in conteudo.get(RASCUNHO, {}).values():
        for chave in list(campos):
            if chave.startswith(("opcao:", "texto:", "principal:")):
                item = chave.partition(":")[2].partition("#")[0]
                if not aplicavel(item, conjunto_da_chave(chave), valores,
                                 fontes.get("ramos_origem", []), fontes.get("regras", {})):
                    campos.pop(chave)
    estados = estados_regua_form2(conteudo)
    confirmar = set()
    for item, valor in conteudo.get("respostas_etapa1", {}).items():
        if "A_CONFIRMAR" in (valor if isinstance(valor, list) else [valor]):
            confirmar.add(item)
    for campos in conteudo.get(RASCUNHO, {}).values():
        for chave, valor in campos.items():
            if chave.startswith("opcao:") and "A_CONFIRMAR" in valor:
                confirmar.add(chave.removeprefix("opcao:"))
    campos14 = conteudo.get(RASCUNHO, {}).get("14", {})
    rotulos = fontes.get("alternativas_bloco14", {})
    def escolhas(item, conjunto=""):
        return [rotulos.get(item, {}).get(c, c) for c in campos14.get("opcao:" + item + conjunto, [])]
    pendencias_declaradas = []
    for chave, texto in campos14.items():
        if chave.startswith("texto:F2-14.2#") and texto.strip():
            conjunto = chave.partition("#")[2]
            sufixo = "#" + conjunto
            principal = campos14.get("principal:F2-14.3.1" + sufixo, "")
            pendencias_declaradas.append({"conjunto": conjunto, "texto": texto,
                "area": campos14.get("texto:F2-14.3" + sufixo, ""),
                "destinos": escolhas("F2-14.3.1", sufixo),
                "principal": rotulos.get("F2-14.3.1", {}).get(principal, principal)})
    pendencias_declaradas.sort(key=lambda p: int(p["conjunto"]))
    return {
        "governanca_v9": fontes.get("governanca_v9", {}),
        "reavaliacoes_pendentes": [i for i in fontes.get("governanca_v9", {}).get("impactos", {}).values()
            if i["estado"] in {"pendente", "complemento_necessario"}],
        "resultado_candidato": escolhas("F2-14.1"),
        "resultado_complemento": campos14.get("texto:F2-14.1", ""),
        "blocos_com_respostas": sorted(estados["salvos"], key=int),
        "blocos_sem_respostas": [str(n) for n in range(1, 15) if str(n) not in estados["salvos"]],
        "itens_a_confirmar": sorted(confirmar),
        "links_a_confirmar": [{"item": item, "bloco": int(re.match(r"F2-(\d+)", item)[1]),
            "ancora": item.partition("#")[0]} for item in sorted(confirmar)],
        "pendencias_declaradas": pendencias_declaradas,
        "encaminhamentos": [{"form": n, "resposta": escolhas(item),
            "justificativa": campos14.get("texto:" + item + ".1", "")}
            for n, item in [(3, "F2-14.5"), (4, "F2-14.6")]],
        "consultas_abertas": [c for c in fontes["consultas"] if c["estado"] != "concluida"],
        "consultas_concluidas": [c for c in fontes["consultas"] if c["estado"] == "concluida"],
        "complementos": fontes["complementos"],
        "conclusao_institucional_habilitada": False,
        "limites": ["Homologação jurídica D11 pendente.",
            "Obrigatoriedade para concluir e classificação de pendências impeditivas dependem de deliberação institucional.",
            "Encaminhamentos aos FORMs 3 e 4 ainda não são executados por esta conferência."],
    }


def consultar(sessao, *, conta_id, participacao_id):
    pessoa, p = _principal(sessao, conta_id, participacao_id)
    fontes = _fontes(sessao, p)
    ultima = (p.conteudo or {}).get(CHAVE)
    historico = sessao.scalars(select(Evento).where(
        Evento.cadeia_tipo == "participacao_form2", Evento.cadeia_id == p.id,
        Evento.tipo_evento == "form2_consolidacao_registrada"
    ).order_by(Evento.sequencia_cadeia.desc())).all()
    return {"p": p, "pessoa": pessoa, "resumo": montar_resumo(fontes),
        "hash_fontes": _hash(fontes), "ultima": ultima,
        "desatualizada": bool(ultima and ultima["hash_fontes"] != _hash(fontes)),
        "historico": [e.conteudo["conteudo"][CHAVE] for e in historico]}


def registrar(sessao, *, conta_id, comando_id, participacao_id, versao, hash_fontes, sintese):
    pessoa, p = _principal(sessao, conta_id, participacao_id, bloquear=True)
    comando, repeticao = abrir_comando(sessao, comando_id, "consolidar_form2_demonstrativo",
        dict(conta_id=conta_id, participacao_id=participacao_id, versao=versao,
             hash_fontes=hash_fontes, sintese=sintese), "pessoa", pessoa.id, conta_id)
    if repeticao is not None:
        return repeticao
    if p.estado != "em_atendimento" or sessao.get(Registro, p.registro_id).estado_atual != "em_andamento":
        raise ValueError("A conferência exige participação e registro em atendimento.")
    if p.versao != versao:
        raise ValueError("A participação mudou. Atualize a conferência antes de registrar.")
    if not isinstance(sintese, str) or not sintese.strip() or len(sintese) > 10000 or "\x00" in sintese:
        raise ValueError("Informe a síntese da conferência em até 10000 caracteres.")
    fontes = _fontes(sessao, p, bloquear=True)
    if _hash(fontes) != hash_fontes:
        raise ValueError("Respostas ou manifestações mudaram. Atualize a conferência antes de registrar.")
    anterior = (p.conteudo or {}).get(CHAVE, {})
    retrato = {"numero": anterior.get("numero", 0) + 1, "em": agora().isoformat(),
        "ator_id": pessoa.id, "sintese": sintese.strip(), "hash_fontes": _hash(fontes),
        "fontes": fontes, "resumo": montar_resumo(fontes),
        "natureza": "conferencia_demonstrativa_sem_homologacao"}
    novo = deepcopy(p.conteudo or {})
    novo[CHAVE] = retrato
    p.conteudo = novo
    p.versao += 1
    evento(sessao, comando, p, "form2_consolidacao_registrada")
    return fechar_comando(comando, {"permitido": True, "numero": retrato["numero"],
        "participacao_id": p.id, "conclusao_institucional": False})
