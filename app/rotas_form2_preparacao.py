"""Fronteira HTTP demonstrativa. Nenhuma rota de habilitação ou submissão."""
from pathlib import Path
from urllib.parse import urlencode
import uuid

from fastapi import APIRouter, Depends, Query, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import inspect

from app.banco import motor
from app.modelos import Pessoa, Unidade
from app.continuidade_apa import apa_em_exercicio
from app.consultas_interface import pode_consultar_registro
from app.apresentacao_form2 import (apresentar_origem, apoio_juridico_etapa1, identificar_agentes,
                                   reapresentar_tentativa_guarda, unidade_guarda, data_local,
                                   rotulo_demonstrativo, PAPEIS)
from app.form2_preparacao import (consultar_preparacao, iniciar_preparacao, projetar_trabalho_aal,
                                  salvar_preparacao, salvar_respostas_bloco)

from app.form2_rev212 import RASCUNHO, mapa_regras, indice_valores, aplicavel, ramos_origem, conjunto_da_chave
from app.contrato_form2_respostas import carregar_contrato
from app.respostas_form2 import estados_regua_form2, CADERNO_REV20, MODOS_IDENTIFICACAO, definicao_revisao, definicao_bloco, limite_texto_revisao, projetar_bloco, _ativa
router = APIRouter()
paginas = Jinja2Templates(directory=Path(__file__).parent / "paginas")
paginas.env.policies["json.dumps_kwargs"] = {**paginas.env.policies["json.dumps_kwargs"], "ensure_ascii": False}
paginas.env.filters.update(data_local=data_local, rotulo_f2=rotulo_demonstrativo)


def sessao_form2():
    with Session(motor) as sessao:
        if not all(inspect(sessao.connection()).has_table(t) for t in
                   ("preparacao_form2", "habilitacao_form2_preparacao")):
            raise HTTPException(503, "Infraestrutura demonstrativa do FORM 2 ainda não instalada.")
        yield sessao


def _contexto_navegacao(request):
    secretaria = request.query_params.get("secretaria_id")
    if request.query_params.get("instrumento") == "form2" and secretaria:
        return {"secretaria_id": secretaria, "instrumento": "form2"}
    return {}


def _pagina(request, sessao, registro_id, conta_id, *, preparacao_id=None,
            snapshot_id=None, erro=None, anotacao_tentada=None, versao_tentada=None,
            tentativa_bloco=None, complementos_tentados=None, tentativa_identificacao=None):
    if not inspect(sessao.connection()).has_table("preparacao_form2"):
        return paginas.TemplateResponse(request=request, name="erro.html", status_code=503,
            context={"titulo": "Preparação indisponível", "mensagem": "Infraestrutura demonstrativa do FORM 2 ainda não instalada neste ambiente."})
    dados = consultar_preparacao(sessao, conta_id=conta_id, registro_id=registro_id,
                                 preparacao_id=preparacao_id, snapshot_id=snapshot_id)
    sessao.commit()
    if not dados["permitido"]:
        return paginas.TemplateResponse(request=request, name="erro.html", status_code=403,
            context={"titulo": "Consulta não autorizada ou indisponível", "mensagem": dados["motivo"]})
    visiveis = dados["preparacoes"]
    trabalho = dados.get("trabalho_aal")
    if trabalho is None:
        trabalho = projetar_trabalho_aal(sessao, visiveis)
    alvo = dados["preparacao"]
    if alvo is None and dados["origem"]:
        sid = dados["origem"]["snapshot"].id
        alvo = next((item for item in visiveis if item.snapshot_id == sid), None)
    elif alvo is None and not dados["e_apa"] and visiveis:
        editaveis = dados["preparacoes_editaveis"]
        alvo = next((item for item in reversed(visiveis) if item.id in editaveis), visiveis[-1])
    exercicio = apa_em_exercicio(sessao, dados["registro"].unidade_principal_atual_id)
    guarda = unidade_guarda(dados)
    identificacao = None
    if guarda and guarda.get("edicao_disponivel"):
        identificacao = projetar_bloco(dados["preparacao"].conteudo, 1)["itens"]
        if tentativa_identificacao is not None:
            valores = {q["id"]: q["valor"] for q in identificacao}
            valores.update(tentativa_identificacao)
            for q in identificacao:
                q["valor"] = valores[q["id"]]
                q["ativa"] = _ativa(q, valores)
    if tentativa_bloco is not None:
        guarda = reapresentar_tentativa_guarda(guarda, tentativa_bloco, complementos_tentados)
    return paginas.TemplateResponse(request=request, name="form2_preparacao.html",
        status_code=409 if erro else 200,
        context={**dados, "trabalho_aal": trabalho, "contexto_navegacao": _contexto_navegacao(request), "alvo": alvo,
                 "secretaria": sessao.get(Unidade, dados["registro"].unidade_principal_atual_id),
                 "apa": sessao.get(Pessoa, exercicio["pessoa_id"]) if exercicio else None,
                 "consulta_historica": apresentar_origem(dados.get("origem")),
                 "guarda": guarda, "identificacao": identificacao,
                 "estados_regua": estados_regua_form2(dados["preparacao"].conteudo) if identificacao else {},
                 "versao_identificacao": versao_tentada if tentativa_identificacao is not None else None,
                 "apoio_juridico": apoio_juridico_etapa1(),
                 "pode_voltar_registro": pode_consultar_registro(sessao, conta_id, registro_id),
                 "agentes": identificar_agentes(sessao, dados), "papeis": PAPEIS,
                 "conta_id": conta_id, "comando_id": str(uuid.uuid4()),
                 "erro": erro, "anotacao_tentada": anotacao_tentada,
                 "versao_tentada": versao_tentada})


