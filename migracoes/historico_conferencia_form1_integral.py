"""Migração 21: histórico da devolução e reapresentação interna do FORM 1."""

from sqlalchemy import text

from app.modelos import HistoricoConferenciaForm1Integral


def aplicar(sessao):
    """Cria o histórico e preserva solicitações pendentes da migração 20."""

    conexao = sessao.connection()
    HistoricoConferenciaForm1Integral.__table__.create(
        bind=conexao, checkfirst=True
    )
    conexao.execute(text("""
        INSERT INTO historico_conferencia_form1_integral (
            id, registro_id, numero_apresentacao, situacao, versao,
            snapshot_id, versao_rascunho, solicitada_por_id, solicitada_em,
            apa_em_exercicio_no_momento_id, evento_solicitacao_id
        )
        SELECT
            'MIG-' || left(md5(registro_id || snapshot_id), 32),
            registro_id, 1, situacao, versao_projecao,
            snapshot_id, versao_rascunho, solicitada_por_id, solicitada_em,
            apa_em_exercicio_no_momento_id, evento_solicitacao_id
        FROM conferencia_interna_form1_integral AS atual
        WHERE NOT EXISTS (
            SELECT 1
            FROM historico_conferencia_form1_integral AS historico
            WHERE historico.snapshot_id = atual.snapshot_id
        )
    """))


def reverter(sessao):
    """Reverte somente quando não apaga devoluções ou reapresentações."""

    conexao = sessao.connection()
    inseguro = conexao.scalar(text("""
        SELECT EXISTS (
            SELECT 1
            FROM historico_conferencia_form1_integral AS historico
            WHERE historico.situacao <> 'aguardando_conferencia_interna_apa'
               OR historico.numero_apresentacao <> 1
               OR NOT EXISTS (
                    SELECT 1
                    FROM conferencia_interna_form1_integral AS atual
                    WHERE atual.registro_id = historico.registro_id
                      AND atual.snapshot_id = historico.snapshot_id
                      AND atual.evento_solicitacao_id = historico.evento_solicitacao_id
               )
        )
    """))
    if inseguro:
        raise RuntimeError(
            "reversão recusada: há devoluções ou reapresentações preservadas"
        )
    HistoricoConferenciaForm1Integral.__table__.drop(
        bind=conexao, checkfirst=True
    )
