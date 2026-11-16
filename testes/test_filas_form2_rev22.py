from sqlalchemy import select, func
from app.modelos import ParticipacaoForm2, AvisoDpo, Designacao
from app.fila_form2 import importar_confirmada, executar
from testes.test_conferencia_interna_form1_integral_8ac import _preparar, _solicitar
from testes.test_confirmacao_conferencia_form1_integral_8ag import _confirmar
import pytest

def origem(sessao):
    r = _preparar(sessao, "FILA")
    _solicitar(sessao, r, comando="FILA-S")
    _confirmar(sessao, r, comando="FILA-C")
    return r

def test_ingresso_idempotente_e_assuncao(sessao):
    r = origem(sessao)
    args=dict(conta_id="CONTA-A1", registro_id=r["registro_id"])
    a = importar_confirmada(sessao, comando_id="ENTRA", **args)
    b = importar_confirmada(sessao, comando_id="ENTRA2", **args)
    assert a["participacao_id"] == b["participacao_id"]
    sessao.flush()
    assert sessao.scalar(select(func.count()).select_from(AvisoDpo)) == 1
    with pytest.raises(PermissionError):
        executar(sessao, conta_id="CONTA-G1", comando_id="NEGA",
            participacao_id=a["participacao_id"], acao="assumir", versao=1)
    sessao.add(Designacao(pessoa_id="PESSOA-B", unidade_id="UNID-NORTE",
                        papel="aal_form2", ativa=True))
    sessao.flush()
    args=dict(conta_id="CONTA-B1", comando_id="ASSUME",
        participacao_id=a["participacao_id"], acao="assumir", versao=1)
    assert executar(sessao, **args)["permitido"]
    assert executar(sessao, **args)["reexecutado"]
    consulta=executar(sessao, conta_id="CONTA-B1", comando_id="CONSULTA",
        participacao_id=a["participacao_id"], acao="consultar", versao=2,
        texto="Questão fictícia", tipo="dpo", unidade_id="UNID-GOV")
    assert consulta["permitido"]
    sessao.flush()
    assert sessao.scalar(select(func.count()).select_from(AvisoDpo)) == 2
    dpo=consulta["participacao_id"]
    executar(sessao, conta_id="CONTA-E1", comando_id="DPO1",
        participacao_id=dpo, acao="assumir", versao=1)
    executar(sessao, conta_id="CONTA-E1", comando_id="DPO2",
        participacao_id=dpo, acao="concluir", versao=2, texto="Manifestação fictícia")
    assert sessao.get(ParticipacaoForm2,dpo).estado == "concluida"

def test_interface_e_blocos(sessao):
    from fastapi.testclient import TestClient
    from app.main import app
    r=origem(sessao)
    p=sessao.scalar(select(ParticipacaoForm2).where(ParticipacaoForm2.registro_id == r["registro_id"]))
    assert p is not None
    sessao.add(Designacao(pessoa_id="PESSOA-B", unidade_id="UNID-NORTE", papel="aal_form2", ativa=True))
    sessao.commit()
    executar(sessao, conta_id="CONTA-B1", comando_id="UI-A", participacao_id=p.id, acao="assumir", versao=1)
    sessao.commit()
    client=TestClient(app)
    assert client.get("/form2/filas?conta_id=CONTA-E1").status_code == 200
    for numero in range(1,15):
        response=client.get(f"/form2/participacoes/{p.id}/blocos/{numero}?conta_id=CONTA-B1")
        assert response.status_code == 200, response.text
    assert client.get(f"/form2/participacoes/{p.id}/blocos/1?conta_id=CONTA-G1").status_code == 403