@router.get("/registros/{registro_id}/form2/preparacao", name="form2_preparacao")
def consultar(request: Request, registro_id: str, conta_id: str = Query(max_length=50),
              preparacao_id: str | None = Query(default=None, max_length=36),
              snapshot_id: str | None = Query(default=None, max_length=36),
              sessao: Session = Depends(sessao_form2)):
    return _pagina(request, sessao, registro_id, conta_id, preparacao_id=preparacao_id,
                   snapshot_id=snapshot_id)


def _redirecionar(request, registro_id, conta_id, preparacao_id, fragmento=''):
    url = str(request.url_for("form2_preparacao", registro_id=registro_id))
    return RedirectResponse(url + "?" + urlencode({"conta_id": conta_id,
        "preparacao_id": preparacao_id, **_contexto_navegacao(request)}) + fragmento, status_code=303)


@router.api_route("/registros/{registro_id}/form2/preparacao/{preparacao_id}/revisao/{bloco}",
                  methods=["GET", "POST"], name="revisao_form2")
async def revisao_form2(request: Request, registro_id: str, preparacao_id: str, bloco: int,
                       conta_id: str = Query(max_length=50), sessao: Session = Depends(sessao_form2)):
    if not 1 <= bloco <= 14:
        raise HTTPException(404, "Bloco inexistente.")
    dados = consultar_preparacao(sessao, conta_id=conta_id, registro_id=registro_id, preparacao_id=preparacao_id)
    sessao.commit()
    if not dados["permitido"] or not dados["pode_editar"]:
        raise HTTPException(403, "Revisão reservada ao AAL autorizado.")
    try:
        definicao = definicao_revisao(bloco)
    except (ValueError, KeyError, OSError, TypeError):
        raise HTTPException(503, "Catálogo local indisponível.")
    prep = dados["preparacao"]
    valores = dict(prep.conteudo.get(RASCUNHO, {}).get(str(bloco), {}))
    versao = prep.versao_rascunho
    erro = None
    if request.method == "POST":
        form = await request.form()
        if form.getlist("edicao") != ["REV21.2"]:
            raise HTTPException(409, "O formulário mudou de edição. Reabra o bloco antes de salvar.")
        if any(len(form.getlist(k)) != 1 for k in ("comando_id", "versao_lida")):
            raise HTTPException(400, "Identificação do rascunho inválida.")
        try:
            versao = int(form["versao_lida"])
        except ValueError:
            raise HTTPException(400, "Versão inválida.")
        campos = {k: form.getlist(k) for k in form if k not in ("comando_id", "versao_lida", "edicao")}
        resultado = salvar_respostas_bloco(sessao, comando_id=form["comando_id"], conta_id=conta_id,
            registro_id=registro_id, preparacao_id=preparacao_id, bloco=bloco, versao_lida=versao,
            alteracoes=campos, revisao=True)
        sessao.commit()
        if resultado["permitido"]:
            return RedirectResponse(str(request.url), status_code=303)
        erro = resultado["motivo"]
        valores.update({k: v if k.startswith("opcao:") else v[0] for k, v in campos.items()})
    ocorrencias = sorted({int(k.split("#")[-1]) for k in valores if "#" in k and k.split("#")[-1].isascii()
                          and k.split("#")[-1].isdigit() and len(k.split("#")[-1]) <= 2})
    regras = mapa_regras(carregar_contrato())
    salvos = indice_valores(prep.conteudo)
    ramos = ramos_origem(dados["origem"])
    def ativa(chave, conjunto):
        return aplicavel(chave, conjunto, salvos, ramos, regras)
    pendencias = []
    for nome, valor in salvos.items():
        if nome.startswith("opcao:") and "A_CONFIRMAR" in valor:
            chave = nome.split(":", 1)[1]
            if ativa(chave.partition("#")[0], conjunto_da_chave(chave)):
                pendencias.append(chave)
    return paginas.TemplateResponse(request=request, name="form2_revisao.html", status_code=409 if erro else 200,
        headers={"Cache-Control": "private, no-store"},
        context={"registro": dados["registro"], "prep": prep, "bloco": definicao, "valores": valores,
                 "estados_regua": estados_regua_form2(prep.conteudo),
                 "versao": versao, "erro": erro, "comando_id": str(uuid.uuid4()), "conta_id": conta_id,
                 "ativa": ativa, "pendencias": pendencias,
                 "origens_repetiveis": [q["id"] for q in definicao["itens"] if q["repetivel"]],
                 "inativas": prep.conteudo.get("respostas_inativas_rev212", {}).get(str(bloco), {}),
                 "fatos_origem": [q for q in dados["origem"].get("perguntas", [])
                                  if q.get("respondida") and q["id"].split(".")[0] in
                                  {8: {"10"}, 9: {"3", "8", "11"}, 10: {"3"}}.get(bloco, set())],
                 "historico20": prep.conteudo.get(CADERNO_REV20, {}).get(str(bloco), {}),
                 "legado": prep.conteudo.get("revisao_blocos_rev18_v2", {}).get(str(bloco), {}),
                 "complementacao": prep.conteudo.get("respostas_etapa1", {}).get("F2-1.3.1"),
                 "revogacao": prep.conteudo.get(RASCUNHO, {}).get("5", {}).get("opcao:F2-5.7"),
                 "ocorrencias": ocorrencias or [1], "limite_texto": limite_texto_revisao,
                 "navegacao": _contexto_navegacao(request)})


