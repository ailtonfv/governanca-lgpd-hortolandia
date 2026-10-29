"""Ensaio reproduzível da jornada de rascunho do FORM 1 integral."""

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.atribuicao_form1_integral import atribuir_arp_form1_integral
from app.continuidade_apa import apa_em_exercicio
from app.eventos import verificar_cadeia
from app.main import app
from app.modelos import Designacao, Evento, RascunhoForm1Integral
from app.pre_validacao_form1_integral import pre_validar_form1_integral
from app.rascunho_form1_integral import (
    adicionar_destinatario_10_2_1_form1_integral,
    adicionar_participante_form1_integral,
    iniciar_rascunho_form1_integral,
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
    salvar_cabecalho_bloco_3_form1_integral,
)
from testes.apoio import g1
from testes.test_bloco13_form1_integral import SITUACAO_IMPRESSAO, SITUACAO_TELA


def _versao(sessao, registro_id):
    sessao.expire_all()
    return sessao.get(RascunhoForm1Integral, registro_id).versao_rascunho


def _salvar(sessao, funcao, registro_id, comando_id, respostas):
    resultado = funcao(
        sessao,
        comando_id=comando_id,
        conta_id="CONTA-G1",
        registro_id=registro_id,
        versao_lida=_versao(sessao, registro_id),
        respostas=respostas,
    )
    sessao.commit()
    assert resultado["permitido"], resultado


