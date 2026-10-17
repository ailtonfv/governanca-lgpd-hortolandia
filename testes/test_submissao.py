"""I3/I4 e G2/G3: submissão, retirada, versão e atomicidade."""

import threading
from copy import deepcopy
from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.alertas_operacionais import listar_alertas_operacionais
from app.banco import motor
from app.eventos import verificar_cadeia
from app.instrumentos import (conteudo_canonico, devolver_instrumento, iniciar_analise,
                              iniciar_ajuste, iniciar_preenchimento, lacre_do_conteudo,
                              reatribuir_analise, retirar_submissao, salvar_rascunho,
                              submeter_instrumento, validar_instrumento)
from app.modelos import (AcaoObrigatoria, AnaliseInstrumento, Ciclo, Comando, Designacao,
                         Evento, EventoAuditoria, Instrumento, Pendencia, Registro,
                         RascunhoInstrumento, VersaoInstrumento)
from migracoes.acao_obrigatoria import aplicar as aplicar_migracao_acao
from migracoes.analise_instrumento import aplicar as aplicar_migracao_analise
from migracoes.imutabilidade_versao import aplicar as aplicar_imutabilidade
from migracoes.pendencia import aplicar as aplicar_migracao_pendencia
from app.pendencias import (aceitar_resposta, assumir_pendencia, devolver_resposta,
                            responder_pendencia, retomar_pendencia)
from testes.apoio import CADASTRO, g1, sem_reexecucao


FORM_VALIDO = {
    "finalidade": "Emitir documento tributário fictício",
    "categorias_titulares": ["TIT-CONTRIBUINTE"],
    "categorias_dados": ["DAD-IDENTIFICACAO"],
    "compartilhamentos": [],
}


def criar_form1(cmd="CMD-S-G1", objeto=CADASTRO, contexto="CTX-TRIB-01"):
    resultado = g1(cmd, objeto, contexto)
    assert resultado["permitido"]
    with Session(motor) as sessao:
        instrumento = sessao.scalars(
            select(Instrumento).where(Instrumento.registro_id == resultado["registro_id"])
        ).one()
        return instrumento.id, resultado["registro_id"], resultado["codigo_lgpd"]


def preparar(instrumento_id, conteudo=None, prefixo="CMD-S"):
    conteudo = deepcopy(FORM_VALIDO if conteudo is None else conteudo)
    with Session(motor) as sessao, sessao.begin():
        inicio = iniciar_preenchimento(
            sessao, comando_id=f"{prefixo}-I1", conta_id="CONTA-A1",
            instrumento_id=instrumento_id,
        )
    assert inicio["permitido"]
    with Session(motor) as sessao, sessao.begin():
        salvo = salvar_rascunho(
            sessao, comando_id=f"{prefixo}-I2", conta_id="CONTA-A1",
            instrumento_id=instrumento_id, versao_lida=1, conteudo=conteudo,
        )
    assert salvo["permitido"]
    return salvo["versao_rascunho"]


def i3(instrumento_id, versao=2, cmd="CMD-S-I3", conta="CONTA-A1", **extra):
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return submeter_instrumento(
            sessao, comando_id=cmd, conta_id=conta,
            instrumento_id=instrumento_id, versao_lida=versao, **extra,
        )


def i4(instrumento_id, cmd="CMD-S-I4", conta="CONTA-A1"):
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return retirar_submissao(
            sessao, comando_id=cmd, conta_id=conta, instrumento_id=instrumento_id,
        )


def i13(instrumento_id, versao_id, cmd="CMD-S-I13", conta="CONTA-B1", **extra):
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return iniciar_analise(
            sessao, comando_id=cmd, conta_id=conta, instrumento_id=instrumento_id,
            versao_id=versao_id, **extra,
        )


def i14(instrumento_id, analise_id, responsavel_lido="PESSOA-B",
        novo_responsavel="PESSOA-F", cmd="CMD-S-I14", conta="CONTA-B1", **extra):
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return reatribuir_analise(
            sessao, comando_id=cmd, conta_id=conta, instrumento_id=instrumento_id,
            analise_id=analise_id, responsavel_lido_id=responsavel_lido,
            novo_responsavel_id=novo_responsavel, **extra,
        )


def i5(instrumento_id, analise_id, versao_id, cmd="CMD-S-I5", conta="CONTA-B1",
       **extra):
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return validar_instrumento(
            sessao, comando_id=cmd, conta_id=conta, instrumento_id=instrumento_id,
            analise_id=analise_id, versao_id=versao_id, **extra,
        )


def i6(instrumento_id, analise_id, versao_id, motivo="Corrigir campo fictício",
       cmd="CMD-S-I6", conta="CONTA-B1", **extra):
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return devolver_instrumento(
            sessao, comando_id=cmd, conta_id=conta, instrumento_id=instrumento_id,
            analise_id=analise_id, versao_id=versao_id, motivo=motivo, **extra,
        )


def p2(pendencia_id, cmd="CMD-S-P2", conta="CONTA-A1", **extra):
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return assumir_pendencia(
            sessao, comando_id=cmd, conta_id=conta, pendencia_id=pendencia_id, **extra,
        )


def i7(instrumento_id, pendencia_id, cmd="CMD-S-I7", conta="CONTA-A1", **extra):
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return iniciar_ajuste(
            sessao, comando_id=cmd, conta_id=conta, instrumento_id=instrumento_id,
            pendencia_id=pendencia_id, **extra,
        )


def p3(instrumento_id, pendencia_id, versao=3, cmd="CMD-S-P3",
       conta="CONTA-A1", **extra):
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return responder_pendencia(
            sessao, comando_id=cmd, conta_id=conta, pendencia_id=pendencia_id,
            instrumento_id=instrumento_id, versao_lida=versao, **extra,
        )


def p4(instrumento_id, pendencia_id, cmd="CMD-S-P4", conta="CONTA-B1", **extra):
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return aceitar_resposta(
            sessao, comando_id=cmd, conta_id=conta, pendencia_id=pendencia_id,
            instrumento_id=instrumento_id, **extra,
        )


def p5(instrumento_id, pendencia_id, motivo="Complementar a justificativa fictícia",
       cmd="CMD-S-P5", conta="CONTA-B1", **extra):
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return devolver_resposta(
            sessao, comando_id=cmd, conta_id=conta, pendencia_id=pendencia_id,
            instrumento_id=instrumento_id, motivo=motivo, **extra,
        )


def p6(instrumento_id, pendencia_id, cmd="CMD-S-P6", conta="CONTA-A1", **extra):
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return retomar_pendencia(
            sessao, comando_id=cmd, conta_id=conta, pendencia_id=pendencia_id,
            instrumento_id=instrumento_id, **extra,
        )


def preparar_analise():
    instrumento_id, registro_id, codigo = criar_form1()
    preparar(instrumento_id)
    submissao = i3(instrumento_id)
    analise = i13(instrumento_id, submissao["versao_id"])
    assert analise["permitido"]
    return instrumento_id, registro_id, codigo, submissao, analise


def preparar_devolucao():
    instrumento_id, registro_id, codigo, submissao, analise = preparar_analise()
    devolucao = i6(instrumento_id, analise["analise_id"], submissao["versao_id"])
    assert devolucao["permitido"]
    return instrumento_id, registro_id, codigo, submissao, analise, devolucao


def criar_acao_sintetica(instrumento_id, registro_id, estado="aberta",
                         acao_id="ACAO-SINTETICA-1"):
    momento = datetime(2026, 10, 16, 18, 30, tzinfo=timezone.utc)
    with Session(motor) as sessao, sessao.begin():
        ciclo = sessao.scalars(select(Ciclo).where(
            Ciclo.registro_id == registro_id, Ciclo.numero == 1
        )).one()
        sessao.add(AcaoObrigatoria(
            id=acao_id, registro_id=registro_id, ciclo_id=ciclo.id,
            instrumento_id=instrumento_id, estado=estado,
            responsavel_id="PESSOA-B", evidencia=None,
            criada_em=momento, atualizada_em=momento,
        ))
    return acao_id


def test_i3_cria_snapshot_e_g2_na_mesma_transacao():
    instrumento_id, registro_id, codigo = criar_form1()
    preparar(instrumento_id)
    momento = datetime(2026, 10, 16, 15, 45, tzinfo=timezone.utc)

    resultado = i3(instrumento_id, momento=momento)

    assert resultado["permitido"]
    assert resultado["numero_versao"] == 1
    assert resultado["evento_i3"] == 3
    assert resultado["evento_g2"] == 2
    assert resultado["alertas_sobreposicao"] == []
    with Session(motor) as sessao:
        instrumento = sessao.get(Instrumento, instrumento_id)
        registro = sessao.get(Registro, registro_id)
        versao = sessao.get(VersaoInstrumento, resultado["versao_id"])
        eventos = sessao.scalars(
            select(Evento).where(Evento.comando_id == "CMD-S-I3").order_by(Evento.ordem_no_comando)
        ).all()
        assert instrumento.estado_instrumento == "pronto_para_validacao"
        assert instrumento.versao_vigente_id is None
        assert registro.estado_atual == "em_validacao" and registro.sequencia_atual == 2
        assert versao.numero == 1 and versao.versao_contrato == 2
        assert versao.conteudo == FORM_VALIDO
        assert versao.conteudo_canonico == conteudo_canonico(FORM_VALIDO)
        assert versao.lacre == lacre_do_conteudo(FORM_VALIDO)
        assert versao.submetida_por == "PESSOA-A" and versao.submetida_em == momento
        assert versao.evento_submissao_id == eventos[0].id
        assert [(e.codigo_evento, e.ordem_no_comando) for e in eventos] == [("I3", 1), ("G2", 2)]
        assert eventos[1].conteudo["evento_causa_id"] == eventos[0].id
        assert verificar_cadeia(sessao, instrumento_id)[0]
        assert verificar_cadeia(sessao, codigo)[0]


