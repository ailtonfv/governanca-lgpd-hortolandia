"""Infraestrutura interna do snapshot do FORM 1 integral — AAA."""

from copy import deepcopy
import threading

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.atribuicao_form1_integral import atribuir_arp_form1_integral
from app.banco import motor
from app.eventos import lacre, verificar_cadeia
from app.main import app
from app.modelos import (
    Comando,
    Evento,
    EventoAuditoria,
    Instrumento,
    RascunhoForm1Integral,
    Registro,
    VersaoForm1Integral,
    VersaoInstrumento,
)
from app.rascunho_form1_integral import (
    iniciar_rascunho_form1_integral,
    salvar_bloco_1_form1_integral,
)
from app.submissao_form1_integral import preparar_snapshot_form1_integral
from migracoes.versao_form1_integral import (
    aplicar as aplicar_migracao,
    reverter as reverter_migracao,
)
from testes.apoio import CADASTRO, g1


def _preparar(sessao, prefixo, *, conta_arp="CONTA-A1", canais=None):
    objeto = "OBJ-SRV-001" if canais is not None else CADASTRO
    contexto = "CTX-TRIB-03" if canais is not None else "CTX-TRIB-01"
    registro = g1(
        f"{prefixo}-G1", objeto, contexto,
        titulo="Atividade sintética para snapshot técnico",
        canais_confirmados_ids=canais,
    )
    modo = "proprio" if conta_arp == "CONTA-A1" else "outro"
    atribuicao = atribuir_arp_form1_integral(
        sessao,
        comando_id=f"{prefixo}-ARP",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        modo=modo,
        arp_pessoa_id=None if modo == "proprio" else "PESSOA-G",
        versao_lida=0,
    )
    inicio = iniciar_rascunho_form1_integral(
        sessao,
        comando_id=f"{prefixo}-INICIO",
        conta_id=conta_arp,
        registro_id=registro["registro_id"],
    )
    sessao.commit()
    assert atribuicao["permitido"] and inicio["permitido"]
    return registro


def _snapshot(sessao, registro, comando, *, conta="CONTA-A1", versao=1):
    resultado = preparar_snapshot_form1_integral(
        sessao,
        comando_id=comando,
        conta_id=conta,
        registro_id=registro["registro_id"],
        versao_lida=versao,
    )
    sessao.commit()
    return resultado


def test_snapshot_congela_envelope_canais_autoria_e_eventos_sem_transicao(sessao):
    # Arrange
    registro = _preparar(
        sessao, "F18C-SUCESSO", canais=["CNL-001", "CNL-002"]
    )
    registro_antes = sessao.get(Registro, registro["registro_id"])
    estado_antes = registro_antes.estado_atual
    instrumento = sessao.scalars(select(Instrumento).where(
        Instrumento.registro_id == registro["registro_id"],
        Instrumento.tipo_instrumento == "FORM1",
    )).one()
    estado_instrumento_antes = instrumento.estado_instrumento

    # Act
    resultado = _snapshot(sessao, registro, "F18C-SNAPSHOT")

    # Assert
    versao = sessao.get(VersaoForm1Integral, resultado["snapshot_id"])
    sessao.refresh(registro_antes)
    sessao.refresh(instrumento)
    assert resultado["permitido"] and resultado["submissao_habilitada"] is False
    assert versao.numero == 1 and versao.versao_rascunho == 1
    assert versao.versao_contrato == 3 and versao.preparado_por == "PESSOA-A"
    assert versao.conteudo["natureza"] == "preparacao_tecnica_sem_submissao"
    assert versao.conteudo["submissao_habilitada"] is False
    assert versao.conteudo["form1_integral"]["respostas"]["1.2"] == "Serviço"
    assert len(versao.conteudo["retrato_canais"]["canais"]) == 2
    assert versao.lacre == lacre(versao.conteudo_canonico)
    assert registro_antes.estado_atual == estado_antes
    assert instrumento.estado_instrumento == estado_instrumento_antes
    assert sessao.scalar(select(func.count()).select_from(VersaoInstrumento)) == 0
    evento = sessao.scalars(select(Evento).where(
        Evento.comando_id == "F18C-SNAPSHOT"
    )).one()
    auditoria = sessao.scalars(select(EventoAuditoria).where(
        EventoAuditoria.comando_id == "F18C-SNAPSHOT"
    )).one()
    assert evento.tipo_evento == "preparar_snapshot_form1_integral"
    assert auditoria.tipo_evento == "snapshot_form1_integral_preparado"
    assert verificar_cadeia(sessao, registro["codigo_lgpd"])[0]


