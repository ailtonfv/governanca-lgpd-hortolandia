"""Incremento 8AG — confirmação preparatória da conferência interna (AAA)."""

import threading

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from app.banco import motor
from app.conferencia_interna_form1_integral import (
    confirmar_conferencia_interna_form1_integral,
    solicitar_conferencia_interna_form1_integral,
)
from app.consultas_interface import carregar_painel, carregar_registro
from app.main import app
from app.modelos import (
    Comando,
    ConferenciaInternaForm1Integral,
    Evento,
    HistoricoConferenciaForm1Integral,
    VersaoForm1Integral,
)
from migracoes.confirmacao_conferencia_form1_integral import (
    aplicar as aplicar_migracao,
    reverter as reverter_migracao,
)
from testes.test_conferencia_interna_form1_integral_8ac import _preparar, _solicitar
from testes.test_devolucao_reapresentacao_form1_integral_8af import (
    _devolver,
    _salvar_ajuste,
)


def _confirmar(
    sessao, registro, *, comando="8AG-CONF", conta="CONTA-A1", versao=1,
):
    resultado = confirmar_conferencia_interna_form1_integral(
        sessao,
        comando_id=comando,
        conta_id=conta,
        registro_id=registro["registro_id"],
        versao_lida=versao,
    )
    sessao.commit()
    return resultado


def _preparar_s2(sessao, prefixo, *, mesma_pessoa=False):
    arp = "PESSOA-A" if mesma_pessoa else "PESSOA-G"
    conta_arp = "CONTA-A1" if mesma_pessoa else "CONTA-G1"
    registro = _preparar(sessao, prefixo, arp=arp, conta_arp=conta_arp)
    s1 = _solicitar(
        sessao, registro, comando=f"{prefixo}-S1", conta=conta_arp,
    )
    _devolver(sessao, registro, comando=f"{prefixo}-DEV")
    ajuste = _salvar_ajuste(
        sessao, registro, comando=f"{prefixo}-AJ", conta=conta_arp,
    )
    s2 = _solicitar(
        sessao, registro, comando=f"{prefixo}-S2", conta=conta_arp,
        versao=ajuste["versao_rascunho"],
    )
    return registro, s1, s2


def test_ciclo_s1_devolucao_s2_confirmada_preserva_snapshots(sessao):
    # Arrange
    registro, s1, s2 = _preparar_s2(sessao, "8AG-CICLO")
    conteudo_s1 = sessao.get(VersaoForm1Integral, s1["snapshot_id"]).conteudo.copy()
    conteudo_s2 = sessao.get(VersaoForm1Integral, s2["snapshot_id"]).conteudo.copy()

    # Act
    resultado = _confirmar(sessao, registro, comando="8AG-CICLO-CONF")

    # Assert
    historico = sessao.scalars(
        select(HistoricoConferenciaForm1Integral)
        .where(HistoricoConferenciaForm1Integral.registro_id == registro["registro_id"])
        .order_by(HistoricoConferenciaForm1Integral.numero_apresentacao)
    ).all()
    assert resultado["permitido"] and resultado["submissao_habilitada"] is False
    assert resultado["conclusao_institucional"] is False
    assert [item.situacao for item in historico] == [
        "devolvida_para_ajustes", "conferencia_interna_confirmada",
    ]
    assert historico[1].snapshot_id == s2["snapshot_id"]
    assert sessao.get(VersaoForm1Integral, s1["snapshot_id"]).conteudo == conteudo_s1
    assert sessao.get(VersaoForm1Integral, s2["snapshot_id"]).conteudo == conteudo_s2
    assert sessao.get(ConferenciaInternaForm1Integral, registro["registro_id"]) is None


def test_confirmacao_remove_providencia_e_permanece_consultavel(sessao):
    # Arrange
    registro, _s1, s2 = _preparar_s2(sessao, "8AG-PAINEL")

    # Act
    _confirmar(sessao, registro, comando="8AG-PAINEL-CONF")
    painel_apa = carregar_painel(sessao, "CONTA-A1")
    painel_arp = carregar_painel(sessao, "CONTA-G1")
    _, detalhe = carregar_registro(sessao, "CONTA-G1", registro["registro_id"])

    # Assert
    assert not any(
        item["registro_id"] == registro["registro_id"]
        for item in painel_apa["proximas_conferencias_form1"]
    )
    assert not any(
        item["registro_id"] == registro["registro_id"]
        for item in painel_arp["proximas_providencias_form1"]
    )
    integral = detalhe["form1_integral"]
    assert integral["confirmacao_interna"]["snapshot_id"] == s2["snapshot_id"]
    assert integral["pode_solicitar_conferencia"] is False
    assert integral["proxima_providencia"]["tipo"] == "conferencia_confirmada"


