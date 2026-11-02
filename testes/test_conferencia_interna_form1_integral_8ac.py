"""Incremento 8AC — conferência interna preparatória do FORM 1 (AAA)."""

import threading

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from app.atribuicao_form1_integral import atribuir_arp_form1_integral
from app.banco import motor
from app.conferencia_interna_form1_integral import (
    solicitar_conferencia_interna_form1_integral,
)
from app.consultas_interface import carregar_painel
from app.main import app
from app.modelos import (
    Comando, ConferenciaInternaForm1Integral, Evento, EventoAuditoria,
    Instrumento, RascunhoForm1Integral, Registro, VersaoForm1Integral,
)
from app.rascunho_form1_integral import (
    iniciar_rascunho_form1_integral, salvar_bloco_1_form1_integral,
)
from testes.apoio import CADASTRO, g1
from migracoes.conferencia_interna_form1_integral import (
    aplicar as aplicar_migracao, reverter as reverter_migracao,
)


def _preparar(sessao, prefixo, *, arp="PESSOA-G", conta_arp="CONTA-G1"):
    registro = g1(f"{prefixo}-G1", CADASTRO, "CTX-TRIB-01")
    modo = "proprio" if arp == "PESSOA-A" else "outro"
    atribuicao = atribuir_arp_form1_integral(
        sessao, comando_id=f"{prefixo}-ARP", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], modo=modo,
        arp_pessoa_id=None if modo == "proprio" else arp, versao_lida=0,
    )
    inicio = iniciar_rascunho_form1_integral(
        sessao, comando_id=f"{prefixo}-INI", conta_id=conta_arp,
        registro_id=registro["registro_id"],
    )
    sessao.commit()
    assert atribuicao["permitido"] and inicio["permitido"]
    return registro


def _solicitar(sessao, registro, comando="8AC-SOL", conta="CONTA-G1", versao=1):
    resultado = solicitar_conferencia_interna_form1_integral(
        sessao, comando_id=comando, conta_id=conta,
        registro_id=registro["registro_id"], versao_lida=versao,
    )
    sessao.commit()
    return resultado


def test_arp_solicita_conferencia_incompleta_com_snapshot_e_sem_submeter(sessao):
    registro = _preparar(sessao, "8AC-OK")
    reg = sessao.get(Registro, registro["registro_id"])
    instrumento = sessao.scalars(select(Instrumento).where(
        Instrumento.registro_id == reg.id,
        Instrumento.tipo_instrumento == "FORM1",
    )).one()
    estados = (reg.estado_atual, instrumento.estado_instrumento)

    resultado = _solicitar(sessao, registro)

    conferencia = sessao.get(ConferenciaInternaForm1Integral, reg.id)
    snapshot = sessao.get(VersaoForm1Integral, conferencia.snapshot_id)
    eventos = sessao.scalars(select(Evento).where(
        Evento.comando_id == "8AC-SOL"
    ).order_by(Evento.ordem_no_comando)).all()
    sessao.refresh(reg)
    sessao.refresh(instrumento)
    assert resultado["permitido"] and resultado["submissao_habilitada"] is False
    assert conferencia.situacao == "aguardando_conferencia_interna_apa"
    assert conferencia.solicitada_por_id == "PESSOA-G"
    assert conferencia.apa_em_exercicio_no_momento_id == "PESSOA-A"
    assert snapshot.versao_rascunho == 1
    assert snapshot.conteudo["submissao_habilitada"] is False
    assert [item.tipo_evento for item in eventos] == [
        "preparar_snapshot_form1_integral",
        "solicitar_conferencia_interna_form1_integral",
    ]
    assert (reg.estado_atual, instrumento.estado_instrumento) == estados


