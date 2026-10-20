"""Balcão HTTP da PoC. As regras continuam nas funções de domínio."""

from pathlib import Path
from urllib.parse import urlencode
import uuid

from fastapi import Depends, FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.banco import motor
from app.consultas_interface import (carregar_opcoes_novo_registro, carregar_painel,
                                     carregar_registro)
from app.eventos import registrar_auditoria
from app.form1_sintetico import (CATEGORIAS_DADOS, CATEGORIAS_TITULARES,
                                 DESTINATARIOS_COMPARTILHAMENTO)
from app.instrumentos import iniciar_preenchimento, salvar_rascunho
from app.modelos import ObjetoCatalogo
from app.workflow import criar_registro


PASTA_APP = Path(__file__).resolve().parent
app = FastAPI(title="PoC LGPD Hortolândia", docs_url=None, redoc_url=None)
app.mount("/estaticos", StaticFiles(directory=PASTA_APP / "estaticos"), name="estaticos")
paginas = Jinja2Templates(directory=PASTA_APP / "paginas")


def obter_sessao():
    with Session(motor) as sessao:
        yield sessao


@app.get("/", response_class=HTMLResponse)
def inicio(
    request: Request,
    conta_id: str = Query(default="CONTA-A1", max_length=50),
    sessao: Session = Depends(obter_sessao),
):
    painel = carregar_painel(sessao, conta_id)
    if painel is None:
        return paginas.TemplateResponse(
            request=request,
            name="erro.html",
            context={"titulo": "Conta indisponível", "mensagem": "A conta fictícia não existe ou está inativa."},
            status_code=404,
        )
    return paginas.TemplateResponse(
        request=request,
        name="inicio.html",
        context={**painel, "conta_id": conta_id},
    )


@app.get("/registros/novo", response_class=HTMLResponse)
def novo_registro(
    request: Request,
    conta_id: str = Query(default="CONTA-A1", max_length=50),
    mensagem: str | None = Query(default=None, max_length=500),
    erro: bool = Query(default=False),
    sessao: Session = Depends(obter_sessao),
):
    opcoes = carregar_opcoes_novo_registro(sessao, conta_id)
    if opcoes is None:
        return paginas.TemplateResponse(
            request=request,
            name="erro.html",
            context={"titulo": "Conta indisponível", "mensagem": "A identidade fictícia não existe ou está inativa."},
            status_code=404,
        )
    return paginas.TemplateResponse(
        request=request,
        name="novo_registro.html",
        context={
            **opcoes,
            "conta_id": conta_id,
            "mensagem": mensagem,
            "erro": erro,
            "comando_g1": str(uuid.uuid4()),
        },
    )


@app.post("/registros")
def criar_registro_pela_tela(
    conta_id: str = Form(max_length=50),
    comando_id: str = Form(max_length=64),
    tipo_objeto: str = Form(max_length=20),
    objeto_principal_id: str = Form(max_length=50),
    unidade_id: str = Form(max_length=50),
    contexto_id: str = Form(max_length=20),
    sessao: Session = Depends(obter_sessao),
):
    objeto = sessao.get(ObjetoCatalogo, objeto_principal_id)
    if objeto is None or not objeto.ativo or tipo_objeto not in {"servico", "processo", "atividade"}:
        parametros = {"conta_id": conta_id, "mensagem": "Objeto ou tipo fora do catálogo ativo.", "erro": "1"}
        return RedirectResponse(url=f"/registros/novo?{urlencode(parametros)}", status_code=303)
    if objeto.tipo_objeto != tipo_objeto:
        parametros = {
            "conta_id": conta_id,
            "mensagem": "O tipo escolhido não corresponde ao item do catálogo.",
            "erro": "1",
        }
        return RedirectResponse(url=f"/registros/novo?{urlencode(parametros)}", status_code=303)
    resultado = criar_registro(
        sessao,
        comando_id=comando_id,
        conta_id=conta_id,
        unidade_id=unidade_id,
        contexto_id=contexto_id,
        titulo_objeto=objeto.nome_canonico,
        objeto_principal_id=objeto.id,
    )
    sessao.commit()
    if resultado["permitido"]:
        parametros = {
            "conta_id": conta_id,
            "mensagem": "Registro criado. Confirme o contexto antes de iniciar o FORM 1.",
            "erro": "0",
        }
        return RedirectResponse(
            url=f"/registros/{resultado['registro_id']}?{urlencode(parametros)}",
            status_code=303,
        )
    parametros = {"conta_id": conta_id, "mensagem": resultado["motivo"], "erro": "1"}
    return RedirectResponse(url=f"/registros/novo?{urlencode(parametros)}", status_code=303)


