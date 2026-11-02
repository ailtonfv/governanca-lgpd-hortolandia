"""Incremento 8AF — devolução e reapresentação interna do FORM 1 (AAA)."""

import threading

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from app.banco import motor
from app.conferencia_interna_form1_integral import (
    devolver_conferencia_interna_form1_integral,
    solicitar_conferencia_interna_form1_integral,
)
from app.consultas_interface import carregar_painel, carregar_registro
from app.main import app
from app.modelos import (
    Comando,
    ConferenciaInternaForm1Integral,
    Evento,
    HistoricoConferenciaForm1Integral,
    RascunhoForm1Integral,
    VersaoForm1Integral,
)
from app.rascunho_form1_integral import salvar_bloco_1_form1_integral
from migracoes.historico_conferencia_form1_integral import (
    aplicar as aplicar_migracao,
    reverter as reverter_migracao,
)
from testes.test_conferencia_interna_form1_integral_8ac import _preparar, _solicitar


def _devolver(
    sessao, registro, *, comando="8AF-DEV", conta="CONTA-A1",
    justificativa="Revisar a descrição fictícia do fluxo.", versao=1,
):
    resultado = devolver_conferencia_interna_form1_integral(
        sessao,
        comando_id=comando,
        conta_id=conta,
        registro_id=registro["registro_id"],
        versao_lida=versao,
        justificativa=justificativa,
    )
    sessao.commit()
    return resultado


def _salvar_ajuste(sessao, registro, *, comando="8AF-AJUSTE", conta="CONTA-G1"):
    rascunho = sessao.get(RascunhoForm1Integral, registro["registro_id"])
    resultado = salvar_bloco_1_form1_integral(
        sessao,
        comando_id=comando,
        conta_id=conta,
        registro_id=registro["registro_id"],
        versao_lida=rascunho.versao_rascunho,
        respostas={"1.1": "A confirmar", "1.4": "Sim"},
    )
    sessao.commit()
    return resultado


def test_ciclo_s1_devolucao_ajuste_s2_preserva_versoes_imutaveis(sessao):
    # Arrange
    registro = _preparar(sessao, "8AF-CICLO")
    s1 = _solicitar(sessao, registro, comando="8AF-CICLO-S1")
    conteudo_s1 = sessao.get(VersaoForm1Integral, s1["snapshot_id"]).conteudo.copy()

    # Act
    devolucao = _devolver(sessao, registro, comando="8AF-CICLO-DEV")
    ajuste = _salvar_ajuste(sessao, registro, comando="8AF-CICLO-AJUSTE")
    s2 = solicitar_conferencia_interna_form1_integral(
        sessao,
        comando_id="8AF-CICLO-S2",
        conta_id="CONTA-G1",
        registro_id=registro["registro_id"],
        versao_lida=ajuste["versao_rascunho"],
    )
    sessao.commit()

    # Assert
    historico = sessao.scalars(
        select(HistoricoConferenciaForm1Integral)
        .where(HistoricoConferenciaForm1Integral.registro_id == registro["registro_id"])
        .order_by(HistoricoConferenciaForm1Integral.numero_apresentacao)
    ).all()
    assert devolucao["permitido"] and s2["permitido"]
    assert [item.numero_apresentacao for item in historico] == [1, 2]
    assert [item.situacao for item in historico] == [
        "devolvida_para_ajustes", "aguardando_conferencia_interna_apa",
    ]
    assert historico[0].snapshot_id == s1["snapshot_id"]
    assert historico[1].snapshot_id == s2["snapshot_id"]
    assert s1["snapshot_id"] != s2["snapshot_id"]
    assert sessao.get(VersaoForm1Integral, s1["snapshot_id"]).conteudo == conteudo_s1
    assert sessao.get(VersaoForm1Integral, s2["snapshot_id"]).conteudo != conteudo_s1
    assert sessao.get(ConferenciaInternaForm1Integral, registro["registro_id"]).snapshot_id == s2["snapshot_id"]


def test_arp_visualiza_justificativa_corrige_e_apa_recebe_reapresentacao(sessao):
    # Arrange
    registro = _preparar(sessao, "8AF-PAINEL")
    _solicitar(sessao, registro, comando="8AF-PAINEL-S1")
    _devolver(
        sessao, registro, comando="8AF-PAINEL-DEV",
        justificativa="Complementar o fluxo fictício antes da reapresentação.",
    )

    # Act / Assert — ARP
    painel_arp = carregar_painel(sessao, "CONTA-G1")
    providencia = next(
        item for item in painel_arp["proximas_providencias_form1"]
        if item["registro_id"] == registro["registro_id"]
    )
    assert providencia["acao_rotulo"] == "Corrigir FORM 1 Integral"
    assert "Complementar o fluxo fictício" in providencia["justificativa_devolucao"]
    _, detalhe = carregar_registro(sessao, "CONTA-G1", registro["registro_id"])
    integral = detalhe["form1_integral"]
    assert integral["devolucao_interna"]["numero_apresentacao"] == 1
    assert integral["pode_solicitar_conferencia"] is False

    ajuste = _salvar_ajuste(sessao, registro, comando="8AF-PAINEL-AJUSTE")
    _, detalhe = carregar_registro(sessao, "CONTA-G1", registro["registro_id"])
    assert detalhe["form1_integral"]["pode_solicitar_conferencia"] is True
    _solicitar(
        sessao, registro, comando="8AF-PAINEL-S2",
        conta="CONTA-G1", versao=ajuste["versao_rascunho"],
    )
    painel_apa = carregar_painel(sessao, "CONTA-A1")
    assert any(
        item["registro_id"] == registro["registro_id"]
        for item in painel_apa["proximas_conferencias_form1"]
    )


