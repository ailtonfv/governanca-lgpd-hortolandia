from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.banco import motor
from app.eventos import registrar_auditoria, verificar_segmento
from app.modelos import EventoAuditoria


def test_auditoria_dez_consultas_simultaneas():
    barreira = Barrier(10)
    def registrar(i):
        with Session(motor) as s, s.begin():
            barreira.wait(timeout=15)
            evento = registrar_auditoria(s, "consulta", "sistema", "ensaio", {"consulta": i})
            return evento.segmento_id
    with ThreadPoolExecutor(10) as pool:
        segmentos = set(pool.map(registrar, range(10)))
    with Session(motor) as s:
        segmento, = segmentos
        eventos = s.scalars(select(EventoAuditoria).where(EventoAuditoria.segmento_id == segmento)).all()
        assert {e.conteudo["consulta"] for e in eventos} == set(range(10))
        assert sorted(e.sequencia_segmento for e in eventos) == list(range(1, 11))
        assert verificar_segmento(s, segmento)[0]


def test_painel_exige_designacao_vigente(sessao):
    from testes.apoio_entrada import ClienteAposApresentacao as TestClient
    from app.main import app
    from app.fila_form2 import agora
    from app.modelos import DesignacaoEncarregado
    c = TestClient(app)
    for conta in ("CONTA-A1", "CONTA-B1"):
        assert c.get("/form2/painel-dpo", params={"conta_id":conta}).status_code == 403
    assert c.get("/form2/painel-dpo?conta_id=CONTA-E1").status_code == 200
    sessao.scalar(select(DesignacaoEncarregado)).fim = agora()
    sessao.commit()
    assert c.get("/form2/painel-dpo?conta_id=CONTA-E1").status_code == 403


def test_exclusividade_no_dominio():
    import pytest
    from app.respostas_form2 import aplicar_revisao, aplicar_bloco
    chave = "opcao:F2-3.1"
    with pytest.raises(ValueError):
        aplicar_revisao({},3,{chave:["ALT_09","A_CONFIRMAR"]},demonstrativo=True)
    aplicar_revisao({},3,{chave:["ALT_09","ANALISE_JURIDICA"]},demonstrativo=True)
    with pytest.raises(ValueError):
        aplicar_bloco({},bloco=2,alteracoes={"F2-2.9.1":["ALT_01","A_CONFIRMAR"]},proxima_versao=1)

from testes.apoio_entrada import ClienteAposApresentacao as TestClient
from app.main import app
from app.modelos import ParticipacaoForm2
from testes.test_governanca_form2_v9 import principal


def test_grade_pendencias_e_retorno(principal):
    cliente = TestClient(app)
    url = f"/form2/participacoes/{principal.id}"
    for n in (1, 7, 14):
        bloco = cliente.get(f"{url}/blocos/{n}?conta_id=CONTA-B1")
        assert bloco.status_code == 200
        assert bloco.text.count('data-numero="') == 14
        assert f'bloco_origem={n}' in bloco.text
        assert "Central de Acesso (trocar servidor)" in bloco.text
        pendencias = cliente.get(f"{url}/governanca?conta_id=CONTA-B1&bloco_origem={n}")
        assert f"Voltar ao bloco {n}" in pendencias.text
        assert ("Acrescentar outra necessidade" in pendencias.text) == (n == 1)


def test_retorno_dpo_e_resposta_aal(sessao, principal):
    cliente = TestClient(app)
    url = f"/form2/participacoes/{principal.id}/orientacao"
    estado = principal.estado
    for conta in ("CONTA-A1", "CONTA-B1"):
        assert cliente.post(url, data={"conta_id": conta, "comando_id": "L5-" + conta,
                            "texto": "Orientação fictícia."}).status_code == 403
        assert 'id="painel-dpo"' not in cliente.get(f"/form2/filas?conta_id={conta}#painel-dpo").text
    recebida = cliente.post(url, data={"conta_id": "CONTA-E1", "comando_id": "L5-OF",
                                       "texto": "Orientação fictícia."})
    assert recebida.status_code == 200
    assert "Manifestação registrada em " in recebida.text
    assert "Aguardando resposta do AAL" in recebida.text
    assert "data-confirmar-ato" in recebida.text
    consulta = sessao.scalar(select(ParticipacaoForm2).where(ParticipacaoForm2.origem_id == principal.id,
                                                             ParticipacaoForm2.tipo == "dpo"))
    respondida = cliente.post(f"/form2/participacoes/{consulta.id}/orientacao",
        data={"conta_id":"CONTA-B1", "comando_id":"L5-RESP", "texto":"Revisão registrada.", "decisao":"Acolhida"})
    assert respondida.status_code == 200 and "Resposta registrada em " in respondida.text
    historico = cliente.get(url + "?conta_id=CONTA-E1")
    assert "Revisão registrada." in historico.text and "Servidor Beta" in historico.text
    painel = cliente.get("/form2/painel-dpo?conta_id=CONTA-E1")
    assert [l['consulta'].id for l in painel.context['grupos_dpo']['respondidas']] == [consulta.id]
    sessao.refresh(principal)
    assert principal.estado == estado


def test_central_e_consulta_principal(principal):
    cliente = TestClient(app)
    url = f"/form2/participacoes/{principal.id}"
    troca = cliente.get("/central?conta_id=CONTA-B1&troca=1")
    assert "Agora você está como" in troca.text
    assert url in troca.text and "Seus itens em andamento" in troca.text
    pagina = cliente.get(url + "?conta_id=CONTA-B1")
    assert "Sua questão" in pagina.text
    assert pagina.text.count(">Encaminhar consulta</button>") == 1
    assert ">Salvar manifestação</button>" not in pagina.text
    assert "Abrir Painel do DPO" in cliente.get("/painel?conta_id=CONTA-E1").text


