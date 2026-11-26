from app.apresentacao_situacoes_form2 import situacao_origem, situacoes_complementacao
from app.obrigatoriedade_forms import conferencia_para_tela, FormularioIncompleto
from app.unidades_interface_form2 import secretarias_ativas
"""Interface de filas institucionais demonstrativas."""
from pathlib import Path
from hashlib import sha256
from uuid import uuid4
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.catalogo_form2_rev18 import titulos_blocos_form2
from sqlalchemy import select, inspect
from sqlalchemy.orm import Session
from app.banco import motor
from carga_ficticia.pessoas import CARGOS_FICTICIOS
from app.apresentacoes_form1 import rotulo_apresentacao
from app.modelos import (ParticipacaoForm2, Registro, Unidade, ComplementoForm2,
    AtribuicaoForm1Integral, HistoricoConferenciaForm1Integral, Pessoa)
from app.fila_form2 import painel, pessoa_ativa, autorizado, executar, importar_confirmada, agora, unidades as unidades_autorizadas
from app.continuidade_apa import pessoa_e_apa_em_exercicio
from app.respostas_form2 import estados_regua_form2, aguarda_temporalidade

router = APIRouter()
paginas = Jinja2Templates(directory=Path(__file__).parent / "paginas")
from app.identidade_demonstrativa import configurar_identidade
configurar_identidade(paginas)
from app.atos_interface import ato_registrado
from app.apresentacao_form2 import data_local
paginas.env.filters["hora_local"] = data_local
paginas.env.globals["aguarda_temporalidade"] = aguarda_temporalidade
paginas.env.globals["titulos_blocos_form2"] = titulos_blocos_form2
paginas.env.filters["chave_comando"] = lambda valor: sha256(str(valor).encode("utf-8")).hexdigest()


def estados_da_participacao(sessao, participacao):
    from app.form2_rev212 import ramos_origem
    from app.origem_form2 import ler_origem
    origem = ler_origem(sessao, participacao.registro_id, participacao.snapshot_id)
    return estados_regua_form2(participacao.conteudo or {}, ramos_origem(origem))


