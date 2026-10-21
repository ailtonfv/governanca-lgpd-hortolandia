"""Primeiro corte HTTP: painel, flags e proteção de leitura."""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.banco import motor
from app.main import app
from app.instrumentos import salvar_rascunho
from app.modelos import (Evento, EventoAuditoria, Instrumento, RascunhoInstrumento,
                         Registro)
from testes.apoio import CADASTRO, LANCAMENTO, g1
from testes.test_pendencia_intersecretarial import p1


cliente = TestClient(app)


def test_painel_identifica_agente_e_mostra_apenas_seu_escopo():
    norte = g1("CMD-UI-NORTE", CADASTRO, "CTX-TRIB-01", titulo="Cadastro imobiliário fictício")
    sul = g1(
        "CMD-UI-SUL", LANCAMENTO, "CTX-TRIB-02", conta="CONTA-C1", unidade="UNID-SUL",
        titulo="Atendimento tributário fictício",
    )

    resposta = cliente.get("/", params={"conta_id": "CONTA-A1"})

    assert resposta.status_code == 200
    assert 'lang="pt-BR"' in resposta.text
    assert "PoC · somente dados fictícios" in resposta.text
    assert "Servidor Alfa (fictício)" in resposta.text
    assert "matrícula MAT-FICT-0001" in resposta.text
    assert "Simular entrada por matrícula" in resposta.text
    assert "A PoC não solicita senha" in resposta.text
    assert norte["codigo_lgpd"] in resposta.text
    assert sul["codigo_lgpd"] not in resposta.text


def test_pendencia_intersecretarial_leva_registro_e_flags_ao_destino():
    registro = g1("CMD-UI-PEND-G1", CADASTRO, "CTX-TRIB-01")
    criada = p1(registro["registro_id"], cmd="CMD-UI-PEND-P1")

    resposta = cliente.get("/", params={"conta_id": "CONTA-C1"})

    assert resposta.status_code == 200
    assert registro["codigo_lgpd"] in resposta.text
    assert "Providência de outra unidade recebida" in resposta.text
    assert "Conclusão bloqueada" in resposta.text
    assert criada["pendencia_id"] not in resposta.text


def test_acesso_direto_a_registro_de_outra_unidade_e_negado_e_auditado():
    registro = g1("CMD-UI-NEGADO", CADASTRO, "CTX-TRIB-01")

    resposta = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-C1"}
    )

    assert resposta.status_code == 403
    assert "Acesso negado" in resposta.text
    with Session(motor) as sessao:
        evento = sessao.scalars(
            select(EventoAuditoria).where(EventoAuditoria.tipo_evento == "tentativa_negada")
        ).one()
        assert evento.ator_id == "PESSOA-C"
        assert evento.conteudo["acao_tentada"] == "consultar_registro"
        assert evento.conteudo["objeto"] == registro["registro_id"]


def test_conta_inexistente_nao_revela_o_painel():
    resposta = cliente.get("/", params={"conta_id": "CONTA-INEXISTENTE"})

    assert resposta.status_code == 404
    assert "Conta indisponível" in resposta.text


def test_novo_registro_define_tipo_unidade_principal_e_contexto_antes_do_form1():
    resposta = cliente.get("/registros/novo", params={"conta_id": "CONTA-A1"})

    assert resposta.status_code == 200
    assert "Qual Secretaria é responsável por este Registro?" in resposta.text
    assert resposta.text.index("1. Secretaria responsável pelo Registro") < resposta.text.index("2. O que será mapeado?")
    assert "Serviço" in resposta.text and "Processo" in resposta.text and "Atividade" in resposta.text
    assert "Secretaria responsável pelo Registro" in resposta.text
    assert "Planejamento Urbano e Gestão Estratégica" in resposta.text
    assert "Finanças" not in resposta.text
    assert "O FORM 1 somente começa depois da criação do Registro" in resposta.text