@router.post("/registros/{registro_id}/form2/preparacao/iniciar", name="iniciar_form2_demo")
async def iniciar(request: Request, registro_id: str, sessao: Session = Depends(sessao_form2)):
    form = await request.form()
    permitidos = {"conta_id", "comando_id", "snapshot_id", "preparador_id"}
    if set(form) != permitidos or any(len(form.getlist(k)) != 1 for k in form):
        return paginas.TemplateResponse(request=request, name="erro.html", status_code=400,
            context={"titulo": "Pedido inválido", "mensagem": "Campos desconhecidos, ausentes ou duplicados."})
    resultado = iniciar_preparacao(sessao, registro_id=registro_id, **dict(form))
    sessao.commit()
    if resultado["permitido"]:
        return _redirecionar(request, registro_id, form["conta_id"], resultado["preparacao_id"])
    return _pagina(request, sessao, registro_id, form["conta_id"], erro=resultado["motivo"])


@router.post("/registros/{registro_id}/form2/preparacao/{preparacao_id}/salvar", name="salvar_form2_demo")
async def salvar(request: Request, registro_id: str, preparacao_id: str,
                 sessao: Session = Depends(sessao_form2)):
    form = await request.form()
    permitidos = {"conta_id", "comando_id", "versao_lida", "anotacao_preparatoria"}
    if set(form) != permitidos or any(len(form.getlist(k)) != 1 for k in form):
        return paginas.TemplateResponse(request=request, name="erro.html", status_code=400,
            context={"titulo": "Pedido inválido", "mensagem": "Campos desconhecidos, ausentes ou duplicados."})
    try:
        versao = int(form["versao_lida"])
    except ValueError:
        versao = None
    resultado = salvar_preparacao(sessao, comando_id=form["comando_id"], conta_id=form["conta_id"],
        registro_id=registro_id, preparacao_id=preparacao_id, versao_lida=versao,
        conteudo={"anotacao_preparatoria": form["anotacao_preparatoria"]})
    sessao.commit()
    if resultado["permitido"]:
        return _redirecionar(request, registro_id, form["conta_id"], preparacao_id, "#anotacoes")
    return _pagina(request, sessao, registro_id, form["conta_id"], preparacao_id=preparacao_id,
        erro=resultado["motivo"], anotacao_tentada=form["anotacao_preparatoria"], versao_tentada=versao)