def test_i3_repetido_e_idempotente():
    instrumento_id, _, _ = criar_form1()
    preparar(instrumento_id)
    original = i3(instrumento_id)
    repetido = i3(instrumento_id)
    assert repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(original)
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(VersaoInstrumento)) == 1
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.comando_id == "CMD-S-I3")) == 2


def test_i3_valida_campos_obrigatorios_sem_criar_versao():
    instrumento_id, registro_id, _ = criar_form1()
    preparar(instrumento_id, {"finalidade": "", "categorias_titulares": [],
                              "categorias_dados": ["DAD-DESCONHECIDO"],
                              "compartilhamentos": "nenhum"})
    resultado = i3(instrumento_id)
    assert not resultado["permitido"] and len(resultado["problemas"]) == 4
    with Session(motor) as sessao:
        assert sessao.get(Instrumento, instrumento_id).estado_instrumento == "em_preenchimento"
        assert sessao.get(Registro, registro_id).estado_atual == "em_andamento"
        assert sessao.scalar(select(func.count()).select_from(VersaoInstrumento)) == 0
        assert sessao.scalars(select(EventoAuditoria).where(
            EventoAuditoria.comando_id == "CMD-S-I3")).one()


def test_i3_recusa_campo_antigo_e_texto_livre_nos_catalogos():
    instrumento_id, _, _ = criar_form1()
    preparar(instrumento_id, {
        "finalidade": "Finalidade fictícia",
        "titulares": ["Nome de pessoa não deve entrar"],
        "categorias_dados": ["Descrição digitada livremente"],
        "compartilhamentos": [],
    })
    resultado = i3(instrumento_id)
    assert not resultado["permitido"]
    assert any("titulares" in problema for problema in resultado["problemas"])
    assert any("categorias_titulares" in problema for problema in resultado["problemas"])
    assert any("código(s) desconhecido(s)" in problema for problema in resultado["problemas"])


def test_i3_recusa_codigos_desconhecidos_em_todos_os_catalogos():
    instrumento_id, _, _ = criar_form1()
    preparar(instrumento_id, {
        "finalidade": "Finalidade fictícia",
        "categorias_titulares": ["TIT-INVENTADO"],
        "categorias_dados": ["DAD-INVENTADO"],
        "compartilhamentos": ["DST-INVENTADO"],
    })
    resultado = i3(instrumento_id)
    assert not resultado["permitido"]
    assert len([p for p in resultado["problemas"] if "desconhecido" in p]) == 3


def test_i3_exige_elaborador_da_unidade_responsavel():
    instrumento_id, registro_id, _ = criar_form1()
    preparar(instrumento_id)
    resultado = i3(instrumento_id, conta="CONTA-B1")
    assert not resultado["permitido"] and "elaborador" in resultado["motivo"]
    with Session(motor) as sessao:
        assert sessao.get(Instrumento, instrumento_id).estado_instrumento == "em_preenchimento"
        assert sessao.get(Registro, registro_id).estado_atual == "em_andamento"
        assert sessao.scalar(select(func.count()).select_from(VersaoInstrumento)) == 0


def test_i3_recusa_rascunho_desatualizado():
    instrumento_id, _, _ = criar_form1()
    preparar(instrumento_id)
    resultado = i3(instrumento_id, versao=1)
    assert not resultado["permitido"] and "desatualizado" in resultado["motivo"]
    assert (resultado["versao_lida"], resultado["versao_atual"]) == (1, 2)


def test_dois_i3_simultaneos_criam_uma_unica_versao():
    instrumento_id, _, codigo = criar_form1()
    preparar(instrumento_id)
    barreira = threading.Barrier(2)
    resultados = []

    def submeter(numero):
        barreira.wait()
        resultados.append(i3(instrumento_id, cmd=f"CMD-S-I3-CONC-{numero}"))

    threads = [threading.Thread(target=submeter, args=(numero,)) for numero in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(r["permitido"] for r in resultados) == [False, True]
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(VersaoInstrumento)) == 1
        assert verificar_cadeia(sessao, instrumento_id)[0]
        assert verificar_cadeia(sessao, codigo)[0]


def test_i3_e_g2_sao_desfeitos_juntos_no_rollback():
    instrumento_id, registro_id, codigo = criar_form1()
    preparar(instrumento_id)
    with pytest.raises(RuntimeError):
        with Session(motor) as sessao, sessao.begin():
            resultado = submeter_instrumento(
                sessao, comando_id="CMD-S-I3-ROLLBACK", conta_id="CONTA-A1",
                instrumento_id=instrumento_id, versao_lida=2,
            )
            assert resultado["permitido"]
            raise RuntimeError("falha simulada antes do commit")
    with Session(motor) as sessao:
        assert sessao.get(Instrumento, instrumento_id).estado_instrumento == "em_preenchimento"
        assert sessao.get(Registro, registro_id).estado_atual == "em_andamento"
        assert sessao.get(Comando, "CMD-S-I3-ROLLBACK") is None
        assert sessao.scalar(select(func.count()).select_from(VersaoInstrumento)) == 0
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.cadeia_id == instrumento_id)) == 2
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.cadeia_id == codigo)) == 1


def test_comparacao_material_gera_alerta_sem_bloquear():
    primeiro, _, _ = criar_form1(cmd="CMD-S-G1-A")
    preparar(primeiro, prefixo="CMD-S-A")
    assert i3(primeiro, cmd="CMD-S-A-I3")["permitido"]

    segundo, _, _ = criar_form1(cmd="CMD-S-G1-B", objeto="OBJ-SRV-900",
                                contexto="CTX-URB-01")
    semelhante = deepcopy(FORM_VALIDO)
    semelhante["finalidade"] = "  emitir DOCUMENTO tributário fictício  "
    semelhante["categorias_dados"] = ["DAD-ENDERECO"]
    preparar(segundo, semelhante, prefixo="CMD-S-B")
    resultado = i3(segundo, cmd="CMD-S-B-I3")

    assert resultado["permitido"]
    assert len(resultado["alertas_sobreposicao"]) == 1
    coincidencias = resultado["alertas_sobreposicao"][0]["coincidencias"]
    assert set(coincidencias) == {"finalidade", "categorias_titulares"}


def test_i2_nao_altera_rascunho_depois_da_submissao():
    instrumento_id, _, _ = criar_form1()
    preparar(instrumento_id)
    assert i3(instrumento_id)["permitido"]
    with Session(motor) as sessao, sessao.begin():
        resultado = salvar_rascunho(
            sessao, comando_id="CMD-S-I2-TARDIO", conta_id="CONTA-A1",
            instrumento_id=instrumento_id, versao_lida=2,
            conteudo={"finalidade": "não deve substituir"},
        )
    assert not resultado["permitido"]
    with Session(motor) as sessao:
        assert sessao.get(RascunhoInstrumento, instrumento_id).conteudo == FORM_VALIDO


def test_versao_submetida_e_imutavel_no_banco():
    instrumento_id, _, _ = criar_form1()
    preparar(instrumento_id)
    resultado = i3(instrumento_id)
    with Session(motor) as sessao, sessao.begin():
        aplicar_imutabilidade(sessao)

    with pytest.raises(DBAPIError):
        with Session(motor) as sessao, sessao.begin():
            sessao.execute(
                update(VersaoInstrumento)
                .where(VersaoInstrumento.id == resultado["versao_id"])
                .values(numero=99)
            )
    with pytest.raises(DBAPIError):
        with Session(motor) as sessao, sessao.begin():
            sessao.execute(text("DELETE FROM versao_instrumento WHERE id = :id"),
                           {"id": resultado["versao_id"]})
    with Session(motor) as sessao:
        assert sessao.get(VersaoInstrumento, resultado["versao_id"]).numero == 1


def test_i4_retorna_ao_rascunho_e_g3_preserva_a_versao():
    instrumento_id, registro_id, codigo = criar_form1()
    preparar(instrumento_id)
    submissao = i3(instrumento_id)

    resultado = i4(instrumento_id)

    assert resultado["permitido"]
    assert resultado["versao_preservada_id"] == submissao["versao_id"]
    assert resultado["evento_i4"] == 4 and resultado["evento_g3"] == 3
    with Session(motor) as sessao:
        instrumento = sessao.get(Instrumento, instrumento_id)
        registro = sessao.get(Registro, registro_id)
        versao = sessao.get(VersaoInstrumento, submissao["versao_id"])
        eventos = sessao.scalars(
            select(Evento).where(Evento.comando_id == "CMD-S-I4").order_by(Evento.ordem_no_comando)
        ).all()
        assert instrumento.estado_instrumento == "em_preenchimento"
        assert registro.estado_atual == "em_andamento" and registro.sequencia_atual == 3
        assert versao.numero == 1 and versao.conteudo == FORM_VALIDO
        assert [(e.codigo_evento, e.ordem_no_comando) for e in eventos] == [("I4", 1), ("G3", 2)]
        assert eventos[1].conteudo["evento_causa_id"] == eventos[0].id
        assert verificar_cadeia(sessao, instrumento_id)[0]
        assert verificar_cadeia(sessao, codigo)[0]


