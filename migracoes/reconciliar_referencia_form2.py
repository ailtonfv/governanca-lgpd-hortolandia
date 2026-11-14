"""Atualiza uma participação legada ainda sem assunção, pelo identificador LGPD."""
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.comandos import abrir_comando, fechar_comando
from app.governanca_form2_v9 import receber_confirmacao
from app.modelos import HistoricoConferenciaForm1Integral as Historico
from app.modelos import ParticipacaoForm2, Registro, VersaoForm1Integral


def reconciliar(sessao, codigo):
    registro = sessao.scalars(select(Registro).where(
        Registro.codigo_lgpd == codigo).with_for_update()).one()
    p = sessao.scalars(select(ParticipacaoForm2).where(
        ParticipacaoForm2.registro_id == registro.id,
        ParticipacaoForm2.tipo == "principal", ParticipacaoForm2.estado != "concluida"
    ).with_for_update().execution_options(populate_existing=True)).one_or_none()
    if not p or p.estado != "aguardando" or p.assumida_em or p.responsavel_id:
        return False
    confirmada = sessao.scalar(select(Historico).where(
        Historico.registro_id == registro.id,
        Historico.situacao == "conferencia_interna_confirmada"
    ).order_by(Historico.numero_apresentacao.desc()).limit(1))
    if not confirmada:
        return False
    atual = sessao.get(VersaoForm1Integral, p.snapshot_id)
    nova = sessao.get(VersaoForm1Integral, confirmada.snapshot_id)
    if nova.numero <= atual.numero:
        return False
    comando, _ = abrir_comando(sessao, str(uuid4()), "reconciliar_referencia_form2",
        {"participacao_id": p.id, "anterior": atual.id, "nova": nova.id}, "sistema", "P17")
    receber_confirmacao(sessao, p, nova.id, comando)
    fechar_comando(comando, {"participacao_id": p.id, "snapshot_id": nova.id})
    return True


if __name__ == "__main__":
    import argparse
    from app.banco import motor

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("codigo")
    with Session(motor) as sessao, sessao.begin():
        mudou = reconciliar(sessao, parser.parse_args().codigo)
    print("Referência atualizada." if mudou else "Nenhuma atualização necessária.")