def test_solicitacao_e_idempotente_e_nao_duplica(sessao):
    registro = _preparar(sessao, "8AC-IDEM")
    parametros = dict(
        comando_id="8AC-IDEM-SOL", conta_id="CONTA-G1",
        registro_id=registro["registro_id"], versao_lida=1,
    )
    primeiro = solicitar_conferencia_interna_form1_integral(sessao, **parametros)
    sessao.commit()
    repetido = solicitar_conferencia_interna_form1_integral(sessao, **parametros)
    sessao.commit()
    assert primeiro["permitido"] and repetido["reexecutado"] is True
    assert repetido["snapshot_id"] == primeiro["snapshot_id"]
    assert sessao.scalar(select(func.count()).select_from(
        ConferenciaInternaForm1Integral
    )) == 1


def test_nega_nao_arp_versao_antiga_e_lacre_invalido(sessao):
    registro = _preparar(sessao, "8AC-NEG")
    nao_arp = solicitar_conferencia_interna_form1_integral(
        sessao, comando_id="8AC-NEG-ATOR", conta_id="CONTA-B1",
        registro_id=registro["registro_id"], versao_lida=1,
    )
    desatualizado = solicitar_conferencia_interna_form1_integral(
        sessao, comando_id="8AC-NEG-V", conta_id="CONTA-G1",
        registro_id=registro["registro_id"], versao_lida=2,
    )
    rascunho = sessao.get(RascunhoForm1Integral, registro["registro_id"])
    rascunho.lacre_conteudo = "0" * 64
    sessao.commit()
    lacre = solicitar_conferencia_interna_form1_integral(
        sessao, comando_id="8AC-NEG-L", conta_id="CONTA-G1",
        registro_id=registro["registro_id"], versao_lida=1,
    )
    sessao.commit()
    assert not nao_arp["permitido"] and "somente o ARP" in nao_arp["motivo"]
    assert not desatualizado["permitido"] and "desatualizado" in desatualizado["motivo"]
    assert not lacre["permitido"] and "lacre" in lacre["motivo"]
    assert sessao.get(ConferenciaInternaForm1Integral, registro["registro_id"]) is None


def test_apa_recebe_providencia_e_consulta_snapshot_imutavel(sessao):
    registro = _preparar(sessao, "8AC-PAINEL")
    resultado = _solicitar(sessao, registro)
    painel = carregar_painel(sessao, "CONTA-A1")
    assert len(painel["proximas_conferencias_form1"]) == 1
    assert painel["proximas_conferencias_form1"][0]["registro_id"] == registro["registro_id"]

    cliente = TestClient(app)
    painel_http = cliente.get("/", params={"conta_id": "CONTA-A1"})
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}/form1-integral/conferencia-interna",
        params={"conta_id": "CONTA-A1"},
    )
    negada = cliente.get(
        f"/registros/{registro['registro_id']}/form1-integral/conferencia-interna",
        params={"conta_id": "CONTA-B1"},
    )
    assert painel_http.status_code == 200
    assert painel_http.text.count('class="cartao-mapeamento"') == 1
    assert "Conferir levantamento" in painel_http.text
    assert "Responsável pela próxima etapa:" in painel_http.text
    assert pagina.status_code == 200
    assert "não é submissão" in pagina.text
    assert resultado["snapshot_id"] in sessao.scalars(
        select(VersaoForm1Integral.id)
    ).all()
    assert negada.status_code == 403
    assert sessao.scalar(select(func.count()).select_from(EventoAuditoria).where(
        EventoAuditoria.tipo_evento == "tentativa_negada",
        EventoAuditoria.ator_id == "PESSOA-B",
    )) == 1