def test_i4_repetido_e_idempotente():
    instrumento_id, _, _ = criar_form1()
    preparar(instrumento_id)
    i3(instrumento_id)
    original = i4(instrumento_id)
    repetido = i4(instrumento_id)
    assert repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(original)
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(VersaoInstrumento)) == 1
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.comando_id == "CMD-S-I4")) == 2


def test_i4_exige_elaborador_e_estado_adequado():
    instrumento_id, _, _ = criar_form1()
    preparar(instrumento_id)
    assert not i4(instrumento_id, cmd="CMD-S-I4-CEDO")["permitido"]
    i3(instrumento_id)
    negado = i4(instrumento_id, cmd="CMD-S-I4-SEM-PAPEL", conta="CONTA-B1")
    assert not negado["permitido"] and "elaborador" in negado["motivo"]
    assert i4(instrumento_id, cmd="CMD-S-I4-OK")["permitido"]
    assert not i4(instrumento_id, cmd="CMD-S-I4-DUPLO")["permitido"]


def test_i4_e_bloqueado_se_i13_ja_iniciou_a_analise():
    instrumento_id, registro_id, _ = criar_form1()
    preparar(instrumento_id)
    submissao = i3(instrumento_id)
    assert i13(instrumento_id, submissao["versao_id"])["permitido"]

    resultado = i4(instrumento_id)
    assert not resultado["permitido"] and "I13" in resultado["motivo"]
    with Session(motor) as sessao:
        assert sessao.get(Instrumento, instrumento_id).estado_instrumento == "pronto_para_validacao"
        assert sessao.get(Registro, registro_id).estado_atual == "em_validacao"
        assert sessao.scalar(select(func.count()).select_from(VersaoInstrumento)) == 1


def test_dois_i4_simultaneos_so_um_retira_a_submissao():
    instrumento_id, _, codigo = criar_form1()
    preparar(instrumento_id)
    i3(instrumento_id)
    barreira = threading.Barrier(2)
    resultados = []

    def retirar(numero):
        barreira.wait()
        resultados.append(i4(instrumento_id, cmd=f"CMD-S-I4-CONC-{numero}"))

    threads = [threading.Thread(target=retirar, args=(numero,)) for numero in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(r["permitido"] for r in resultados) == [False, True]
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(VersaoInstrumento)) == 1
        assert verificar_cadeia(sessao, instrumento_id)[0]
        assert verificar_cadeia(sessao, codigo)[0]


def test_i4_e_g3_sao_desfeitos_juntos_no_rollback():
    instrumento_id, registro_id, codigo = criar_form1()
    preparar(instrumento_id)
    i3(instrumento_id)
    with pytest.raises(RuntimeError):
        with Session(motor) as sessao, sessao.begin():
            resultado = retirar_submissao(
                sessao, comando_id="CMD-S-I4-ROLLBACK", conta_id="CONTA-A1",
                instrumento_id=instrumento_id,
            )
            assert resultado["permitido"]
            raise RuntimeError("falha simulada antes do commit")
    with Session(motor) as sessao:
        assert sessao.get(Instrumento, instrumento_id).estado_instrumento == "pronto_para_validacao"
        assert sessao.get(Registro, registro_id).estado_atual == "em_validacao"
        assert sessao.get(Comando, "CMD-S-I4-ROLLBACK") is None
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.cadeia_id == instrumento_id)) == 3
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.cadeia_id == codigo)) == 2


def test_a11_nova_submissao_cria_versao_2_sem_apagar_versao_1():
    instrumento_id, _, _ = criar_form1()
    preparar(instrumento_id)
    primeira = i3(instrumento_id)
    assert i4(instrumento_id)["permitido"]
    alterado = deepcopy(FORM_VALIDO)
    alterado["finalidade"] = "Finalidade corrigida fictícia"
    with Session(motor) as sessao, sessao.begin():
        salvo = salvar_rascunho(
            sessao, comando_id="CMD-S-A11-I2", conta_id="CONTA-A1",
            instrumento_id=instrumento_id, versao_lida=2, conteudo=alterado,
        )
    segunda = i3(instrumento_id, versao=salvo["versao_rascunho"], cmd="CMD-S-A11-I3")

    assert segunda["permitido"] and segunda["numero_versao"] == 2
    with Session(motor) as sessao:
        versoes = sessao.scalars(
            select(VersaoInstrumento)
            .where(VersaoInstrumento.instrumento_id == instrumento_id)
            .order_by(VersaoInstrumento.numero)
        ).all()
        assert [(v.numero, v.conteudo) for v in versoes] == [(1, FORM_VALIDO), (2, alterado)]
        assert versoes[0].id == primeira["versao_id"]


def test_i13_inicia_analise_sem_mudar_os_estados():
    instrumento_id, registro_id, codigo = criar_form1()
    preparar(instrumento_id)
    submissao = i3(instrumento_id)
    momento = datetime(2026, 10, 16, 17, 30, tzinfo=timezone.utc)

    resultado = i13(instrumento_id, submissao["versao_id"], momento=momento)

    assert resultado["permitido"] and resultado["responsavel_atual_id"] == "PESSOA-B"
    assert resultado["evento_i13"] == 4
    with Session(motor) as sessao:
        analise = sessao.get(AnaliseInstrumento, resultado["analise_id"])
        evento = sessao.scalars(select(Evento).where(Evento.comando_id == "CMD-S-I13")).one()
        assert analise.versao_id == submissao["versao_id"]
        assert analise.responsavel_atual_id == "PESSOA-B"
        assert analise.iniciada_por == "PESSOA-B"
        assert analise.iniciada_em == momento and analise.atualizada_em == momento
        assert analise.situacao == "ativa" and analise.evento_inicio_id == evento.id
        assert sessao.get(Instrumento, instrumento_id).estado_instrumento == "pronto_para_validacao"
        assert sessao.get(Registro, registro_id).estado_atual == "em_validacao"
        assert verificar_cadeia(sessao, instrumento_id)[0]
        assert verificar_cadeia(sessao, codigo)[0]


def test_i13_repetido_e_idempotente():
    instrumento_id, _, _ = criar_form1()
    preparar(instrumento_id)
    submissao = i3(instrumento_id)
    original = i13(instrumento_id, submissao["versao_id"])
    repetido = i13(instrumento_id, submissao["versao_id"])
    assert repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(original)
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(AnaliseInstrumento)) == 1


def test_i13_compara_a_pessoa_e_impede_autor_da_submissao():
    instrumento_id, _, _ = criar_form1()
    preparar(instrumento_id)
    submissao = i3(instrumento_id)
    with Session(motor) as sessao, sessao.begin():
        sessao.add(Designacao(pessoa_id="PESSOA-A", unidade_id="UNID-NORTE",
                              papel="analista", ativa=True))

    resultado = i13(instrumento_id, submissao["versao_id"], conta="CONTA-A2")

    assert not resultado["permitido"] and "segregação" in resultado["motivo"]
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(AnaliseInstrumento)) == 0
        assert sessao.scalars(select(EventoAuditoria).where(
            EventoAuditoria.comando_id == "CMD-S-I13")).one()


def test_i13_exige_analista_da_unidade_responsavel():
    instrumento_id, _, _ = criar_form1()
    preparar(instrumento_id)
    submissao = i3(instrumento_id)
    resultado = i13(instrumento_id, submissao["versao_id"], conta="CONTA-C1")
    assert not resultado["permitido"] and "analista" in resultado["motivo"]


def test_i13_recusa_versao_antiga_depois_de_nova_submissao():
    instrumento_id, _, _ = criar_form1()
    preparar(instrumento_id)
    primeira = i3(instrumento_id)
    i4(instrumento_id)
    alterado = deepcopy(FORM_VALIDO)
    alterado["finalidade"] = "Outra finalidade fictícia"
    with Session(motor) as sessao, sessao.begin():
        salvo = salvar_rascunho(
            sessao, comando_id="CMD-S-I13-I2", conta_id="CONTA-A1",
            instrumento_id=instrumento_id, versao_lida=2, conteudo=alterado,
        )
    segunda = i3(instrumento_id, versao=salvo["versao_rascunho"], cmd="CMD-S-I13-I3")
    resultado = i13(instrumento_id, primeira["versao_id"])
    assert not resultado["permitido"] and "mais recente" in resultado["motivo"]
    assert segunda["numero_versao"] == 2


