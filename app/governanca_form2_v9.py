"""Contrato demonstrativo REV22 v9. Projeção aditiva; eventos preservam cada revisão.

Todas as mutações são serializadas pela participação principal. Não há migração
destrutiva nem mudança dos snapshots do FORM 1 ou das manifestações anteriores.
"""
from copy import deepcopy
from datetime import datetime, timezone, date
from uuid import uuid4
from sqlalchemy import select
from app.modelos import (ParticipacaoForm2, ComplementoForm2, Registro, Unidade,
    VersaoForm1Integral, HistoricoConferenciaForm1Integral, AtribuicaoForm1Integral)
from app.comandos import abrir_comando, fechar_comando

CHAVE = "governanca_v9"


def agora():
    """Ponto de injeção do relógio nos testes; nunca aceito da requisição web."""
    return datetime.now(timezone.utc)


def instante():
    return agora().isoformat()


def texto(valor, limite=2000):
    if not isinstance(valor, str) or not valor.strip() or len(valor) > limite or "\x00" in valor:
        raise ValueError(f"Informe texto de 1 a {limite} caracteres.")
    return valor.strip()


def estado(sessao, p):
    """Leitura compatível do legado, sem escrever durante GET nem fracionar texto."""
    g = deepcopy((p.conteudo or {}).get(CHAVE, {}))
    g.setdefault("pendencias", {})
    g.setdefault("retornos", {})
    g.setdefault("impactos", {})
    g.setdefault("fontes", [])
    legado = sessao.scalar(select(ComplementoForm2).where(ComplementoForm2.participacao_id == p.id))
    if legado and legado.id not in g["pendencias"]:
        g["pendencias"][legado.id] = {
            "id": legado.id, "texto": legado.solicitacao, "estado": legado.estado,
            "origens": [{"item": "F2-1.3.1#1", "snapshot_id": legado.snapshot_origem_id}],
            "solicitantes": {p.id: legado.estado}, "snapshot_resposta_id": legado.snapshot_resposta_id,
            "criada_em": legado.criada_em.isoformat(), "unidade_id": None,
            "area": "", "destinos": [], "principal": "", "prazo": None,
            "historico": [{"ato": "leitura_legado_preservado"}], "legado": True}
    return g


def guardar(p, g):
    novo = deepcopy(p.conteudo or {})
    novo[CHAVE] = g
    p.conteudo = novo


def registrar(pend, ato, pessoa_id, **dados):
    pend.setdefault("historico", []).append(dict(ato=ato, em=instante(), ator=pessoa_id, **dados))


def nova(g, p, referencia, descricao, pessoa_id):
    ident = str(uuid4())
    g["pendencias"][ident] = dict(id=ident, texto=descricao, estado="aberta",
        origens=[dict(item=referencia, snapshot_id=p.snapshot_id)],
        solicitantes={p.id: "aberta"}, criada_em=instante(), unidade_id=None,
        area="", destinos=[], principal="", prazo=None, historico=[])
    registrar(g["pendencias"][ident], "abertura", pessoa_id)
    return g["pendencias"][ident]