def test_contexto_inicial_diferencia_contexto_e_finalidade_por_exemplo():
    resposta = cliente.get("/registros/novo", params={"conta_id": "CONTA-A1"})

    assert resposta.status_code == 200
    assert 'aria-describedby="exemplo-contexto"' in resposta.text
    assert "fornecimento de medicamento de alto custo" in resposta.text
    assert "Assistência farmacêutica" in resposta.text
    assert "somente os dados de identificação, contato e saúde necessários" in resposta.text
    assert "verificar os requisitos, fornecer o medicamento" in resposta.text
    assert "Pergunta-chave:" in resposta.text
    assert "para que os dados pessoais são utilizados?" in resposta.text


def test_catalogo_da_tela_respeita_a_secretaria_do_agente():
    planejamento = cliente.get("/registros/novo", params={"conta_id": "CONTA-A1"})
    financas = cliente.get("/registros/novo", params={"conta_id": "CONTA-C1"})

    assert planejamento.status_code == 200
    assert financas.status_code == 200
    assert "Serviço financeiro fictício de demonstração" not in planejamento.text
    assert "Fornecimento de medicamento de alto custo" not in planejamento.text
    assert "Serviço financeiro fictício de demonstração" in financas.text
    assert 'data-unidades="UNID-SUL"' in financas.text
    assert "Fornecimento de medicamento de alto custo" not in financas.text


def test_g1_recusa_item_de_outra_secretaria_mesmo_se_forjado():
    resposta = cliente.post(
        "/registros",
        data={
            "conta_id": "CONTA-A1",
            "comando_id": "CMD-UI-CATALOGO-FORJADO",
            "tipo_objeto": "servico",
            "objeto_principal_id": "OBJ-SRV-902",
            "unidade_id": "UNID-NORTE",
            "contexto_id": "CTX-TRIB-03",
        },
    )

    assert resposta.status_code == 200
    assert "objeto não vinculado à Secretaria responsável" in resposta.text
    with Session(motor) as sessao:
        assert sessao.query(Registro).count() == 0


def test_g1_pela_tela_cria_registro_contextualizado_e_form1_nao_iniciado():
    resposta = cliente.post(
        "/registros",
        data={
            "conta_id": "CONTA-A1",
            "comando_id": "CMD-UI-NOVO-G1",
            "tipo_objeto": "servico",
            "objeto_principal_id": "OBJ-SRV-002",
            "unidade_id": "UNID-NORTE",
            "contexto_id": "CTX-TRIB-03",
        },
    )

    assert resposta.status_code == 200
    assert "Registro criado. Confirme o contexto antes de iniciar o FORM 1." in resposta.text
    assert "ciclo 1" in resposta.text
    assert "Certidão de débitos (fictício)" in resposta.text
    assert "Planejamento Urbano e Gestão Estratégica" in resposta.text
    assert "CTX-TRIB-03" in resposta.text
    assert "Não iniciado" in resposta.text
    with Session(motor) as sessao:
        registro = sessao.scalars(
            select(Registro).where(Registro.titulo_objeto == "Certidão de débitos (fictício)")
        ).one()
        instrumento = sessao.scalars(
            select(Instrumento).where(Instrumento.registro_id == registro.id)
        ).one()
        assert registro.tipo_objeto == "servico"
        assert registro.unidade_principal_atual_id == "UNID-NORTE"
        assert registro.contexto_atuacao_id == "CTX-TRIB-03"
        assert instrumento.estado_instrumento == "nao_iniciado"


def test_tela_recusa_tipo_diferente_do_item_do_catalogo():
    resposta = cliente.post(
        "/registros",
        data={
            "conta_id": "CONTA-A1",
            "comando_id": "CMD-UI-NOVO-TIPO",
            "tipo_objeto": "servico",
            "objeto_principal_id": "OBJ-ATV-020",
            "unidade_id": "UNID-NORTE",
            "contexto_id": "CTX-TRIB-01",
        },
    )

    assert resposta.status_code == 200
    assert "O tipo escolhido não corresponde ao item do catálogo" in resposta.text
    with Session(motor) as sessao:
        assert sessao.query(Registro).count() == 0


