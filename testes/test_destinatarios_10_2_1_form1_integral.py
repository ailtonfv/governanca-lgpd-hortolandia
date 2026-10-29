"""Ocorrências estruturadas e repetíveis de destinatários do item 10.2.1."""

from sqlalchemy import select

from app.modelos import Evento, EventoAuditoria, RascunhoForm1Integral
from app.pre_validacao_form1_integral import pre_validar_form1_integral
from app.rascunho_form1_integral import (
    adicionar_destinatario_10_2_1_form1_integral,
    atualizar_destinatario_10_2_1_form1_integral,
    remover_destinatario_10_2_1_form1_integral,
    salvar_bloco_10_form1_integral,
)
from testes.test_bloco7_form1_integral import _rascunho


def _preparar(sessao, prefixo, categorias):
    registro = _rascunho(sessao, prefixo)
    resultado = salvar_bloco_10_form1_integral(
        sessao, comando_id=f"{prefixo}-B10", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=1,
        respostas={"10.1": "Sim", "10.2": categorias, "10.9": "Titular"},
    )
    sessao.commit()
    assert resultado["permitido"]
    return registro


def _adicionar(sessao, registro, comando, versao, **dados):
    padrao = {"categoria": "Outra Secretaria", "modalidade": "identificado",
              "unidade_id": "UNID-SUL", "instrumento": "Ato fictício 01"}
    return adicionar_destinatario_10_2_1_form1_integral(
        sessao, comando_id=comando, conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=versao,
        dados={**padrao, **dados},
    )


def test_adiciona_um_e_varios_destinatarios_com_idempotencia(sessao):
    registro = _preparar(sessao, "F1102-REP", ["Outra Secretaria"])
    primeiro = _adicionar(sessao, registro, "F1102-REP-D1", 2)
    sessao.commit()
    repetido = _adicionar(sessao, registro, "F1102-REP-D1", 2)
    segundo = _adicionar(sessao, registro, "F1102-REP-D2", 3,
                         unidade_id="UNID-NORTE", instrumento="Ato fictício 02")
    sessao.commit()
    conteudo = sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo
    assert primeiro["permitido"], primeiro
    assert repetido["reexecutado"] and segundo["permitido"]
    assert len(conteudo["destinatarios_10_2_1"]) == 2
    assert sessao.scalars(select(Evento).where(
        Evento.comando_id.in_({"F1102-REP-D1", "F1102-REP-D2"})
    )).all()


def test_aceita_multiplas_categorias_e_modalidades_controladas(sessao):
    registro = _preparar(sessao, "F1102-MULT", ["Outra Secretaria", "Público em geral", "Outro órgão público"])
    assert _adicionar(sessao, registro, "F1102-MULT-D1", 2)["permitido"]
    sessao.commit()
    assert _adicionar(sessao, registro, "F1102-MULT-D2", 3,
        categoria="Público em geral", meio_publicacao="Portal fictício",
        instrumento="Norma fictícia")["permitido"]
    sessao.commit()
    assert _adicionar(sessao, registro, "F1102-MULT-D3", 4,
        categoria="Outro órgão público", modalidade="requisicao_eventual",
        unidade_id="", instrumento="", classe_orgao_requisitante="Órgão de controle",
        hipotese_requisicao="Requisição formal fictícia")["permitido"]
    sessao.commit()
    assert len(sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo["destinatarios_10_2_1"]) == 3


def test_rascunho_incompleto_e_pre_validacao_por_ocorrencia(sessao):
    registro = _preparar(sessao, "F1102-PRE", ["Empresa contratada", "Outro"])
    parcial = _adicionar(sessao, registro, "F1102-PRE-D1", 2,
        categoria="Empresa contratada", identificacao="Empresa Fictícia A",
        unidade_id="", instrumento="", cnpj="")
    sessao.commit()
    justificativa = _adicionar(sessao, registro, "F1102-PRE-D2", 3,
        categoria="Outro", modalidade="nao_determinavel", unidade_id="",
        instrumento="", justificativa="Destinatário ainda depende de instrumento futuro fictício")
    sessao.commit()
    conteudo = sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo
    pre = pre_validar_form1_integral(conteudo, nome_institucional="Agente Fictício")
    detalhes = " ".join(item["detalhe"] for item in pre["incompletos"])
    assert parcial["permitido"] and justificativa["permitido"]
    assert "cnpj" in detalhes and "instrumento" in detalhes
    assert any(item["tipo"] == "validacao_humana" for item in pre["regras_pendentes"])


def test_rejeita_categoria_nao_selecionada_unidade_forjada_e_nome_em_requisicao(sessao):
    registro = _preparar(sessao, "F1102-INV", ["Outra Secretaria"])
    fora = _adicionar(sessao, registro, "F1102-INV-D1", 2, categoria="Consórcio")
    unidade = _adicionar(sessao, registro, "F1102-INV-D2", 2, unidade_id="UNID-FORJADA")
    nominal = _adicionar(sessao, registro, "F1102-INV-D3", 2,
        modalidade="requisicao_eventual", identificacao="Destino inventado")
    sessao.commit()
    assert not fora["permitido"] and not unidade["permitido"] and not nominal["permitido"]