@router.post("/registros/{registro_id}/form2/preparacao/{preparacao_id}/blocos/{bloco}/salvar",
             name="salvar_bloco_form2")
async def salvar_bloco(request: Request, registro_id: str, preparacao_id: str, bloco: int,
                       sessao: Session = Depends(sessao_form2)):
    form = await request.form()
    campos_resposta = {"resposta_F2-2.9", "resposta_F2-2.9.1",
                       "resposta_F2-2.9.2", "resposta_F2-2.9.3"}
    campos_reativar = {"reativar_F2-2.9.1", "reativar_F2-2.9.3"}
    campo_complemento = "complemento_F2-2.9.1_ALT_05"
    permitidos = {"conta_id", "comando_id", "versao_lida", campo_complemento,
                  *campos_resposta, *campos_reativar}
    obrigatorios = {"conta_id", "comando_id", "versao_lida"}
    if bloco == 1:
        permitidos = obrigatorios | {"resposta_" + k for k in MODOS_IDENTIFICACAO} | {"reativar_F2-1.3.1"}
        if not obrigatorios <= set(form) <= permitidos or any(len(form.getlist(k)) != 1 for k in form):
            raise HTTPException(400, "Campos inválidos no Bloco 1.")
        try:
            versao = int(form["versao_lida"])
        except ValueError:
            raise HTTPException(400, "Versão inválida.")
        valores = {k: form["resposta_" + k] or None for k in MODOS_IDENTIFICACAO if "resposta_" + k in form}
        reativar = {"F2-1.3.1"} if form.get("reativar_F2-1.3.1") == "1" else set()
        if reativar and not valores.get("F2-1.3.1"):
            valores.pop("F2-1.3.1", None)
        resultado = salvar_respostas_bloco(sessao, comando_id=form["comando_id"], conta_id=form["conta_id"],
            registro_id=registro_id, preparacao_id=preparacao_id, bloco=1, versao_lida=versao,
            alteracoes=valores, reativar=reativar)
        sessao.commit()
        if resultado["permitido"]:
            return _redirecionar(request, registro_id, form["conta_id"], preparacao_id, "#identificacao")
        return _pagina(request, sessao, registro_id, form["conta_id"], preparacao_id=preparacao_id,
                       erro=resultado["motivo"], versao_tentada=versao, tentativa_identificacao=valores)
    escalares = obrigatorios | {campo_complemento} | campos_reativar | (
        campos_resposta - {"resposta_F2-2.9.1"})
    if (bloco != 2 or not obrigatorios <= set(form) or not set(form) <= permitidos
            or any(len(form.getlist(k)) != 1 for k in escalares if k in form)):
        return paginas.TemplateResponse(request=request, name="erro.html", status_code=400,
            context={"titulo": "Pedido inválido", "mensagem": "Campos desconhecidos, ausentes ou duplicados."})
    try:
        versao = int(form["versao_lida"])
    except ValueError:
        versao = None
    alteracoes = {}
    for item_id in ("F2-2.9", "F2-2.9.2", "F2-2.9.3"):
        nome = "resposta_" + item_id
        if nome in form:
            alteracoes[item_id] = form[nome] or None
    if "resposta_F2-2.9.1" in form:
        valores = [valor for valor in form.getlist("resposta_F2-2.9.1") if valor]
        alteracoes["F2-2.9.1"] = valores or None
    complemento = form.get(campo_complemento, "").strip()
    complementos = {"F2-2.9.1": {"ALT_05": complemento}} if complemento else {}
    reativar = {nome.removeprefix("reativar_") for nome in campos_reativar if nome in form}
    for item_id in reativar:
        if alteracoes.get(item_id) is None:
            alteracoes.pop(item_id, None)
    resultado = salvar_respostas_bloco(
        sessao, comando_id=form["comando_id"], conta_id=form["conta_id"],
        registro_id=registro_id, preparacao_id=preparacao_id, bloco=bloco,
        versao_lida=versao, alteracoes=alteracoes, complementos=complementos,
        reativar=reativar,
    )
    sessao.commit()
    if resultado["permitido"]:
        return _redirecionar(request, registro_id, form["conta_id"], preparacao_id, "#unidade-guarda")
    return _pagina(request, sessao, registro_id, form["conta_id"], preparacao_id=preparacao_id,
                   erro=resultado["motivo"], versao_tentada=versao,
                   tentativa_bloco=alteracoes,
                   complementos_tentados={"F2-2.9.1": {"ALT_05": complemento}})