def test_apa_que_tambem_e_arp_pratica_dois_atos_separados(sessao):
    registro = _preparar(
        sessao, "8AC-MESMA-PESSOA", arp="PESSOA-A", conta_arp="CONTA-A1"
    )
    resultado = _solicitar(
        sessao, registro, comando="8AC-MESMA-SOL", conta="CONTA-A1"
    )
    painel = carregar_painel(sessao, "CONTA-A1")
    assert resultado["permitido"]
    assert painel["proximas_conferencias_form1"]
    assert sessao.scalars(select(Evento).where(
        Evento.comando_id == "8AC-MESMA-SOL"
    )).all()
    assert not any(
        evento.tipo_evento in {"confirmar_conclusao", "submeter_form1_integral"}
        for evento in sessao.scalars(select(Evento).where(
            Evento.registro_id == registro["registro_id"]
        ))
    )


def test_falha_na_auditoria_reverte_snapshot_solicitacao_eventos_e_comando(sessao, monkeypatch):
    registro = _preparar(sessao, "8AC-RB")

    def falhar(*args, **kwargs):
        raise RuntimeError("falha fictícia controlada")

    monkeypatch.setattr(
        "app.conferencia_interna_form1_integral.registrar_auditoria", falhar
    )
    with pytest.raises(RuntimeError, match="falha fictícia"):
        solicitar_conferencia_interna_form1_integral(
            sessao, comando_id="8AC-RB-SOL", conta_id="CONTA-G1",
            registro_id=registro["registro_id"], versao_lida=1,
        )
        sessao.commit()
    sessao.rollback()
    assert sessao.get(ConferenciaInternaForm1Integral, registro["registro_id"]) is None
    assert sessao.scalar(select(func.count()).select_from(VersaoForm1Integral)) == 0
    assert sessao.get(Comando, "8AC-RB-SOL") is None
    assert sessao.scalar(select(func.count()).select_from(Evento).where(
        Evento.comando_id == "8AC-RB-SOL"
    )) == 0


def test_solicitacoes_concorrentes_preservam_uma_unica_versao(sessao):
    registro = _preparar(sessao, "8AC-CONC")
    barreira = threading.Barrier(2)
    resultados = []

    def solicitar(numero):
        with Session(motor) as outra, outra.begin():
            barreira.wait()
            resultados.append(solicitar_conferencia_interna_form1_integral(
                outra, comando_id=f"8AC-CONC-{numero}", conta_id="CONTA-G1",
                registro_id=registro["registro_id"], versao_lida=1,
            ))

    threads = [threading.Thread(target=solicitar, args=(numero,)) for numero in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    sessao.expire_all()
    assert sorted(item["permitido"] for item in resultados) == [False, True]
    assert sessao.scalar(select(func.count()).select_from(
        ConferenciaInternaForm1Integral
    )) == 1
    assert sessao.scalar(select(func.count()).select_from(VersaoForm1Integral)) == 1


def test_rota_solicita_e_exibe_ato_preparatorio_sem_acao_final(sessao):
    registro = _preparar(sessao, "8AC-HTTP")
    cliente = TestClient(app)
    detalhe = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-G1"}
    )
    assert detalhe.status_code == 200
    assert "Solicitar conferência interna do APA" in detalhe.text
    resposta = cliente.post(
        f"/registros/{registro['registro_id']}/form1-integral/conferencia-interna/solicitar",
        data={"conta_id": "CONTA-G1", "comando_id": "8AC-HTTP-SOL", "versao_lida": "1"},
        follow_redirects=True,
    )
    assert resposta.status_code == 200
    assert "Isso não submete nem conclui o FORM 1" in resposta.text
    assert "Confirmar conclusão institucional" not in resposta.text


def test_migracao_20_e_nao_destrutiva_e_reversivel_quando_vazia(sessao):
    with motor.begin() as conexao:
        ConferenciaInternaForm1Integral.__table__.drop(bind=conexao)
    with Session(motor) as outra, outra.begin():
        aplicar_migracao(outra)
    assert inspect(motor).has_table("conferencia_interna_form1_integral")
    with Session(motor) as outra, outra.begin():
        reverter_migracao(outra)
    assert not inspect(motor).has_table("conferencia_interna_form1_integral")
    with Session(motor) as outra, outra.begin():
        aplicar_migracao(outra)
