"""Consultas preparadas para a interface, sem regras de negócio nos templates."""

from sqlalchemy import select

from app.alertas_operacionais import listar_alertas_operacionais
from app.form1_sintetico import (CATEGORIAS_DADOS, CATEGORIAS_TITULARES,
                                 DESTINATARIOS_COMPARTILHAMENTO)
from app.modelos import (Conta, ContextoAtuacao, Designacao, Instrumento,
                         ObjetoCatalogo, ObjetoContextoCatalogo,
                         UnidadeObjetoCatalogo, Pendencia, Pessoa,
                         RascunhoInstrumento, Registro, Unidade)


ROTULOS_ESTADO = {
    "em_andamento": "Em andamento",
    "em_validacao": "Em validação",
    "em_execucao": "Em execução",
    "suspenso": "Suspenso",
    "concluido": "Concluído",
    "cancelado": "Cancelado",
}

ROTULOS_ESTADO_FORM1 = {
    "nao_iniciado": "Não iniciado",
    "em_preenchimento": "Em preenchimento",
    "pronto_para_validacao": "Pronto para validação",
    "devolvido_para_ajuste": "Devolvido para ajuste",
    "validado": "Validado",
}

ROTULOS_ALERTA = {
    "CORRECAO_SOLICITADA": "Correção solicitada",
    "PENDENCIA_ATRIBUIDA_A_VOCE": "Pendência atribuída a você",
    "RESPOSTA_AGUARDANDO_DECISAO": "Resposta aguardando decisão",
    "COMPLEMENTACAO_SOLICITADA": "Complementação solicitada",
    "SUBMISSAO_BLOQUEADA": "Submissão bloqueada",
    "PROVIDENCIA_INTERSECRETARIAL_RECEBIDA": "Providência de outra unidade recebida",
    "PROVIDENCIA_INTERSECRETARIAL_ATRIBUIDA_A_VOCE": "Providência atribuída a você",
    "RESPOSTA_INTERSECRETARIAL_AGUARDANDO_DECISAO": "Resposta de outra unidade aguardando decisão",
    "CONCLUSAO_BLOQUEADA": "Conclusão bloqueada",
}


def _identidade(sessao, conta_id):
    conta = sessao.get(Conta, conta_id)
    if conta is None or not conta.ativa:
        return None
    pessoa = sessao.get(Pessoa, conta.pessoa_id)
    if pessoa is None or not pessoa.ativa:
        return None

    designacoes = sessao.execute(
        select(Designacao.papel, Unidade.id, Unidade.nome)
        .join(Unidade, Unidade.id == Designacao.unidade_id)
        .where(Designacao.pessoa_id == pessoa.id, Designacao.ativa.is_(True))
        .order_by(Unidade.nome, Designacao.papel)
    ).all()
    return {
        "conta_id": conta.id,
        "pessoa_id": pessoa.id,
        "matricula": pessoa.matricula,
        "nome": pessoa.nome,
        "designacoes": [
            {"papel": papel, "unidade_id": unidade_id, "unidade": unidade}
            for papel, unidade_id, unidade in designacoes
        ],
    }


def _ids_visiveis(sessao, identidade):
    """Registros da unidade da pessoa ou alcançados por pendência vigente."""
    unidades = {item["unidade_id"] for item in identidade["designacoes"]}
    unidades_pendencia = {
        item["unidade_id"]
        for item in identidade["designacoes"]
        if item["papel"] in {"agente_pendencia", "preenchedor", "validador"}
    }
    ids = set(sessao.scalars(
        select(Registro.id).where(Registro.unidade_principal_atual_id.in_(unidades))
    ).all()) if unidades else set()

    pendencias = sessao.scalars(
        select(Pendencia).where(Pendencia.estado.not_in({"encerrada", "cancelada"}))
    ).all()
    for pendencia in pendencias:
        participa = (
            pendencia.responsavel_atual_id == identidade["pessoa_id"]
            or pendencia.unidade_destino_id in unidades_pendencia
            or pendencia.unidade_origem_id in unidades_pendencia
        )
        if participa:
            ids.add(pendencia.registro_id)
    return ids


def _resumo_registro(registro, unidade):
    return {
        "id": registro.id,
        "codigo_lgpd": registro.codigo_lgpd,
        "titulo": registro.titulo_objeto,
        "tipo": registro.tipo_objeto.capitalize(),
        "estado": ROTULOS_ESTADO.get(registro.estado_atual, registro.estado_atual),
        "estado_codigo": registro.estado_atual,
        "unidade": unidade.nome,
        "contexto_id": registro.contexto_atuacao_id,
        "ciclo": registro.ciclo_atual,
    }


def carregar_painel(sessao, conta_id):
    identidade = _identidade(sessao, conta_id)
    if identidade is None:
        return None
    ids = _ids_visiveis(sessao, identidade)
    linhas = sessao.execute(
        select(Registro, Unidade)
        .join(Unidade, Unidade.id == Registro.unidade_principal_atual_id)
        .where(Registro.id.in_(ids))
        .order_by(Registro.codigo_lgpd)
    ).all() if ids else []
    registros = [_resumo_registro(registro, unidade) for registro, unidade in linhas]

    codigos = {item["id"]: item["codigo_lgpd"] for item in registros}
    alertas = listar_alertas_operacionais(sessao, conta_id)
    for alerta in alertas:
        alerta["rotulo"] = ROTULOS_ALERTA.get(alerta["codigo"], alerta["codigo"])
        alerta["codigo_lgpd"] = codigos.get(alerta["registro_id"], "Registro relacionado")
    pode_criar_registro = any(
        item["papel"] == "responsavel_registro" for item in identidade["designacoes"]
    )
    return {
        "identidade": identidade,
        "registros": registros,
        "alertas": alertas,
        "pode_criar_registro": pode_criar_registro,
    }


