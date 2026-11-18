"""Leitura interna de fatos existentes; não concede acesso nem avalia risco."""
from sqlalchemy import select
from app.modelos import IdentidadeForms34, ReferenciaParticipacaoForms34
from app.base_forms34 import historico


def fatos_existentes(sessao, *, registro_ids):
    """O adaptador futuro fornece escopo já autorizado; não há rota pública.

    Nenhuma participação técnica representa ingresso/avaliação/conclusão. O
    dashboard deve conservar None como ausência de informação, não convertê-lo
    em zero, cumprimento de prazo ou conformidade.
    """
    if not isinstance(registro_ids, (list, tuple, set, frozenset)):
        raise ValueError("Informe explicitamente o escopo dos Registros.")
    objetos = sessao.scalars(select(IdentidadeForms34).where(
        IdentidadeForms34.registro_id.in_(registro_ids)).order_by(
            IdentidadeForms34.registro_id, IdentidadeForms34.tipo, IdentidadeForms34.numero)).all()
    fatos = []
    for obj in objetos:
        ref = sessao.get(ReferenciaParticipacaoForms34, obj.participacao_id)
        eventos = historico(sessao, obj.id)
        ultimo = eventos[-1] if eventos else None
        fatos.append(dict(identidade_id=obj.id, codigo=obj.codigo, tipo=obj.tipo,
            registro_id=obj.registro_id, participacao_id=obj.participacao_id,
            origem=dict(form=ref.fonte_form, id=ref.fonte_id, versao=ref.fonte_versao,
                        lacre=ref.fonte_lacre, snapshot_form1_id=ref.snapshot_form1_id),
            retirada_tecnica=any(e.tipo_evento == 'base34_retirada_tecnica' for e in eventos),
            revisao_historico=ultimo.sequencia_cadeia if ultimo else None,
            ultimo_autor_id=ultimo.ator_id if ultimo else None,
            ultima_data=ultimo.ocorrido_em.isoformat() if ultimo else None,
            nivel_risco=None, percentual=None, prazo=None, estado_institucional=None))
    return dict(fatos=fatos, quantidade_identidades=len(fatos) if fatos else None,
                nivel_risco=None, percentual=None, cobertura=None,
                situacao='fatos_tecnicos' if fatos else 'sem_fatos')