@app.get("/registros/{registro_id}", response_class=HTMLResponse)
def detalhe_registro(
    registro_id: str,
    request: Request,
    conta_id: str = Query(default="CONTA-A1", max_length=50),
    mensagem: str | None = Query(default=None, max_length=300),
    erro: bool = Query(default=False),
    sessao: Session = Depends(obter_sessao),
):
    identidade, registro = carregar_registro(sessao, conta_id, registro_id)
    if identidade is None:
        return paginas.TemplateResponse(
            request=request,
            name="erro.html",
            context={"titulo": "Conta indisponível", "mensagem": "A conta fictícia não existe ou está inativa."},
            status_code=404,
        )
    if registro is None:
        return paginas.TemplateResponse(
            request=request,
            name="erro.html",
            context={"titulo": "Registro não encontrado", "mensagem": "O Registro informado não existe."},
            status_code=404,
        )
    if registro is False:
        registrar_auditoria(
            sessao,
            "tentativa_negada",
            "pessoa",
            identidade["pessoa_id"],
            {
                "acao_tentada": "consultar_registro",
                "objeto": registro_id,
                "conta_id": conta_id,
                "motivo": "Registro fora do alcance institucional da pessoa",
            },
        )
        sessao.commit()
        return paginas.TemplateResponse(
            request=request,
            name="erro.html",
            context={
                "titulo": "Acesso negado",
                "mensagem": "Este Registro não pertence ao alcance institucional do agente simulado.",
            },
            status_code=403,
        )
    return paginas.TemplateResponse(
        request=request,
        name="registro.html",
        context={
            "identidade": identidade,
            "registro": registro,
            "conta_id": conta_id,
            "mensagem": mensagem,
            "erro": erro,
            "comando_i1": str(uuid.uuid4()),
            "comando_i2": str(uuid.uuid4()),
        },
    )


def _voltar_ao_registro(registro_id, conta_id, resultado, sucesso):
    parametros = {
        "conta_id": conta_id,
        "mensagem": sucesso if resultado["permitido"] else resultado["motivo"],
        "erro": "0" if resultado["permitido"] else "1",
    }
    return RedirectResponse(
        url=f"/registros/{registro_id}?{urlencode(parametros)}",
        status_code=303,
    )


@app.post("/registros/{registro_id}/form1/iniciar")
def iniciar_form1(
    registro_id: str,
    conta_id: str = Form(max_length=50),
    comando_id: str = Form(max_length=64),
    sessao: Session = Depends(obter_sessao),
):
    _, registro = carregar_registro(sessao, conta_id, registro_id)
    if not isinstance(registro, dict):
        return RedirectResponse(url=f"/?{urlencode({'conta_id': conta_id})}", status_code=303)
    resultado = iniciar_preenchimento(
        sessao,
        comando_id=comando_id,
        conta_id=conta_id,
        instrumento_id=registro["form1"]["id"],
    )
    sessao.commit()
    return _voltar_ao_registro(
        registro_id, conta_id, resultado, "FORM 1 iniciado. O rascunho está pronto para preenchimento."
    )


def _conteudo_form1(finalidade, titulares, dados, compartilhamentos):
    listas = (
        ("categorias de titulares", titulares, CATEGORIAS_TITULARES),
        ("categorias de dados", dados, CATEGORIAS_DADOS),
        ("compartilhamentos", compartilhamentos, DESTINATARIOS_COMPARTILHAMENTO),
    )
    for nome, valores, catalogo in listas:
        if len(valores) != len(set(valores)) or any(valor not in catalogo for valor in valores):
            return None, f"{nome}: a seleção contém opção inválida ou repetida"
    finalidade = finalidade.strip()
    if len(finalidade) > 500:
        return None, "a finalidade deve ter no máximo 500 caracteres"
    return {
        "finalidade": finalidade,
        "categorias_titulares": titulares,
        "categorias_dados": dados,
        "compartilhamentos": compartilhamentos,
    }, None


@app.post("/registros/{registro_id}/form1/salvar")
def salvar_form1(
    registro_id: str,
    conta_id: str = Form(max_length=50),
    comando_id: str = Form(max_length=64),
    versao_lida: int = Form(ge=1),
    finalidade: str = Form(default="", max_length=500),
    categorias_titulares: list[str] | None = Form(default=None),
    categorias_dados: list[str] | None = Form(default=None),
    compartilhamentos: list[str] | None = Form(default=None),
    sessao: Session = Depends(obter_sessao),
):
    _, registro = carregar_registro(sessao, conta_id, registro_id)
    if not isinstance(registro, dict):
        return RedirectResponse(url=f"/?{urlencode({'conta_id': conta_id})}", status_code=303)
    conteudo, problema = _conteudo_form1(
        finalidade,
        categorias_titulares or [],
        categorias_dados or [],
        compartilhamentos or [],
    )
    if problema:
        return _voltar_ao_registro(
            registro_id, conta_id, {"permitido": False, "motivo": problema}, ""
        )
    resultado = salvar_rascunho(
        sessao,
        comando_id=comando_id,
        conta_id=conta_id,
        instrumento_id=registro["form1"]["id"],
        versao_lida=versao_lida,
        conteudo=conteudo,
    )
    sessao.commit()
    return _voltar_ao_registro(
        registro_id, conta_id, resultado, "Rascunho salvo com segurança."
    )