def test_assuncao_explicada_confirmada_e_identificada_na_fila(sessao):
    from fastapi.testclient import TestClient
    from app.apresentacoes_form1 import rotulo_apresentacao
    from app.fila_form2 import unidades
    from app.main import app
    from app.modelos import Pessoa, VersaoForm1Integral

    registro = origem(sessao)
    p = sessao.scalar(select(ParticipacaoForm2).where(
        ParticipacaoForm2.registro_id == registro["registro_id"]))
    for papel in ("aal_form2", "gestor_fila"):
        if p.unidade_id not in unidades(sessao, "PESSOA-B", papel):
            sessao.add(Designacao(pessoa_id="PESSOA-B", unidade_id=p.unidade_id, papel=papel, ativa=True))
    sessao.commit()
    cliente = TestClient(app)
    url = f"/form2/participacoes/{p.id}"
    fila = "/form2/filas?conta_id=CONTA-B1"
    antes = cliente.get(fila)
    assert "Atribuir responsável" in antes.text and "Novas versões do FORM 1 dependerão" in antes.text
    detalhe = cliente.get(url, params={"conta_id": "CONTA-B1"})
    assert detalhe.status_code == 200
    referencia = rotulo_apresentacao(sessao.get(VersaoForm1Integral, p.snapshot_id))
    assert referencia in detalhe.text and "Assumir a participação?" in detalhe.text
    for conta in ("CONTA-G1", "CONTA-A1"):
        impedido = cliente.get(url, params={"conta_id": conta})
        assert impedido.status_code == 403
        assert "Você apresentou ou confirmou" in impedido.text
        assert "Assumir participação" not in impedido.text
    assert sessao.get(ParticipacaoForm2, p.id).assumida_em is None
    resposta = cliente.post(url, data={"conta_id": "CONTA-B1", "comando_id": "VISTORIA-ASSUME",
        "acao": "assumir", "versao": p.versao}, follow_redirects=True)
    assert resposta.status_code == 200
    assert resposta.url.path == url
    assert "Você assumiu a participação principal" in resposta.text and referencia in resposta.text
    assert "Começar pelo bloco 1" in resposta.text
    codigo = resposta.context["registro"].codigo_lgpd
    bloco = cliente.get(url + "/blocos/1?conta_id=CONTA-B1")
    assert f"{codigo} · FORM 2 · Bloco 1 — Identificação" in bloco.text
    for pagina in (resposta, bloco):
        assert f"Versão do FORM 1 em análise:</strong> {referencia}" in pagina.text
    assert "Analista de gestão (fictício)" in bloco.text and "Cargo não informado" not in bloco.text
    assert "Aguarda homologação jurídica (D11)" in bloco.text
    salvo = cliente.post(url + "/blocos/1", data={"conta_id":"CONTA-B1", "comando_id":"CONTINUAR",
        "versao":2, "resposta_F2-1.3":"SIM"})
    assert salvo.status_code == 200
    assert "Continuar no bloco 2" in cliente.get(url + "?conta_id=CONTA-B1").text
    nome = sessao.get(Pessoa, "PESSOA-B").nome
    depois = cliente.get(fila)
    assert f"Responsável: {nome}" in depois.text
    assert "Não há outro AAL habilitado nesta fila" in depois.text and "conta como primeira assunção" not in depois.text


def test_envio_configuravel_e_reprocessamento(sessao):
    from app.avisos_dpo import entregar_pendentes
    r=origem(sessao)
    p=sessao.scalar(select(ParticipacaoForm2).where(ParticipacaoForm2.registro_id == r["registro_id"]))
    sessao.commit()
    caixa=[]
    assert entregar_pendentes(sessao, caixa.append, ciencia_individual=False, base_url="http://localhost:8001") == 0
    assert entregar_pendentes(sessao, caixa.append, base_url="http://localhost:8001") == 1
    assert entregar_pendentes(sessao, caixa.append, base_url="http://localhost:8001") == 0
    assert len(caixa) == 1
    assert p.questao not in ["Questão sigilosa"]


def test_falha_de_envio_exige_conferencia(sessao):
    from app.avisos_dpo import entregar_pendentes
    origem(sessao)
    sessao.commit()
    def falhar(mensagem):
        raise TimeoutError()
    with pytest.raises(TimeoutError):
        entregar_pendentes(sessao, falhar, base_url="http://localhost:8001")
    assert sessao.scalar(select(AvisoDpo)).estado == "conferir_entrega"


def test_assuncao_concorrente(sessao):
    from concurrent.futures import ThreadPoolExecutor
    from sqlalchemy.orm import Session
    from app.banco import motor
    r=origem(sessao)
    p=sessao.scalar(select(ParticipacaoForm2).where(ParticipacaoForm2.registro_id == r["registro_id"]))
    for pessoa in ("PESSOA-B", "PESSOA-F"):
        sessao.add(Designacao(pessoa_id=pessoa, unidade_id="UNID-NORTE", papel="aal_form2", ativa=True))
    sessao.commit()
    def assumir(conta):
        with Session(motor) as s:
            try:
                resultado=executar(s, conta_id=conta, comando_id="CONC-"+conta,
                    participacao_id=p.id, acao="assumir", versao=1)
                s.commit()
                return resultado["permitido"]
            except ValueError:
                s.rollback()
                return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(assumir, ("CONTA-B1","CONTA-F1"))) == [False,True]