def carregar_opcoes_novo_registro(sessao, conta_id):
    """Catálogos e unidades em que a pessoa pode criar um Registro pelo G1."""
    identidade = _identidade(sessao, conta_id)
    if identidade is None:
        return None
    unidades = []
    vistos = set()
    for item in identidade["designacoes"]:
        if item["papel"] == "responsavel_registro" and item["unidade_id"] not in vistos:
            vistos.add(item["unidade_id"])
            unidades.append({"id": item["unidade_id"], "nome": item["unidade"]})
    linhas_objetos = sessao.execute(
        select(ObjetoCatalogo, UnidadeObjetoCatalogo.unidade_id)
        .join(UnidadeObjetoCatalogo, UnidadeObjetoCatalogo.objeto_id == ObjetoCatalogo.id)
        .where(
            ObjetoCatalogo.ativo.is_(True),
            UnidadeObjetoCatalogo.unidade_id.in_(vistos),
            UnidadeObjetoCatalogo.papel == "RESPONSAVEL",
            UnidadeObjetoCatalogo.vigente_ate.is_(None),
        )
        .order_by(ObjetoCatalogo.tipo_objeto, ObjetoCatalogo.nome_canonico)
    ).all() if vistos else []
    objetos_por_id = {}
    for objeto, unidade_id in linhas_objetos:
        item = objetos_por_id.setdefault(objeto.id, {
            "id": objeto.id,
            "tipo_objeto": objeto.tipo_objeto,
            "nome_canonico": objeto.nome_canonico,
            "unidades": [],
        })
        item["unidades"].append(unidade_id)
    objetos = list(objetos_por_id.values())
    ids_objetos = set(objetos_por_id)
    linhas_contextos = sessao.execute(
        select(ContextoAtuacao, ObjetoContextoCatalogo.objeto_id)
        .join(ObjetoContextoCatalogo,
              ObjetoContextoCatalogo.contexto_id == ContextoAtuacao.id)
        .where(
            ContextoAtuacao.ativo.is_(True),
            ObjetoContextoCatalogo.objeto_id.in_(ids_objetos),
            ObjetoContextoCatalogo.vigente_ate.is_(None),
        )
        .order_by(ContextoAtuacao.nome)
    ).all() if ids_objetos else []
    contextos_por_id = {}
    for contexto, objeto_id in linhas_contextos:
        item = contextos_por_id.setdefault(contexto.id, {
            "id": contexto.id,
            "nome": contexto.nome,
            "objetos": [],
        })
        item["objetos"].append(objeto_id)
    contextos = list(contextos_por_id.values())
    return {
        "identidade": identidade,
        "unidades": unidades,
        "objetos": objetos,
        "contextos": contextos,
    }


def carregar_registro(sessao, conta_id, registro_id):
    identidade = _identidade(sessao, conta_id)
    if identidade is None:
        return None, None
    registro = sessao.get(Registro, registro_id)
    if registro is None:
        return identidade, None
    if registro.id not in _ids_visiveis(sessao, identidade):
        return identidade, False
    unidade = sessao.get(Unidade, registro.unidade_principal_atual_id)
    resumo = _resumo_registro(registro, unidade)
    instrumento = sessao.scalars(
        select(Instrumento).where(
            Instrumento.registro_id == registro.id,
            Instrumento.tipo_instrumento == "FORM1",
        )
    ).one()
    rascunho = sessao.get(RascunhoInstrumento, instrumento.id)
    autor_salvamento = None
    if rascunho is not None:
        pessoa = sessao.get(Pessoa, rascunho.salvo_por)
        autor_salvamento = pessoa.nome if pessoa is not None else rascunho.salvo_por
    pode_preencher = any(
        item["unidade_id"] == registro.unidade_principal_atual_id
        and item["papel"] == "preenchedor"
        for item in identidade["designacoes"]
    )
    resumo["form1"] = {
        "id": instrumento.id,
        "estado": instrumento.estado_instrumento,
        "estado_rotulo": ROTULOS_ESTADO_FORM1.get(
            instrumento.estado_instrumento, instrumento.estado_instrumento.replace("_", " ").capitalize()
        ),
        "pode_preencher": pode_preencher,
        "rascunho": None if rascunho is None else {
            "conteudo": rascunho.conteudo,
            "versao": rascunho.versao_rascunho,
            "salvo_por": autor_salvamento,
            "salvo_em": rascunho.salvo_em,
        },
        "catalogos": {
            "titulares": CATEGORIAS_TITULARES,
            "dados": CATEGORIAS_DADOS,
            "compartilhamentos": DESTINATARIOS_COMPARTILHAMENTO,
        },
    }
    return identidade, resumo