def test_devolucao_exige_apa_justificativa_e_nao_se_repete(sessao):
    # Arrange
    registro = _preparar(sessao, "8AF-NEG")
    _solicitar(sessao, registro, comando="8AF-NEG-S1")

    # Act
    sem_justificativa = devolver_conferencia_interna_form1_integral(
        sessao, comando_id="8AF-NEG-VAZIA", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1, justificativa="  ",
    )
    nao_autorizado = devolver_conferencia_interna_form1_integral(
        sessao, comando_id="8AF-NEG-BETA", conta_id="CONTA-B1",
        registro_id=registro["registro_id"], versao_lida=1,
        justificativa="Tentativa fictícia.",
    )
    permitido = devolver_conferencia_interna_form1_integral(
        sessao, comando_id="8AF-NEG-OK", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        justificativa="Ajustar informação fictícia.",
    )
    duplicado = devolver_conferencia_interna_form1_integral(
        sessao, comando_id="8AF-NEG-OUTRA", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        justificativa="Outra devolução fictícia.",
    )
    sessao.commit()

    # Assert
    assert not sem_justificativa["permitido"]
    assert not nao_autorizado["permitido"]
    assert permitido["permitido"]
    assert not duplicado["permitido"]
    assert sessao.scalar(select(func.count()).select_from(Evento).where(
        Evento.tipo_evento == "devolver_conferencia_interna_form1_integral",
        Evento.registro_id == registro["registro_id"],
    )) == 1


def test_devolucao_e_idempotente_e_reutilizacao_incompativel_e_negada(sessao):
    # Arrange
    registro = _preparar(sessao, "8AF-IDEM")
    _solicitar(sessao, registro, comando="8AF-IDEM-S1")
    parametros = dict(
        comando_id="8AF-IDEM-DEV", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        justificativa="Revisar o conteúdo fictício.",
    )

    # Act
    primeiro = devolver_conferencia_interna_form1_integral(sessao, **parametros)
    sessao.commit()
    repetido = devolver_conferencia_interna_form1_integral(sessao, **parametros)
    sessao.commit()
    incompatível = devolver_conferencia_interna_form1_integral(
        sessao, **{**parametros, "justificativa": "Conteúdo diferente fictício."}
    )
    sessao.commit()

    # Assert
    assert primeiro["permitido"] and repetido["reexecutado"] is True
    assert not incompatível["permitido"]
    assert "reutilização indevida" in incompatível["motivo"]
    assert sessao.scalar(select(func.count()).select_from(Evento).where(
        Evento.tipo_evento == "devolver_conferencia_interna_form1_integral",
        Evento.registro_id == registro["registro_id"],
    )) == 1