def sincronizar(sessao, p, novo, bloco, pessoa_id):
    """Salvamento não encerra pendências nem confunde texto igual com mesma necessidade."""
    g = estado(sessao, p)
    entradas = []
    if bloco == 1:
        valor = novo.get("respostas_etapa1", {}).get("F2-1.3.1")
        if valor:
            entradas.append(("F2-1.3.1#1", valor, None))
    if bloco == 14:
        from app.form2_rev212 import RASCUNHO
        campos = novo.get(RASCUNHO, {}).get("14", {})
        for chave, valor in campos.items():
            if chave.startswith("texto:F2-14.2#") and valor.strip():
                sufixo = "#" + chave.partition("#")[2]
                entradas.append((chave.removeprefix("texto:"), texto(valor, 300), {
                    "area": campos.get("texto:F2-14.3"+sufixo, ""),
                    "destinos": campos.get("opcao:F2-14.3.1"+sufixo, []),
                    "principal": campos.get("principal:F2-14.3.1"+sufixo, "")}))
    # Apenas respostas ativas do bloco salvo; comentário e resposta oculta não abrem solicitação.
    from app.form2_rev212 import RASCUNHO
    for item, valor in novo.get("respostas_etapa1", {}).items():
        if item.startswith(f"F2-{bloco}.") and "A_CONFIRMAR" in (valor if isinstance(valor, list) else [valor]):
            entradas.append((item, "Confirmar informação registrada em " + item, None))
    for chave, valor in novo.get(RASCUNHO, {}).get(str(bloco), {}).items():
        if chave.startswith("opcao:") and "A_CONFIRMAR" in valor:
            ref = chave.removeprefix("opcao:")
            entradas.append((ref, "Confirmar informação registrada em " + ref, None))
    for ref, descricao, metadados in entradas:
        pend = next((d for d in g["pendencias"].values()
                     if d["estado"] != "vinculada" and any(o["item"] == ref for o in d["origens"])), None)
        if not pend:
            pend = nova(g, p, ref, descricao, pessoa_id)
        elif pend["origens"][0]["item"] == ref and pend["texto"] != descricao:
            registrar(pend, "revisao_solicitacao", pessoa_id, anterior=pend["texto"])
            pend["texto"] = descricao
            pend["estado"] = "aberta"
            pend["solicitantes"] = {s: "aberta" for s in pend["solicitantes"]}
            pend.pop("snapshot_resposta_id", None)
        if metadados and pend["origens"][0]["item"] == ref and any(pend.get(k) != v for k, v in metadados.items()):
            registrar(pend, "destinacao_editorial", pessoa_id, anterior={k: pend.get(k) for k in metadados})
            pend.update(metadados)
    novo[CHAVE] = g


def origem_autorizada(sessao, pessoa, p):
    from app.fila_form2 import unidades
    from app.continuidade_apa import pessoa_e_apa_em_exercicio
    r = sessao.get(Registro, p.registro_id)
    a = sessao.get(AtribuicaoForm1Integral, r.id)
    return pessoa_e_apa_em_exercicio(sessao, pessoa.id, r.unidade_principal_atual_id) or (
        a and a.arp_atual_id == pessoa.id and r.unidade_principal_atual_id in unidades(sessao, pessoa.id, "preenchedor"))


def marcar_impactos(sessao, p, g, snapshot_id):
    for c in sessao.scalars(select(ParticipacaoForm2).where(ParticipacaoForm2.origem_id == p.id)):
        if c.snapshot_id != snapshot_id:
            chave = snapshot_id + ":" + c.id
            g["impactos"].setdefault(chave, dict(participacao_id=c.id, snapshot_id=snapshot_id,
                estado="pendente", historico=[]))
    g["impactos"].setdefault(snapshot_id+":propria", dict(participacao_id=p.id,
        snapshot_id=snapshot_id, estado="pendente", historico=[]))


def receber_confirmacao(sessao, p, snapshot_id, comando):
    """Confirmar S2 informa disponibilidade, não responde nem troca a fonte ativa."""
    from app.fila_form2 import evento
    if snapshot_id == p.snapshot_id:
        return
    g = estado(sessao, p)
    if snapshot_id not in g["retornos"]:
        g["retornos"][snapshot_id] = dict(estado="confirmada_disponivel", em=instante())
        guardar(p, g)
        p.versao += 1
        evento(sessao, comando, p, "form2_nova_origem_disponivel")