def test_conferencia_entre_titular_e_suplente(sessao):
    from testes.test_form2_preparacao import base
    from app.conferencia_interna_form1_integral import (
        solicitar_conferencia_interna_form1_integral, confirmar_conferencia_interna_form1_integral,
    )
    rid, _ = base(sessao)
    from testes.test_conferencia_interna_form1_integral_8ac import _salvar_para_apresentar
    versao = _salvar_para_apresentar(sessao, {"registro_id":rid}, "CONTA-A1")
    args = dict(registro_id=rid, versao_lida=versao)
    assert solicitar_conferencia_interna_form1_integral(sessao, **args, conta_id="CONTA-A1",
            comando_id="L5-AP")["permitido"]
    sessao.commit()
    from app.modelos import ConferenciaInternaForm1Integral
    args["versao_lida"]=sessao.get(ConferenciaInternaForm1Integral,rid).versao_projecao
    cliente = TestClient(app)
    registro = f"/registros/{rid}"
    espera = cliente.get(registro + "?conta_id=CONTA-A1")
    assert "Você apresentou esta versão" in espera.text and "APA suplente" in espera.text
    consulta = cliente.get(registro + "/form1-integral/conferencia-interna?conta_id=CONTA-F1")
    assert "APA titular apresentou" in consulta.text and "como APA suplente" in consulta.text
    assert confirmar_conferencia_interna_form1_integral(sessao, **args, conta_id="CONTA-F1",
            comando_id="L5-CF")["permitido"]
    sessao.commit()
    recibo = cliente.get(registro + "?conta_id=CONTA-F1")
    assert "APA suplente — conferiu a Apresentação" in recibo.text
    assert "Encaminhado à fila do FORM 2" in recibo.text and "DPO comunicado" in recibo.text


def test_bloco_parcial_e_avisos_de_guarda(principal):
    from app.respostas_form2 import GUARDA_INSTITUCIONAL
    c = TestClient(app)
    url = f"/form2/participacoes/{principal.id}/blocos/2"
    salvo = c.post(url, data={"conta_id":"CONTA-B1","comando_id":"L5-GUARDA","versao":principal.versao,
                                "resposta_F2-2.9":GUARDA_INSTITUCIONAL})
    assert salvo.status_code == 200
    assert "Em preenchimento · 1 de 10 perguntas ativas" in salvo.text and salvo.text.count("Guarda em definição") >= 2
    assert "Respostas completas" not in salvo.text
    painel = c.get("/form2/painel-dpo?conta_id=CONTA-E1")
    assert "Temporalidade em definição: 1 Registro" in painel.text


def test_exclusividade_do_catalogo_completo():
    import pytest
    from app.respostas_form2 import definicao_revisao, aplicar_revisao
    for n in range(3,15):
        for q in definicao_revisao(n)["itens"]:
            if "múltipla" not in q["controle"].lower():
                continue
            exclusiva = next((a for a in q["alternativas"] if a["rotulo"].strip().casefold() == "a confirmar"), None)
            if exclusiva:
                outra = next(a for a in q["alternativas"] if a != exclusiva)
                with pytest.raises(ValueError):
                    aplicar_revisao({}, n, {"opcao:" + q["id"]: [outra["codigo"], exclusiva["codigo"]]},
                                    demonstrativo=True)


def test_p86_condicional_altera_total_sem_contar_historico_ou_comentario():
    from app.form2_rev212 import RASCUNHO
    from app.respostas_form2 import estados_regua_form2

    respostas = {"F2-1.2": "CONFIRMADA", "F2-1.2.1": "Descrição fictícia", "F2-1.3": "SIM"}
    conteudo = {"respostas_etapa1": respostas, RASCUNHO: {"1": {"comentario:F2-1.1": "Conferido"}}}
    assert estados_regua_form2(conteudo)["situacao"]["1"] == "✓ Todas as perguntas ativas respondidas"
    respostas["F2-1.3"] = "NAO"
    assert estados_regua_form2(conteudo)["situacao"]["1"] == "◐ Em preenchimento · 3 de 4 perguntas ativas"
    respostas["F2-1.3.1"] = "Solicitar complemento."
    assert estados_regua_form2(conteudo)["situacao"]["1"] == "✓ Todas as perguntas ativas respondidas"
    respostas.clear()
    respostas["F2-1.3.1"] = "Resposta antiga ao ramo agora bloqueado"
    assert estados_regua_form2(conteudo)["situacao"]["1"] == "— Ainda não preenchido"


def test_p86_conjuntos_e_campos_da_mesma_pergunta():
    from app.form2_rev212 import RASCUNHO
    from app.respostas_form2 import contagem_perguntas_ativas

    campos = {"opcao:F2-8.1": ["SIM"], "texto:F2-8.3#1": "Exemplo"}
    conteudo = {RASCUNHO: {"8": campos}}
    respondidas, total = contagem_perguntas_ativas(conteudo, [8])[8]
    campos["comentario:F2-8.1"] = "Comentário"
    assert contagem_perguntas_ativas(conteudo, [8])[8] == (respondidas, total)
    campos["texto:F2-8.3#2"] = "Segundo exemplo"
    novas, novo_total = contagem_perguntas_ativas(conteudo, [8])[8]
    assert novas == respondidas + 1 and novo_total > total


def test_p86_ramo_depende_da_apresentacao_em_analise():
    from app.respostas_form2 import contagem_perguntas_ativas

    sem_ramo = contagem_perguntas_ativas({}, [11])[11]
    com_ouvidoria = contagem_perguntas_ativas({}, [11], {"OUV"})[11]
    assert com_ouvidoria == (0, sem_ramo[1] + 4)