def test_salvamento_cria_pendencia_e_rollback(sessao):
    from app.modelos import ComplementoForm2, Comando
    from app.fila_form2 import salvar_bloco
    r=origem(sessao)
    p=sessao.scalar(select(ParticipacaoForm2).where(ParticipacaoForm2.registro_id == r["registro_id"]))
    sessao.add(Designacao(pessoa_id="PESSOA-B", unidade_id="UNID-NORTE", papel="aal_form2", ativa=True))
    sessao.commit()
    executar(sessao, conta_id="CONTA-B1", comando_id="P-A", participacao_id=p.id, acao="assumir", versao=1)
    sessao.commit()
    salvar_bloco(sessao, conta_id="CONTA-B1", comando_id="P-S", participacao_id=p.id,
        versao=2, bloco=1, campos={"F2-1.2":"DIVERGENTE","F2-1.3":"SIM","F2-1.3.1":"Complemento fictício"})
    sessao.flush()
    assert sessao.scalar(select(ComplementoForm2)).solicitacao == "Complemento fictício"
    sessao.rollback()
    assert sessao.scalar(select(ComplementoForm2)) is None
    assert sessao.get(Comando,"P-S") is None
    p=sessao.get(ParticipacaoForm2,p.id)
    assert p.versao == 2


def test_confirmacao_salvar_bloco_sem_consolidacao(sessao):
    from fastapi.testclient import TestClient
    from app.main import app
    r = origem(sessao)
    p = sessao.scalar(select(ParticipacaoForm2).where(ParticipacaoForm2.registro_id == r["registro_id"]))
    sessao.add(Designacao(pessoa_id="PESSOA-B", unidade_id="UNID-NORTE", papel="aal_form2", ativa=True))
    sessao.commit()
    executar(sessao, conta_id="CONTA-B1", comando_id="MSG-A", participacao_id=p.id, acao="assumir", versao=1)
    sessao.commit()
    client = TestClient(app)
    url = f"/form2/participacoes/{p.id}/blocos/1"
    assert 'id="confirmacao-salvamento"' not in client.get(url+"?conta_id=CONTA-B1&salvo=inexistente").text
    dados = {"conta_id":"CONTA-B1", "comando_id":"MSG-S", "versao":"2",
        "resposta_F2-1.2":"DIVERGENTE", "resposta_F2-1.3":"SIM",
        "resposta_F2-1.3.1":"Complemento fictício"}
    response = client.post(url, data=dados)
    assert response.status_code == 200
    assert 'role="status">Bloco salvo. Complementação solicitada à origem.' in response.text
    assert client.post(url, data=dados).status_code == 200
    outro = client.get(url.replace('/blocos/1', '/blocos/2')+'?conta_id=CONTA-B1&salvo=MSG-S')
    assert 'id="confirmacao-salvamento"' not in outro.text
    response = client.post(url.replace('/blocos/1', '/blocos/2'), data={
        "conta_id":"CONTA-B1", "comando_id":"MSG-S2", "versao":"3"})
    assert response.status_code == 200
    assert 'role="status">Bloco salvo.</p>' in response.text
    assert 'Complementação solicitada à origem.' not in response.text
    assert 'id="confirmacao-salvamento"' not in client.get(url+'?conta_id=CONTA-B1&salvo=MSG-S').text


