"""Consultas preparadas para a interface, sem regras de negócio nos templates."""

from sqlalchemy import func, or_, select

from app.alertas_operacionais import listar_alertas_operacionais
from app.continuidade_apa import apa_em_exercicio, unidades_em_que_e_apa_atual
from app.form1_sintetico import (CATEGORIAS_DADOS, CATEGORIAS_TITULARES,
                                 DESTINATARIOS_COMPARTILHAMENTO)
from app.form1_integral import (CONDICOES_BLOCO_2, CONDICOES_BLOCO_4, CONDICOES_BLOCO_6, CONDICOES_BLOCO_8,
                                CONDICOES_BLOCO_9,
                                CONDICOES_CANAIS_BLOCO_2,
                                FAIXAS_VOLUME_REV13, IDS_BLOCO_2, IDS_BLOCO_4,
                                IDS_BLOCO_5, IDS_BLOCO_6, IDS_BLOCO_7, IDS_BLOCO_8, IDS_BLOCO_9,
                                IDS_PARTICIPANTE_BLOCO_3,
                                campos_por_id)
from app.modelos import (AtribuicaoForm1Integral, Conta, ContextoAtuacao, Designacao, Instrumento,
                         Canal, ConfirmacaoCanaisRegistro, ObjetoCanal,
                         ObjetoCatalogo, ObjetoContextoCatalogo, RegistroCanal,
                         UnidadeObjetoCatalogo, Pendencia, Pessoa,
                          RascunhoForm1Integral, RascunhoInstrumento, Registro, Unidade)


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
    pode_criar_registro = bool(
        unidades_em_que_e_apa_atual(sessao, identidade["pessoa_id"])
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
    unidades_apa = unidades_em_que_e_apa_atual(sessao, identidade["pessoa_id"])
    unidades = []
    vistos = set()
    for item in identidade["designacoes"]:
        if item["unidade_id"] in unidades_apa and item["unidade_id"] not in vistos:
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
    linhas_canais = sessao.execute(
        select(ObjetoCanal, Canal)
        .join(Canal, Canal.id == ObjetoCanal.canal_id)
        .where(
            ObjetoCanal.objeto_id.in_(ids_objetos),
            ObjetoCanal.vigente_de <= func.now(),
            or_(ObjetoCanal.vigente_ate.is_(None), ObjetoCanal.vigente_ate > func.now()),
            Canal.ativo.is_(True),
        )
        .order_by(ObjetoCanal.objeto_id, Canal.nome_canonico)
    ).all() if ids_objetos else []
    for vinculo, canal in linhas_canais:
        objetos_por_id[vinculo.objeto_id].setdefault("canais", []).append({
            "id": canal.id,
            "nome": canal.nome_canonico,
        })
    for objeto in objetos:
        objeto.setdefault("canais", [])
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
    confirmacao_canais = sessao.get(ConfirmacaoCanaisRegistro, registro.id)
    canais_registro = sessao.scalars(
        select(RegistroCanal)
        .where(RegistroCanal.registro_id == registro.id)
        .order_by(RegistroCanal.canal_nome_snapshot)
    ).all() if confirmacao_canais is not None else []
    confirmador_canais = (
        None if confirmacao_canais is None
        else sessao.get(Pessoa, confirmacao_canais.confirmado_por_id)
    )
    resumo["confirmacao_canais"] = (
        None if confirmacao_canais is None else {
            "objeto_id": confirmacao_canais.objeto_id,
            "confirmado_por_id": confirmacao_canais.confirmado_por_id,
            "confirmado_em": confirmacao_canais.confirmado_em,
            "confirmado_por_nome": (
                confirmador_canais.nome
                if confirmador_canais is not None
                else confirmacao_canais.confirmado_por_id
            ),
            "canais": [
                {"id": item.canal_id_snapshot, "nome": item.canal_nome_snapshot}
                for item in canais_registro
            ],
        }
    )
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
    exercicio_apa = apa_em_exercicio(sessao, registro.unidade_principal_atual_id)
    pode_atribuir_arp = bool(
        exercicio_apa is not None
        and exercicio_apa["pessoa_id"] == identidade["pessoa_id"]
    )
    apa_abertura = sessao.get(Pessoa, registro.criado_por)
    apa_atual = (
        None if exercicio_apa is None
        else sessao.get(Pessoa, exercicio_apa["pessoa_id"])
    )
    atribuicao_integral = sessao.get(AtribuicaoForm1Integral, registro.id)
    arp_atual = (None if atribuicao_integral is None
                 else sessao.get(Pessoa, atribuicao_integral.arp_atual_id))
    rascunho_integral = sessao.get(RascunhoForm1Integral, registro.id)
    autor_integral = None
    if rascunho_integral is not None:
        pessoa = sessao.get(Pessoa, rascunho_integral.salvo_por)
        autor_integral = pessoa.nome if pessoa is not None else rascunho_integral.salvo_por
    resposta_legada_2_1 = (
        None if rascunho_integral is None
        else rascunho_integral.conteudo.get("respostas", {}).get("2.1")
    )
    if confirmacao_canais is None:
        leitura_2_1 = {
            "estado": "sem_confirmacao_historica",
            "somente_leitura": False,
            "canais": [],
            "resposta_legada": resposta_legada_2_1,
            "confirmado_por": None,
            "confirmado_em": None,
        }
    else:
        leitura_2_1 = {
            "estado": (
                "canais_confirmados" if canais_registro
                else "ausencia_confirmada"
            ),
            "somente_leitura": True,
            "canais": [
                {"id": item.canal_id_snapshot, "nome": item.canal_nome_snapshot}
                for item in canais_registro
            ],
            "resposta_legada": resposta_legada_2_1,
            "confirmado_por": resumo["confirmacao_canais"]["confirmado_por_nome"],
            "confirmado_em": confirmacao_canais.confirmado_em,
        }
    pode_editar_integral = bool(
        atribuicao_integral is not None
        and atribuicao_integral.arp_atual_id == identidade["pessoa_id"]
        and pode_preencher
    )
    catalogo_integral = campos_por_id()
    secretarias_integral = sessao.scalars(
        select(Unidade).where(
            Unidade.ativa.is_(True), Unidade.id != "UNID-GOV"
        ).order_by(Unidade.nome)
    ).all()

    def metadado_integral(campo_id):
        campo = catalogo_integral[campo_id]
        alternativas = campo.alternativas
        if campo_id in {"2.2", "2.4.1"}:
            alternativas = tuple((item.id, item.nome) for item in secretarias_integral)
        elif campo_id in {"2.8", "2.9", "2.10"}:
            alternativas = tuple((item, item) for item in FAIXAS_VOLUME_REV13)
        elif campo_id in {"4.2.5.1", "6.2.2", "9.2.2"}:
            alternativas = tuple(
                (item, item) for item in catalogo_integral["5.1"].alternativas
            )
        else:
            alternativas = tuple((item, item) for item in alternativas)
        condicao = (
            CONDICOES_BLOCO_2.get(campo_id)
            or CONDICOES_BLOCO_4.get(campo_id)
            or CONDICOES_BLOCO_6.get(campo_id)
            or CONDICOES_BLOCO_8.get(campo_id)
            or CONDICOES_BLOCO_9.get(campo_id)
        )
        condicoes = () if not condicao else (
            (condicao,) if isinstance(condicao[0], str) else condicao
        )
        return {
            "id": campo.id,
            "pergunta": campo.pergunta,
            "controle": campo.controle,
            "alternativas": alternativas,
            "instrucao": campo.instrucao,
            "condicao": condicao if condicao and isinstance(condicao[0], str) else None,
            "condicoes": condicoes,
            "condicao_canal_ativa": (
                None
                if confirmacao_canais is None
                or campo_id not in CONDICOES_CANAIS_BLOCO_2
                else CONDICOES_CANAIS_BLOCO_2[campo_id] in {
                    item.classificacao_form1_snapshot for item in canais_registro
                }
            ),
        }
    candidatos_arp = sessao.scalars(
        select(Pessoa)
        .join(Designacao, Designacao.pessoa_id == Pessoa.id)
        .where(
            Pessoa.ativa.is_(True),
            Pessoa.id != identidade["pessoa_id"],
            Designacao.unidade_id == registro.unidade_principal_atual_id,
            Designacao.papel == "preenchedor",
            Designacao.ativa.is_(True),
            Pessoa.contas.any(Conta.ativa.is_(True)),
        )
        .order_by(Pessoa.nome)
    ).unique().all()
    resumo["form1_integral"] = {
        "situacao": "rascunho" if rascunho_integral is not None else "nao_iniciado",
        "pode_atribuir_arp": pode_atribuir_arp,
        "pode_editar": pode_editar_integral,
        "apa_abertura": None if apa_abertura is None else {
            "id": apa_abertura.id,
            "nome": apa_abertura.nome,
        },
        "apa_atual": None if apa_atual is None else {
            "id": apa_atual.id,
            "nome": apa_atual.nome,
            "modalidade": exercicio_apa["modalidade"],
            "titular_id": exercicio_apa["titular_id"],
        },
        "arp_atual": None if arp_atual is None else {
            "id": arp_atual.id,
            "nome": arp_atual.nome,
        },
        "versao_atribuicao": (0 if atribuicao_integral is None
                              else atribuicao_integral.versao),
        "candidatos_arp": [
            {"id": pessoa.id, "nome": pessoa.nome}
            for pessoa in candidatos_arp
        ],
        "rascunho": None if rascunho_integral is None else {
            "conteudo": rascunho_integral.conteudo,
            "respostas": rascunho_integral.conteudo.get("respostas", {}),
            "participantes": rascunho_integral.conteudo.get("participantes", []),
            "versao": rascunho_integral.versao_rascunho,
            "salvo_por": autor_integral,
            "salvo_em": rascunho_integral.salvo_em,
        },
        "campos_bloco_1": {
            campo_id: {
                "id": catalogo_integral[campo_id].id,
                "pergunta": catalogo_integral[campo_id].pergunta,
                "alternativas": catalogo_integral[campo_id].alternativas,
                "instrucao": catalogo_integral[campo_id].instrucao,
            }
            for campo_id in ("1.1", "1.1.1", "1.2", "1.3", "1.4")
        },
        "campos_bloco_2": {
            campo_id: metadado_integral(campo_id) for campo_id in IDS_BLOCO_2
        },
        "leitura_2_1": leitura_2_1,
        "campo_3_1": metadado_integral("3.1"),
        "campos_participante": {
            campo_id: metadado_integral(campo_id)
            for campo_id in IDS_PARTICIPANTE_BLOCO_3
        },
        "campos_bloco_4": {
            campo_id: metadado_integral(campo_id) for campo_id in IDS_BLOCO_4
        },
        "campos_bloco_5": {
            campo_id: metadado_integral(campo_id) for campo_id in IDS_BLOCO_5
        },
        "campos_bloco_6": {
            campo_id: metadado_integral(campo_id) for campo_id in IDS_BLOCO_6
        },
        "campos_bloco_7": {
            campo_id: metadado_integral(campo_id) for campo_id in IDS_BLOCO_7
        },
        "campos_bloco_8": {
            campo_id: metadado_integral(campo_id) for campo_id in IDS_BLOCO_8
        },
        "campos_bloco_9": {
            campo_id: metadado_integral(campo_id) for campo_id in IDS_BLOCO_9
        },
        "etapas": (
            {"numero": 1, "titulo": "Identificação e funcionamento do serviço", "blocos": "1 a 3"},
            {"numero": 2, "titulo": "Dados pessoais e operações de tratamento", "blocos": "4 a 8"},
            {"numero": 3, "titulo": "Acesso, compartilhamento e armazenamento", "blocos": "9 a 11"},
            {"numero": 4, "titulo": "Guarda, situações observadas e pendências", "blocos": "12 a 14"},
        ),
    }
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
