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
