"""Balcão HTTP da PoC. As regras continuam nas funções de domínio."""

from pathlib import Path
from urllib.parse import urlencode
import uuid

from fastapi import Depends, FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.atribuicao_form1_integral import atribuir_arp_form1_integral
from app.banco import motor
from app.consultas_interface import (carregar_opcoes_novo_registro, carregar_painel,
                                     carregar_registro)
from app.eventos import registrar_auditoria
from app.form1_sintetico import (CATEGORIAS_DADOS, CATEGORIAS_TITULARES,
                                 DESTINATARIOS_COMPARTILHAMENTO)
from app.form1_integral import (IDS_BLOCO_2, IDS_BLOCO_4, IDS_BLOCO_5, IDS_BLOCO_6, IDS_BLOCO_7, IDS_BLOCO_8, IDS_BLOCO_9, IDS_BLOCO_10, IDS_BLOCO_11, IDS_BLOCO_12, IDS_BLOCO_13, IDS_BLOCO_14,
                                IDS_PARTICIPANTE_BLOCO_3,
                                alternativas_outro_por_campo, campos_por_id)
from app.instrumentos import iniciar_preenchimento, salvar_rascunho
from app.modelos import ObjetoCatalogo
from app.rascunho_form1_integral import (adicionar_participante_form1_integral,
                                         iniciar_rascunho_form1_integral,
                                         remover_participante_form1_integral,
                                         salvar_bloco_1_form1_integral,
                                         salvar_bloco_2_form1_integral,
                                         salvar_bloco_4_form1_integral,
                                         salvar_bloco_5_form1_integral,
                                         salvar_bloco_6_form1_integral,
                                         salvar_bloco_7_form1_integral,
                                         salvar_bloco_8_form1_integral,
                                         salvar_bloco_9_form1_integral,
                                         salvar_bloco_10_form1_integral,
                                         salvar_bloco_11_form1_integral,
                                         salvar_bloco_12_form1_integral,
                                         salvar_bloco_13_form1_integral,
                                         salvar_bloco_14_form1_integral,
                                         salvar_cabecalho_bloco_3_form1_integral)
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
    canais_ids: list[str] | None = Form(default=None),
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
        canais_confirmados_ids=[] if canais_ids is None else canais_ids,
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
            "comando_atribuir_arp": str(uuid.uuid4()),
            "comando_iniciar_integral": str(uuid.uuid4()),
            "comando_salvar_integral": str(uuid.uuid4()),
            "comando_salvar_bloco_2": str(uuid.uuid4()),
            "comando_salvar_bloco_3": str(uuid.uuid4()),
            "comando_adicionar_participante": str(uuid.uuid4()),
            "comando_salvar_bloco_4": str(uuid.uuid4()),
            "comando_salvar_bloco_5": str(uuid.uuid4()),
            "comando_salvar_bloco_6": str(uuid.uuid4()),
            "comando_salvar_bloco_7": str(uuid.uuid4()),
            "comando_salvar_bloco_8": str(uuid.uuid4()),
            "comando_salvar_bloco_9": str(uuid.uuid4()),
            "comando_salvar_bloco_10": str(uuid.uuid4()),
            "comando_salvar_bloco_11": str(uuid.uuid4()),
            "comando_salvar_bloco_12": str(uuid.uuid4()),
            "comando_salvar_bloco_13": str(uuid.uuid4()),
            "comando_salvar_bloco_14": str(uuid.uuid4()),
            "comandos_remover_participante": {
                participante["id"]: str(uuid.uuid4())
                for participante in (
                    registro["form1_integral"]["rascunho"]["participantes"]
                    if registro["form1_integral"]["rascunho"] else []
                )
            },
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


@app.post("/registros/{registro_id}/form1-integral/atribuir-arp")
def atribuir_arp_integral(
    registro_id: str,
    conta_id: str = Form(max_length=50),
    comando_id: str = Form(max_length=64),
    modo: str = Form(max_length=20),
    arp_pessoa_id: str | None = Form(default=None, max_length=50),
    versao_lida: int = Form(ge=0),
    sessao: Session = Depends(obter_sessao),
):
    _, registro = carregar_registro(sessao, conta_id, registro_id)
    if not isinstance(registro, dict):
        return RedirectResponse(url=f"/?{urlencode({'conta_id': conta_id})}", status_code=303)
    resultado = atribuir_arp_form1_integral(
        sessao,
        comando_id=comando_id,
        conta_id=conta_id,
        registro_id=registro_id,
        modo=modo,
        arp_pessoa_id=arp_pessoa_id,
        versao_lida=versao_lida,
    )
    sessao.commit()
    return _voltar_ao_registro(
        registro_id, conta_id, resultado, "Responsável pelo preenchimento do FORM 1 integral definido."
    )


