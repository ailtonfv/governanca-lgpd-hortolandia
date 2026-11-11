"""Somente registros fictícios; nenhuma redação do catálogo privado."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import select, func
from sqlalchemy.orm import Session
import pytest
from fastapi.testclient import TestClient
from app.modelos import ParticipacaoForm2, Designacao, Evento, Comando, ComplementoForm2
from app.fila_form2 import executar, agora
from app.consolidacao_form2 import consultar, registrar, CHAVE, montar_resumo
from testes.test_filas_form2_rev22 import origem


def preparar(sessao):
    r = origem(sessao)
    p = sessao.scalar(select(ParticipacaoForm2).where(ParticipacaoForm2.registro_id == r["registro_id"]))
    sessao.add(Designacao(pessoa_id="PESSOA-B", unidade_id="UNID-NORTE", papel="aal_form2", ativa=True))
    sessao.flush()
    executar(sessao, conta_id="CONTA-B1", comando_id="ASSUMIR-CONS", participacao_id=p.id,
             acao="assumir", versao=p.versao)
    sessao.commit()
    return p


def argumentos(sessao, p, comando="CONSOLIDAR"):
    tela = consultar(sessao, conta_id="CONTA-B1", participacao_id=p.id)
    return dict(conta_id="CONTA-B1", participacao_id=p.id, comando_id=comando,
                versao=p.versao, hash_fontes=tela["hash_fontes"], sintese="Conferência fictícia.")


def test_registro_idempotente_historico_sem_concluir(sessao):
    p = preparar(sessao)
    args = argumentos(sessao, p)
    assert registrar(sessao, **args)["numero"] == 1
    sessao.commit()
    assert registrar(sessao, **args)["reexecutado"]
    assert p.estado == "em_atendimento"
    assert not consultar(sessao, conta_id="CONTA-B1", participacao_id=p.id)["desatualizada"]
    primeira = deepcopy(p.conteudo[CHAVE])
    registrar(sessao, **argumentos(sessao, p, "CONSOLIDAR2"))
    sessao.commit()
    historico = consultar(sessao, conta_id="CONTA-B1", participacao_id=p.id)["historico"]
    assert len(historico) == 2
    assert historico[-1] == primeira
    assert p.conteudo[CHAVE]["numero"] == 2
    assert not p.conteudo[CHAVE]["resumo"]["conclusao_institucional_habilitada"]
    with pytest.raises(ValueError, match="D11"):
        executar(sessao, conta_id="CONTA-B1", comando_id="NAO-CONCLUI",
                 participacao_id=p.id, acao="concluir", versao=p.versao)
    sessao.rollback()


def test_consulta_posterior_invalida_retrato_e_tela(sessao):
    p = preparar(sessao)
    registrar(sessao, **argumentos(sessao, p))
    resultado = executar(sessao, conta_id="CONTA-B1", comando_id="QUESTAO-CONS",
        participacao_id=p.id, acao="consultar", versao=p.versao,
        tipo="dpo", unidade_id="UNID-GOV", texto="Questão fictícia para teste.")
    sessao.commit()
    assert consultar(sessao, conta_id="CONTA-B1", participacao_id=p.id)["desatualizada"]
    args = argumentos(sessao, p, "TELA-ANTIGA")
    filho = sessao.get(ParticipacaoForm2, resultado["participacao_id"])
    executar(sessao, conta_id="CONTA-E1", comando_id="ASSUME-DPO", participacao_id=filho.id,
        acao="assumir", versao=filho.versao)
    executar(sessao, conta_id="CONTA-E1", comando_id="RESPONDE-DPO", participacao_id=filho.id,
        acao="concluir", versao=filho.versao, texto="Manifestação fictícia concluída.")
    sessao.commit()
    with pytest.raises(ValueError, match="manifestações mudaram"):
        registrar(sessao, **args)
    sessao.rollback()
    tela = consultar(sessao, conta_id="CONTA-B1", participacao_id=p.id)
    assert len(tela["resumo"]["consultas_concluidas"]) == 1
    assert not tela["resumo"]["consultas_abertas"]


@pytest.mark.parametrize("conta", ["CONTA-G1", "CONTA-E1", "CONTA-A1"])
def test_consolidacao_restrita_ao_responsavel(sessao, conta):
    p = preparar(sessao)
    with pytest.raises(PermissionError):
        consultar(sessao, conta_id=conta, participacao_id=p.id)
    args = argumentos(sessao, p)
    args["conta_id"] = conta
    with pytest.raises(PermissionError):
        registrar(sessao, **args)
    assert CHAVE not in (p.conteudo or {})


def test_rollback_integral(sessao, monkeypatch):
    import app.consolidacao_form2 as dominio
    p = preparar(sessao)
    versao = p.versao
    real = dominio.evento
    def falhar(*args, **kwargs):
        real(*args, **kwargs)
        raise RuntimeError("Falha fictícia depois do evento")
    monkeypatch.setattr(dominio, "evento", falhar)
    with pytest.raises(RuntimeError):
        registrar(sessao, **argumentos(sessao, p))
    sessao.rollback()
    sessao.refresh(p)
    assert p.versao == versao
    assert CHAVE not in (p.conteudo or {})
    assert sessao.get(Comando, "CONSOLIDAR") is None
    assert sessao.scalar(select(func.count()).select_from(Evento).where(
        Evento.tipo_evento == "form2_consolidacao_registrada")) == 0


def test_versao_e_sintese_invalidas(sessao):
    p = preparar(sessao)
    args = argumentos(sessao, p)
    args["versao"] -= 1
    with pytest.raises(ValueError, match="participação mudou"):
        registrar(sessao, **args)
    sessao.rollback()
    args = argumentos(sessao, p)
    args["sintese"] = " "
    with pytest.raises(ValueError, match="síntese"):
        registrar(sessao, **args)
    sessao.rollback()


def test_concorrencia_registra_uma_versao(sessao):
    from app.banco import motor
    p = preparar(sessao)
    args = argumentos(sessao, p)
    sessao.commit()
    def gravar(numero):
        with Session(motor) as s:
            try:
                registrar(s, **{**args, "comando_id": f"CONCORRENTE-{numero}"})
                s.commit()
                return True
            except ValueError:
                s.rollback()
                return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(gravar, [1, 2])) == [False, True]
    sessao.refresh(p)
    assert p.conteudo[CHAVE]["numero"] == 1


def test_pendencia_resolvida_e_origem_preservada(sessao):
    p = preparar(sessao)
    c = ComplementoForm2(id="COMPLEMENTO-FICTICIO", participacao_id=p.id,
        snapshot_origem_id=p.snapshot_id, solicitacao="Complemento fictício.",
        estado="aberta", criada_em=agora())
    sessao.add(c)
    sessao.commit()
    registrar(sessao, **argumentos(sessao, p))
    sessao.commit()
    c.estado = "resolvida"
    sessao.commit()
    tela = consultar(sessao, conta_id="CONTA-B1", participacao_id=p.id)
    assert tela["desatualizada"]
    assert tela["resumo"]["complementos"][0]["estado"] == "resolvida"
    assert tela["ultima"]["fontes"]["complementos"][0]["estado"] == "aberta"


def test_http_preserva_texto_no_conflito_e_escapa_html(sessao):
    from app.main import app
    p = preparar(sessao)
    args = argumentos(sessao, p)
    client = TestClient(app)
    url = f"/form2/participacoes/{p.id}/consolidacao"
    response = client.get(url + "?conta_id=CONTA-B1")
    assert response.status_code == 200
    assert "Registrar conferência demonstrativa" in response.text
    args.pop("participacao_id")
    args["hash_fontes"] = "tela-desatualizada"
    args["sintese"] = '<script>alert("fictício")</script>'
    response = client.post(url, data=args)
    assert response.status_code == 409
    assert '&lt;script&gt;' in response.text
    assert '<script>alert' not in response.text
    assert client.get(url + "?conta_id=CONTA-G1").status_code == 403
    dados = argumentos(sessao, p, "HTTP-SUCESSO")
    dados.pop("participacao_id")
    response = client.post(url, data=dados)
    assert response.status_code == 200
    assert "Conferência 1" in response.text
    assert "Conferência fictícia." in response.text


def test_sinais_nao_confundem_comentario_ou_inativo_com_resposta():
    from app.form2_rev212 import RASCUNHO
    fontes = {"conteudo": {RASCUNHO: {"6": {"comentario:F2-6.1": "A_CONFIRMAR",
        "opcao:F2-6.2": ["A_CONFIRMAR"]}},
        "respostas_inativas_etapa1": {"F2-1.2": {"valor": "A_CONFIRMAR"}}},
        "consultas": [], "complementos": []}
    resumo = montar_resumo(fontes)
    assert resumo["itens_a_confirmar"] == ["F2-6.2"]
    assert resumo["blocos_com_respostas"] == ["6"]
    assert resumo["conclusao_institucional_habilitada"] is False


def test_condicao_atual_e_conjuntos_independentes():
    from app.form2_rev212 import RASCUNHO
    fontes = {"conteudo": {RASCUNHO: {"14": {
        "texto:F2-14.2#2": "Pendência fictícia B", "texto:F2-14.3#2": "Área B",
        "opcao:F2-14.3.1#2": ["DESTINO_B"], "principal:F2-14.3.1#2": "DESTINO_B",
        "texto:F2-14.2#1": "Pendência fictícia A", "opcao:F2-14.5": ["SIM"],
        "texto:F2-14.5.1": "Motivo fictício", "opcao:F2-14.4": ["NAO"],
        "opcao:F2-14.4.2": ["A_CONFIRMAR"]}}}, "consultas": [], "complementos": [],
        "regras": {"F2-14.4.2": [{"origem":"F2-14.4", "operador":"IGUAL",
            "codigo_valor":"SIM", "combinar":"E"}]},
        "alternativas_bloco14": {"F2-14.3.1": {"DESTINO_B":"Destino fictício B"}}}
    resumo = montar_resumo(fontes)
    assert not resumo["itens_a_confirmar"]
    assert [p["conjunto"] for p in resumo["pendencias_declaradas"]] == ["1", "2"]
    assert resumo["pendencias_declaradas"][1]["principal"] == "Destino fictício B"
    assert resumo["encaminhamentos"][0]["justificativa"] == "Motivo fictício"
    assert "opcao:F2-14.4.2" in fontes["conteudo"][RASCUNHO]["14"]