def retorno_consultivo(request, sessao, conta_id, principal):
    from app.modelos import Evento
    chave = request.query_params.get("registrado")
    if not chave:
        return None
    tipos = {"form2_consulta_encaminhada":"Consulta encaminhada",
             "form2_orientacao_registrada":"Manifestação registrada",
             "form2_orientacao_respondida":"Resposta registrada"}
    ato = sessao.scalar(select(Evento).join(ParticipacaoForm2, Evento.cadeia_id == ParticipacaoForm2.id)
        .where(Evento.comando_id == chave, Evento.ator_id == pessoa_ativa(sessao, conta_id).id, Evento.tipo_evento.in_(tuple(tipos)),
               (ParticipacaoForm2.id == principal.id) | (ParticipacaoForm2.origem_id == principal.id)))
    return f"{tipos[ato.tipo_evento]} em {data_local(ato.ocorrido_em)}." if ato else None


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
                HistoricoConferenciaForm1Integral.numero_apresentacao, HistoricoConferenciaForm1Integral.versao_rascunho,
                HistoricoConferenciaForm1Integral.solicitada_em,
                HistoricoConferenciaForm1Integral.solicitada_por_id,
                HistoricoConferenciaForm1Integral.confirmada_em)
            .join(HistoricoConferenciaForm1Integral, HistoricoConferenciaForm1Integral.snapshot_id == VersaoForm1Integral.id)
            .where(VersaoForm1Integral.registro_id == p.registro_id,
                HistoricoConferenciaForm1Integral.situacao == "conferencia_interna_confirmada")
            .order_by(VersaoForm1Integral.numero.desc())).all()
        from types import SimpleNamespace
        versoes = [SimpleNamespace(id=v.id, numero=v.numero,
            nome_apresentacao=rotulo_apresentacao(v),
            rotulo=rotulo_apresentacao(v) + " · Apresentado por " + (sessao.get(Pessoa, v.solicitada_por_id).nome) +
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
        if p.estado == 'concluida' and (p.conteudo or {}).get('conclusao_analise'):
            versoes_aceitas = novas_versoes
        from app.unidade_retorno_institucional import consultar as consultar_retorno
        retorno_institucional = consultar_retorno(sessao, p.registro_id)
        comparacao = []
        if e_aal:
            from app.origem_form2 import ler_origem
            for v in versoes:
                consulta = ler_origem(sessao, p.registro_id, v.id)
                comparacao.append({"rotulo": v.nome_apresentacao, "ativa": v.id == p.snapshot_id,
                    "perguntas": [q for q in consulta["perguntas"] if q["respondida"]]})
        from app.eventos import registrar_auditoria
        registrar_auditoria(sessao, "consulta_governanca_form2_v9", "pessoa", pessoa.id,
            {"participacao_id": alvo.id, "finalidade": "resposta ou conferência de pendências no escopo autorizado"})
        sessao.commit()
        return paginas.TemplateResponse(request=request, name="governanca_form2_v9.html", context={
            "p": p, "alvo": alvo, "registro": sessao.get(Registro, p.registro_id), "conta_id": conta_id,
            "bloco_origem": next((n for n in range(1,15) if str(n)==request.query_params.get("bloco_origem")),None),
            "estados_regua": estados_da_participacao(sessao, p) if e_aal else {},
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
    parametros = {"conta_id": conta}
    origem = request.query_params.get("bloco_origem")
    if origem in {str(n) for n in range(1, 15)}:
        parametros["bloco_origem"] = origem
    return RedirectResponse(f"/form2/participacoes/{participacao_id}/governanca?" + urlencode(parametros), status_code=303)


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
    contexto.update(conferencia_r17=conferencia_para_tela(sessao,contexto["p"]),base_r17=f"/form2/participacoes/{participacao_id}/blocos",conta_id=conta_id, comando_id=str(uuid4()),
        registro=sessao.get(Registro, contexto["p"].registro_id),
        estados_regua=estados_da_participacao(sessao, contexto["p"]),
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
            context={"conferencia_r17":getattr(erro,"conferencia",None),"base_r17":getattr(erro,"base",""),"conta_id": conta_id, "participacao_id": participacao_id, "erro": str(erro),
                     "sintese": dados.get("sintese", "")},
            status_code=403 if isinstance(erro, PermissionError) else 409)
    return RedirectResponse(str(request.url_for("consolidacao_fila_form2",
        participacao_id=participacao_id))+"?"+urlencode({"conta_id": conta_id}), status_code=303)


def duracao_fila(inicio, fim):
    horas = max(0, int((fim - inicio).total_seconds() // 3600))
    return f"{horas // 24} d {horas % 24} h" if horas >= 24 else (f"{horas} h" if horas else "menos de 1 h")


def entrada_fila(p, momento):
    data = data_local(p.entrada_em)
    espera = duracao_fila(p.entrada_em, p.assumida_em or momento)
    return f"Entrou na fila em {data} · " + (f"aguardou {espera}" if p.assumida_em else f"aguardando há {espera}")


@router.get("/form2/painel-dpo", name="painel_dpo")
def painel_dpo(request: Request, conta_id: str, sessao: Session = Depends(sessao_fila)):
    try:
        pessoa = pessoa_ativa(sessao, conta_id)
    except PermissionError as erro:
        raise HTTPException(403, str(erro))
    if not unidades_autorizadas(sessao, pessoa.id, "governanca_protecao_dados"):
        raise HTTPException(403, "Este painel exige designação vigente como Encarregado.")
    return filas(request, conta_id, sessao)


@router.get("/form2/filas", name="filas_form2")
def filas(request: Request, conta_id: str, sessao: Session = Depends(sessao_fila)):
    try:
        pessoa, participacoes, principais, dpo = painel(sessao, conta_id)
    except PermissionError as erro:
        raise HTTPException(403, str(erro))
    registros = {r.id: r for r in sessao.scalars(select(Registro))}
    unidades = {u.id: u for u in sessao.scalars(select(Unidade))}
    from app.modelos import AvisoDpo
    comunicados = dict(sessao.execute(select(AvisoDpo.participacao_id, AvisoDpo.criado_em).where(
        AvisoDpo.tipo == "ciencia", AvisoDpo.participacao_id.in_([p.id for p in principais]))).all())
    from app.continuidade_apa import conferente_da_apresentacao
    from app.modelos import ConferenciaInternaForm1Integral
    sem_conferente = [registros[c.registro_id].codigo_lgpd for c in sessao.scalars(
        select(ConferenciaInternaForm1Integral)) if not conferente_da_apresentacao(sessao, registros[c.registro_id], c)] if dpo else []
    linhas = []
    for p in principais:
        consultas = sessao.scalars(select(ParticipacaoForm2).where(
            ParticipacaoForm2.origem_id == p.id, ParticipacaoForm2.tipo == "dpo",
            ParticipacaoForm2.estado != "concluida")).all()
        orientacoes = [c.conteudo for c in sessao.scalars(select(ParticipacaoForm2).where(
            ParticipacaoForm2.origem_id == p.id, ParticipacaoForm2.tipo == "dpo",
            ParticipacaoForm2.estado == "concluida")) if (c.conteudo or {}).get("de_oficio")]
        linhas.append({"p": p, "aguarda_resposta_aal": any(not c.get("resposta") for c in orientacoes),
            "ultima_resposta": max((c["resposta"]["data"] for c in orientacoes if c.get("resposta")), default=None), "registro": registros[p.registro_id],
            "secretaria": unidades[registros[p.registro_id].unidade_principal_atual_id].nome,
            "fila": unidades[p.unidade_id].nome,
            "espera": duracao_fila(p.entrada_em, p.assumida_em or agora()),
            "dpo": duracao_fila(min(q.entrada_em for q in consultas), agora()) if consultas else "—",
            "comunicado_em": comunicados.get(p.id), "consulta_pendente": bool(consultas), "situacao": p.estado})
    from carga_ficticia.pessoas import SECRETARIAS
    secretarias = {codigo for codigo, _ in SECRETARIAS}
    cobertura = [{"nome": u.nome, "total": sum(registros[p.registro_id].unidade_principal_atual_id == u.id for p in principais)}
        for u in unidades.values() if u.ativa and u.id in secretarias] if dpo else []
    cobertura.sort(key=lambda u: (-u["total"], u["nome"]))
    from app.governanca_form2_v9 import estado as estado_v9, origem_autorizada
    from app.segregacao_form2_v9 import impedido
    complementos = []
    from app.fila_form2 import candidatos_atribuicao, aguardando_definicao_analise
    impedimentos = {}
    for participacao in sessao.scalars(select(ParticipacaoForm2)):
        if aguardando_definicao_analise(sessao, participacao):
            impedimentos[participacao.id] = "Aguardando definição de quem fará a análise"
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
            situacao = situacoes_complementacao(sessao, pendencias)
            complementos.append(dict(p=participacao, registro=registro,
                situacao=situacao if pendencias else None))
    for l in linhas:
        if l["p"].id in impedimentos:
            l["situacao"] = impedimentos[l["p"].id]
    gestores = unidades_autorizadas(sessao, pessoa.id, "gestor_fila")
    gerenciaveis = sessao.scalars(select(ParticipacaoForm2).where(
        ParticipacaoForm2.unidade_id.in_(gestores),
        ParticipacaoForm2.estado != "concluida").order_by(ParticipacaoForm2.responsavel_id.is_not(None), ParticipacaoForm2.entrada_em)).all() if gestores else []
    from app.modelos import Comando, VersaoForm1Integral
    referencias = {p.id: rotulo_apresentacao(sessao.get(VersaoForm1Integral, p.snapshot_id)) for p in gerenciaveis}
    chave = request.query_params.get("atribuicao")
    comando = sessao.get(Comando, chave) if chave else None
    mensagem = None
    if (comando and comando.tipo == "reatribuir_fila_form2" and comando.conta_id == conta_id
            and comando.ator_id == pessoa.id and comando.resultado
            and comando.resultado.get("participacao_id") in {p.id for p in gerenciaveis}):
        mensagem = comando.resultado.get("mensagem")
    agentes = sessao.scalars(select(Pessoa).where(Pessoa.ativa.is_(True))).all() if gestores else []
    responsaveis = dict(sessao.execute(select(Pessoa.id, Pessoa.nome).where(
        Pessoa.id.in_({p.responsavel_id for p in [*participacoes, *gerenciaveis] if p.responsavel_id}))).all())
    from app.modelos import Evento
    atribuidores = {}
    minhas = {p.id: p for p in [*participacoes, *gerenciaveis] if p.responsavel_id}
    if minhas:
        atos = sessao.execute(select(Evento, Pessoa.nome).join(Pessoa, Pessoa.id == Evento.ator_id)
            .where(Evento.cadeia_tipo == "participacao_form2", Evento.cadeia_id.in_(minhas),
                   Evento.tipo_evento == "form2_reatribuida").order_by(Evento.sequencia_cadeia.desc()))
        for ato, nome in atos:
            if ato.cadeia_id in atribuidores or ato.conteudo.get("responsavel_id") != minhas[ato.cadeia_id].responsavel_id:
                continue
            unidade = minhas[ato.cadeia_id].unidade_id
            exercicio = pessoa_e_apa_em_exercicio(sessao, ato.ator_id, unidade, ato.ocorrido_em)
            papel = ("APA titular" if exercicio["modalidade"] == "titular" else "APA suplente") if exercicio else "gestor da fila"
            data = ato.ocorrido_em.astimezone(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y às %Hh%M")
            anterior = sessao.scalar(select(Evento).where(Evento.cadeia_tipo == 'participacao_form2',
                Evento.cadeia_id == ato.cadeia_id, Evento.sequencia_cadeia < ato.sequencia_cadeia)
                .order_by(Evento.sequencia_cadeia.desc()).limit(1))
            acao = 'Reatribuído' if anterior and anterior.conteudo.get('responsavel_id') else 'Atribuído'
            atribuidores[ato.cadeia_id] = f"{acao} por {nome}, {papel}, em {data}"
    cartoes = {}
    for p in participacoes:
        cartoes.setdefault(p.registro_id, dict(registro=registros[p.registro_id],
            participacoes=[], complementos=[]))["participacoes"].append(p)
    for c in complementos:
        cartoes.setdefault(c["registro"].id, dict(registro=c["registro"],
            participacoes=[], complementos=[]))["complementos"].append(c)
    from app.modelos import ContextoAtuacao
    contextos = {c.id:c.nome for c in sessao.scalars(select(ContextoAtuacao))}
    tipos = {'processo':'Processo','servico':'Serviço','atividade':'Atividade'}
    identificacoes = {rid:'Contexto: '+contextos.get(r.contexto_atuacao_id,'Não informado') for rid,r in registros.items()}
    for cartao in cartoes.values():
        cartao['identificacao'] = identificacoes[cartao['registro'].id]
    momento = agora()
    from app.origem_form2 import nome_objeto_em_analise
    nomes_objetos = {p.id: nome_objeto_em_analise(sessao, p.registro_id, p.snapshot_id) for p in participacoes}
    entradas = {p.id: entrada_fila(p, momento) for p in [*participacoes, *gerenciaveis]}
    historicos_origem = sessao.scalars(select(HistoricoConferenciaForm1Integral).where(
        HistoricoConferenciaForm1Integral.registro_id.in_(cartoes)
    ).order_by(HistoricoConferenciaForm1Integral.numero_apresentacao.desc()))
    for historico in historicos_origem:
        cartoes[historico.registro_id].setdefault("origem", situacao_origem(historico))
    for cartao in cartoes.values():
        aguardando = [p.entrada_em for p in cartao["participacoes"] if not p.responsavel_id and p.estado == "aguardando"]
        cartao["aguardando"] = min(aguardando) if aguardando else None
    ordenados = sorted(cartoes.values(), key=lambda c: (c["aguardando"] is None, c["aguardando"] or momento))
    unidades_apa = [u.id for u in unidades.values() if u.ativa and
                    pessoa_e_apa_em_exercicio(sessao, pessoa.id, u.id)]
    confirmadas = sessao.scalars(select(HistoricoConferenciaForm1Integral)
        .join(Registro, Registro.id == HistoricoConferenciaForm1Integral.registro_id)
        .where(Registro.unidade_principal_atual_id.in_(unidades_apa),
               HistoricoConferenciaForm1Integral.situacao == "conferencia_interna_confirmada",
               ~Registro.id.in_(select(ParticipacaoForm2.registro_id).where(
                   ParticipacaoForm2.tipo == "principal")))
        .order_by(Registro.codigo_lgpd, HistoricoConferenciaForm1Integral.numero_apresentacao.desc()))
    encaminhaveis = {}
    for item in confirmadas:
        encaminhaveis.setdefault(item.registro_id, {
            "snapshot": item.snapshot_id, "codigo": registros[item.registro_id].codigo_lgpd,
            "rotulo": rotulo_apresentacao(item)})
    return paginas.TemplateResponse(request=request, name="filas_form2.html",
        context={"ato_registrado": ato_registrado(sessao, chave, conta_id), "nomes_objetos": nomes_objetos, "referencias": referencias, "mensagem_atribuicao": mensagem, "atribuidores": atribuidores, "cartoes": ordenados, "identificacoes":identificacoes, "entradas": entradas, "pode_encaminhar": bool(unidades_apa), "encaminhaveis": encaminhaveis,
                 "conta_id": conta_id, "pessoa": pessoa, "participacoes": participacoes,
                 "registros": registros, "unidades": unidades, "linhas": linhas,
                 "impedimentos": impedimentos, "complementos": complementos, "gerenciaveis": gerenciaveis, "agentes": {p.id: candidatos_atribuicao(sessao, p, pessoa.id) for p in gerenciaveis},
                 "responsaveis": responsaveis, "dpo": dpo, "sem_conferente": sem_conferente, "aguardando_guarda": len({p.registro_id for p in principais if aguarda_temporalidade(p.conteudo)}), "cobertura": cobertura, "comando_id": str(uuid4())})


@router.get("/form2/participacoes/{participacao_id}", name="participacao_form2")
def participacao(request: Request, participacao_id: str, conta_id: str,
                  sessao: Session = Depends(sessao_fila)):
    try:
        pessoa = pessoa_ativa(sessao, conta_id)
        p = sessao.get(ParticipacaoForm2, participacao_id)
        if p and p.estado == "aguardando":
            from app.segregacao_form2_v9 import impedido
            from app.fila_form2 import PAPEIS
            from app.governanca_form2_v9 import origem_autorizada
            if p.unidade_id in unidades_autorizadas(sessao, pessoa.id, PAPEIS[p.tipo]) or (
                    p.tipo == "principal" and origem_autorizada(sessao, pessoa, p)):
                if impedido(sessao, pessoa.id, p):
                    return paginas.TemplateResponse(request=request, name="impedimento_assuncao_form2.html",
                        status_code=403, context={"conta_id": conta_id})
        if not p or not autorizado(sessao, pessoa, p) or (p.responsavel_id and p.responsavel_id != pessoa.id):
            raise PermissionError("Participação fora do seu escopo.")
    except PermissionError as erro:
        raise HTTPException(403, str(erro))
    from app.eventos import registrar_auditoria
    registrar_auditoria(sessao, "consulta_participacao_form2", "pessoa", pessoa.id,
        {"participacao_id": p.id, "finalidade": "atendimento da participação atribuída à unidade"})
    sessao.commit()
    from app.modelos import Comando, VersaoForm1Integral
    snapshot = sessao.get(VersaoForm1Integral, p.snapshot_id)
    data_confirmacao = snapshot.apresentacao.confirmada_em if snapshot.apresentacao else None
    chave = request.query_params.get("assumida")
    comando = sessao.get(Comando, chave) if chave and p.responsavel_id == pessoa.id else None
    assumida = (comando and comando.tipo == "fila_form2_assumir" and comando.conta_id == conta_id
                and comando.ator_id == pessoa.id and (comando.resultado or {}).get("participacao_id") == p.id
                and comando.resultado.get("permitido"))
    from app.form2_rev212 import catalogo
    consulta_item = request.query_params.get("consulta_item", "")
    consulta_tipo = request.query_params.get("consulta_tipo", "dpo")
    if consulta_item and consulta_item not in catalogo():
        raise HTTPException(400, "Referência de pergunta desconhecida.")
    if consulta_tipo not in ("dpo", "juridico", "tematica"):
        raise HTTPException(400, "Tipo de consulta desconhecido.")
    return paginas.TemplateResponse(request=request, name="participacao_form2.html",
        context={"conferencia_r17":conferencia_para_tela(sessao,p) if p.tipo=="principal" else None,"base_r17":f"/form2/participacoes/{p.id}/blocos","consulta_item": consulta_item, "consulta_tipo": consulta_tipo, "atuacao": contexto_atuacao(sessao, pessoa, p), "conta_id": conta_id, "p": p, "estados_regua": estados_da_participacao(sessao, p), "pessoa": pessoa,
                 "autor_conclusao": sessao.get(Pessoa, (p.conteudo or {}).get('conclusao_analise', {}).get('pessoa_id')) if (p.conteudo or {}).get('conclusao_analise') else None,
                 "rotulo_origem": rotulo_apresentacao(snapshot),
                 "confirmada_em": data_confirmacao.astimezone(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y às %Hh%M") if data_confirmacao else None,
                 "assumida": assumida, "retorno": retorno_consultivo(request,sessao,conta_id,p),
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
        if isinstance(erro, FormularioIncompleto):
            return paginas.TemplateResponse(request=request, name='forms34_erro.html', status_code=409,
                context={'conta_id':conta_id,'erro':str(erro), 'retorno':f'/form2/participacoes/{participacao_id}',
                         'conferencia_r17':erro.conferencia, 'base_r17':erro.base})
        raise HTTPException(409 if isinstance(erro, ValueError) else 403, str(erro))
    if dados.get("acao") == "consultar":
        return RedirectResponse(f"/form2/participacoes/{participacao_id}?" + urlencode(
            {"conta_id":conta_id, "registrado":dados["comando_id"]}), status_code=303)
    if dados.get("acao") == "assumir":
        destino = request.url_for("participacao_form2", participacao_id=participacao_id)
        return RedirectResponse(str(destino)+"?"+urlencode({"conta_id": conta_id, "assumida": dados["comando_id"]}), status_code=303)
    return RedirectResponse("/form2/filas?"+urlencode({"conta_id": conta_id}), status_code=303)


@router.post("/form2/filas/encaminhar")
async def encaminhar(request: Request, sessao: Session = Depends(sessao_fila)):
    dados = await request.form()
    try:
        snapshot_id = dados.get("snapshot_id")
        registro_id = dados.get("registro_id")
        if snapshot_id:
            registro_id = sessao.scalar(select(HistoricoConferenciaForm1Integral.registro_id).where(
                HistoricoConferenciaForm1Integral.snapshot_id == snapshot_id))
        resultado = importar_confirmada(sessao, conta_id=dados.get("conta_id"), snapshot_id=snapshot_id,
            comando_id=dados.get("comando_id"), registro_id=registro_id)
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
    from app.complementos_form2 import complementos_pendentes
    from app.confirmacoes_form2 import itens_a_confirmar
    from app.fatos_abertura_form2 import projetar_fatos_abertura
    from app.campos_form2 import data_exata
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
    projetar_fatos_abertura(definicao['itens'], origem)
    regras = mapa_regras(carregar_contrato())
    valores = indice_valores(conteudo)
    valores_bloco = conteudo.get(RASCUNHO, {}).get(str(bloco), {})
    conjuntos = [int(chave.rsplit("#", 1)[1]) for chave in valores_bloco
                 if "#" in chave and chave.rsplit("#", 1)[1].isdigit()]
    ocorrencias = range(1, max([1, *conjuntos]) + 1)
    origens_repetiveis = [item["id"] for item in definicao["itens"] if item.get("repetivel")]
    ramos = ramos_origem(origem)
    from app.form2_rev212 import condicoes_de_tela
    condicoes_de_tela(definicao["itens"], regras, valores, ramos)
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
        context={"conferencia_r17":conferencia_para_tela(sessao,p) if p.tipo=="principal" else None,"base_r17":f"/form2/participacoes/{p.id}/blocos","ato_registrado": ato_registrado(sessao, request.query_params.get("salvo"), conta_id, participacao_id=p.id) if confirmacao else None, "atuacao": contexto_atuacao(sessao, pessoa, p), "p": p, "estados_regua": estados_regua_form2(conteudo, ramos), "pessoa": pessoa, "conta_id": conta_id, "bloco": definicao,
        "cargo": CARGOS_FICTICIOS.get(pessoa.id), "numero": bloco, "confirmacao": confirmacao, "ocorrencias": ocorrencias, "origens_repetiveis": origens_repetiveis,
        "comando_id": str(uuid4()),
        "finalidade_validada": conteudo.get(RASCUNHO, {}).get("2", {}).get("texto:F2-2.3"),
        "secretarias_selecao": secretarias_ativas(sessao),
        "fatos_origem": origem["conteudo"],
        "registro": sessao.get(Registro, p.registro_id),
        "secretaria": sessao.get(Unidade, sessao.get(Registro, p.registro_id).unidade_principal_atual_id),
        "rotulo_origem": rotulo_apresentacao(origem["snapshot"]),
        "perguntas_origem": [q for q in origem["perguntas"] if q["respondida"]],
        "revogacao": [a["rotulo"] for q in definicao_revisao(5)["itens"] if q["id"] == "F2-5.7" for a in q["alternativas"] if a["codigo"] in valores.get("opcao:F2-5.7", [])],
        "complementacao": conteudo.get("respostas_etapa1", {}).get("F2-1.3.1"),
        "complementos_pendentes": complementos_pendentes(conteudo, ramos),
        "confirmacoes_por_bloco": itens_a_confirmar(conteudo, ramos),
        "valores": conteudo.get(RASCUNHO, {}).get(str(bloco), {}),
        "ativa": lambda item, sufixo: aplicavel(item, sufixo, valores, ramos, regras),
        "data_exata": data_exata, "limite_texto": limite_texto_revisao})


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
            elif bloco >= 2 and chave.startswith(("opcao:", "texto:", "comentario:", "principal:", "unidade:")):
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
    destino = str(request.url_for("bloco_fila_form2", participacao_id=participacao_id, bloco=bloco)) + "?" + urlencode({"conta_id": conta_id, "salvo": dados.get("comando_id")}) + "#confirmacao-salvamento"
    if request.headers.get("X-Salvar-Bloco") == "1":
        return JSONResponse({"salvo": True, "destino": destino})
    return RedirectResponse(destino, status_code=303)


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
        return paginas.TemplateResponse(request=request, name="erro.html",
            context={"titulo": "Atribuição indisponível", "mensagem": str(erro)}, status_code=409)
    return RedirectResponse("/form2/filas?"+urlencode({"conta_id": dados.get("conta_id"), "atribuicao": dados["comando_id"]}),status_code=303)


@router.get("/form2/participacoes/{participacao_id}/orientacao")
def consultar_orientacoes(request: Request, participacao_id: str, conta_id: str, sessao: Session = Depends(sessao_fila)):
    try:
        pessoa = pessoa_ativa(sessao, conta_id)
    except PermissionError as erro:
        raise HTTPException(403, str(erro)) from erro
    if not unidades_autorizadas(sessao, pessoa.id, "governanca_protecao_dados"):
        raise HTTPException(403, "Esta consulta exige o perfil do DPO.")
    principal = sessao.get(ParticipacaoForm2, participacao_id)
    if not principal or principal.tipo != "principal":
        raise HTTPException(404, "Participação principal indisponível.")
    consultas = sessao.scalars(select(ParticipacaoForm2).where(
        ParticipacaoForm2.origem_id == principal.id, ParticipacaoForm2.tipo == "dpo"
    ).order_by(ParticipacaoForm2.entrada_em.desc()))
    from app.origem_form2 import ler_origem
    from app.respostas_form2 import RASCUNHO
    origem = ler_origem(sessao, principal.registro_id, principal.snapshot_id)
    return paginas.TemplateResponse(request=request, name="orientacao_dpo.html", context={
        "pessoa": pessoa, "p": principal, "secretaria": sessao.get(Unidade,principal.unidade_id),
        "aal": sessao.get(Pessoa,principal.responsavel_id) if principal.responsavel_id else None,
        "revisoes": (principal.conteudo or {}).get(RASCUNHO, {}), "referencia": rotulo_apresentacao(origem["snapshot"]), "perguntas": origem["perguntas"],
        "retorno": retorno_consultivo(request,sessao,conta_id,principal),
        "registro": sessao.get(Registro, principal.registro_id), "conta_id": conta_id,
        "orientacoes": list(consultas),
        "comando_id": str(uuid4()),
    })


@router.post("/form2/participacoes/{participacao_id}/orientacao")
async def registrar_orientacao(request: Request, participacao_id: str, sessao: Session = Depends(sessao_fila)):
    from app.fila_form2 import manifestar_de_oficio
    dados = await request.form()
    conta = dados.get("conta_id", "")
    try:
        resultado = manifestar_de_oficio(sessao, conta_id=conta, participacao_id=participacao_id,
            comando_id=dados.get("comando_id"), texto=dados.get("texto", ""), decisao=dados.get("decisao"))
        consulta = sessao.get(ParticipacaoForm2, resultado["participacao_id"])
        destino = f"/form2/participacoes/{consulta.origem_id}" if dados.get("decisao") else f"/form2/participacoes/{consulta.origem_id}/orientacao"
        sessao.commit()
    except (PermissionError, ValueError) as erro:
        sessao.rollback()
        raise HTTPException(403 if isinstance(erro, PermissionError) else 409, str(erro))
    return RedirectResponse(destino + "?" + urlencode({"conta_id": conta, "registrado": dados.get("comando_id")}), status_code=303)
