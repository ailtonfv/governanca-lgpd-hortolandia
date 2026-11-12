"""Interface de filas institucionais demonstrativas."""
from pathlib import Path
from hashlib import sha256
from uuid import uuid4
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, inspect
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import (ParticipacaoForm2, Registro, Unidade, ComplementoForm2,
    AtribuicaoForm1Integral, HistoricoConferenciaForm1Integral, Pessoa)
from app.fila_form2 import painel, pessoa_ativa, autorizado, executar, importar_confirmada, agora, unidades as unidades_autorizadas
from app.continuidade_apa import pessoa_e_apa_em_exercicio
from app.respostas_form2 import estados_regua_form2

router = APIRouter()
paginas = Jinja2Templates(directory=Path(__file__).parent / "paginas")
paginas.env.filters["chave_comando"] = lambda valor: sha256(str(valor).encode("utf-8")).hexdigest()


def contexto_atuacao(sessao, pessoa, participacao):
    """Identificação visível; não concede permissões."""
    assumida = participacao.responsavel_id == pessoa.id and autorizado(sessao, pessoa, participacao)
    rotulos = {"principal": "AAL — Agente de Análise de Legitimidade",
        "tematica": "AAL — Agente de Análise de Legitimidade",
        "juridico": "Responsável pela manifestação do Jurídico",
        "dpo": "DPO — Encarregado de proteção de dados"}
    return {"servidor": pessoa.nome,
        "funcao": rotulos.get(participacao.tipo) if assumida else None,
        "unidade": sessao.get(Unidade, participacao.unidade_id).nome if assumida else None,
        "editavel": assumida and participacao.estado == "em_atendimento"}


@router.api_route("/registros/{registro_id}/unidade-retorno", methods=["GET", "POST"])
async def unidade_retorno(request: Request, registro_id: str):
    from app.unidade_retorno_institucional import consultar, registrar
    dados = await request.form() if request.method == "POST" else request.query_params
    conta = str(dados.get("conta_id", ""))
    with Session(motor) as s:
        pessoa = pessoa_ativa(s, conta)
        r = s.get(Registro, registro_id)
        if not r:
            raise HTTPException(404, "Registro inexistente.")
        e_apa = pessoa_e_apa_em_exercicio(s,pessoa.id,r.unidade_principal_atual_id)
        p = s.scalar(select(ParticipacaoForm2).where(ParticipacaoForm2.registro_id == registro_id,
            ParticipacaoForm2.tipo == "principal", ParticipacaoForm2.responsavel_id == pessoa.id,
            ParticipacaoForm2.estado == "em_atendimento").limit(1))
        e_aal = bool(p and autorizado(s,pessoa,p))
        if not (e_apa or e_aal):
            raise HTTPException(403, "Somente o APA ou o AAL responsável acessa esta definição.")
        if request.method == "POST":
            try:
                resultado = registrar(s,conta_id=conta,comando_id=dados.get("comando_id"),registro_id=registro_id,
                    versao=int(dados.get("versao",0)),acao=dados.get("acao"),unidade_id=dados.get("unidade_id"),
                    canal=dados.get("canal"),motivo=dados.get("motivo",""))
                if not resultado["permitido"]:
                    raise ValueError(resultado.get("motivo"))
                s.commit()
            except (ValueError,PermissionError) as e:
                s.rollback()
                raise HTTPException(409,str(e))
            return RedirectResponse(f"/registros/{registro_id}/unidade-retorno?"+urlencode({"conta_id":conta}),status_code=303)
        return paginas.TemplateResponse(request=request,name="unidade_retorno_institucional.html",context={
            "r":r,"conta_id":conta,"e_apa":e_apa,"e_aal":e_aal,"atual":consultar(s,registro_id),
            "unidades":s.scalars(select(Unidade).where(Unidade.ativa.is_(True))).all(),"comando_id":str(uuid4())})