def test_dois_i13_simultaneos_criam_uma_unica_analise():
    instrumento_id, _, codigo = criar_form1()
    preparar(instrumento_id)
    submissao = i3(instrumento_id)
    barreira = threading.Barrier(2)
    resultados = []

    def analisar(numero):
        barreira.wait()
        resultados.append(i13(instrumento_id, submissao["versao_id"],
                               cmd=f"CMD-S-I13-CONC-{numero}"))

    threads = [threading.Thread(target=analisar, args=(numero,)) for numero in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(r["permitido"] for r in resultados) == [False, True]
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(AnaliseInstrumento)) == 1
        assert verificar_cadeia(sessao, instrumento_id)[0]
        assert verificar_cadeia(sessao, codigo)[0]


def test_i13_e_atomico_se_a_transacao_falha():
    instrumento_id, _, _ = criar_form1()
    preparar(instrumento_id)
    submissao = i3(instrumento_id)
    with pytest.raises(RuntimeError):
        with Session(motor) as sessao, sessao.begin():
            resultado = iniciar_analise(
                sessao, comando_id="CMD-S-I13-ROLLBACK", conta_id="CONTA-B1",
                instrumento_id=instrumento_id, versao_id=submissao["versao_id"],
            )
            assert resultado["permitido"]
            raise RuntimeError("falha simulada antes do commit")
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(AnaliseInstrumento)) == 0
        assert sessao.get(Comando, "CMD-S-I13-ROLLBACK") is None
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.cadeia_id == instrumento_id)) == 3


def test_migracao_4_recria_a_tabela_de_analise():
    with motor.begin() as conexao:
        AnaliseInstrumento.__table__.drop(bind=conexao, checkfirst=True)
        with Session(bind=conexao) as sessao:
            aplicar_migracao_analise(sessao)
        assert "analise_instrumento" in conexao.dialect.get_table_names(conexao)


def test_i14_troca_responsavel_sem_apagar_autoria_do_i13():
    instrumento_id, registro_id, codigo, _, inicio = preparar_analise()
    momento = datetime(2026, 10, 16, 18, 15, tzinfo=timezone.utc)

    resultado = i14(instrumento_id, inicio["analise_id"], momento=momento)

    assert resultado["permitido"]
    assert resultado["responsavel_anterior_id"] == "PESSOA-B"
    assert resultado["responsavel_atual_id"] == "PESSOA-F"
    assert resultado["evento_i14"] == 5
    with Session(motor) as sessao:
        analise = sessao.get(AnaliseInstrumento, inicio["analise_id"])
        evento = sessao.scalars(select(Evento).where(Evento.comando_id == "CMD-S-I14")).one()
        assert analise.iniciada_por == "PESSOA-B"
        assert analise.responsavel_atual_id == "PESSOA-F"
        assert analise.atualizada_em == momento
        assert evento.conteudo["responsavel_anterior_id"] == "PESSOA-B"
        assert evento.conteudo["responsavel_atual_id"] == "PESSOA-F"
        assert sessao.get(Instrumento, instrumento_id).estado_instrumento == "pronto_para_validacao"
        assert sessao.get(Registro, registro_id).estado_atual == "em_validacao"
        assert verificar_cadeia(sessao, instrumento_id)[0]
        assert verificar_cadeia(sessao, codigo)[0]


def test_i14_repetido_e_idempotente():
    instrumento_id, _, _, _, inicio = preparar_analise()
    original = i14(instrumento_id, inicio["analise_id"])
    repetido = i14(instrumento_id, inicio["analise_id"])
    assert repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(original)
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento == "I14")) == 1


def test_i14_exige_validador_e_novo_responsavel_analista():
    instrumento_id, _, _, _, inicio = preparar_analise()
    sem_competencia = i14(instrumento_id, inicio["analise_id"], conta="CONTA-C1",
                          cmd="CMD-S-I14-SEM-COMPETENCIA")
    assert not sem_competencia["permitido"] and "validador" in sem_competencia["motivo"]
    sem_papel = i14(instrumento_id, inicio["analise_id"], novo_responsavel="PESSOA-C",
                    cmd="CMD-S-I14-ALVO-SEM-PAPEL")
    assert not sem_papel["permitido"] and "analista" in sem_papel["motivo"]


def test_i14_nao_pode_atribuir_analise_ao_autor_da_submissao():
    instrumento_id, _, _, _, inicio = preparar_analise()
    with Session(motor) as sessao, sessao.begin():
        sessao.add(Designacao(pessoa_id="PESSOA-A", unidade_id="UNID-NORTE",
                              papel="analista", ativa=True))
    resultado = i14(instrumento_id, inicio["analise_id"], novo_responsavel="PESSOA-A")
    assert not resultado["permitido"] and "segregação" in resultado["motivo"]


def test_dois_i14_simultaneos_com_mesmo_responsavel_lido_so_um_vence():
    instrumento_id, _, codigo, _, inicio = preparar_analise()
    with Session(motor) as sessao, sessao.begin():
        sessao.add(Designacao(pessoa_id="PESSOA-C", unidade_id="UNID-NORTE",
                              papel="analista", ativa=True))
    barreira = threading.Barrier(2)
    resultados = []

    def reatribuir(numero, destino):
        barreira.wait()
        resultados.append(i14(
            instrumento_id, inicio["analise_id"], novo_responsavel=destino,
            cmd=f"CMD-S-I14-CONC-{numero}",
        ))

    threads = [threading.Thread(target=reatribuir, args=(1, "PESSOA-C")),
               threading.Thread(target=reatribuir, args=(2, "PESSOA-F"))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(r["permitido"] for r in resultados) == [False, True]
    with Session(motor) as sessao:
        analise = sessao.get(AnaliseInstrumento, inicio["analise_id"])
        assert analise.responsavel_atual_id in {"PESSOA-C", "PESSOA-F"}
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento == "I14")) == 1
        assert verificar_cadeia(sessao, instrumento_id)[0]
        assert verificar_cadeia(sessao, codigo)[0]


def test_i14_e_atomico_se_a_transacao_falha():
    instrumento_id, _, _, _, inicio = preparar_analise()
    with pytest.raises(RuntimeError):
        with Session(motor) as sessao, sessao.begin():
            resultado = reatribuir_analise(
                sessao, comando_id="CMD-S-I14-ROLLBACK", conta_id="CONTA-B1",
                instrumento_id=instrumento_id, analise_id=inicio["analise_id"],
                responsavel_lido_id="PESSOA-B", novo_responsavel_id="PESSOA-F",
            )
            assert resultado["permitido"]
            raise RuntimeError("falha simulada antes do commit")
    with Session(motor) as sessao:
        analise = sessao.get(AnaliseInstrumento, inicio["analise_id"])
        assert analise.responsavel_atual_id == "PESSOA-B"
        assert sessao.get(Comando, "CMD-S-I14-ROLLBACK") is None
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento == "I14")) == 0


def test_i5_valida_versao_e_g4_retorna_registro_a_em_andamento_sem_acao():
    instrumento_id, registro_id, codigo, submissao, inicio = preparar_analise()
    momento = datetime(2026, 10, 16, 19, 0, tzinfo=timezone.utc)

    resultado = i5(instrumento_id, inicio["analise_id"], submissao["versao_id"],
                    momento=momento)

    assert resultado["permitido"]
    assert resultado["estado_instrumento"] == "validado"
    assert resultado["estado_registro"] == "em_andamento"
    assert resultado["criterio_g4"] == "sem_instrumento_pronto_ou_acao_aberta"
    assert resultado["evento_i5"] == 5 and resultado["evento_g4"] == 3
    with Session(motor) as sessao:
        instrumento = sessao.get(Instrumento, instrumento_id)
        registro = sessao.get(Registro, registro_id)
        analise = sessao.get(AnaliseInstrumento, inicio["analise_id"])
        eventos = sessao.scalars(
            select(Evento).where(Evento.comando_id == "CMD-S-I5").order_by(Evento.ordem_no_comando)
        ).all()
        assert instrumento.versao_vigente_id == submissao["versao_id"]
        assert instrumento.estado_instrumento == "validado"
        assert analise.situacao == "encerrada" and analise.atualizada_em == momento
        assert registro.estado_atual == "em_andamento" and registro.sequencia_atual == 3
        assert [(evento.codigo_evento, evento.ordem_no_comando) for evento in eventos] == [
            ("I5", 1), ("G4", 2),
        ]
        assert eventos[1].conteudo["evento_causa_id"] == eventos[0].id
        assert verificar_cadeia(sessao, instrumento_id)[0]
        assert verificar_cadeia(sessao, codigo)[0]


def test_g4_leva_registro_a_em_execucao_quando_ha_acao_aberta():
    instrumento_id, registro_id, _, submissao, inicio = preparar_analise()
    acao_id = criar_acao_sintetica(instrumento_id, registro_id)

    resultado = i5(instrumento_id, inicio["analise_id"], submissao["versao_id"])

    assert resultado["permitido"]
    assert resultado["estado_registro"] == "em_execucao"
    assert resultado["criterio_g4"] == "acao_obrigatoria_aberta"
    assert resultado["acoes_obrigatorias_abertas"] == [acao_id]
    with Session(motor) as sessao:
        evento_g4 = sessao.scalars(select(Evento).where(
            Evento.comando_id == "CMD-S-I5", Evento.codigo_evento == "G4"
        )).one()
        assert evento_g4.conteudo["acoes_obrigatorias_abertas"] == [acao_id]
        assert sessao.get(Registro, registro_id).estado_atual == "em_execucao"