def test_percurso_completo_contexto_g1_i1_i2_pela_interface():
    criado = cliente.post(
        "/registros",
        data={
            "conta_id": "CONTA-A1",
            "comando_id": "CMD-UI-PONTA-G1",
            "tipo_objeto": "atividade",
            "objeto_principal_id": "OBJ-ATV-001",
            "unidade_id": "UNID-NORTE",
            "contexto_id": "CTX-TRIB-02",
        },
        follow_redirects=False,
    )
    assert criado.status_code == 303
    registro_id = criado.headers["location"].split("/registros/", 1)[1].split("?", 1)[0]

    iniciado = cliente.post(
        f"/registros/{registro_id}/form1/iniciar",
        data={"conta_id": "CONTA-A1", "comando_id": "CMD-UI-PONTA-I1"},
    )
    assert iniciado.status_code == 200
    assert "FORM 1 iniciado" in iniciado.text

    salvo = cliente.post(
        f"/registros/{registro_id}/form1/salvar",
        data={
            "conta_id": "CONTA-A1",
            "comando_id": "CMD-UI-PONTA-I2",
            "versao_lida": "1",
            "finalidade": "Calcular valor venal com dados exclusivamente fictícios",
            "categorias_titulares": "TIT-CONTRIBUINTE",
            "categorias_dados": ["DAD-IDENTIFICACAO", "DAD-ENDERECO"],
        },
    )
    assert salvo.status_code == 200
    assert "Rascunho salvo com segurança" in salvo.text
    assert "Rascunho 2" in salvo.text

    with Session(motor) as sessao:
        registro = sessao.get(Registro, registro_id)
        instrumento = sessao.scalars(
            select(Instrumento).where(Instrumento.registro_id == registro_id)
        ).one()
        rascunho = sessao.get(RascunhoInstrumento, instrumento.id)
        eventos = sessao.scalars(
            select(Evento).where(Evento.registro_id == registro_id).order_by(Evento.sequencia_cadeia)
        ).all()
        assert registro.tipo_objeto == "atividade"
        assert registro.unidade_principal_atual_id == "UNID-NORTE"
        assert registro.contexto_atuacao_id == "CTX-TRIB-02"
        assert instrumento.estado_instrumento == "em_preenchimento"
        assert rascunho.versao_rascunho == 2
        assert rascunho.conteudo["categorias_titulares"] == ["TIT-CONTRIBUINTE"]
        assert [evento.codigo_evento for evento in eventos] == ["G1", "I1", "I2"]


def _registro_com_form1(prefixo="CMD-UI-FORM"):
    registro = g1(prefixo, CADASTRO, "CTX-TRIB-01")
    with Session(motor) as sessao:
        instrumento = sessao.scalars(
            select(Instrumento).where(Instrumento.registro_id == registro["registro_id"])
        ).one()
        return registro, instrumento.id


def test_detalhe_oferece_i1_apenas_ao_elaborador():
    registro, _ = _registro_com_form1("CMD-UI-I1-VISIVEL")

    alfa = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )
    beta = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-B1"}
    )

    assert "Iniciar preenchimento (I1)" in alfa.text
    assert "Iniciar preenchimento (I1)" not in beta.text
    assert "não possui o papel de elaborador" in beta.text


def test_i1_pela_tela_cria_rascunho_e_exibe_formulario():
    registro, instrumento_id = _registro_com_form1("CMD-UI-I1-G1")

    resposta = cliente.post(
        f"/registros/{registro['registro_id']}/form1/iniciar",
        data={"conta_id": "CONTA-A1", "comando_id": "CMD-UI-I1-POST"},
    )

    assert resposta.status_code == 200
    assert "FORM 1 iniciado" in resposta.text
    assert "Salvar rascunho (I2)" in resposta.text
    with Session(motor) as sessao:
        assert sessao.get(RascunhoInstrumento, instrumento_id).versao_rascunho == 1


def test_formulario_orienta_selecao_multipla_pelo_contexto_do_objeto():
    registro, _ = _registro_com_form1("CMD-UI-AJUDA-G1")
    cliente.post(
        f"/registros/{registro['registro_id']}/form1/iniciar",
        data={"conta_id": "CONTA-A1", "comando_id": "CMD-UI-AJUDA-I1"},
    )

    resposta = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )

    assert resposta.status_code == 200
    assert "Você pode marcar mais de uma opção" in resposta.text
    assert "relevantes para este serviço, processo ou atividade" in resposta.text
    assert "fora deste contexto" in resposta.text