def test_snapshot_e_idempotente_e_recusa_reuso_da_chave(sessao):
    registro = _preparar(sessao, "F18C-IDEM")
    parametros = dict(
        comando_id="F18C-IDEM-SNAPSHOT",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        versao_lida=1,
    )

    original = preparar_snapshot_form1_integral(sessao, **parametros)
    sessao.commit()
    repetido = preparar_snapshot_form1_integral(sessao, **parametros)
    reutilizado = preparar_snapshot_form1_integral(
        sessao, **{**parametros, "versao_lida": 2}
    )
    sessao.commit()

    assert original["permitido"] and repetido["reexecutado"] is True
    assert repetido["snapshot_id"] == original["snapshot_id"]
    assert not reutilizado["permitido"] and "reutilização indevida" in reutilizado["motivo"]
    assert sessao.scalar(select(func.count()).select_from(VersaoForm1Integral)) == 1


def test_snapshot_recusa_ator_versao_e_lacre_invalidos_sem_criar_versao(sessao):
    registro = _preparar(sessao, "F18C-NEGACOES")
    rascunho = sessao.get(RascunhoForm1Integral, registro["registro_id"])
    rascunho.lacre_conteudo = "0" * 64
    sessao.commit()

    nao_arp = preparar_snapshot_form1_integral(
        sessao, comando_id="F18C-NEG-ATOR", conta_id="CONTA-G1",
        registro_id=registro["registro_id"], versao_lida=1,
    )
    desatualizado = preparar_snapshot_form1_integral(
        sessao, comando_id="F18C-NEG-VERSAO", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=2,
    )
    lacre_invalido = preparar_snapshot_form1_integral(
        sessao, comando_id="F18C-NEG-LACRE", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
    )
    sessao.commit()

    assert not nao_arp["permitido"] and "somente o ARP" in nao_arp["motivo"]
    assert not desatualizado["permitido"] and "desatualizado" in desatualizado["motivo"]
    assert not lacre_invalido["permitido"] and "lacre" in lacre_invalido["motivo"]
    assert sessao.scalar(select(func.count()).select_from(VersaoForm1Integral)) == 0


def test_nova_versao_do_rascunho_gera_novo_snapshot_sem_alterar_o_anterior(sessao):
    registro = _preparar(sessao, "F18C-VERSOES")
    primeiro = _snapshot(sessao, registro, "F18C-VERSOES-S1")
    conteudo_primeiro = deepcopy(
        sessao.get(VersaoForm1Integral, primeiro["snapshot_id"]).conteudo
    )
    salvo = salvar_bloco_1_form1_integral(
        sessao, comando_id="F18C-VERSOES-B1", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"1.4": "Sim"},
    )
    sessao.commit()

    segundo = _snapshot(
        sessao, registro, "F18C-VERSOES-S2", versao=salvo["versao_rascunho"]
    )

    assert segundo["numero"] == 2
    assert sessao.get(VersaoForm1Integral, primeiro["snapshot_id"]).conteudo == conteudo_primeiro
    assert sessao.get(VersaoForm1Integral, segundo["snapshot_id"]).conteudo[
        "form1_integral"
    ]["respostas"]["1.4"] == "Sim"