def test_lista_e_confirmacao_da_atribuicao(sessao):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.modelos import Registro
    registro = origem(sessao)
    p = sessao.scalar(select(ParticipacaoForm2).where(
        ParticipacaoForm2.registro_id == registro["registro_id"]))
    for pessoa in ("PESSOA-A", "PESSOA-B", "PESSOA-G", "PESSOA-F"):
        sessao.add(Designacao(pessoa_id=pessoa, unidade_id=p.unidade_id, papel="aal_form2"))
    sessao.add(Designacao(pessoa_id="PESSOA-A", unidade_id=p.unidade_id, papel="gestor_fila"))
    sessao.commit()
    cliente = TestClient(app)
    fila = cliente.get("/form2/filas?conta_id=CONTA-A1")
    opcoes = fila.text.split('name="responsavel_id"', 1)[1].split('</select>', 1)[0]
    assert 'value="">Escolha…' in opcoes
    assert {a.id for a in fila.context["agentes"][p.id]} == {"PESSOA-B", "PESSOA-F"}
    url = f"/form2/participacoes/{p.id}/reatribuir"
    dados = {"conta_id": "CONTA-A1", "comando_id": "ESCOLHA", "versao": p.versao, "motivo": "Distribuição fictícia"}
    for impedido in ("", "PESSOA-A", "PESSOA-G"):
        resposta = cliente.post(url, data={**dados, "responsavel_id": impedido})
        assert resposta.status_code == 409
        assert "Atribuição indisponível" in resposta.text
    codigo = sessao.get(Registro, p.registro_id).codigo_lgpd
    primeira = cliente.post(url, data={**dados, "responsavel_id": "PESSOA-B"})
    assert "Gestão da fila" in primeira.text and 'class="mensagem mensagem-sucesso"' in primeira.text
    cartao_beta = cliente.get("/form2/filas?conta_id=CONTA-B1")
    assert "Atribuído por Servidor Alfa" in cartao_beta.text and "(APA) em " in cartao_beta.text
    assert "Entrou na fila em" in cartao_beta.text
    mensagem = primeira.context["mensagem_atribuicao"]
    assert "Servidor Beta" in mensagem and codigo in mensagem and "Apresentação" in mensagem
    from app.modelos import Evento
    def contar_atos():
        return sessao.scalar(select(func.count()).select_from(Evento).where(Evento.cadeia_id == p.id))
    antes = contar_atos()
    mesmo = cliente.post(url, data={**dados, "versao": dados["versao"] + 1,
        "comando_id": "MESMA-PESSOA", "responsavel_id": "PESSOA-B"})
    assert mesmo.status_code == 409 and "já é responsável" in mesmo.text
    assert contar_atos() == antes
    assert {a.id for a in primeira.context["agentes"][p.id]} == {"PESSOA-F"}
    segunda = cliente.post(url, data={**dados, "versao": dados["versao"] + 1,
        "comando_id": "SUBSTITUIR", "responsavel_id": "PESSOA-F"})
    assert "Servidor Delta" in segunda.context["mensagem_atribuicao"]
    assert "no lugar de Servidor Beta" in segunda.context["mensagem_atribuicao"]


def test_condicionais_inativas_e_pedidos_de_origem(sessao):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.modelos import ComplementoForm2

    registro = origem(sessao)
    p = sessao.scalar(select(ParticipacaoForm2).where(ParticipacaoForm2.registro_id == registro["registro_id"]))
    sessao.add(Designacao(pessoa_id="PESSOA-B", unidade_id=p.unidade_id, papel="aal_form2"))
    sessao.flush()
    executar(sessao, conta_id="CONTA-B1", comando_id="COND-ASSUME", participacao_id=p.id, acao="assumir", versao=1)
    sessao.commit()
    cliente = TestClient(app)
    url = f"/form2/participacoes/{p.id}/blocos/"
    def enviar(bloco, chave, campos):
        return cliente.post(url + str(bloco), data={"conta_id": "CONTA-B1", "versao": 2,
            "comando_id": chave, **campos}, follow_redirects=False)
    resposta = enviar(1, "INATIVA", {"resposta_F2-1.3": "SIM", "resposta_F2-1.3.1": "Pedido fictício"})
    assert resposta.status_code >= 400
    assert sessao.scalar(select(ComplementoForm2)) is None
    bloco = cliente.get(url + "2?conta_id=CONTA-B1")
    dependentes = [q for q in bloco.context["bloco"]["itens"] if q["gatilhos"]]
    assert {q["id"] for q in dependentes} == {f"F2-2.{i}" for i in ("1.1","4.1","6.1","7.1","9.1","9.3")}
    for q in dependentes:
        prefixo = "resposta_" if q["edicao"] == "habilitada" else ("opcao:" if q["alternativas"] else "texto:")
        valor = q["alternativas"][0]["codigo"] if q["alternativas"] else "Texto fictício"
        resposta = enviar(2, q["id"], {prefixo + q["id"]: valor})
        assert resposta.status_code >= 400, q["id"]
    resposta = enviar(1, "PEDIDO", {"resposta_F2-1.3": "NAO", "resposta_F2-1.3.1": "Pedido fictício"})
    assert resposta.status_code == 303
    assert sessao.scalar(select(ComplementoForm2)).solicitacao == "Pedido fictício"