@app.post("/registros/{registro_id}/form1-integral/iniciar")
def iniciar_form1_integral(
    registro_id: str,
    conta_id: str = Form(max_length=50),
    comando_id: str = Form(max_length=64),
    sessao: Session = Depends(obter_sessao),
):
    _, registro = carregar_registro(sessao, conta_id, registro_id)
    if not isinstance(registro, dict):
        return RedirectResponse(url=f"/?{urlencode({'conta_id': conta_id})}", status_code=303)
    resultado = iniciar_rascunho_form1_integral(
        sessao,
        comando_id=comando_id,
        conta_id=conta_id,
        registro_id=registro_id,
    )
    sessao.commit()
    return _voltar_ao_registro(
        registro_id, conta_id, resultado, "Rascunho do FORM 1 integral iniciado."
    )


@app.post("/registros/{registro_id}/form1-integral/bloco-1/salvar")
def salvar_bloco_1_integral(
    registro_id: str,
    conta_id: str = Form(max_length=50),
    comando_id: str = Form(max_length=64),
    versao_lida: int = Form(ge=1),
    referencia_existente: str = Form(default="", max_length=100),
    referencia_institucional: str = Form(default="", max_length=500),
    fluxo_recorrente: str = Form(default="", max_length=100),
    sessao: Session = Depends(obter_sessao),
):
    _, registro = carregar_registro(sessao, conta_id, registro_id)
    if not isinstance(registro, dict):
        return RedirectResponse(url=f"/?{urlencode({'conta_id': conta_id})}", status_code=303)
    respostas = {
        chave: valor.strip()
        for chave, valor in {
            "1.1": referencia_existente,
            "1.1.1": referencia_institucional,
            "1.4": fluxo_recorrente,
        }.items()
        if valor.strip()
    }
    resultado = salvar_bloco_1_form1_integral(
        sessao,
        comando_id=comando_id,
        conta_id=conta_id,
        registro_id=registro_id,
        versao_lida=versao_lida,
        respostas=respostas,
    )
    sessao.commit()
    return _voltar_ao_registro(
        registro_id, conta_id, resultado, "Bloco 1 do FORM 1 integral salvo com segurança."
    )


def _respostas_do_formulario(formulario, campo_ids):
    catalogo = campos_por_id()
    respostas = {}
    for campo_id in campo_ids:
        nome = f"campo__{campo_id}"
        if catalogo[campo_id].controle in {
            "seleção múltipla (combo com marcações)",
            "reuso do catálogo de referência (ver campo indicado)",
        }:
            valores = [valor.strip() for valor in formulario.getlist(nome) if valor.strip()]
            if valores:
                respostas[campo_id] = valores
        else:
            valor = str(formulario.get(nome, "")).strip()
            if valor:
                respostas[campo_id] = valor
    return respostas


def _complementos_outro_do_formulario(formulario, campo_ids):
    elegiveis = set(alternativas_outro_por_campo()) & set(campo_ids)
    return {
        campo_id: str(formulario.get(f"complemento_outro__{campo_id}", ""))
        for campo_id in elegiveis
    }


@app.post("/registros/{registro_id}/form1-integral/bloco-2/salvar")
async def salvar_bloco_2_integral(
    registro_id: str, request: Request, sessao: Session = Depends(obter_sessao),
):
    formulario = await request.form()
    conta_id = str(formulario.get("conta_id", ""))[:50]
    _, registro = carregar_registro(sessao, conta_id, registro_id)
    if not isinstance(registro, dict):
        return RedirectResponse(url=f"/?{urlencode({'conta_id': conta_id})}", status_code=303)
    resultado = salvar_bloco_2_form1_integral(
        sessao,
        comando_id=str(formulario.get("comando_id", ""))[:64],
        conta_id=conta_id,
        registro_id=registro_id,
        versao_lida=int(formulario.get("versao_lida", 0)),
        respostas=_respostas_do_formulario(formulario, IDS_BLOCO_2),
        complementos_outro=_complementos_outro_do_formulario(formulario, IDS_BLOCO_2),
    )
    sessao.commit()
    return _voltar_ao_registro(
        registro_id, conta_id, resultado, "Bloco 2 do FORM 1 integral salvo com segurança."
    )