def test_snapshots_concorrentes_da_mesma_versao_produzem_apenas_um(sessao):
    registro = _preparar(sessao, "F18C-CONCORRENCIA")
    barreira = threading.Barrier(2)
    resultados = []

    def preparar(numero):
        with Session(motor) as outra, outra.begin():
            barreira.wait()
            resultados.append(preparar_snapshot_form1_integral(
                outra,
                comando_id=f"F18C-CONC-{numero}",
                conta_id="CONTA-A1",
                registro_id=registro["registro_id"],
                versao_lida=1,
            ))

    threads = [threading.Thread(target=preparar, args=(numero,)) for numero in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(item["permitido"] for item in resultados) == [False, True]
    assert any("já possui snapshot" in item["motivo"] for item in resultados if not item["permitido"])
    sessao.expire_all()
    assert sessao.scalar(select(func.count()).select_from(VersaoForm1Integral)) == 1


def test_falha_na_auditoria_desfaz_snapshot_evento_e_comando(sessao, monkeypatch):
    registro = _preparar(sessao, "F18C-ROLLBACK")

    def falhar(*args, **kwargs):
        raise RuntimeError("falha fictícia controlada")

    monkeypatch.setattr("app.submissao_form1_integral.registrar_auditoria", falhar)
    with pytest.raises(RuntimeError, match="falha fictícia"):
        preparar_snapshot_form1_integral(
            sessao, comando_id="F18C-ROLLBACK-SNAPSHOT", conta_id="CONTA-A1",
            registro_id=registro["registro_id"], versao_lida=1,
        )
        sessao.commit()
    sessao.rollback()

    assert sessao.scalar(select(func.count()).select_from(VersaoForm1Integral)) == 0
    assert sessao.get(Comando, "F18C-ROLLBACK-SNAPSHOT") is None
    assert sessao.scalar(select(func.count()).select_from(Evento).where(
        Evento.comando_id == "F18C-ROLLBACK-SNAPSHOT"
    )) == 0


def test_snapshot_nao_possui_endpoint_nem_acao_na_interface(sessao):
    registro = _preparar(sessao, "F18C-HTTP")

    pagina = TestClient(app).get(
        f"/registros/{registro['registro_id']}?conta_id=CONTA-A1"
    )
    rotas = {getattr(rota, "path", "") for rota in app.routes}

    assert pagina.status_code == 200
    assert "Submeter FORM 1 integral" not in pagina.text
    assert not any("snapshot" in rota or "form1-integral/submeter" in rota for rota in rotas)


def test_migracao_cria_tabela_reversivel_e_snapshot_e_imutavel_no_banco(sessao):
    with motor.begin() as conexao:
        VersaoForm1Integral.__table__.drop(bind=conexao)
    with Session(motor) as outra, outra.begin():
        aplicar_migracao(outra)
    assert inspect(motor).has_table("versao_form1_integral")
    with Session(motor) as outra, outra.begin():
        reverter_migracao(outra)
    assert not inspect(motor).has_table("versao_form1_integral")
    with Session(motor) as outra, outra.begin():
        aplicar_migracao(outra)

    registro = _preparar(sessao, "F18C-IMUTAVEL")
    resultado = _snapshot(sessao, registro, "F18C-IMUTAVEL-SNAPSHOT")

    with pytest.raises(DBAPIError):
        with Session(motor) as outra, outra.begin():
            outra.execute(
                update(VersaoForm1Integral)
                .where(VersaoForm1Integral.id == resultado["snapshot_id"])
                .values(numero=99)
            )
    with pytest.raises(DBAPIError):
        with Session(motor) as outra, outra.begin():
            outra.execute(
                text("DELETE FROM versao_form1_integral WHERE id = :id"),
                {"id": resultado["snapshot_id"]},
            )
    with Session(motor) as outra:
        assert outra.get(VersaoForm1Integral, resultado["snapshot_id"]).numero == 1
    with pytest.raises(RuntimeError, match="contém snapshots"):
        with Session(motor) as outra, outra.begin():
            reverter_migracao(outra)