def test_bloco_dois_exibe_respostas_da_apresentacao(sessao):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.modelos import RascunhoForm1Integral

    r = _preparar(sessao, "ORIGEM-FATOS")
    rascunho = sessao.get(RascunhoForm1Integral, r["registro_id"])
    from app.rascunho_form1_integral import salvar_bloco_2_form1_integral, salvar_bloco_12_form1_integral
    dados = {"conta_id": "CONTA-G1", "registro_id": r["registro_id"]}
    assert salvar_bloco_2_form1_integral(sessao, **dados, comando_id="FINALIDADE", versao_lida=1,
        respostas={"2.11": "Organizar oficinas fictícias"})["permitido"]
    assert salvar_bloco_12_form1_integral(sessao, **dados, comando_id="GUARDA", versao_lida=2,
        respostas={"12.1": "Sim", "12.1.1": "9", "12.1.2": "Dias", "12.1.3": ["Outro", "Regra do sistema ou fornecedor"]}, complementos_outro={"12.1.3": "Fonte fictícia de teste"})["permitido"]
    sessao.commit()
    assert _solicitar(sessao, r, comando="FATOS-S", versao=3)["permitido"]
    assert _confirmar(sessao, r, comando="FATOS-C")["permitido"]
    p = sessao.scalar(select(ParticipacaoForm2).where(ParticipacaoForm2.registro_id == r["registro_id"]))
    sessao.add(Designacao(pessoa_id="PESSOA-B", unidade_id=p.unidade_id, papel="aal_form2"))
    sessao.flush()
    executar(sessao, conta_id="CONTA-B1", comando_id="FATOS-A", participacao_id=p.id, acao="assumir", versao=1)
    rascunho.conteudo = {**rascunho.conteudo, "respostas": {"2.11": "Alteração posterior"}}
    sessao.commit()
    pagina = TestClient(app).get(f"/form2/participacoes/{p.id}/blocos/2?conta_id=CONTA-B1")
    for pergunta, fato in (("F2-2.1", "F1-2.11 — Organizar oficinas fictícias"),
                           ("F2-2.9", "F1-12.1 — Sim")):
        quadro = pagina.text.split(f'id="{pergunta}"', 1)[1].split("</aside>", 1)[0]
        assert f"No FORM 1 · {pagina.context['rotulo_origem']}" in quadro and fato in quadro
    assert "F1-12.1.1) — 9" in quadro and "F1-12.1.2) — Dias" in quadro
    assert "Regra do sistema ou fornecedor" in quadro and "Fonte fictícia de teste" in quadro
    assert "Alteração posterior" not in pagina.text


def test_lista_de_origens_confirmadas_do_apa(sessao, monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app

    # Simula uma confirmação histórica anterior ao ingresso automático.
    with monkeypatch.context() as legado:
        legado.setattr("app.fila_form2.ingresso", lambda *args: None)
        registro = origem(sessao)
    cliente = TestClient(app)
    fila = "/form2/filas"
    html = cliente.get(fila, params={"conta_id": "CONTA-A1"}).text
    assert registro["codigo_lgpd"] in html and "Apresentação 1 (rascunho 1)" in html
    from app.modelos import HistoricoConferenciaForm1Integral
    snapshot = sessao.scalar(select(HistoricoConferenciaForm1Integral.snapshot_id).where(
        HistoricoConferenciaForm1Integral.registro_id == registro["registro_id"]))
    dados = {"snapshot_id": snapshot, "comando_id": "LISTA-APA"}
    negada = cliente.post(fila + "/encaminhar", data={**dados, "conta_id": "CONTA-G1"})
    assert negada.status_code == 400
    enviada = cliente.post(fila + "/encaminhar", data={**dados, "conta_id": "CONTA-A1"})
    assert enviada.status_code == 200
    assert "Nenhuma apresentação confirmada aguarda ingresso" in enviada.text
    detalhe = cliente.get("/registros/" + registro["registro_id"], params={"conta_id": "CONTA-A1"})
    assert "Fila do FORM 2:" in detalhe.text and "Aguardando responsável" in detalhe.text
    painel = cliente.get("/painel", params={"conta_id": "CONTA-A1"})
    assert "Ingressou na fila do FORM 2 em " in painel.text
