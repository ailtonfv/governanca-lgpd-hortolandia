"""Segregação pela Pessoa canônica, compartilhada por todas as suas contas."""
from sqlalchemy import select, inspect
from app.modelos import ParticipacaoForm2, HistoricoConferenciaForm1Integral, Registro


def impedido(sessao, pessoa_id, p):
    historicos = sessao.scalars(select(HistoricoConferenciaForm1Integral).where(
        HistoricoConferenciaForm1Integral.registro_id == p.registro_id,
        HistoricoConferenciaForm1Integral.situacao == "conferencia_interna_confirmada")
        .order_by(HistoricoConferenciaForm1Integral.numero_apresentacao.desc())).all()
    relevantes = [h for h in historicos if h.snapshot_id == p.snapshot_id]
    if historicos:
        relevantes.append(historicos[0])
    return any(pessoa_id in {h.solicitada_por_id, h.confirmada_por_id} for h in relevantes)


def aal_em_exercicio(sessao, registro_id, pessoa_id):
    if not inspect(sessao.connection()).has_table("participacao_form2"):
        return False
    return sessao.scalar(select(ParticipacaoForm2.id).where(
        ParticipacaoForm2.registro_id == registro_id,
        ParticipacaoForm2.tipo.in_(["principal", "tematica"]),
        ParticipacaoForm2.responsavel_id == pessoa_id,
        ParticipacaoForm2.estado == "em_atendimento").limit(1)) is not None


def bloquear_registro(sessao, p):
    if p:
        sessao.scalar(select(Registro).where(Registro.id == p.registro_id).with_for_update())
