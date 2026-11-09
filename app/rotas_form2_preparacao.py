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
from app.modelos import Unidade
from app.consultas_interface import pode_consultar_registro
from app.apresentacao_form2 import apresentar_origem, identificar_agentes, unidade_guarda, PAPEIS
from app.form2_preparacao import consultar_preparacao, iniciar_preparacao, salvar_preparacao

router = APIRouter()
paginas = Jinja2Templates(directory=Path(__file__).parent / "paginas")


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
            snapshot_id=None, erro=None, anotacao_tentada=None, versao_tentada=None):
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
    alvo = dados["preparacao"]
    if alvo is None and dados["origem"]:
        sid = dados["origem"]["snapshot"].id
        alvo = next((item for item in visiveis if item.snapshot_id == sid), None)
    elif alvo is None and not dados["e_apa"] and visiveis:
        editaveis = dados["preparacoes_editaveis"]
        alvo = next((item for item in reversed(visiveis) if item.id in editaveis), visiveis[-1])
    return paginas.TemplateResponse(request=request, name="form2_preparacao.html",
        status_code=409 if erro else 200,
        context={**dados, "contexto_navegacao": _contexto_navegacao(request), "alvo": alvo,
                 "secretaria": sessao.get(Unidade, dados["registro"].unidade_principal_atual_id),
                 "consulta_historica": apresentar_origem(dados.get("origem")),
                 "guarda": unidade_guarda(dados),
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


def _redirecionar(request, registro_id, conta_id, preparacao_id):
    url = str(request.url_for("form2_preparacao", registro_id=registro_id))
    return RedirectResponse(url + "?" + urlencode({"conta_id": conta_id,
        "preparacao_id": preparacao_id, **_contexto_navegacao(request)}) + "#anotacoes", status_code=303)


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
        return _redirecionar(request, registro_id, form["conta_id"], preparacao_id)
    return _pagina(request, sessao, registro_id, form["conta_id"], preparacao_id=preparacao_id,
        erro=resultado["motivo"], anotacao_tentada=form["anotacao_preparatoria"], versao_tentada=versao)
