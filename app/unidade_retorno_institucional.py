"""Metadado de Ouvidoria/e-SIC, distinto do destino de uma pendência.

Registro versionado no livro de eventos existente; não acrescenta pergunta aos FORMs.
"""
from sqlalchemy import select
from app.modelos import Evento, Registro, Unidade, ParticipacaoForm2
from app.fila_form2 import pessoa_ativa, autorizado
from app.continuidade_apa import pessoa_e_apa_em_exercicio
from app.comandos import abrir_comando, fechar_comando
from app.eventos import registrar_evento, registrar_auditoria
from app.governanca_form2_v9 import texto

TIPO = "unidade_retorno_institucional"


def consultar(sessao, registro_id):
    e = sessao.scalar(select(Evento).where(Evento.registro_id == registro_id,
        Evento.tipo_evento == TIPO).order_by(Evento.id.desc()).limit(1))
    return dict(e.conteudo) if e else {"versao": 0, "situacao": "Não informada"}


def registrar(sessao, *, conta_id, comando_id, registro_id, versao, acao, unidade_id=None, canal=None, motivo=""):
    pessoa = pessoa_ativa(sessao, conta_id)
    r = sessao.scalar(select(Registro).where(Registro.id == registro_id).with_for_update())
    if not r:
        raise ValueError("Registro inexistente.")
    atual = consultar(sessao, registro_id)
    e_apa = pessoa_e_apa_em_exercicio(sessao, pessoa.id, r.unidade_principal_atual_id)
    p = sessao.scalar(select(ParticipacaoForm2).where(ParticipacaoForm2.registro_id == registro_id,
        ParticipacaoForm2.tipo == "principal", ParticipacaoForm2.estado == "em_atendimento")
        .order_by(ParticipacaoForm2.entrada_em.desc()).limit(1))
    if not ((acao == "informar" and e_apa) or (acao == "confirmar" and p and p.responsavel_id == pessoa.id and autorizado(sessao,pessoa,p))):
        raise PermissionError("O APA informa a unidade; o AAL responsável confirma no FORM 2.")
    comando, repeticao = abrir_comando(sessao, comando_id, TIPO+"_"+acao,
        dict(conta_id=conta_id,registro_id=registro_id,versao=versao,acao=acao,
            unidade_id=unidade_id,canal=canal,motivo=motivo),"pessoa",pessoa.id,conta_id)
    if repeticao is not None:
        return repeticao
    if atual["versao"] != versao or r.estado_atual != "em_andamento":
        raise ValueError("Registro alterado ou fora de andamento. Atualize a página.")
    motivo = texto(motivo)
    if acao == "informar":
        u = sessao.get(Unidade, unidade_id)
        if not u or not u.ativa or canal not in {"OUV", "ESIC"}:
            raise ValueError("Informe unidade ativa e canal Ouvidoria ou e-SIC.")
        novo = dict(unidade_id=unidade_id, canal=canal, situacao="Aguardando confirmação do AAL", informado_por=pessoa.id)
    else:
        if not atual.get("unidade_id"):
            raise ValueError("O APA precisa informar a unidade antes da confirmação.")
        novo = dict(atual, situacao="Confirmada pelo AAL", confirmado_por=pessoa.id,
            snapshot_id=p.snapshot_id, participacao_id=p.id)
    novo.update(versao=versao+1, motivo=motivo)
    registrar_evento(sessao,comando,"registro",r.id,TIPO,novo,registro_id=r.id,versao_regra="F2-REV22-V9")
    registrar_auditoria(sessao,TIPO,"pessoa",pessoa.id,{"registro_id":r.id,"acao":acao},comando_id=comando.id)
    return fechar_comando(comando,dict(permitido=True,versao=versao+1))