@app.post("/registros/{registro_id}/form1-integral/bloco-4/salvar")
async def salvar_bloco_4_integral(
    registro_id: str, request: Request, sessao: Session = Depends(obter_sessao),
):
    formulario = await request.form()
    conta_id = str(formulario.get("conta_id", ""))[:50]
    resultado = salvar_bloco_4_form1_integral(
        sessao,
        comando_id=str(formulario.get("comando_id", ""))[:64],
        conta_id=conta_id,
        registro_id=registro_id,
        versao_lida=int(formulario.get("versao_lida", 0)),
        respostas=_respostas_do_formulario(formulario, IDS_BLOCO_4),
        complementos_outro=_complementos_outro_do_formulario(formulario, IDS_BLOCO_4),
    )
    sessao.commit()
    return _voltar_ao_registro(
        registro_id, conta_id, resultado, "Bloco 4 do FORM 1 integral salvo com segurança."
    )


@app.post("/registros/{registro_id}/form1-integral/bloco-5/salvar")
async def salvar_bloco_5_integral(
    registro_id: str, request: Request, sessao: Session = Depends(obter_sessao),
):
    formulario = await request.form()
    conta_id = str(formulario.get("conta_id", ""))[:50]
    resultado = salvar_bloco_5_form1_integral(
        sessao,
        comando_id=str(formulario.get("comando_id", ""))[:64],
        conta_id=conta_id,
        registro_id=registro_id,
        versao_lida=int(formulario.get("versao_lida", 0)),
        respostas=_respostas_do_formulario(formulario, IDS_BLOCO_5),
        complemento_outro=formulario.get("complemento_outro_5_1", ""),
    )
    sessao.commit()
    return _voltar_ao_registro(
        registro_id, conta_id, resultado, "Bloco 5 do FORM 1 integral salvo com segurança."
    )


@app.post("/registros/{registro_id}/form1-integral/bloco-6/salvar")
async def salvar_bloco_6_integral(
    registro_id: str, request: Request, sessao: Session = Depends(obter_sessao),
):
    formulario = await request.form()
    conta_id = str(formulario.get("conta_id", ""))[:50]
    resultado = salvar_bloco_6_form1_integral(
        sessao,
        comando_id=str(formulario.get("comando_id", ""))[:64],
        conta_id=conta_id,
        registro_id=registro_id,
        versao_lida=int(formulario.get("versao_lida", 0)),
        respostas=_respostas_do_formulario(formulario, IDS_BLOCO_6),
        complementos_outro=_complementos_outro_do_formulario(formulario, IDS_BLOCO_6),
    )
    sessao.commit()
    return _voltar_ao_registro(
        registro_id, conta_id, resultado, "Bloco 6 do FORM 1 integral salvo com segurança."
    )


@app.post("/registros/{registro_id}/form1-integral/bloco-7/salvar")
async def salvar_bloco_7_integral(
    registro_id: str, request: Request, sessao: Session = Depends(obter_sessao),
):
    formulario = await request.form()
    conta_id = str(formulario.get("conta_id", ""))[:50]
    resultado = salvar_bloco_7_form1_integral(
        sessao, comando_id=str(formulario.get("comando_id", ""))[:64],
        conta_id=conta_id, registro_id=registro_id,
        versao_lida=int(formulario.get("versao_lida", 0)),
        respostas=_respostas_do_formulario(formulario, IDS_BLOCO_7),
        complementos_outro=_complementos_outro_do_formulario(formulario, IDS_BLOCO_7),
    )
    sessao.commit()
    return _voltar_ao_registro(
        registro_id, conta_id, resultado, "Bloco 7 do FORM 1 integral salvo com segurança."
    )