def test_nega_usuario_nao_autorizado_versao_antiga_e_decisao_repetida(sessao):
    # Arrange
    registro, _s1, _s2 = _preparar_s2(sessao, "8AG-NEG")

    # Act
    nao_autorizado = confirmar_conferencia_interna_form1_integral(
        sessao, comando_id="8AG-NEG-BETA", conta_id="CONTA-B1",
        registro_id=registro["registro_id"], versao_lida=1,
    )
    desatualizada = confirmar_conferencia_interna_form1_integral(
        sessao, comando_id="8AG-NEG-V", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=2,
    )
    permitida = confirmar_conferencia_interna_form1_integral(
        sessao, comando_id="8AG-NEG-OK", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
    )
    repetida = confirmar_conferencia_interna_form1_integral(
        sessao, comando_id="8AG-NEG-OUTRA", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
    )
    sessao.commit()

    # Assert
    assert not nao_autorizado["permitido"]
    assert not desatualizada["permitido"] and "desatualizada" in desatualizada["motivo"]
    assert permitida["permitido"]
    assert not repetida["permitido"] and "não existe solicitação" in repetida["motivo"]
    assert sessao.scalar(select(func.count()).select_from(Evento).where(
        Evento.tipo_evento == "confirmar_conferencia_interna_form1_integral",
        Evento.registro_id == registro["registro_id"],
    )) == 1


def test_confirmacao_e_idempotente(sessao):
    # Arrange
    registro, _s1, _s2 = _preparar_s2(sessao, "8AG-IDEM")
    parametros = dict(
        comando_id="8AG-IDEM-CONF", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
    )

    # Act
    primeiro = confirmar_conferencia_interna_form1_integral(sessao, **parametros)
    sessao.commit()
    repetido = confirmar_conferencia_interna_form1_integral(sessao, **parametros)
    sessao.commit()

    # Assert
    assert primeiro["permitido"] and repetido["reexecutado"] is True
    assert repetido["snapshot_id"] == primeiro["snapshot_id"]
    assert sessao.scalar(select(func.count()).select_from(Evento).where(
        Evento.tipo_evento == "confirmar_conferencia_interna_form1_integral",
        Evento.registro_id == registro["registro_id"],
    )) == 1