def test_concorrencia_na_devolucao_produz_um_unico_ato(sessao):
    # Arrange
    registro = _preparar(sessao, "8AF-CONC")
    _solicitar(sessao, registro, comando="8AF-CONC-S1")
    barreira = threading.Barrier(2)
    resultados = []

    # Act
    def devolver(numero):
        with Session(motor) as outra, outra.begin():
            barreira.wait()
            resultados.append(devolver_conferencia_interna_form1_integral(
                outra, comando_id=f"8AF-CONC-DEV-{numero}", conta_id="CONTA-A1",
                registro_id=registro["registro_id"], versao_lida=1,
                justificativa=f"Justificativa fictícia {numero}.",
            ))

    threads = [threading.Thread(target=devolver, args=(numero,)) for numero in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Assert
    sessao.expire_all()
    assert sorted(item["permitido"] for item in resultados) == [False, True]
    assert sessao.scalar(select(func.count()).select_from(Evento).where(
        Evento.tipo_evento == "devolver_conferencia_interna_form1_integral",
        Evento.registro_id == registro["registro_id"],
    )) == 1
    assert sessao.get(ConferenciaInternaForm1Integral, registro["registro_id"]) is None


def test_falha_na_auditoria_reverte_devolucao_integralmente(sessao, monkeypatch):
    # Arrange
    registro = _preparar(sessao, "8AF-RB")
    _solicitar(sessao, registro, comando="8AF-RB-S1")

    def falhar(*args, **kwargs):
        raise RuntimeError("falha fictícia controlada")

    monkeypatch.setattr(
        "app.conferencia_interna_form1_integral.registrar_auditoria", falhar
    )

    # Act
    with pytest.raises(RuntimeError, match="falha fictícia"):
        devolver_conferencia_interna_form1_integral(
            sessao, comando_id="8AF-RB-DEV", conta_id="CONTA-A1",
            registro_id=registro["registro_id"], versao_lida=1,
            justificativa="Justificativa fictícia.",
        )
        sessao.commit()
    sessao.rollback()

    # Assert
    conferencia = sessao.get(ConferenciaInternaForm1Integral, registro["registro_id"])
    historico = sessao.scalars(select(HistoricoConferenciaForm1Integral).where(
        HistoricoConferenciaForm1Integral.registro_id == registro["registro_id"]
    )).one()
    assert conferencia is not None
    assert historico.situacao == "aguardando_conferencia_interna_apa"
    assert sessao.get(Comando, "8AF-RB-DEV") is None
    assert sessao.scalar(select(func.count()).select_from(Evento).where(
        Evento.comando_id == "8AF-RB-DEV"
    )) == 0


def test_apa_igual_arp_preserva_papeis_e_submissao_bloqueada(sessao):
    # Arrange
    registro = _preparar(
        sessao, "8AF-MESMA", arp="PESSOA-A", conta_arp="CONTA-A1"
    )

    # Act
    _solicitar(sessao, registro, comando="8AF-MESMA-S1", conta="CONTA-A1")
    devolucao = _devolver(sessao, registro, comando="8AF-MESMA-DEV")

    # Assert
    eventos = sessao.scalars(select(Evento).where(
        Evento.registro_id == registro["registro_id"],
        Evento.tipo_evento.in_((
            "solicitar_conferencia_interna_form1_integral",
            "devolver_conferencia_interna_form1_integral",
        )),
    ).order_by(Evento.sequencia_cadeia)).all()
    assert devolucao["submissao_habilitada"] is False
    assert [evento.conteudo["papel_ator"] for evento in eventos] == ["ARP", "APA"]
    assert len({evento.comando_id for evento in eventos}) == 2
    assert not any(evento.tipo_evento in {
        "submeter_form1_integral", "confirmar_conclusao_institucional",
    } for evento in sessao.scalars(select(Evento).where(
        Evento.registro_id == registro["registro_id"]
    )))


def test_rotas_exibem_snapshot_devolucao_e_correcao_sem_submeter(sessao):
    # Arrange
    registro = _preparar(sessao, "8AF-HTTP")
    _solicitar(sessao, registro, comando="8AF-HTTP-S1")
    cliente = TestClient(app)

    # Act
    pagina_apa = cliente.get(
        f"/registros/{registro['registro_id']}/form1-integral/conferencia-interna",
        params={"conta_id": "CONTA-A1"},
    )
    resposta = cliente.post(
        f"/registros/{registro['registro_id']}/form1-integral/conferencia-interna/devolver",
        data={
            "conta_id": "CONTA-A1", "comando_id": "8AF-HTTP-DEV",
            "versao_lida": "1", "justificativa": "Rever o fluxo fictício.",
        },
        follow_redirects=True,
    )
    painel_arp = cliente.get("/", params={"conta_id": "CONTA-G1"})

    # Assert
    assert pagina_apa.status_code == 200
    assert "Devolver para ajustes" in pagina_apa.text
    assert resposta.status_code == 200
    assert "Rever o fluxo fictício" in resposta.text
    assert painel_arp.status_code == 200
    assert "Corrigir FORM 1" in painel_arp.text
    assert "submissão institucional" not in resposta.text.lower() or "não" in resposta.text.lower()


def test_migracao_21_preserva_pendente_e_recusa_reversao_com_historico(sessao):
    # Arrange — cria uma solicitação da projeção anterior e remove só a nova tabela.
    registro = _preparar(sessao, "8AF-MIG")
    _solicitar(sessao, registro, comando="8AF-MIG-S1")
    with motor.begin() as conexao:
        HistoricoConferenciaForm1Integral.__table__.drop(bind=conexao)

    # Act
    with Session(motor) as outra, outra.begin():
        aplicar_migracao(outra)

    # Assert
    assert inspect(motor).has_table("historico_conferencia_form1_integral")
    with Session(motor) as outra:
        historico = outra.scalars(select(HistoricoConferenciaForm1Integral)).one()
        assert historico.registro_id == registro["registro_id"]
        assert historico.numero_apresentacao == 1

    # Uma devolução torna a reversão destrutiva e, portanto, proibida.
    with Session(motor) as outra, outra.begin():
        resultado = devolver_conferencia_interna_form1_integral(
            outra, comando_id="8AF-MIG-DEV", conta_id="CONTA-A1",
            registro_id=registro["registro_id"], versao_lida=1,
            justificativa="Justificativa fictícia.",
        )
        assert resultado["permitido"]
    with Session(motor) as outra, pytest.raises(RuntimeError, match="reversão recusada"):
        with outra.begin():
            reverter_migracao(outra)