def test_g4_ignora_acao_que_ja_foi_concluida():
    instrumento_id, registro_id, _, submissao, inicio = preparar_analise()
    criar_acao_sintetica(instrumento_id, registro_id, estado="concluida")

    resultado = i5(instrumento_id, inicio["analise_id"], submissao["versao_id"])

    assert resultado["permitido"]
    assert resultado["estado_registro"] == "em_andamento"
    assert resultado["acoes_obrigatorias_abertas"] == []


def test_i5_so_aceita_o_responsavel_vigente_da_analise():
    instrumento_id, _, _, submissao, inicio = preparar_analise()
    assert i14(instrumento_id, inicio["analise_id"])["permitido"]

    anterior = i5(instrumento_id, inicio["analise_id"], submissao["versao_id"],
                   cmd="CMD-S-I5-ANTERIOR", conta="CONTA-B1")
    vigente = i5(instrumento_id, inicio["analise_id"], submissao["versao_id"],
                  cmd="CMD-S-I5-VIGENTE", conta="CONTA-F1")

    assert not anterior["permitido"] and "responsável vigente" in anterior["motivo"]
    assert vigente["permitido"]


def test_i5_repetido_e_idempotente():
    instrumento_id, _, _, submissao, inicio = preparar_analise()
    original = i5(instrumento_id, inicio["analise_id"], submissao["versao_id"])
    repetido = i5(instrumento_id, inicio["analise_id"], submissao["versao_id"])

    assert repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(original)
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.comando_id == "CMD-S-I5")) == 2


def test_dois_i5_simultaneos_so_um_valida():
    instrumento_id, _, codigo, submissao, inicio = preparar_analise()
    barreira = threading.Barrier(2)
    resultados = []

    def validar(numero):
        barreira.wait()
        resultados.append(i5(
            instrumento_id, inicio["analise_id"], submissao["versao_id"],
            cmd=f"CMD-S-I5-CONC-{numero}",
        ))

    threads = [threading.Thread(target=validar, args=(numero,)) for numero in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(resultado["permitido"] for resultado in resultados) == [False, True]
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento == "I5")) == 1
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento == "G4")) == 1
        assert verificar_cadeia(sessao, instrumento_id)[0]
        assert verificar_cadeia(sessao, codigo)[0]


def test_i5_e_g4_sao_desfeitos_juntos_no_rollback():
    instrumento_id, registro_id, _, submissao, inicio = preparar_analise()
    with pytest.raises(RuntimeError):
        with Session(motor) as sessao, sessao.begin():
            resultado = validar_instrumento(
                sessao, comando_id="CMD-S-I5-ROLLBACK", conta_id="CONTA-B1",
                instrumento_id=instrumento_id, analise_id=inicio["analise_id"],
                versao_id=submissao["versao_id"],
            )
            assert resultado["permitido"]
            raise RuntimeError("falha simulada antes do commit")

    with Session(motor) as sessao:
        instrumento = sessao.get(Instrumento, instrumento_id)
        analise = sessao.get(AnaliseInstrumento, inicio["analise_id"])
        assert instrumento.estado_instrumento == "pronto_para_validacao"
        assert instrumento.versao_vigente_id is None
        assert analise.situacao == "ativa"
        assert sessao.get(Registro, registro_id).estado_atual == "em_validacao"
        assert sessao.get(Comando, "CMD-S-I5-ROLLBACK") is None
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento.in_(["I5", "G4"]))) == 0


def test_migracao_6_recria_tabela_de_acao_obrigatoria():
    with motor.begin() as conexao:
        AcaoObrigatoria.__table__.drop(bind=conexao, checkfirst=True)
        with Session(bind=conexao) as sessao:
            aplicar_migracao_acao(sessao)
        assert "acao_obrigatoria" in conexao.dialect.get_table_names(conexao)


def test_i6_cria_pendencia_e_g3_preservando_a_versao():
    instrumento_id, registro_id, codigo, submissao, inicio = preparar_analise()
    momento = datetime(2026, 10, 16, 20, 30, tzinfo=timezone.utc)

    resultado = i6(instrumento_id, inicio["analise_id"], submissao["versao_id"],
                    motivo="Complementar finalidade fictícia", momento=momento)

    assert resultado["permitido"]
    assert resultado["estado_instrumento"] == "devolvido_para_ajuste"
    assert resultado["estado_pendencia"] == "aberta"
    assert resultado["estado_registro"] == "em_andamento"
    assert resultado["evento_i6"] == 5 and resultado["evento_p1"] == 1
    assert resultado["evento_g3"] == 3
    with Session(motor) as sessao:
        instrumento = sessao.get(Instrumento, instrumento_id)
        registro = sessao.get(Registro, registro_id)
        analise = sessao.get(AnaliseInstrumento, inicio["analise_id"])
        versao = sessao.get(VersaoInstrumento, submissao["versao_id"])
        pendencia = sessao.get(Pendencia, resultado["pendencia_id"])
        eventos = sessao.scalars(
            select(Evento).where(Evento.comando_id == "CMD-S-I6").order_by(Evento.ordem_no_comando)
        ).all()
        assert instrumento.estado_instrumento == "devolvido_para_ajuste"
        assert instrumento.versao_vigente_id is None
        assert registro.estado_atual == "em_andamento" and registro.sequencia_atual == 3
        assert analise.situacao == "encerrada" and analise.atualizada_em == momento
        assert versao.numero == 1 and versao.conteudo == FORM_VALIDO
        assert pendencia.tipo_pendencia == "devolucao"
        assert pendencia.unidade_destino_id == registro.unidade_principal_atual_id
        assert pendencia.responsavel_atual_id is None
        assert pendencia.bloqueante and pendencia.gate_bloqueado == "submissao"
        assert pendencia.motivo == "Complementar finalidade fictícia"
        assert [(evento.codigo_evento, evento.ordem_no_comando) for evento in eventos] == [
            ("I6", 1), ("P1", 2), ("G3", 3),
        ]
        assert eventos[1].conteudo["evento_causa_id"] == eventos[0].id
        assert eventos[2].conteudo["evento_causa_id"] == eventos[0].id
        assert verificar_cadeia(sessao, instrumento_id)[0]
        assert verificar_cadeia(sessao, resultado["pendencia_id"])[0]
        assert verificar_cadeia(sessao, codigo)[0]


def test_i6_exige_motivo_util_e_limitado():
    instrumento_id, _, _, submissao, inicio = preparar_analise()
    vazio = i6(instrumento_id, inicio["analise_id"], submissao["versao_id"],
               motivo="   ", cmd="CMD-S-I6-VAZIO")
    longo = i6(instrumento_id, inicio["analise_id"], submissao["versao_id"],
               motivo="x" * 1001, cmd="CMD-S-I6-LONGO")

    assert not vazio["permitido"] and "motivo" in vazio["motivo"]
    assert not longo["permitido"] and "1000" in longo["motivo"]
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Pendencia)) == 0


def test_i6_so_aceita_o_responsavel_vigente_da_analise():
    instrumento_id, _, _, submissao, inicio = preparar_analise()
    assert i14(instrumento_id, inicio["analise_id"])["permitido"]

    anterior = i6(instrumento_id, inicio["analise_id"], submissao["versao_id"],
                   cmd="CMD-S-I6-ANTERIOR", conta="CONTA-B1")
    vigente = i6(instrumento_id, inicio["analise_id"], submissao["versao_id"],
                  cmd="CMD-S-I6-VIGENTE", conta="CONTA-F1")

    assert not anterior["permitido"] and "responsável vigente" in anterior["motivo"]
    assert vigente["permitido"]


def test_i6_mantem_segregacao_mesmo_diante_de_projecao_inconsistente():
    instrumento_id, _, _, submissao, inicio = preparar_analise()
    with Session(motor) as sessao, sessao.begin():
        analise = sessao.get(AnaliseInstrumento, inicio["analise_id"])
        analise.responsavel_atual_id = "PESSOA-A"

    resultado = i6(instrumento_id, inicio["analise_id"], submissao["versao_id"],
                    cmd="CMD-S-I6-SEGREGACAO", conta="CONTA-A2")

    assert not resultado["permitido"] and "segregação" in resultado["motivo"]
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Pendencia)) == 0


def test_i6_recusa_versao_diferente_da_analise():
    instrumento_id, _, _, submissao, inicio = preparar_analise()
    resultado = i6(instrumento_id, inicio["analise_id"], "VERSAO-INEXISTENTE",
                    cmd="CMD-S-I6-VERSAO")
    assert not resultado["permitido"] and "versão analisada" in resultado["motivo"]
    assert submissao["versao_id"] != "VERSAO-INEXISTENTE"


def test_i6_repetido_e_idempotente():
    instrumento_id, _, _, submissao, inicio = preparar_analise()
    original = i6(instrumento_id, inicio["analise_id"], submissao["versao_id"])
    repetido = i6(instrumento_id, inicio["analise_id"], submissao["versao_id"])

    assert repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(original)
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Pendencia)) == 1
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.comando_id == "CMD-S-I6")) == 3


