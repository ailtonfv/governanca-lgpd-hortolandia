"""Leitura histórica pura. Autorização deve preceder sua chamada pelo serviço."""
from copy import deepcopy
import json

from app.eventos import lacre, texto_canonico, CAMPOS_LACRADOS_DOMINIO
from app.extensao_medidas_form1 import catalogo_efetivo, versao_estrutura
from app.modelos import Evento, VersaoForm1Integral
from app.form1_integral import REVISAO_FONTE_FORM1_INTEGRAL


def canonico(conteudo):
    return json.dumps(conteudo, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def ler_origem(sessao, registro_id, snapshot_id):
    snapshot = sessao.get(VersaoForm1Integral, snapshot_id)
    if snapshot is None or snapshot.registro_id != registro_id:
        raise ValueError("Snapshot indisponível para este Registro.")
    pacote = snapshot.conteudo
    if (not isinstance(pacote, dict) or canonico(pacote) != snapshot.conteudo_canonico
            or lacre(snapshot.conteudo_canonico) != snapshot.lacre):
        raise ValueError("Integridade do snapshot não confere.")
    contrato = pacote.get("contrato", {})
    fonte = pacote.get("form1_integral", {})
    if (snapshot.versao_contrato != 3 or contrato.get("versao") != 3
            or snapshot.revisao_fonte != REVISAO_FONTE_FORM1_INTEGRAL
            or contrato.get("revisao_fonte") != snapshot.revisao_fonte
            or fonte.get("versao_contrato") != 3
            or fonte.get("revisao_fonte") != snapshot.revisao_fonte
            or pacote.get("natureza") != "preparacao_tecnica_sem_submissao"
            or pacote.get("submissao_habilitada") is not False):
        raise ValueError("Contrato da origem não reconhecido.")
    estrutura = versao_estrutura(fonte)
    # Snapshots anteriores às extensões não declaravam versao_estrutura.
    declarada = contrato.get("versao_estrutura")
    if declarada is None and estrutura != "F1-C3-REV13":
        raise ValueError("Extensão da origem sem identificação explícita.")
    if declarada is not None and declarada != estrutura:
        raise ValueError("Estrutura da origem incompatível.")
    evento = sessao.get(Evento, snapshot.evento_preparacao_id)
    if (evento is None or evento.tipo_evento != "preparar_snapshot_form1_integral"
            or evento.registro_id != registro_id
            or evento.conteudo.get("snapshot_id") != snapshot.id
            or evento.conteudo.get("lacre") != snapshot.lacre
            or evento.conteudo.get("versao_rascunho") != snapshot.versao_rascunho
            or texto_canonico(evento, CAMPOS_LACRADOS_DOMINIO) != evento.payload_canonico
            or lacre(evento.payload_canonico) != evento.hash):
        raise ValueError("Evento da origem não confere.")
    catalogo = catalogo_efetivo(fonte)
    respostas = fonte.get("respostas", {})
    if not isinstance(respostas, dict):
        raise ValueError("Respostas históricas em formato desconhecido.")
    perguntas = [
        {"id": campo.id, "pergunta": campo.pergunta,
         "respondida": campo.id in respostas, "valor": deepcopy(respostas.get(campo.id))}
        for campo in catalogo.values()
    ]
    if "revisao_22" in fonte:
        from app.rev22_form1 import respostas_conjuntos
        perguntas.extend(respostas_conjuntos(fonte))
    return {"snapshot": snapshot, "estrutura": estrutura, "perguntas": perguntas,
            "conteudo": deepcopy(fonte), "canais": deepcopy(pacote.get("retrato_canais", {}))}