def test_atualiza_remove_preserva_historico_e_controla_concorrencia(sessao):
    registro = _preparar(sessao, "F1102-ALT", ["Outra Secretaria"])
    criado = _adicionar(sessao, registro, "F1102-ALT-D1", 2)
    sessao.commit()
    destinatario_id = sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo["destinatarios_10_2_1"][0]["id"]
    desatualizado = atualizar_destinatario_10_2_1_form1_integral(
        sessao, comando_id="F1102-ALT-X", conta_id="CONTA-A1", registro_id=registro["registro_id"],
        versao_lida=2, destinatario_id=destinatario_id,
        dados={"categoria": "Outra Secretaria", "modalidade": "identificado",
               "unidade_id": "UNID-SUL", "instrumento": "Ato fictício revisado"})
    atualizado = atualizar_destinatario_10_2_1_form1_integral(
        sessao, comando_id="F1102-ALT-U", conta_id="CONTA-A1", registro_id=registro["registro_id"],
        versao_lida=3, destinatario_id=destinatario_id,
        dados={"categoria": "Outra Secretaria", "modalidade": "identificado",
               "unidade_id": "UNID-SUL", "instrumento": "Ato fictício revisado"})
    sessao.commit()
    removido = remover_destinatario_10_2_1_form1_integral(
        sessao, comando_id="F1102-ALT-R", conta_id="CONTA-A1", registro_id=registro["registro_id"],
        versao_lida=4, destinatario_id=destinatario_id)
    sessao.commit()
    conteudo = sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo
    assert criado["permitido"] and not desatualizado["permitido"]
    assert atualizado["permitido"] and removido["permitido"]
    assert not conteudo["destinatarios_10_2_1"] and len(conteudo["destinatarios_10_2_1_inativos"]) == 2


def test_alterar_categoria_arquiva_ocorrencia_sem_apagar_historico(sessao):
    registro = _preparar(sessao, "F1102-RAMO", ["Outra Secretaria"])
    _adicionar(sessao, registro, "F1102-RAMO-D1", 2)
    sessao.commit()
    salvo = salvar_bloco_10_form1_integral(
        sessao, comando_id="F1102-RAMO-B", conta_id="CONTA-A1",
        registro_id=registro["registro_id"], versao_lida=3,
        respostas={"10.1": "Não", "10.9": "Não se aplica"})
    sessao.commit()
    conteudo = sessao.get(RascunhoForm1Integral, registro["registro_id"]).conteudo
    assert salvo["permitido"] and not conteudo["destinatarios_10_2_1"]
    assert conteudo["destinatarios_10_2_1_inativos"][0]["motivo_desativacao"]


def test_preserva_texto_legado_sem_converter(sessao):
    registro = _preparar(sessao, "F1102-LEG", ["Outra Secretaria"])
    rascunho = sessao.get(RascunhoForm1Integral, registro["registro_id"])
    rascunho.conteudo = {**rascunho.conteudo,
                         "respostas": {**rascunho.conteudo["respostas"],
                                       "10.2.1": "Destinatário institucional fictício legado"}}
    sessao.commit()
    pre = pre_validar_form1_integral(rascunho.conteudo, nome_institucional="Agente Fictício")
    assert not rascunho.conteudo["destinatarios_10_2_1"]
    assert any(item["tipo"] == "compatibilidade_legada" for item in pre["regras_pendentes"])


def test_somente_arp_pode_alterar_destinatarios(sessao):
    registro = _preparar(sessao, "F1102-AUT", ["Outra Secretaria"])
    negado = adicionar_destinatario_10_2_1_form1_integral(
        sessao, comando_id="F1102-AUT-D1", conta_id="CONTA-G1",
        registro_id=registro["registro_id"], versao_lida=2,
        dados={"categoria": "Outra Secretaria", "modalidade": "identificado",
               "unidade_id": "UNID-SUL", "instrumento": "Ato fictício 01"},
    )
    sessao.commit()
    assert not negado["permitido"] and "ARP atual" in negado["motivo"]
    assert sessao.scalars(select(EventoAuditoria).where(
        EventoAuditoria.comando_id == "F1102-AUT-D1"
    )).one()


def test_rollback_nao_persiste_ocorrencia_evento_ou_nova_versao(sessao):
    registro = _preparar(sessao, "F1102-RBK", ["Outra Secretaria"])
    resultado = _adicionar(sessao, registro, "F1102-RBK-D1", 2)
    assert resultado["permitido"]
    sessao.rollback()
    rascunho = sessao.get(RascunhoForm1Integral, registro["registro_id"])
    assert rascunho.versao_rascunho == 2
    assert not rascunho.conteudo["destinatarios_10_2_1"]