def test_dois_i6_simultaneos_criam_uma_unica_pendencia():
    instrumento_id, _, codigo, submissao, inicio = preparar_analise()
    barreira = threading.Barrier(2)
    resultados = []

    def devolver(numero):
        barreira.wait()
        resultados.append(i6(
            instrumento_id, inicio["analise_id"], submissao["versao_id"],
            cmd=f"CMD-S-I6-CONC-{numero}",
        ))

    threads = [threading.Thread(target=devolver, args=(numero,)) for numero in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(resultado["permitido"] for resultado in resultados) == [False, True]
    with Session(motor) as sessao:
        pendencia = sessao.scalars(select(Pendencia)).one()
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento == "I6")) == 1
        assert verificar_cadeia(sessao, instrumento_id)[0]
        assert verificar_cadeia(sessao, pendencia.id)[0]
        assert verificar_cadeia(sessao, codigo)[0]


def test_i6_p1_e_g3_sao_desfeitos_juntos_no_rollback():
    instrumento_id, registro_id, _, submissao, inicio = preparar_analise()
    with pytest.raises(RuntimeError):
        with Session(motor) as sessao, sessao.begin():
            resultado = devolver_instrumento(
                sessao, comando_id="CMD-S-I6-ROLLBACK", conta_id="CONTA-B1",
                instrumento_id=instrumento_id, analise_id=inicio["analise_id"],
                versao_id=submissao["versao_id"], motivo="Correção fictícia",
            )
            assert resultado["permitido"]
            raise RuntimeError("falha simulada antes do commit")

    with Session(motor) as sessao:
        instrumento = sessao.get(Instrumento, instrumento_id)
        analise = sessao.get(AnaliseInstrumento, inicio["analise_id"])
        assert instrumento.estado_instrumento == "pronto_para_validacao"
        assert analise.situacao == "ativa"
        assert sessao.get(Registro, registro_id).estado_atual == "em_validacao"
        assert sessao.get(Comando, "CMD-S-I6-ROLLBACK") is None
        assert sessao.scalar(select(func.count()).select_from(Pendencia)) == 0
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento.in_(["I6", "P1", "G3"]))) == 0


def test_migracao_7_recria_tabela_de_pendencia():
    with motor.begin() as conexao:
        Pendencia.__table__.drop(bind=conexao, checkfirst=True)
        with Session(bind=conexao) as sessao:
            aplicar_migracao_pendencia(sessao)
        assert "pendencia" in conexao.dialect.get_table_names(conexao)


def test_p2_assume_pendencia_e_atualiza_flags_calculadas():
    instrumento_id, _, _, _, _, devolucao = preparar_devolucao()
    pendencia_id = devolucao["pendencia_id"]
    with Session(motor) as sessao:
        antes = listar_alertas_operacionais(sessao, "CONTA-A1")
        assert {alerta["codigo"] for alerta in antes} == {
            "CORRECAO_SOLICITADA", "SUBMISSAO_BLOQUEADA",
        }
        assert listar_alertas_operacionais(sessao, "CONTA-C1") == []

    resultado = p2(pendencia_id)

    assert resultado["permitido"]
    assert resultado["estado_pendencia"] == "em_atendimento"
    assert resultado["responsavel_atual_id"] == "PESSOA-A"
    assert resultado["evento_p2"] == 2
    with Session(motor) as sessao:
        pendencia = sessao.get(Pendencia, pendencia_id)
        assert pendencia.estado == "em_atendimento"
        assert pendencia.responsavel_atual_id == "PESSOA-A"
        assert verificar_cadeia(sessao, pendencia_id)[0]
        depois = listar_alertas_operacionais(sessao, "CONTA-A1")
        assert {alerta["codigo"] for alerta in depois} == {
            "PENDENCIA_ATRIBUIDA_A_VOCE", "SUBMISSAO_BLOQUEADA",
        }
        assert all(alerta["instrumento_id"] == instrumento_id for alerta in depois)


def test_p2_exige_agente_autorizado_na_unidade_destino():
    _, _, _, _, _, devolucao = preparar_devolucao()
    resultado = p2(devolucao["pendencia_id"], conta="CONTA-C1")
    assert not resultado["permitido"] and "autorizada" in resultado["motivo"]
    with Session(motor) as sessao:
        assert sessao.get(Pendencia, devolucao["pendencia_id"]).estado == "aberta"


def test_p2_repetido_e_idempotente():
    _, _, _, _, _, devolucao = preparar_devolucao()
    original = p2(devolucao["pendencia_id"])
    repetido = p2(devolucao["pendencia_id"])
    assert repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(original)
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento == "P2")) == 1


def test_dois_p2_simultaneos_so_um_assume_a_pendencia():
    _, _, _, _, _, devolucao = preparar_devolucao()
    pendencia_id = devolucao["pendencia_id"]
    barreira = threading.Barrier(2)
    resultados = []

    def assumir(numero):
        barreira.wait()
        resultados.append(p2(pendencia_id, cmd=f"CMD-S-P2-CONC-{numero}"))

    threads = [threading.Thread(target=assumir, args=(numero,)) for numero in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(resultado["permitido"] for resultado in resultados) == [False, True]
    with Session(motor) as sessao:
        assert sessao.get(Pendencia, pendencia_id).responsavel_atual_id == "PESSOA-A"
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento == "P2")) == 1


def test_p2_e_desfeito_no_rollback():
    _, _, _, _, _, devolucao = preparar_devolucao()
    pendencia_id = devolucao["pendencia_id"]
    with pytest.raises(RuntimeError):
        with Session(motor) as sessao, sessao.begin():
            resultado = assumir_pendencia(
                sessao, comando_id="CMD-S-P2-ROLLBACK", conta_id="CONTA-A1",
                pendencia_id=pendencia_id,
            )
            assert resultado["permitido"]
            raise RuntimeError("falha simulada antes do commit")
    with Session(motor) as sessao:
        pendencia = sessao.get(Pendencia, pendencia_id)
        assert pendencia.estado == "aberta" and pendencia.responsavel_atual_id is None
        assert sessao.get(Comando, "CMD-S-P2-ROLLBACK") is None
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento == "P2")) == 0


def test_i7_exige_que_a_pendencia_tenha_sido_assumida():
    instrumento_id, _, _, _, _, devolucao = preparar_devolucao()
    resultado = i7(instrumento_id, devolucao["pendencia_id"])
    assert not resultado["permitido"] and "assumida" in resultado["motivo"]
    with Session(motor) as sessao:
        assert sessao.get(Instrumento, instrumento_id).estado_instrumento == "devolvido_para_ajuste"


def test_i7_cria_novo_rascunho_da_versao_devolvida_e_libera_i2():
    instrumento_id, _, codigo, submissao, _, devolucao = preparar_devolucao()
    assert p2(devolucao["pendencia_id"])["permitido"]
    momento = datetime(2026, 10, 16, 21, 0, tzinfo=timezone.utc)

    resultado = i7(instrumento_id, devolucao["pendencia_id"], momento=momento)

    assert resultado["permitido"] and resultado["versao_rascunho"] == 3
    assert resultado["estado_instrumento"] == "em_preenchimento"
    assert resultado["estado_pendencia"] == "em_atendimento"
    with Session(motor) as sessao:
        instrumento = sessao.get(Instrumento, instrumento_id)
        rascunho = sessao.get(RascunhoInstrumento, instrumento_id)
        versao = sessao.get(VersaoInstrumento, submissao["versao_id"])
        assert instrumento.estado_instrumento == "em_preenchimento"
        assert rascunho.conteudo == versao.conteudo == FORM_VALIDO
        assert rascunho.lacre_conteudo == versao.lacre
        assert rascunho.versao_rascunho == 3
        assert rascunho.salvo_por == "PESSOA-A" and rascunho.salvo_em == momento
        assert sessao.get(Pendencia, devolucao["pendencia_id"]).estado == "em_atendimento"
        assert verificar_cadeia(sessao, instrumento_id)[0]
        assert verificar_cadeia(sessao, codigo)[0]

    corrigido = deepcopy(FORM_VALIDO)
    corrigido["finalidade"] = "Finalidade corrigida depois da devolução"
    with Session(motor) as sessao, sessao.begin():
        salvo = salvar_rascunho(
            sessao, comando_id="CMD-S-I7-I2", conta_id="CONTA-A1",
            instrumento_id=instrumento_id, versao_lida=3, conteudo=corrigido,
        )
    assert salvo["permitido"] and salvo["versao_rascunho"] == 4


def test_i7_so_pode_ser_executado_por_quem_assumiu_a_pendencia():
    instrumento_id, _, _, _, _, devolucao = preparar_devolucao()
    with Session(motor) as sessao, sessao.begin():
        sessao.add(Designacao(pessoa_id="PESSOA-F", unidade_id="UNID-NORTE",
                              papel="elaborador", ativa=True))
    assert p2(devolucao["pendencia_id"])["permitido"]

    resultado = i7(instrumento_id, devolucao["pendencia_id"],
                    cmd="CMD-S-I7-OUTRO", conta="CONTA-F1")
    assert not resultado["permitido"] and "assumiu" in resultado["motivo"]