@app.post("/registros/{registro_id}/form1-integral/bloco-8/salvar")
async def salvar_bloco_8_integral(
    registro_id: str, request: Request, sessao: Session = Depends(obter_sessao),
):
    formulario = await request.form()
    conta_id = str(formulario.get("conta_id", ""))[:50]
    resultado = salvar_bloco_8_form1_integral(
        sessao, comando_id=str(formulario.get("comando_id", ""))[:64],
        conta_id=conta_id, registro_id=registro_id,
        versao_lida=int(formulario.get("versao_lida", 0)),
        respostas=_respostas_do_formulario(formulario, IDS_BLOCO_8),
        complementos_outro=_complementos_outro_do_formulario(formulario, IDS_BLOCO_8),
    )
    sessao.commit()
    return _voltar_ao_registro(
        registro_id, conta_id, resultado, "Bloco 8 do FORM 1 integral salvo com segurança."
    )


@app.post("/registros/{registro_id}/form1-integral/bloco-9/salvar")
async def salvar_bloco_9_integral(
    registro_id: str, request: Request, sessao: Session = Depends(obter_sessao),
):
    formulario = await request.form()
    conta_id = str(formulario.get("conta_id", ""))[:50]
    resultado = salvar_bloco_9_form1_integral(
        sessao, comando_id=str(formulario.get("comando_id", ""))[:64],
        conta_id=conta_id, registro_id=registro_id,
        versao_lida=int(formulario.get("versao_lida", 0)),
        respostas=_respostas_do_formulario(formulario, IDS_BLOCO_9),
        complementos_outro=_complementos_outro_do_formulario(formulario, IDS_BLOCO_9),
    )
    sessao.commit()
    return _voltar_ao_registro(
        registro_id, conta_id, resultado, "Bloco 9 do FORM 1 integral salvo com segurança."
    )


@app.post("/registros/{registro_id}/form1-integral/bloco-10/salvar")
async def salvar_bloco_10_integral(
    registro_id: str, request: Request, sessao: Session = Depends(obter_sessao),
):
    formulario = await request.form()
    conta_id = str(formulario.get("conta_id", ""))[:50]
    resultado = salvar_bloco_10_form1_integral(
        sessao, comando_id=str(formulario.get("comando_id", ""))[:64],
        conta_id=conta_id, registro_id=registro_id,
        versao_lida=int(formulario.get("versao_lida", 0)),
        respostas=_respostas_do_formulario(formulario, IDS_BLOCO_10),
        complementos_outro=_complementos_outro_do_formulario(formulario, IDS_BLOCO_10),
    )
    sessao.commit()
    return _voltar_ao_registro(
        registro_id, conta_id, resultado, "Bloco 10 do FORM 1 integral salvo com segurança."
    )


@app.post("/registros/{registro_id}/form1-integral/bloco-11/salvar")
async def salvar_bloco_11_integral(
    registro_id: str, request: Request, sessao: Session = Depends(obter_sessao),
):
    formulario = await request.form()
    conta_id = str(formulario.get("conta_id", ""))[:50]
    resultado = salvar_bloco_11_form1_integral(
        sessao, comando_id=str(formulario.get("comando_id", ""))[:64], conta_id=conta_id,
        registro_id=registro_id, versao_lida=int(formulario.get("versao_lida", 0)),
        respostas=_respostas_do_formulario(formulario, IDS_BLOCO_11),
        complementos_outro=_complementos_outro_do_formulario(formulario, IDS_BLOCO_11),
    )
    sessao.commit()
    return _voltar_ao_registro(registro_id, conta_id, resultado, "Bloco 11 do FORM 1 integral salvo com segurança.")


@app.post("/registros/{registro_id}/form1-integral/bloco-12/salvar")
async def salvar_bloco_12_integral(
    registro_id: str, request: Request, sessao: Session = Depends(obter_sessao),
):
    formulario = await request.form()
    conta_id = str(formulario.get("conta_id", ""))[:50]
    resultado = salvar_bloco_12_form1_integral(
        sessao, comando_id=str(formulario.get("comando_id", ""))[:64], conta_id=conta_id,
        registro_id=registro_id, versao_lida=int(formulario.get("versao_lida", 0)),
        respostas=_respostas_do_formulario(formulario, IDS_BLOCO_12),
        complementos_outro=_complementos_outro_do_formulario(formulario, IDS_BLOCO_12),
    )
    sessao.commit()
    return _voltar_ao_registro(registro_id, conta_id, resultado, "Bloco 12 do FORM 1 integral salvo com segurança.")