def test_percurso_sintetico_dos_14_blocos_preserva_rascunho_autoria_e_bloqueio(sessao):
    # Arrange — APA titular, suplente formal e Registro com canais históricos.
    exercicio = apa_em_exercicio(sessao, "UNID-NORTE")
    suplente = sessao.scalars(select(Designacao).where(
        Designacao.pessoa_id == "PESSOA-F",
        Designacao.unidade_id == "UNID-NORTE",
        Designacao.papel == "responsavel_registro",
    )).one()
    assert exercicio["pessoa_id"] == "PESSOA-A"
    assert suplente.tipo_apa == "suplente" and suplente.autorizado_por_id == "PESSOA-E"

    registro = g1(
        "F18B-G1", "OBJ-SRV-001", "CTX-TRIB-03",
        titulo="Serviço sintético para ensaio do FORM 1",
        canais_confirmados_ids=["CNL-001", "CNL-002"],
    )
    atribuicao = atribuir_arp_form1_integral(
        sessao, comando_id="F18B-ARP", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], modo="outro",
        arp_pessoa_id="PESSOA-G", versao_lida=0,
    )
    sessao.commit()
    inicio = iniciar_rascunho_form1_integral(
        sessao, comando_id="F18B-INICIO", conta_id="CONTA-G1",
        registro_id=registro["registro_id"],
    )
    sessao.commit()
    assert atribuicao["permitido"] and inicio["permitido"]

    # Act — percorre todos os blocos com respostas sintéticas representativas.
    _salvar(sessao, salvar_bloco_1_form1_integral, registro["registro_id"], "F18B-B1", {
        "1.1": "Sim", "1.1.1": "Referência institucional fictícia", "1.4": "Sim",
    })
    _salvar(sessao, salvar_bloco_2_form1_integral, registro["registro_id"], "F18B-B2", {
        "2.2": "UNID-NORTE", "2.3": "Unidade fictícia de atendimento",
        "2.4": "Sim", "2.5": ["Recebe demanda"],
        "2.6": "Recebimento sintético para demonstração.",
    })
    cabecalho = salvar_cabecalho_bloco_3_form1_integral(
        sessao, comando_id="F18B-B3", conta_id="CONTA-G1",
        registro_id=registro["registro_id"],
        versao_lida=_versao(sessao, registro["registro_id"]), resposta_3_1="Sim",
    )
    sessao.commit()
    participante = adicionar_participante_form1_integral(
        sessao, comando_id="F18B-B3-P1", conta_id="CONTA-G1",
        registro_id=registro["registro_id"],
        versao_lida=_versao(sessao, registro["registro_id"]),
        respostas={
            "3.2": ["Outra Secretaria"], "3.3": "Secretaria participante fictícia",
            "3.4": ["Recebe encaminhamento"], "3.5": "Não",
        },
    )
    sessao.commit()
    assert cabecalho["permitido"] and participante["permitido"]

    _salvar(sessao, salvar_bloco_4_form1_integral, registro["registro_id"], "F18B-B4", {
        "4.1": ["Munícipe"], "4.2": "Sim", "4.2.1": ["Responsável legal"],
    })
    resultado_b5 = salvar_bloco_5_form1_integral(
        sessao, comando_id="F18B-B5", conta_id="CONTA-G1",
        registro_id=registro["registro_id"],
        versao_lida=_versao(sessao, registro["registro_id"]),
        respostas={"5.1": ["Nome", "Outro"]},
        complemento_outro="Identificador sintético complementar",
    )
    sessao.commit()
    assert resultado_b5["permitido"]
    _salvar(sessao, salvar_bloco_6_form1_integral, registro["registro_id"], "F18B-B6", {
        "6.1": ["Do próprio titular"], "6.2": "Sim",
        "6.2.1": "Sistema fictício", "6.2.2": ["Nome"],
    })
    _salvar(sessao, salvar_bloco_7_form1_integral, registro["registro_id"], "F18B-B7", {
        "7.1": ["Coleta", "Armazenamento"],
    })
    _salvar(sessao, salvar_bloco_8_form1_integral, registro["registro_id"], "F18B-B8", {
        "8.1": "Ambos",
        "8.2": ["DOCS", "Processo administrativo físico"],
        "8.2.1": "Sim",
        "8.2.1.1": "Ambiente municipal fictício",
        "8.2.2": "Em alguns casos",
        "8.2.2.1": ["Sistema contratado"],
        "8.2.2.2": "Fornecedor fictício",
        "8.3": ["WhatsApp corporativo"],
        "8.7": "Institucional ou corporativo",
        "8.8": "Sempre",
        "8.8.1": "Protocolo fictício",
        "8.9": "Não",
    })
    _salvar(sessao, salvar_bloco_9_form1_integral, registro["registro_id"], "F18B-B9", {
        "9.1": ["AGENTE PÚBLICO AUTORIZADO da unidade responsável"],
        "9.2": "Sim", "9.3": "Equipe fictícia autorizada",
    })
    _salvar(sessao, salvar_bloco_10_form1_integral, registro["registro_id"], "F18B-B10", {
        "10.1": "Sim", "10.2": ["Outra Secretaria"],
        "10.3": ["Sistema"], "10.4": ["Nome"], "10.5": "Sob demanda",
        "10.6": "Atendimento institucional fictício", "10.7": "Não",
        "10.8": "Não", "10.9": "Titular",
    })
    destinatario = adicionar_destinatario_10_2_1_form1_integral(
        sessao, comando_id="F18B-B10-D1", conta_id="CONTA-G1",
        registro_id=registro["registro_id"],
        versao_lida=_versao(sessao, registro["registro_id"]),
        dados={
            "categoria": "Outra Secretaria", "modalidade": "identificado",
            "unidade_id": "UNID-SUL", "instrumento": "Ato sintético de cooperação",
        },
    )
    sessao.commit()
    assert destinatario["permitido"]
    _salvar(sessao, salvar_bloco_11_form1_integral, registro["registro_id"], "F18B-B11", {
        "11.1": ["Sistema institucional"], "11.2": "Infraestrutura da Prefeitura",
        "11.3": "Não",
    })
    _salvar(sessao, salvar_bloco_12_form1_integral, registro["registro_id"], "F18B-B12", {
        "12.1": "Não", "12.2": "A confirmar", "12.3": "Não",
        "12.4": "Não", "12.5": "Não",
    })
    _salvar(sessao, salvar_bloco_13_form1_integral, registro["registro_id"], "F18B-B13", {
        "13.1": [SITUACAO_TELA, SITUACAO_IMPRESSAO], "13.2": "Às vezes",
        "13.3": "Não", "13.4": ["Atendimento", "Área de impressão"],
    })
    _salvar(sessao, salvar_bloco_14_form1_integral, registro["registro_id"], "F18B-B14", {
        "14.1": "Não", "14.2": "Sim", "14.2.1": "Armazenamento",
        "14.2.2": "Achado sintético para futura complementação.", "14.2.3": "Não",
    })

    # Assert — reabre a página, preserva respostas e autoria e apenas consulta pendências.
    rascunho = sessao.get(RascunhoForm1Integral, registro["registro_id"])
    conteudo_antes = dict(rascunho.conteudo)
    pre_validacao = pre_validar_form1_integral(
        rascunho.conteudo, nome_institucional="Servidor Épsilon (fictício)",
    )
    assert pre_validacao["quantidades"]["incompletos"] > 0
    assert rascunho.conteudo == conteudo_antes
    assert len(rascunho.conteudo["participantes"]) == 1
    assert len(rascunho.conteudo["destinatarios_10_2_1"]) == 1
    assert rascunho.conteudo["respostas"]["14.2.2"].startswith("Achado sintético")

    pagina = TestClient(app).get(
        f"/registros/{registro['registro_id']}?conta_id=CONTA-G1"
    )
    assert pagina.status_code == 200
    for etapa in range(1, 5):
        assert f'data-etapa-alvo="{etapa}"' in pagina.text
        assert f'id="form1-etapa-{etapa}"' in pagina.text
    for bloco in range(1, 15):
        assert f"Bloco {bloco} de 14" in pagina.text
    assert "Secretaria participante fictícia" in pagina.text
    assert "Ato sintético de cooperação" in pagina.text
    assert "Pendências antes da futura submissão" in pagina.text
    assert "/form1-integral/submeter" not in pagina.text

    eventos = sessao.scalars(select(Evento).where(
        Evento.registro_id == registro["registro_id"]
    )).all()
    assert next(evento for evento in eventos if evento.codigo_evento == "G1").ator_id == "PESSOA-A"
    eventos_rascunho = [evento for evento in eventos if evento.tipo_evento.startswith(("salvar_bloco_", "adicionar_"))]
    assert eventos_rascunho and {evento.ator_id for evento in eventos_rascunho} == {"PESSOA-G"}
    assert verificar_cadeia(sessao, registro["codigo_lgpd"])[0]