def test_i7_repetido_e_idempotente_e_rollback_preserva_estado_anterior():
    instrumento_id, _, _, _, _, devolucao = preparar_devolucao()
    pendencia_id = devolucao["pendencia_id"]
    assert p2(pendencia_id)["permitido"]

    with pytest.raises(RuntimeError):
        with Session(motor) as sessao, sessao.begin():
            resultado = iniciar_ajuste(
                sessao, comando_id="CMD-S-I7-ROLLBACK", conta_id="CONTA-A1",
                instrumento_id=instrumento_id, pendencia_id=pendencia_id,
            )
            assert resultado["permitido"]
            raise RuntimeError("falha simulada antes do commit")
    with Session(motor) as sessao:
        assert sessao.get(Instrumento, instrumento_id).estado_instrumento == "devolvido_para_ajuste"
        assert sessao.get(RascunhoInstrumento, instrumento_id).versao_rascunho == 2
        assert sessao.get(Comando, "CMD-S-I7-ROLLBACK") is None
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento == "I7")) == 0

    original = i7(instrumento_id, pendencia_id)
    repetido = i7(instrumento_id, pendencia_id)
    assert original["permitido"] and repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(original)


def preparar_correcao():
    instrumento_id, registro_id, codigo, submissao, analise, devolucao = preparar_devolucao()
    pendencia_id = devolucao["pendencia_id"]
    assert p2(pendencia_id)["permitido"]
    assert i7(instrumento_id, pendencia_id)["permitido"]
    corrigido = deepcopy(FORM_VALIDO)
    corrigido["finalidade"] = "Finalidade corrigida e pronta para conferência"
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        salvo = salvar_rascunho(
            sessao, comando_id="CMD-S-P3-I2", conta_id="CONTA-A1",
            instrumento_id=instrumento_id, versao_lida=3, conteudo=corrigido,
        )
    assert salvo["permitido"] and salvo["versao_rascunho"] == 4
    return (instrumento_id, registro_id, codigo, submissao, analise,
            devolucao, salvo)


def test_p3_registra_lacre_da_correcao_e_congela_o_rascunho():
    instrumento_id, _, _, _, _, devolucao, salvo = preparar_correcao()
    pendencia_id = devolucao["pendencia_id"]
    momento = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)

    resultado = p3(instrumento_id, pendencia_id, versao=4, momento=momento)

    assert resultado["permitido"]
    assert resultado["estado_pendencia"] == "respondida"
    assert resultado["lacre_resposta"] == salvo["lacre_conteudo"]
    assert resultado["evento_p3"] == 3
    with Session(motor) as sessao:
        pendencia = sessao.get(Pendencia, pendencia_id)
        rascunho = sessao.get(RascunhoInstrumento, instrumento_id)
        assert pendencia.estado == "respondida"
        assert pendencia.lacre_resposta == rascunho.lacre_conteudo
        assert pendencia.atualizada_em == momento
        assert verificar_cadeia(sessao, pendencia_id)[0]
        assert {alerta["codigo"] for alerta in listar_alertas_operacionais(
            sessao, "CONTA-B1"
        )} == {"RESPOSTA_AGUARDANDO_DECISAO"}

    alterado = deepcopy(FORM_VALIDO)
    alterado["finalidade"] = "Tentativa de alterar depois da resposta"
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        bloqueado = salvar_rascunho(
            sessao, comando_id="CMD-S-P3-I2-BLOQ", conta_id="CONTA-A1",
            instrumento_id=instrumento_id, versao_lida=4, conteudo=alterado,
        )
    assert not bloqueado["permitido"] and "congelado" in bloqueado["motivo"]


def test_p3_recusa_rascunho_desatualizado():
    instrumento_id, _, _, _, _, devolucao, _ = preparar_correcao()
    resultado = p3(instrumento_id, devolucao["pendencia_id"], versao=3)
    assert not resultado["permitido"] and "desatualizado" in resultado["motivo"]
    assert resultado["versao_atual"] == 4
    with Session(motor) as sessao:
        pendencia = sessao.get(Pendencia, devolucao["pendencia_id"])
        assert pendencia.estado == "em_atendimento" and pendencia.lacre_resposta is None


def test_p3_so_pode_ser_executado_por_quem_assumiu_a_pendencia():
    instrumento_id, _, _, _, _, devolucao, _ = preparar_correcao()
    with Session(motor) as sessao, sessao.begin():
        sessao.add(Designacao(pessoa_id="PESSOA-F", unidade_id="UNID-NORTE",
                              papel="elaborador", ativa=True))

    resultado = p3(instrumento_id, devolucao["pendencia_id"], versao=4,
                    cmd="CMD-S-P3-OUTRO", conta="CONTA-F1")
    assert not resultado["permitido"] and "assumiu" in resultado["motivo"]


def test_p3_repetido_e_idempotente():
    instrumento_id, _, _, _, _, devolucao, _ = preparar_correcao()
    pendencia_id = devolucao["pendencia_id"]
    original = p3(instrumento_id, pendencia_id, versao=4)
    repetido = p3(instrumento_id, pendencia_id, versao=4)
    assert original["permitido"] and repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(original)
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento == "P3")) == 1


def test_dois_p3_simultaneos_registram_uma_unica_resposta():
    instrumento_id, _, _, _, _, devolucao, _ = preparar_correcao()
    pendencia_id = devolucao["pendencia_id"]
    barreira = threading.Barrier(2)
    resultados = []

    def responder(numero):
        barreira.wait()
        resultados.append(p3(
            instrumento_id, pendencia_id, versao=4,
            cmd=f"CMD-S-P3-CONC-{numero}",
        ))

    threads = [threading.Thread(target=responder, args=(numero,)) for numero in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(resultado["permitido"] for resultado in resultados) == [False, True]
    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento == "P3")) == 1


def test_p3_e_desfeito_no_rollback():
    instrumento_id, _, _, _, _, devolucao, salvo = preparar_correcao()
    pendencia_id = devolucao["pendencia_id"]
    with pytest.raises(RuntimeError):
        with Session(motor) as sessao, sessao.begin():
            resultado = responder_pendencia(
                sessao, comando_id="CMD-S-P3-ROLLBACK", conta_id="CONTA-A1",
                pendencia_id=pendencia_id, instrumento_id=instrumento_id,
                versao_lida=4,
            )
            assert resultado["permitido"]
            raise RuntimeError("falha simulada antes do commit")

    with Session(motor) as sessao:
        pendencia = sessao.get(Pendencia, pendencia_id)
        assert pendencia.estado == "em_atendimento" and pendencia.lacre_resposta is None
        assert sessao.get(RascunhoInstrumento, instrumento_id).lacre_conteudo == salvo["lacre_conteudo"]
        assert sessao.get(Comando, "CMD-S-P3-ROLLBACK") is None
        assert sessao.scalar(select(func.count()).select_from(Evento)
                             .where(Evento.codigo_evento == "P3")) == 0


def preparar_resposta():
    dados = preparar_correcao()
    instrumento_id, _, _, _, _, devolucao, _ = dados
    resposta = p3(instrumento_id, devolucao["pendencia_id"], versao=4)
    assert resposta["permitido"]
    return (*dados, resposta)


def test_p4_aceita_o_lacre_e_libera_a_versao_2():
    instrumento_id, _, _, _, _, devolucao, salvo, _ = preparar_resposta()
    pendencia_id = devolucao["pendencia_id"]

    aceite = p4(instrumento_id, pendencia_id)

    assert aceite["permitido"] and aceite["estado_pendencia"] == "encerrada"
    assert aceite["lacre_aceito"] == salvo["lacre_conteudo"]
    with Session(motor) as sessao:
        pendencia = sessao.get(Pendencia, pendencia_id)
        assert not pendencia.bloqueante and pendencia.gate_bloqueado is None
        assert pendencia.lacre_aceito == salvo["lacre_conteudo"]
        assert verificar_cadeia(sessao, pendencia_id)[0]

    submissao_2 = i3(instrumento_id, versao=4, cmd="CMD-S-A2A-I3-2")
    assert submissao_2["permitido"] and submissao_2["numero_versao"] == 2
    assert submissao_2["lacre_conteudo"] == aceite["lacre_aceito"]


def test_p4_exige_validador_distinto_do_autor_da_submissao():
    instrumento_id, _, _, _, _, devolucao, _, _ = preparar_resposta()
    pendencia_id = devolucao["pendencia_id"]

    mesmo_autor = p4(instrumento_id, pendencia_id, cmd="CMD-S-P4-AUTOR",
                      conta="CONTA-A2")
    sem_competencia = p4(instrumento_id, pendencia_id, cmd="CMD-S-P4-SEM-PAPEL",
                         conta="CONTA-F1")

    assert not mesmo_autor["permitido"] and "segregação" in mesmo_autor["motivo"]
    assert not sem_competencia["permitido"] and "validador" in sem_competencia["motivo"]