@app.post("/registros/{registro_id}/form1-integral/bloco-13/salvar")
async def salvar_bloco_13_integral(
    registro_id: str, request: Request, sessao: Session = Depends(obter_sessao),
):
    formulario = await request.form()
    conta_id = str(formulario.get("conta_id", ""))[:50]
    resultado = salvar_bloco_13_form1_integral(
        sessao, comando_id=str(formulario.get("comando_id", ""))[:64], conta_id=conta_id,
        registro_id=registro_id, versao_lida=int(formulario.get("versao_lida", 0)),
        respostas=_respostas_do_formulario(formulario, IDS_BLOCO_13),
        complementos_outro=_complementos_outro_do_formulario(formulario, IDS_BLOCO_13),
    )
    sessao.commit()
    return _voltar_ao_registro(registro_id, conta_id, resultado, "Bloco 13 do FORM 1 integral salvo com segurança.")


@app.post("/registros/{registro_id}/form1-integral/bloco-14/salvar")
async def salvar_bloco_14_integral(
    registro_id: str, request: Request, sessao: Session = Depends(obter_sessao),
):
    formulario = await request.form()
    conta_id = str(formulario.get("conta_id", ""))[:50]
    resultado = salvar_bloco_14_form1_integral(
        sessao, comando_id=str(formulario.get("comando_id", ""))[:64], conta_id=conta_id,
        registro_id=registro_id, versao_lida=int(formulario.get("versao_lida", 0)),
        respostas=_respostas_do_formulario(formulario, IDS_BLOCO_14),
        complementos_outro=_complementos_outro_do_formulario(formulario, IDS_BLOCO_14),
    )
    sessao.commit()
    return _voltar_ao_registro(registro_id, conta_id, resultado, "Bloco 14 do FORM 1 integral salvo com segurança.")


@app.post("/registros/{registro_id}/form1-integral/bloco-3/salvar")
def salvar_bloco_3_integral(
    registro_id: str,
    conta_id: str = Form(max_length=50),
    comando_id: str = Form(max_length=64),
    versao_lida: int = Form(ge=1),
    resposta_3_1: str = Form(default="", max_length=50),
    sessao: Session = Depends(obter_sessao),
):
    resultado = salvar_cabecalho_bloco_3_form1_integral(
        sessao, comando_id=comando_id, conta_id=conta_id,
        registro_id=registro_id, versao_lida=versao_lida,
        resposta_3_1=resposta_3_1.strip(),
    )
    sessao.commit()
    return _voltar_ao_registro(
        registro_id, conta_id, resultado, "Bloco 3 do FORM 1 integral salvo com segurança."
    )


@app.post("/registros/{registro_id}/form1-integral/participantes/adicionar")
async def adicionar_participante_integral(
    registro_id: str, request: Request, sessao: Session = Depends(obter_sessao),
):
    formulario = await request.form()
    conta_id = str(formulario.get("conta_id", ""))[:50]
    resultado = adicionar_participante_form1_integral(
        sessao,
        comando_id=str(formulario.get("comando_id", ""))[:64],
        conta_id=conta_id,
        registro_id=registro_id,
        versao_lida=int(formulario.get("versao_lida", 0)),
        respostas=_respostas_do_formulario(formulario, IDS_PARTICIPANTE_BLOCO_3),
        complementos_outro=_complementos_outro_do_formulario(
            formulario, IDS_PARTICIPANTE_BLOCO_3
        ),
    )
    sessao.commit()
    return _voltar_ao_registro(
        registro_id, conta_id, resultado, "Participante do Bloco 3 adicionado."
    )


@app.post("/registros/{registro_id}/form1-integral/participantes/{participante_id}/remover")
def remover_participante_integral(
    registro_id: str,
    participante_id: str,
    conta_id: str = Form(max_length=50),
    comando_id: str = Form(max_length=64),
    versao_lida: int = Form(ge=1),
    sessao: Session = Depends(obter_sessao),
):
    resultado = remover_participante_form1_integral(
        sessao, comando_id=comando_id, conta_id=conta_id,
        registro_id=registro_id, versao_lida=versao_lida,
        participante_id=participante_id,
    )
    sessao.commit()
    return _voltar_ao_registro(
        registro_id, conta_id, resultado, "Participante do Bloco 3 removido."
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