@router.get("/form2/participacoes/{participacao_id}/governanca", name="governanca_form2")
def governanca(request: Request, participacao_id: str, conta_id: str):
    from app.governanca_form2_v9 import resumo, origem_autorizada
    from app.modelos import VersaoForm1Integral
    with Session(motor) as sessao:
        pessoa = pessoa_ativa(sessao, conta_id)
        alvo = sessao.get(ParticipacaoForm2, participacao_id)
        if not alvo:
            raise HTTPException(404, "Participação inexistente.")
        p = sessao.get(ParticipacaoForm2, alvo.origem_id or alvo.id)
        e_aal = autorizado(sessao, pessoa, p) and p.responsavel_id == pessoa.id
        e_origem = origem_autorizada(sessao, pessoa, p)
        e_participante = autorizado(sessao, pessoa, alvo) and alvo.responsavel_id == pessoa.id
        if not (e_aal or e_origem or e_participante):
            raise HTTPException(403, "Retorno fora do seu escopo.")
        g = resumo(sessao, p)
        pendencias = [d for d in g["pendencias"].values() if d["estado"] != "vinculada"]
        if not e_aal:
            pendencias = [d for d in pendencias if (e_origem and any(o["item"].startswith("F2-1.3.1") for o in d["origens"]))
                or (e_participante and alvo.id in d["solicitantes"])]
        versoes = sessao.execute(select(VersaoForm1Integral.id, VersaoForm1Integral.numero,
                HistoricoConferenciaForm1Integral.solicitada_em,
                HistoricoConferenciaForm1Integral.solicitada_por_id,
                HistoricoConferenciaForm1Integral.confirmada_em)
            .join(HistoricoConferenciaForm1Integral, HistoricoConferenciaForm1Integral.snapshot_id == VersaoForm1Integral.id)
            .where(VersaoForm1Integral.registro_id == p.registro_id,
                HistoricoConferenciaForm1Integral.situacao == "conferencia_interna_confirmada")
            .order_by(VersaoForm1Integral.numero.desc())).all()
        from types import SimpleNamespace
        versoes = [SimpleNamespace(id=v.id, numero=v.numero,
            rotulo="Apresentado por " + (sessao.get(Pessoa, v.solicitada_por_id).nome) +
                " em " + v.solicitada_em.astimezone(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y às %H:%M:%S") +
                " · confirmado pelo APA" +
                (" em " + v.confirmada_em.astimezone(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y às %H:%M:%S") if v.confirmada_em else ""))
            for v in versoes]
        for d in pendencias:
            origem_pedido = sessao.get(VersaoForm1Integral, d["origens"][0]["snapshot_id"])
            d["versoes_resposta"] = [v for v in versoes
                if origem_pedido and v.numero > origem_pedido.numero]
            envio = next((h for h in reversed(d.get("historico", []))
                if h.get("ato") == "responder" and
                h.get("dados", {}).get("snapshot_id") == d.get("snapshot_resposta_id")), None)
            d["resposta_recebida"] = None
            if envio:
                autor = sessao.get(Pessoa, envio.get("ator"))
                d["resposta_recebida"] = {"autor": autor.nome if autor else "Origem do FORM 1",
                    "texto": envio.get("motivo", ""),
                    "apresentacao": next((v.rotulo for v in versoes if v.id == d.get("snapshot_resposta_id")), "")}
            d["form1_confirmado"] = None
            if e_aal and d.get("snapshot_resposta_id") in {v.id for v in versoes}:
                from app.origem_form2 import ler_origem
                d["form1_confirmado"] = ler_origem(sessao, p.registro_id, d["snapshot_resposta_id"])
        numero_atual = next((v.numero for v in versoes if v.id == p.snapshot_id), 0)
        novas_versoes = [v for v in versoes if v.numero > numero_atual]
        versoes_aceitas = [v for v in novas_versoes if any(
            d.get("snapshot_resposta_id") == v.id and d["estado"] == "resolvida"
            for d in pendencias)]
        from app.unidade_retorno_institucional import consultar as consultar_retorno
        retorno_institucional = consultar_retorno(sessao, p.registro_id)
        comparacao = []
        if e_aal:
            from app.origem_form2 import ler_origem
            for v in versoes:
                consulta = ler_origem(sessao, p.registro_id, v.id)
                comparacao.append({"numero": v.numero, "ativa": v.id == p.snapshot_id,
                    "perguntas": [q for q in consulta["perguntas"] if q["respondida"]]})
        from app.eventos import registrar_auditoria
        registrar_auditoria(sessao, "consulta_governanca_form2_v9", "pessoa", pessoa.id,
            {"participacao_id": alvo.id, "finalidade": "resposta ou conferência de pendências no escopo autorizado"})
        sessao.commit()
        return paginas.TemplateResponse(request=request, name="governanca_form2_v9.html", context={
            "p": p, "alvo": alvo, "registro": sessao.get(Registro, p.registro_id), "conta_id": conta_id,
            "e_aal": e_aal, "e_origem": e_origem, "e_participante": e_participante,
            "atuacao": contexto_atuacao(sessao, pessoa, alvo),
            "pendencias": pendencias, "g": g if e_aal else {}, "versoes": versoes,
            "comparacao": comparacao, "novas_versoes": novas_versoes,
            "versoes_aceitas": versoes_aceitas,
            "tem_retorno_institucional": retorno_institucional.get("canal") in {"OUV", "ESIC"},
            "solicitantes": sessao.scalars(select(ParticipacaoForm2).where(
                ParticipacaoForm2.origem_id == p.id, ParticipacaoForm2.estado != "concluida")).all() if e_aal else [],
            "unidades": sessao.scalars(select(Unidade).where(Unidade.ativa.is_(True))).all(),
            "comando_id": str(uuid4())})


@router.post("/form2/participacoes/{participacao_id}/governanca")
async def agir_governanca(request: Request, participacao_id: str):
    from app.governanca_form2_v9 import executar as executar_v9
    dados = await request.form()
    conta = str(dados.get("conta_id", ""))
    with Session(motor) as sessao:
        try:
            campos = {k: str(v) for k, v in dados.items()
                if k not in {"conta_id", "comando_id", "versao", "acao", "pendencia_id"}}
            resultado = executar_v9(sessao, conta_id=conta, comando_id=dados.get("comando_id"),
                participacao_id=participacao_id, versao=int(dados.get("versao", 0)),
                acao=dados.get("acao"), pendencia_id=dados.get("pendencia_id"), dados=campos)
            if not resultado["permitido"]:
                raise ValueError(resultado.get("motivo"))
            sessao.commit()
        except (PermissionError, ValueError) as erro:
            sessao.rollback()
            return paginas.TemplateResponse(request=request, name="erro_governanca_form2.html", context={
                "erro": str(erro), "participacao_id": participacao_id, "conta_id": conta,
                "motivo": dados.get("motivo", ""), "descricao": dados.get("descricao", "")},
                status_code=403 if isinstance(erro, PermissionError) else 409)
    return RedirectResponse(f"/form2/participacoes/{participacao_id}/governanca?"+urlencode({"conta_id": conta}), status_code=303)


def sessao_fila():
    with Session(motor) as sessao:
        if not inspect(sessao.connection()).has_table("participacao_form2"):
            raise HTTPException(503, "Instale a migração de filas do FORM 2.")
        yield sessao


@router.get("/form2/participacoes/{participacao_id}/consolidacao", name="consolidacao_fila_form2")
def consolidacao_fila(request: Request, participacao_id: str, conta_id: str,
                     sessao: Session = Depends(sessao_fila)):
    from app.consolidacao_form2 import consultar
    from app.eventos import registrar_auditoria
    try:
        contexto = consultar(sessao, conta_id=conta_id, participacao_id=participacao_id)
    except PermissionError as erro:
        raise HTTPException(403, str(erro))
    registrar_auditoria(sessao, "consulta_consolidacao_form2", "pessoa", contexto["pessoa"].id,
        {"participacao_id": participacao_id, "finalidade": "conferência pelo AAL responsável"})
    sessao.commit()
    contexto.update(conta_id=conta_id, comando_id=str(uuid4()),
        registro=sessao.get(Registro, contexto["p"].registro_id),
        estados_regua=estados_regua_form2(contexto["p"].conteudo or {}),
        unidades={u.id: u.nome for u in sessao.scalars(select(Unidade))},
        agentes={a.id: a.nome for a in sessao.scalars(select(Pessoa))})
    return paginas.TemplateResponse(request=request, name="consolidacao_fila_form2.html", context=contexto)


@router.post("/form2/participacoes/{participacao_id}/consolidacao")
async def registrar_consolidacao_fila(request: Request, participacao_id: str,
                                     sessao: Session = Depends(sessao_fila)):
    from app.consolidacao_form2 import registrar
    dados = await request.form()
    conta_id = str(dados.get("conta_id", ""))
    try:
        resultado = registrar(sessao, conta_id=conta_id, participacao_id=participacao_id,
            comando_id=dados.get("comando_id"), versao=int(dados.get("versao", 0)),
            hash_fontes=dados.get("hash_fontes", ""), sintese=dados.get("sintese", ""))
        if not resultado["permitido"]:
            raise ValueError(resultado.get("motivo"))
        sessao.commit()
    except (PermissionError, ValueError) as erro:
        sessao.rollback()
        return paginas.TemplateResponse(request=request, name="erro_consolidacao_form2.html",
            context={"conta_id": conta_id, "participacao_id": participacao_id, "erro": str(erro),
                     "sintese": dados.get("sintese", "")},
            status_code=403 if isinstance(erro, PermissionError) else 409)
    return RedirectResponse(str(request.url_for("consolidacao_fila_form2",
        participacao_id=participacao_id))+"?"+urlencode({"conta_id": conta_id}), status_code=303)


@router.get("/form2/filas", name="filas_form2")
def filas(request: Request, conta_id: str, sessao: Session = Depends(sessao_fila)):
    try:
        pessoa, participacoes, principais, dpo = painel(sessao, conta_id)
    except PermissionError as erro:
        raise HTTPException(403, str(erro))
    registros = {r.id: r for r in sessao.scalars(select(Registro))}
    unidades = {u.id: u for u in sessao.scalars(select(Unidade))}
    linhas = []
    for p in principais:
        consultas = sessao.scalars(select(ParticipacaoForm2).where(
            ParticipacaoForm2.origem_id == p.id, ParticipacaoForm2.tipo == "dpo",
            ParticipacaoForm2.estado != "concluida")).all()
        linhas.append({"p": p, "registro": registros[p.registro_id],
            "secretaria": unidades[registros[p.registro_id].unidade_principal_atual_id].nome,
            "fila": unidades[p.unidade_id].nome,
            "espera": round(((p.assumida_em or agora())-p.entrada_em).total_seconds()/3600, 1),
            "dpo": round(max(((agora()-q.entrada_em).total_seconds()/3600 for q in consultas), default=0), 1),
            "situacao": "Aguardando manifestação" if consultas else "Para ciência"})
    cobertura = [{"nome": u.nome, "total": sum(registros[p.registro_id].unidade_principal_atual_id == u.id for p in principais)}
        for u in unidades.values() if u.ativa] if dpo else []
    from app.governanca_form2_v9 import estado as estado_v9, origem_autorizada
    from app.segregacao_form2_v9 import impedido
    complementos = []
    impedimentos = {}
    for participacao in sessao.scalars(select(ParticipacaoForm2)):
        if participacao.responsavel_id and impedido(sessao, participacao.responsavel_id, participacao):
            impedimentos[participacao.id] = "Designação pendente por impedimento"
        if participacao.tipo != "principal":
            continue
        registro = registros[participacao.registro_id]
        e_origem = origem_autorizada(sessao, pessoa, participacao)
        e_aal = participacao.responsavel_id == pessoa.id and autorizado(sessao, pessoa, participacao)
        if (e_origem or e_aal) and estado_v9(sessao, participacao)["pendencias"]:
            pendencias = [d for d in estado_v9(sessao, participacao)["pendencias"].values()
                if any(o["item"].startswith("F2-1.3.1") for o in d["origens"])]
            estados = {d["estado"] for d in pendencias}
            situacao = ("definir unidade responsável pela resposta" if any(d["estado"] == "aberta" and not d.get("unidade_id") for d in pendencias) else
                "aguardando resposta" if "aberta" in estados else
                "resposta recebida, aguardando conferência" if "respondida" in estados else
                "consulte o histórico")
            complementos.append(dict(p=participacao, registro=registro,
                situacao=situacao if pendencias else None))
    for l in linhas:
        if l["p"].id in impedimentos:
            l["situacao"] = impedimentos[l["p"].id]
    gestores = unidades_autorizadas(sessao, pessoa.id, "gestor_fila")
    gerenciaveis = sessao.scalars(select(ParticipacaoForm2).where(
        ParticipacaoForm2.unidade_id.in_(gestores),
        ParticipacaoForm2.estado != "concluida")).all() if gestores else []
    agentes = sessao.scalars(select(Pessoa).where(Pessoa.ativa.is_(True))).all() if gestores else []
    cartoes = {}
    for p in participacoes:
        cartoes.setdefault(p.registro_id, dict(registro=registros[p.registro_id],
            participacoes=[], complementos=[]))["participacoes"].append(p)
    for c in complementos:
        cartoes.setdefault(c["registro"].id, dict(registro=c["registro"],
            participacoes=[], complementos=[]))["complementos"].append(c)
    pode_encaminhar = any(pessoa_e_apa_em_exercicio(sessao, pessoa.id, u.id)
        for u in unidades.values() if u.ativa)
    return paginas.TemplateResponse(request=request, name="filas_form2.html",
        context={"cartoes": list(cartoes.values()), "pode_encaminhar": pode_encaminhar,
                 "conta_id": conta_id, "pessoa": pessoa, "participacoes": participacoes,
                 "registros": registros, "unidades": unidades, "linhas": linhas,
                 "impedimentos": impedimentos, "complementos": complementos, "gerenciaveis": gerenciaveis, "agentes": agentes,
                 "dpo": dpo, "cobertura": cobertura, "comando_id": str(uuid4())})


@router.get("/form2/participacoes/{participacao_id}", name="participacao_form2")
def participacao(request: Request, participacao_id: str, conta_id: str,
                  sessao: Session = Depends(sessao_fila)):
    try:
        pessoa = pessoa_ativa(sessao, conta_id)
        p = sessao.get(ParticipacaoForm2, participacao_id)
        if not p or not autorizado(sessao, pessoa, p) or (p.responsavel_id and p.responsavel_id != pessoa.id):
            raise PermissionError("Participação fora do seu escopo.")
    except PermissionError as erro:
        raise HTTPException(403, str(erro))
    from app.eventos import registrar_auditoria
    registrar_auditoria(sessao, "consulta_participacao_form2", "pessoa", pessoa.id,
        {"participacao_id": p.id, "finalidade": "atendimento da participação atribuída à unidade"})
    sessao.commit()
    return paginas.TemplateResponse(request=request, name="participacao_form2.html",
        context={"atuacao": contexto_atuacao(sessao, pessoa, p), "conta_id": conta_id, "p": p, "estados_regua": estados_regua_form2(p.conteudo or {}), "pessoa": pessoa,
                 "registro": sessao.get(Registro, p.registro_id),
                 "unidades": sessao.scalars(select(Unidade).where(Unidade.ativa.is_(True))).all(),
                 "consultas": sessao.scalars(select(ParticipacaoForm2).where(ParticipacaoForm2.origem_id == p.id)).all(),
                 "comando_id": str(uuid4())})


@router.post("/form2/participacoes/{participacao_id}")
async def agir(request: Request, participacao_id: str,
               sessao: Session = Depends(sessao_fila)):
    dados = await request.form()
    conta_id = str(dados.get("conta_id", ""))
    try:
        resultado = executar(sessao, conta_id=conta_id, comando_id=dados.get("comando_id"),
            participacao_id=participacao_id, acao=dados.get("acao"),
            versao=int(dados.get("versao", 0)), texto=str(dados.get("texto", "")),
            unidade_id=dados.get("unidade_id"), tipo=dados.get("tipo"))
        if not resultado["permitido"]:
            raise ValueError(resultado.get("motivo"))
        sessao.commit()
    except (ValueError, PermissionError) as erro:
        sessao.rollback()
        raise HTTPException(409 if isinstance(erro, ValueError) else 403, str(erro))
    return RedirectResponse("/form2/filas?"+urlencode({"conta_id": conta_id}), status_code=303)


@router.post("/form2/filas/encaminhar")
async def encaminhar(request: Request, sessao: Session = Depends(sessao_fila)):
    dados = await request.form()
    try:
        resultado = importar_confirmada(sessao, conta_id=dados.get("conta_id"),
            comando_id=dados.get("comando_id"), registro_id=dados.get("registro_id"))
        if not resultado["permitido"]:
            raise ValueError(resultado.get("motivo"))
        sessao.commit()
    except (ValueError, PermissionError) as erro:
        sessao.rollback()
        raise HTTPException(400, str(erro))
    return RedirectResponse("/form2/filas?"+urlencode({"conta_id": dados.get("conta_id")}), status_code=303)


@router.get("/form2/participacoes/{participacao_id}/blocos/{bloco}", name="bloco_fila_form2")
def bloco_fila(request: Request, participacao_id: str, bloco: int, conta_id: str,
               sessao: Session = Depends(sessao_fila)):
    from app.respostas_form2 import projetar_bloco, definicao_revisao, limite_texto_revisao
    from app.form2_rev212 import RASCUNHO, ramos_origem, indice_valores, aplicavel, mapa_regras
    from app.contrato_form2_respostas import carregar_contrato
    from app.origem_form2 import ler_origem
    from app.eventos import registrar_auditoria
    pessoa = pessoa_ativa(sessao, conta_id)
    p = sessao.get(ParticipacaoForm2, participacao_id)
    if not p or p.tipo != "principal" or not autorizado(sessao, pessoa, p) or p.responsavel_id != pessoa.id:
        raise HTTPException(403, "Formulário fora do seu escopo.")
    if not 1 <= bloco <= 14:
        raise HTTPException(404, "Bloco inexistente.")
    origem = ler_origem(sessao, p.registro_id, p.snapshot_id)
    conteudo = p.conteudo or {}
    definicao = projetar_bloco(conteudo, bloco) if bloco in (1, 2) else definicao_revisao(bloco)
    regras = mapa_regras(carregar_contrato())
    valores = indice_valores(conteudo)
    valores_bloco = conteudo.get(RASCUNHO, {}).get(str(bloco), {})
    conjuntos = [int(chave.rsplit("#", 1)[1]) for chave in valores_bloco
                 if "#" in chave and chave.rsplit("#", 1)[1].isdigit()]
    ocorrencias = range(1, max([1, *conjuntos]) + 1)
    origens_repetiveis = [item["id"] for item in definicao["itens"] if item.get("repetivel")]
    ramos = ramos_origem(origem)
    registrar_auditoria(sessao, "consulta_form2_fila", "pessoa", pessoa.id,
        {"participacao_id": p.id, "bloco": bloco})
    sessao.commit()
    from app.modelos import Comando
    salvo = sessao.get(Comando, request.query_params.get("salvo")) if request.query_params.get("salvo") else None
    confirmacao = None
    if (salvo and salvo.tipo == "fila_form2_bloco" and salvo.ator_id == pessoa.id
            and salvo.conta_id == conta_id):
        resultado_salvo = salvo.resultado or {}
        if (resultado_salvo.get("permitido") and resultado_salvo.get("participacao_id") == p.id
                and resultado_salvo.get("bloco") == bloco and resultado_salvo.get("versao") == p.versao):
            confirmacao = "Bloco salvo."
            if resultado_salvo.get("complemento_solicitado"):
                confirmacao += " Complementação solicitada à origem."
    return paginas.TemplateResponse(request=request, name="bloco_fila_form2.html",
        context={"atuacao": contexto_atuacao(sessao, pessoa, p), "p": p, "estados_regua": estados_regua_form2(p.conteudo or {}), "pessoa": pessoa, "conta_id": conta_id, "bloco": definicao,
        "numero": bloco, "confirmacao": confirmacao, "ocorrencias": ocorrencias, "origens_repetiveis": origens_repetiveis,
        "comando_id": str(uuid4()),
        "fatos_origem": origem["conteudo"],
        "registro": sessao.get(Registro, p.registro_id),
        "secretaria": sessao.get(Unidade, sessao.get(Registro, p.registro_id).unidade_principal_atual_id),
        "numero_origem": origem["snapshot"].numero,
        "perguntas_origem": [q for q in origem["perguntas"] if q["respondida"]],
        "revogacao": [a["rotulo"] for q in definicao_revisao(5)["itens"] if q["id"] == "F2-5.7" for a in q["alternativas"] if a["codigo"] in valores.get("opcao:F2-5.7", [])],
        "complementacao": conteudo.get("respostas_etapa1", {}).get("F2-1.3.1"),
        "valores": conteudo.get(RASCUNHO, {}).get(str(bloco), {}),
        "ativa": lambda item, sufixo: aplicavel(item, sufixo, valores, ramos, regras),
        "limite_texto": limite_texto_revisao})


@router.post("/form2/participacoes/{participacao_id}/blocos/{bloco}")
async def salvar_bloco_fila(request: Request, participacao_id: str, bloco: int,
                            sessao: Session = Depends(sessao_fila)):
    from app.fila_form2 import salvar_bloco
    dados = await request.form()
    conta_id = dados.get("conta_id", "")
    try:
        campos = {}
        for chave in dados:
            if bloco in (1, 2) and chave.startswith("resposta_"):
                item = chave.removeprefix("resposta_")
                lista = [v for v in dados.getlist(chave) if v]
                campos[item] = (lista or None) if item == "F2-2.9.1" else (lista[0] if lista else None)
            elif bloco >= 2 and chave.startswith(("opcao:", "texto:", "comentario:", "principal:")):
                campos[chave] = dados.getlist(chave)
        complemento = dados.get("complemento_outro", "").strip()
        resultado = salvar_bloco(sessao, conta_id=conta_id,
            comando_id=dados.get("comando_id"), participacao_id=participacao_id,
            versao=int(dados.get("versao", 0)), bloco=bloco, campos=campos,
            complementos={"F2-2.9.1": {"ALT_05": complemento}} if complemento else {})
        if not resultado["permitido"]:
            raise ValueError(resultado.get("motivo"))
        sessao.commit()
    except (PermissionError, ValueError) as erro:
        sessao.rollback()
        raise HTTPException(409, str(erro))
    return RedirectResponse(str(request.url_for("bloco_fila_form2",
        participacao_id=participacao_id, bloco=bloco))+"?"+urlencode({"conta_id": conta_id, "salvo": dados.get("comando_id")})+"#confirmacao-salvamento", status_code=303)


@router.post("/form2/participacoes/{participacao_id}/complemento")
async def resposta_complemento(request: Request, participacao_id: str,
                               sessao: Session = Depends(sessao_fila)):
    # Endereço antigo não pode contornar o contrato v9 e o controle de versão.
    raise HTTPException(409, "Abra Ver pendências e respostas para conferir a versão e registrar a justificativa.")


@router.post("/form2/participacoes/{participacao_id}/reatribuir")
async def reatribuir_participacao(request: Request, participacao_id: str,
                                 sessao: Session = Depends(sessao_fila)):
    from app.fila_form2 import reatribuir
    dados = await request.form()
    try:
        resultado = reatribuir(sessao, conta_id=dados.get("conta_id"),
            comando_id=dados.get("comando_id"), participacao_id=participacao_id,
            versao=int(dados.get("versao",0)), responsavel_id=dados.get("responsavel_id"),
            motivo=dados.get("motivo",""))
        if not resultado["permitido"]:
            raise ValueError(resultado.get("motivo"))
        sessao.commit()
    except (ValueError, PermissionError) as erro:
        sessao.rollback()
        raise HTTPException(409,str(erro))
    return RedirectResponse("/form2/filas?"+urlencode({"conta_id": dados.get("conta_id")}),status_code=303)
