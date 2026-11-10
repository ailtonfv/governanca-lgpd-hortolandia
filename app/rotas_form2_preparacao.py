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
            tentativa_bloco=None, complementos_tentados=None):
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
    if tentativa_bloco is not None:
        guarda = reapresentar_tentativa_guarda(guarda, tentativa_bloco, complementos_tentados)
    return paginas.TemplateResponse(request=request, name="form2_preparacao.html",
        status_code=409 if erro else 200,
        context={**dados, "trabalho_aal": trabalho, "contexto_navegacao": _contexto_navegacao(request), "alvo": alvo,
                 "secretaria": sessao.get(Unidade, dados["registro"].unidade_principal_atual_id),
                 "apa": sessao.get(Pessoa, exercicio["pessoa_id"]) if exercicio else None,
                 "consulta_historica": apresentar_origem(dados.get("origem")),
                 "guarda": guarda,
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