def test_confirmacoes_concorrentes_produzem_uma_decisao(sessao):
    # Arrange
    registro, _s1, _s2 = _preparar_s2(sessao, "8AG-CONC")
    barreira = threading.Barrier(2)
    resultados = []

    # Act
    def confirmar(numero):
        with Session(motor) as outra, outra.begin():
            barreira.wait()
            resultados.append(confirmar_conferencia_interna_form1_integral(
                outra, comando_id=f"8AG-CONC-{numero}", conta_id="CONTA-A1",
                registro_id=registro["registro_id"], versao_lida=1,
            ))

    threads = [threading.Thread(target=confirmar, args=(numero,)) for numero in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Assert
    sessao.expire_all()
    assert sorted(item["permitido"] for item in resultados) == [False, True]
    assert sessao.scalar(select(func.count()).select_from(Evento).where(
        Evento.tipo_evento == "confirmar_conferencia_interna_form1_integral",
        Evento.registro_id == registro["registro_id"],
    )) == 1


def test_falha_na_auditoria_reverte_confirmacao(sessao, monkeypatch):
    # Arrange
    registro, _s1, s2 = _preparar_s2(sessao, "8AG-RB")

    def falhar(*args, **kwargs):
        raise RuntimeError("falha fictícia controlada")

    monkeypatch.setattr(
        "app.conferencia_interna_form1_integral.registrar_auditoria", falhar
    )

    # Act
    with pytest.raises(RuntimeError, match="falha fictícia"):
        confirmar_conferencia_interna_form1_integral(
            sessao, comando_id="8AG-RB-CONF", conta_id="CONTA-A1",
            registro_id=registro["registro_id"], versao_lida=1,
        )
        sessao.commit()
    sessao.rollback()

    # Assert
    conferencia = sessao.get(ConferenciaInternaForm1Integral, registro["registro_id"])
    historico = sessao.scalars(select(HistoricoConferenciaForm1Integral).where(
        HistoricoConferenciaForm1Integral.snapshot_id == s2["snapshot_id"]
    )).one()
    assert conferencia is not None
    assert historico.situacao == "aguardando_conferencia_interna_apa"
    assert sessao.get(Comando, "8AG-RB-CONF") is None


def test_apa_igual_arp_confirma_em_ato_separado(sessao):
    # Arrange
    registro, _s1, _s2 = _preparar_s2(
        sessao, "8AG-MESMA", mesma_pessoa=True
    )

    # Act
    resultado = _confirmar(sessao, registro, comando="8AG-MESMA-CONF")

    # Assert
    eventos = sessao.scalars(select(Evento).where(
        Evento.registro_id == registro["registro_id"],
        Evento.tipo_evento.in_((
            "solicitar_conferencia_interna_form1_integral",
            "confirmar_conferencia_interna_form1_integral",
        )),
    ).order_by(Evento.sequencia_cadeia)).all()
    assert resultado["permitido"] and resultado["submissao_habilitada"] is False
    assert eventos[-2].conteudo["papel_ator"] == "ARP"
    assert eventos[-1].conteudo["papel_ator"] == "APA"
    assert eventos[-2].comando_id != eventos[-1].comando_id


def test_rota_confirma_snapshot_exato_e_permite_consulta_autorizada(sessao):
    # Arrange
    registro, _s1, s2 = _preparar_s2(sessao, "8AG-HTTP")
    cliente = TestClient(app)
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}/form1-integral/conferencia-interna",
        params={"conta_id": "CONTA-A1"},
    )

    # Act
    resposta = cliente.post(
        f"/registros/{registro['registro_id']}/form1-integral/conferencia-interna/confirmar",
        data={
            "conta_id": "CONTA-A1", "comando_id": "8AG-HTTP-CONF",
            "versao_lida": "1",
        },
        follow_redirects=True,
    )
    consulta_apa = cliente.get(
        f"/registros/{registro['registro_id']}/form1-integral/conferencia-interna",
        params={"conta_id": "CONTA-A1"},
    )
    consulta_arp = cliente.get(
        f"/registros/{registro['registro_id']}/form1-integral/conferencia-interna",
        params={"conta_id": "CONTA-G1"},
    )
    negada = cliente.get(
        f"/registros/{registro['registro_id']}/form1-integral/conferencia-interna",
        params={"conta_id": "CONTA-B1"},
    )

    # Assert
    assert pagina.status_code == 200 and "Confirmar conferência interna" in pagina.text
    assert resposta.status_code == 200 and "Conferência interna confirmada" in resposta.text
    assert consulta_apa.status_code == consulta_arp.status_code == 200
    assert str(s2["numero_snapshot"]) in consulta_apa.text
    assert "Conferência interna confirmada" in consulta_arp.text
    assert negada.status_code == 403


def test_migracao_22_e_reversivel_vazia_e_protegida_com_confirmacao(sessao):
    # Arrange / Act — simula o esquema 21 sem decisões confirmadas.
    with Session(motor) as outra, outra.begin():
        reverter_migracao(outra)
    colunas_antes = {item["name"] for item in inspect(motor).get_columns(
        "historico_conferencia_form1_integral"
    )}
    with Session(motor) as outra, outra.begin():
        aplicar_migracao(outra)
    colunas_depois = {item["name"] for item in inspect(motor).get_columns(
        "historico_conferencia_form1_integral"
    )}

    # Assert — evolução não destrutiva e reversão protegida quando passa a haver uso.
    assert "confirmada_por_id" not in colunas_antes
    assert {"confirmada_por_id", "confirmada_em", "evento_confirmacao_id"} <= colunas_depois
    registro = _preparar(sessao, "8AG-MIG")
    _solicitar(sessao, registro, comando="8AG-MIG-S1")
    _confirmar(sessao, registro, comando="8AG-MIG-CONF")
    with Session(motor) as outra, pytest.raises(RuntimeError, match="reversão recusada"):
        with outra.begin():
            reverter_migracao(outra)