def test_i3_bloqueia_pendencia_ativa_e_rascunho_diferente_do_aceito():
    instrumento_id, _, _, _, _, devolucao, _, _ = preparar_resposta()
    pendencia_id = devolucao["pendencia_id"]

    bloqueado = i3(instrumento_id, versao=4, cmd="CMD-S-I3-ANTES-P4")
    assert not bloqueado["permitido"] and "P4" in bloqueado["motivo"]
    assert p4(instrumento_id, pendencia_id)["permitido"]

    alterado = deepcopy(FORM_VALIDO)
    alterado["finalidade"] = "Conteúdo alterado depois do aceite"
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        salvo = salvar_rascunho(
            sessao, comando_id="CMD-S-I2-DEPOIS-P4", conta_id="CONTA-A1",
            instrumento_id=instrumento_id, versao_lida=4, conteudo=alterado,
        )
    assert salvo["permitido"] and salvo["versao_rascunho"] == 5
    divergente = i3(instrumento_id, versao=5, cmd="CMD-S-I3-LACRE-DIVERGENTE")
    assert not divergente["permitido"] and "não coincide" in divergente["motivo"]


def test_p4_e_idempotente_e_rollback_preserva_a_resposta():
    instrumento_id, _, _, _, _, devolucao, _, _ = preparar_resposta()
    pendencia_id = devolucao["pendencia_id"]
    with pytest.raises(RuntimeError):
        with Session(motor) as sessao, sessao.begin():
            resultado = aceitar_resposta(
                sessao, comando_id="CMD-S-P4-ROLLBACK", conta_id="CONTA-B1",
                pendencia_id=pendencia_id, instrumento_id=instrumento_id,
            )
            assert resultado["permitido"]
            raise RuntimeError("falha simulada antes do commit")
    with Session(motor) as sessao:
        pendencia = sessao.get(Pendencia, pendencia_id)
        assert pendencia.estado == "respondida" and pendencia.lacre_aceito is None
        assert pendencia.bloqueante

    original = p4(instrumento_id, pendencia_id)
    repetido = p4(instrumento_id, pendencia_id)
    assert original["permitido"] and repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(original)


def test_p5_exige_motivo_e_devolve_a_mesma_pendencia():
    instrumento_id, _, _, _, _, devolucao, _, _ = preparar_resposta()
    pendencia_id = devolucao["pendencia_id"]
    sem_motivo = p5(instrumento_id, pendencia_id, motivo="   ",
                    cmd="CMD-S-P5-SEM-MOTIVO")
    assert not sem_motivo["permitido"] and "motivo" in sem_motivo["motivo"]

    resultado = p5(instrumento_id, pendencia_id,
                   motivo="  Explicar melhor a finalidade fictícia  ")
    assert resultado["permitido"]
    assert resultado["estado_pendencia"] == "devolvida_para_complementacao"
    assert resultado["motivo_complementacao"] == "Explicar melhor a finalidade fictícia"
    with Session(motor) as sessao:
        pendencia = sessao.get(Pendencia, pendencia_id)
        assert pendencia.estado == "devolvida_para_complementacao"
        assert pendencia.motivo == "Explicar melhor a finalidade fictícia"
        assert sessao.scalar(select(func.count()).select_from(Pendencia)) == 1
        assert {alerta["codigo"] for alerta in listar_alertas_operacionais(
            sessao, "CONTA-A1"
        )} == {"COMPLEMENTACAO_SOLICITADA", "SUBMISSAO_BLOQUEADA"}

    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        bloqueado = salvar_rascunho(
            sessao, comando_id="CMD-S-P5-I2-BLOQ", conta_id="CONTA-A1",
            instrumento_id=instrumento_id, versao_lida=4, conteudo=FORM_VALIDO,
        )
    assert not bloqueado["permitido"] and "congelado" in bloqueado["motivo"]


def test_p6_exige_responsavel_e_libera_nova_correcao():
    instrumento_id, _, _, _, _, devolucao, _, _ = preparar_resposta()
    pendencia_id = devolucao["pendencia_id"]
    assert p5(instrumento_id, pendencia_id)["permitido"]
    with Session(motor) as sessao, sessao.begin():
        sessao.add(Designacao(pessoa_id="PESSOA-F", unidade_id="UNID-NORTE",
                              papel="elaborador", ativa=True))

    outro = p6(instrumento_id, pendencia_id, cmd="CMD-S-P6-OUTRO", conta="CONTA-F1")
    assert not outro["permitido"] and "responsável" in outro["motivo"]
    retomada = p6(instrumento_id, pendencia_id)
    assert retomada["permitido"] and retomada["estado_pendencia"] == "em_atendimento"
    with Session(motor) as sessao:
        assert {alerta["codigo"] for alerta in listar_alertas_operacionais(
            sessao, "CONTA-A1"
        )} == {"PENDENCIA_ATRIBUIDA_A_VOCE", "SUBMISSAO_BLOQUEADA"}

    complemento = deepcopy(FORM_VALIDO)
    complemento["finalidade"] = "Finalidade fictícia novamente complementada"
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        salvo = salvar_rascunho(
            sessao, comando_id="CMD-S-P6-I2", conta_id="CONTA-A1",
            instrumento_id=instrumento_id, versao_lida=4, conteudo=complemento,
        )
    assert salvo["permitido"] and salvo["versao_rascunho"] == 5


def test_a2b_reutiliza_a_pendencia_e_preserva_as_duas_respostas():
    instrumento_id, _, _, _, _, devolucao, primeira_correcao, primeira_resposta = preparar_resposta()
    pendencia_id = devolucao["pendencia_id"]
    assert p5(instrumento_id, pendencia_id, motivo="Detalhar melhor")["permitido"]
    assert p6(instrumento_id, pendencia_id)["permitido"]

    complemento = deepcopy(FORM_VALIDO)
    complemento["finalidade"] = "Finalidade fictícia detalhada na segunda resposta"
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        salvo_2 = salvar_rascunho(
            sessao, comando_id="CMD-S-A2B-I2-2", conta_id="CONTA-A1",
            instrumento_id=instrumento_id, versao_lida=4, conteudo=complemento,
        )
    resposta_2 = p3(instrumento_id, pendencia_id, versao=5, cmd="CMD-S-A2B-P3-2")
    assert resposta_2["permitido"] and resposta_2["lacre_resposta"] == salvo_2["lacre_conteudo"]
    assert resposta_2["lacre_resposta"] != primeira_resposta["lacre_resposta"]
    assert p4(instrumento_id, pendencia_id)["permitido"]
    submissao_2 = i3(instrumento_id, versao=5, cmd="CMD-S-A2B-I3-2")
    assert submissao_2["permitido"] and submissao_2["numero_versao"] == 2

    with Session(motor) as sessao:
        assert sessao.scalar(select(func.count()).select_from(Pendencia)) == 1
        eventos_p3 = sessao.scalars(
            select(Evento).where(Evento.codigo_evento == "P3")
            .order_by(Evento.sequencia_cadeia)
        ).all()
        assert [evento.conteudo["lacre_resposta"] for evento in eventos_p3] == [
            primeira_correcao["lacre_conteudo"], salvo_2["lacre_conteudo"],
        ]


def test_p4_e_p5_concorrentes_registram_uma_unica_decisao():
    instrumento_id, _, _, _, _, devolucao, _, _ = preparar_resposta()
    pendencia_id = devolucao["pendencia_id"]
    barreira = threading.Barrier(2)
    resultados = []

    def decidir(aceitar):
        barreira.wait()
        if aceitar:
            resultados.append(p4(instrumento_id, pendencia_id, cmd="CMD-S-P4-CONC"))
        else:
            resultados.append(p5(instrumento_id, pendencia_id, cmd="CMD-S-P5-CONC"))

    threads = [threading.Thread(target=decidir, args=(valor,)) for valor in (True, False)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(resultado["permitido"] for resultado in resultados) == [False, True]
    with Session(motor) as sessao:
        total = sessao.scalar(
            select(func.count()).select_from(Evento)
            .where(Evento.codigo_evento.in_(["P4", "P5"]))
        )
        assert total == 1


def test_p5_e_p6_sao_idempotentes_e_rollback_nao_avanca_estado():
    instrumento_id, _, _, _, _, devolucao, _, _ = preparar_resposta()
    pendencia_id = devolucao["pendencia_id"]
    with pytest.raises(RuntimeError):
        with Session(motor) as sessao, sessao.begin():
            resultado = devolver_resposta(
                sessao, comando_id="CMD-S-P5-ROLLBACK", conta_id="CONTA-B1",
                pendencia_id=pendencia_id, instrumento_id=instrumento_id,
                motivo="Motivo que será desfeito",
            )
            assert resultado["permitido"]
            raise RuntimeError("falha simulada antes do commit")
    assert p5(instrumento_id, pendencia_id)["permitido"]
    assert p5(instrumento_id, pendencia_id)["reexecutado"] is True

    with pytest.raises(RuntimeError):
        with Session(motor) as sessao, sessao.begin():
            resultado = retomar_pendencia(
                sessao, comando_id="CMD-S-P6-ROLLBACK", conta_id="CONTA-A1",
                pendencia_id=pendencia_id, instrumento_id=instrumento_id,
            )
            assert resultado["permitido"]
            raise RuntimeError("falha simulada antes do commit")
    with Session(motor) as sessao:
        assert sessao.get(Pendencia, pendencia_id).estado == "devolvida_para_complementacao"

    original = p6(instrumento_id, pendencia_id)
    repetido = p6(instrumento_id, pendencia_id)
    assert original["permitido"] and repetido["reexecutado"] is True
    assert sem_reexecucao(repetido) == sem_reexecucao(original)