def executar(sessao, *, conta_id, comando_id, participacao_id, versao, acao,
             pendencia_id=None, dados=None):
    from app.fila_form2 import pessoa_ativa, autorizado, evento
    pessoa = pessoa_ativa(sessao, conta_id)
    # Ordem de locks: principal -> participação. Também usada pelas manifestações.
    alvo = sessao.get(ParticipacaoForm2, participacao_id)
    if not alvo:
        raise ValueError("Participação inexistente.")
    from app.segregacao_form2_v9 import bloquear_registro
    bloquear_registro(sessao, alvo)
    principal_id = alvo.origem_id or alvo.id
    p = sessao.scalar(select(ParticipacaoForm2).where(ParticipacaoForm2.id == principal_id)
        .with_for_update().execution_options(populate_existing=True))
    if alvo.id == p.id:
        alvo = p
    else:
        alvo = sessao.scalar(select(ParticipacaoForm2).where(ParticipacaoForm2.id == alvo.id)
            .with_for_update().execution_options(populate_existing=True))
    dados = dados or {}
    e_aal = autorizado(sessao, pessoa, p) and p.responsavel_id == pessoa.id
    e_participante = autorizado(sessao, pessoa, alvo) and alvo.responsavel_id == pessoa.id
    e_origem = origem_autorizada(sessao, pessoa, p)
    if acao == "responder":
        permitido = e_origem
    elif acao in {"aceitar", "rejeitar"}:
        permitido = e_participante
    else:
        permitido = e_aal and alvo.id == p.id
    if not permitido:
        raise PermissionError("A operação não pertence ao seu papel nesta participação.")
    comando, repeticao = abrir_comando(sessao, comando_id, "governanca_v9_"+acao,
        dict(conta_id=conta_id, participacao_id=participacao_id, versao=versao,
             acao=acao, pendencia_id=pendencia_id, dados=dados), "pessoa", pessoa.id, conta_id)
    if repeticao is not None:
        return repeticao
    if p.versao != versao:
        raise ValueError("O processo mudou. Atualize a página antes de agir.")
    if p.estado != "em_atendimento" or sessao.get(Registro, p.registro_id).estado_atual != "em_andamento":
        raise ValueError("A operação exige atendimento em andamento.")
    g = estado(sessao, p)
    pend = g["pendencias"].get(pendencia_id)
    if acao in {"destinar", "responder", "aceitar", "rejeitar", "retirar", "vincular", "solicitante"} and not pend:
        raise ValueError("Pendência inexistente neste processo.")
    motivo = texto(dados.get("motivo", ""))
    if acao == "adicionar":
        r = (p.conteudo or {}).get("respostas_etapa1", {})
        if not (r.get("F2-1.2") == "DIVERGENTE" or r.get("F2-1.3") in {"NAO", "PARCIAL"}):
            raise ValueError("F2-1.3.1 depende de divergência ou insuficiência da origem.")
        n = 1 + max([0] + [int(o["item"].split("#")[1]) for d in g["pendencias"].values()
            for o in d["origens"] if o["item"].startswith("F2-1.3.1#")])
        pend = nova(g, p, f"F2-1.3.1#{n}", texto(dados.get("descricao"), 200), pessoa.id)
        pendencia_id = pend["id"]
    elif acao == "destinar":
        unidade = sessao.get(Unidade, dados.get("unidade_id"))
        if not unidade or not unidade.ativa:
            raise ValueError("Escolha uma unidade ativa para o retorno.")
        prazo = dados.get("prazo") or None
        if prazo:
            try:
                date.fromisoformat(prazo)
            except (ValueError, TypeError):
                raise ValueError("Prazo inválido; use uma data ou deixe sem definição.")
        pend.update(unidade_id=unidade.id, prazo=prazo, area=unidade.nome,
            finalidade_retorno=texto(dados.get("finalidade", motivo)),
            destinos=[unidade.id], principal=unidade.id)
    elif acao == "vincular":
        ref = texto(dados.get("referencia"), 80)
        if ref.startswith("F1-"):
            snap = sessao.get(VersaoForm1Integral, p.snapshot_id)
            chave = ref.removeprefix("F1-")
            origem = snap.conteudo.get("form1_integral", snap.conteudo)
            if chave not in origem.get("respostas", {}):
                raise ValueError("A referência não existe na versão de origem consultada.")
            vinculo = dict(item=ref, snapshot_id=p.snapshot_id)
            if vinculo not in pend["origens"]:
                pend["origens"].append(vinculo)
        else:
            outra = g["pendencias"].get(ref)
            if not outra or outra is pend or outra["estado"] not in {"aberta", "respondida"} or pend["estado"] not in {"aberta", "respondida"}:
                raise ValueError("Escolha outra pendência ativa deste processo.")
            for o in outra["origens"]:
                if o not in pend["origens"]:
                    pend["origens"].append(o)
            pend["solicitantes"].update(outra["solicitantes"])
            outra["estado"] = "vinculada"
            outra["vinculada_a"] = pend["id"]
            registrar(outra, "vinculada", pessoa.id, destino=pend["id"], motivo=motivo)
    elif acao == "solicitante":
        participante = sessao.get(ParticipacaoForm2, dados.get("solicitante_id"))
        if not participante or participante.origem_id != p.id or participante.estado == "concluida":
            raise ValueError("Selecione uma participação aberta deste processo.")
        if pend["estado"] not in {"aberta", "respondida"}:
            raise ValueError("Vínculo exige pendência ativa.")
        pend["solicitantes"].setdefault(participante.id, pend["estado"])
    elif acao == "responder":
        sid = dados.get("snapshot_id")
        snap = sessao.get(VersaoForm1Integral, sid)
        antigo = sessao.get(VersaoForm1Integral, pend["origens"][0]["snapshot_id"])
        confirmado = sessao.scalar(select(HistoricoConferenciaForm1Integral).where(
            HistoricoConferenciaForm1Integral.registro_id == p.registro_id,
            HistoricoConferenciaForm1Integral.snapshot_id == sid,
            HistoricoConferenciaForm1Integral.situacao == "conferencia_interna_confirmada"))
        if not confirmado or not snap or snap.registro_id != p.registro_id or snap.numero <= antigo.numero or pend["estado"] != "aberta":
            raise ValueError("A resposta exige nova versão do mesmo FORM 1 confirmada pelo APA.")
        if not any(o["item"].startswith("F2-1.3.1") for o in pend["origens"]):
            raise PermissionError("O retorno da origem exige solicitação de complementação vinculada em F2-1.3.1.")
        pend.update(snapshot_resposta_id=sid, estado="respondida")
        pend["solicitantes"] = {s: "respondida" for s in pend["solicitantes"]}
        g["retornos"][sid] = dict(estado="retornada", em=instante(), pessoa_id=pessoa.id)
        marcar_impactos(sessao, p, g, sid)
    elif acao in {"aceitar", "rejeitar"}:
        h = sessao.scalar(select(HistoricoConferenciaForm1Integral).where(
            HistoricoConferenciaForm1Integral.snapshot_id == pend.get("snapshot_resposta_id")))
        if h and pessoa.id in {h.solicitada_por_id, h.confirmada_por_id}:
            raise PermissionError("Designação pendente por impedimento: apresentante ou confirmador da resposta não pode validá-la.")
        if alvo.id not in pend["solicitantes"] or pend["solicitantes"][alvo.id] != "respondida":
            raise ValueError("Esta participação não tem resposta aguardando conferência.")
        pend["solicitantes"][alvo.id] = "resolvida" if acao == "aceitar" else "aberta"
        estados = set(pend["solicitantes"].values())
        pend["estado"] = "resolvida" if estados == {"resolvida"} else "aberta" if "aberta" in estados else "respondida"
    elif acao == "retirar":
        if pend["estado"] not in {"aberta", "respondida"}:
            raise ValueError("A retirada exige pendência ativa.")
        pend["estado"] = "retirada"
    elif acao == "fonte":
        sid = dados.get("snapshot_id")
        ultima = sessao.scalar(select(VersaoForm1Integral).where(VersaoForm1Integral.registro_id == p.registro_id)
            .order_by(VersaoForm1Integral.numero.desc()).limit(1))
        if not ultima or ultima.id != sid or g["retornos"].get(sid, {}).get("estado") != "retornada":
            raise ValueError("Use a versão mais recente do FORM 1, confirmada e devolvida pela origem.")
        if not any(d.get("snapshot_resposta_id") == sid and d["estado"] == "resolvida" for d in g["pendencias"].values()):
            raise ValueError("Confira e aceite a resposta antes de usar a nova versão na análise.")
        h = sessao.scalar(select(HistoricoConferenciaForm1Integral).where(HistoricoConferenciaForm1Integral.snapshot_id == sid))
        if pessoa.id in {h.solicitada_por_id, h.confirmada_por_id}:
            raise PermissionError("Quem apresentou ou confirmou esta versão do FORM 1 não pode validá-la. Solicite outro responsável.")
        g["fontes"].append(dict(anterior=p.snapshot_id, nova=sid, motivo=motivo, em=instante(), ator=pessoa.id))
        p.snapshot_id = sid
        marcar_impactos(sessao, p, g, sid)
    elif acao == "manter_fonte":
        sid = dados.get("snapshot_id")
        if not any(d.get("snapshot_resposta_id") == sid and d["estado"] == "resolvida" for d in g["pendencias"].values()):
            raise ValueError("Aceite a resposta antes de decidir continuar usando a versão atual.")
        g["fontes"].append(dict(anterior=p.snapshot_id, nova=p.snapshot_id, resposta_sid=sid,
            motivo=motivo, em=instante(), ator=pessoa.id, decisao="manter_fonte"))
    elif acao == "impacto":
        chave = dados.get("impacto_id")
        impacto = g["impactos"].get(chave)
        if not impacto or (impacto["snapshot_id"] != p.snapshot_id and not any(
                f.get("resposta_sid") == impacto["snapshot_id"] and f.get("decisao") == "manter_fonte" for f in g["fontes"])):
            raise ValueError("Defina a versão do FORM 1 usada na análise antes de conferir as manifestações afetadas.")
        decisao = dados.get("decisao")
        if decisao not in {"nao_afetada", "complemento_necessario", "reavaliada"}:
            raise ValueError("Decisão de impacto inválida.")
        if impacto["participacao_id"] != p.id and decisao == "reavaliada":
            raise ValueError("O AAL não substitui a manifestação da área competente.")
        if decisao == "complemento_necessario":
            anterior = sessao.get(ParticipacaoForm2, impacto["participacao_id"])
            if anterior.id == p.id:
                raise ValueError("Reavalie as respostas próprias nos blocos antes de confirmar.")
            if impacto.get("suplemento_id"):
                raise ValueError("Já existe solicitação de complemento para esta manifestação.")
            filho = ParticipacaoForm2(id=str(uuid4()), registro_id=p.registro_id, snapshot_id=p.snapshot_id,
                unidade_id=anterior.unidade_id, origem_id=p.id, tipo=anterior.tipo, estado="aguardando",
                entrada_em=datetime.now(timezone.utc), versao=1, questao=motivo, manifestacao="",
                conteudo={"reavalia_manifestacao_id": anterior.id, "contexto_form2": {
                    k: deepcopy(v) for k, v in (p.conteudo or {}).items()
                    if k not in {CHAVE, "consolidacao_demonstrativa_v1"}}})
            sessao.add(filho)
            sessao.flush()
            impacto["suplemento_id"] = filho.id
            if filho.tipo == "dpo":
                from app.fila_form2 import aviso
                aviso(sessao, filho, "manifestacao")
            evento(sessao, comando, filho, "form2_complemento_manifestacao", ordem=19)
        impacto["estado"] = decisao
        registrar(impacto, "avaliacao_impacto", pessoa.id, motivo=motivo, decisao=decisao)
    else:
        raise ValueError("Operação desconhecida.")
    if pend:
        registrar(pend, acao, pessoa.id, motivo=motivo, dados=dados)
    guardar(p, g)
    p.versao += 1
    evento(sessao, comando, p, "form2_v9_"+acao)
    return fechar_comando(comando, dict(permitido=True, participacao_id=p.id, pendencia_id=pendencia_id, versao=p.versao))


def resumo(sessao, p):
    g = estado(sessao, p)
    hoje = agora().date()
    for d in g["pendencias"].values():
        d["destinacao"] = d.get("area") or "Destinação pendente"
        d["dias_em_aberto"] = max(0, (hoje-datetime.fromisoformat(d["criada_em"]).date()).days)
        d["prazo_rotulo"] = d.get("prazo") or "Prazo não definido"
        d["atrasada"] = bool(d.get("prazo") and date.fromisoformat(d["prazo"]) < hoje and d["estado"] in {"aberta", "respondida"})
        d["escalonamento"] = "Escalonamento não configurado"
    return g