def test_i2_pela_tela_salva_somente_opcoes_fechadas():
    registro, instrumento_id = _registro_com_form1("CMD-UI-I2-G1")
    cliente.post(
        f"/registros/{registro['registro_id']}/form1/iniciar",
        data={"conta_id": "CONTA-A1", "comando_id": "CMD-UI-I2-I1"},
    )

    resposta = cliente.post(
        f"/registros/{registro['registro_id']}/form1/salvar",
        data={
            "conta_id": "CONTA-A1",
            "comando_id": "CMD-UI-I2-POST",
            "versao_lida": "1",
            "finalidade": "Emitir documento tributário fictício",
            "categorias_titulares": "TIT-CONTRIBUINTE",
            "categorias_dados": ["DAD-IDENTIFICACAO", "DAD-FINANCEIRO"],
            "compartilhamentos": "DST-ORGAO-MUNICIPAL",
        },
    )

    assert resposta.status_code == 200
    assert "Rascunho salvo com segurança" in resposta.text
    assert "Rascunho 2" in resposta.text
    with Session(motor) as sessao:
        rascunho = sessao.get(RascunhoInstrumento, instrumento_id)
        assert rascunho.conteudo == {
            "finalidade": "Emitir documento tributário fictício",
            "categorias_titulares": ["TIT-CONTRIBUINTE"],
            "categorias_dados": ["DAD-IDENTIFICACAO", "DAD-FINANCEIRO"],
            "compartilhamentos": ["DST-ORGAO-MUNICIPAL"],
        }
        assert rascunho.versao_rascunho == 2


def test_i2_recusa_tela_desatualizada_sem_sobrescrever():
    registro, instrumento_id = _registro_com_form1("CMD-UI-I2-ST-G1")
    cliente.post(
        f"/registros/{registro['registro_id']}/form1/iniciar",
        data={"conta_id": "CONTA-A1", "comando_id": "CMD-UI-I2-ST-I1"},
    )
    vencedor = {
        "finalidade": "Conteúdo vencedor fictício",
        "categorias_titulares": [], "categorias_dados": [], "compartilhamentos": [],
    }
    with Session(motor) as sessao, sessao.begin():
        assert salvar_rascunho(
            sessao, comando_id="CMD-UI-I2-ST-VENCE", conta_id="CONTA-A1",
            instrumento_id=instrumento_id, versao_lida=1, conteudo=vencedor,
        )["permitido"]

    resposta = cliente.post(
        f"/registros/{registro['registro_id']}/form1/salvar",
        data={
            "conta_id": "CONTA-A1", "comando_id": "CMD-UI-I2-ST-PERDE",
            "versao_lida": "1", "finalidade": "Conteúdo antigo fictício",
        },
    )

    assert resposta.status_code == 200
    assert "rascunho desatualizado" in resposta.text
    with Session(motor) as sessao:
        rascunho = sessao.get(RascunhoInstrumento, instrumento_id)
        assert rascunho.conteudo == vencedor and rascunho.versao_rascunho == 2
        eventos_i2 = sessao.scalars(select(Evento).where(
            Evento.cadeia_id == instrumento_id, Evento.codigo_evento == "I2"
        )).all()
        assert len(eventos_i2) == 1


def test_i2_recusa_codigo_de_catalogo_forjado():
    registro, instrumento_id = _registro_com_form1("CMD-UI-I2-CAT-G1")
    cliente.post(
        f"/registros/{registro['registro_id']}/form1/iniciar",
        data={"conta_id": "CONTA-A1", "comando_id": "CMD-UI-I2-CAT-I1"},
    )

    resposta = cliente.post(
        f"/registros/{registro['registro_id']}/form1/salvar",
        data={
            "conta_id": "CONTA-A1", "comando_id": "CMD-UI-I2-CAT-POST",
            "versao_lida": "1", "categorias_titulares": "TIT-INVENTADO",
        },
    )

    assert "seleção contém opção inválida" in resposta.text
    with Session(motor) as sessao:
        assert sessao.get(RascunhoInstrumento, instrumento_id).versao_rascunho == 1
