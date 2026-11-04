"""Incremento 8K — painel consultivo de progresso e pendências."""

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.consultas_interface import carregar_registro
from app.main import app
from app.modelos import Evento
from app.rascunho_form1_integral import salvar_bloco_5_form1_integral
from testes.test_bloco5_form1_integral import _rascunho_pronto


cliente = TestClient(app)


def test_painel_distingue_salvamento_pendencias_e_dependencias(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F1-8K-ESTADO")
    salvar_bloco_5_form1_integral(
        sessao,
        comando_id="F1-8K-ESTADO-B5",
        conta_id="CONTA-A1",
        registro_id=registro["registro_id"],
        versao_lida=1,
        respostas={"5.1": ["Nome"]},
        complemento_outro="",
    )
    sessao.commit()
    _, projecao = carregar_registro(sessao, "CONTA-A1", registro["registro_id"])
    progresso = projecao["form1_integral"]["painel_progresso"]

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )

    # Assert
    assert progresso["blocos_salvos"] == [5]
    assert progresso["quantidade_salvos"] == 1
    assert progresso["blocos_com_respostas_salvas"] == [1, 5]
    assert progresso["quantidade_com_respostas_salvas"] == 2
    assert progresso["quantidade_incompletos"] > 0
    assert progresso["quantidade_governanca"] > 0
    assert 'data-blocos-salvos="5"' in pagina.text
    assert "<strong>2 de 14</strong><span>blocos possuem respostas salvas" in pagina.text
    assert "dependência(s) institucional(is) ou regra(s) de governança" in pagina.text
    assert "Pendências a resolver" in pagina.text
    assert 'class="contador-pendencias-form1"' in pagina.text
    assert "pendências segundo a política atualmente configurada" in pagina.text
    assert "Há informações obrigatórias a resolver." in pagina.text


def test_painel_oferece_proxima_pendencia_e_distribuicao_por_bloco(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F1-8K-PENDENCIA")
    _, projecao = carregar_registro(sessao, "CONTA-A1", registro["registro_id"])
    progresso = projecao["form1_integral"]["painel_progresso"]
    proxima = progresso["proxima_pendencia"]

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )

    # Assert
    assert proxima is not None
    assert f'data-pendencia-campo="{proxima["campo_id"]}"' in pagina.text
    assert f'data-pendencia-bloco="{proxima["bloco"]}"' in pagina.text
    assert "Próxima pergunta pendente" in pagina.text
    for grupo in progresso["pendencias_por_bloco"]:
        assert f"<strong>Bloco {grupo['bloco']}</strong>" in pagina.text


def test_jornada_usa_sessao_do_navegador_sem_gravar_evento(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F1-8K-VISITA")
    quantidade_antes = sessao.scalar(select(func.count()).select_from(Evento))

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )
    sessao.expire_all()
    quantidade_depois = sessao.scalar(select(func.count()).select_from(Evento))

    # Assert
    assert quantidade_depois == quantidade_antes
    assert pagina.text.count('<button type="button" data-painel-bloco="') == 14
    assert 'class="indicadores-compactos-form1"' in pagina.text
    assert "gauge-form1" not in pagina.text
    assert "blocos visitados nesta sessão" in pagina.text
    assert "form1-integral-visitados-" in pagina.text
    assert "Ele não mede conformidade com a LGPD." in pagina.text
    assert "porcentagem de conformidade" not in pagina.text.lower()


def test_mapa_distingue_visitado_salvo_e_sem_pendencia_sem_declarar_conclusao(sessao):
    # Arrange
    registro = _rascunho_pronto(sessao, "F1-8K-ROTULOS")

    # Act
    pagina = cliente.get(
        f"/registros/{registro['registro_id']}", params={"conta_id": "CONTA-A1"}
    )

    # Assert
    assert "Visitado nesta sessão" in pagina.text
    assert "Salvo" in pagina.text or 'data-blocos-salvos=""' in pagina.text
    assert "Sem pendências obrigatórias ativas" in pagina.text
    assert "Ainda não preenchido" in pagina.text
    trecho = pagina.text[
        pagina.text.index('class="painel-progresso-form1 '):
        pagina.text.index('class="legenda-form1-integral ')
    ]
    assert "concluído" not in trecho.lower()
    assert "adequado" not in trecho.lower()
