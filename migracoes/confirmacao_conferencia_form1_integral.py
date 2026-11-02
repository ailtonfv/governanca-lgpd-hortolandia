"""Migração 22: confirmação preparatória da conferência interna do FORM 1."""

from sqlalchemy import text


def aplicar(sessao):
    """Acrescenta o desfecho confirmado sem reescrever apresentações anteriores."""

    conexao = sessao.connection()
    conexao.execute(text("""
        ALTER TABLE historico_conferencia_form1_integral
            ADD COLUMN IF NOT EXISTS confirmada_por_id VARCHAR(50),
            ADD COLUMN IF NOT EXISTS confirmada_em TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS evento_confirmacao_id BIGINT
    """))
    conexao.execute(text("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_historico_conferencia_form1_confirmada_por'
            ) THEN
                ALTER TABLE historico_conferencia_form1_integral
                    ADD CONSTRAINT fk_historico_conferencia_form1_confirmada_por
                    FOREIGN KEY (confirmada_por_id) REFERENCES pessoa(id);
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_historico_conferencia_form1_evento_confirmacao'
            ) THEN
                ALTER TABLE historico_conferencia_form1_integral
                    ADD CONSTRAINT fk_historico_conferencia_form1_evento_confirmacao
                    FOREIGN KEY (evento_confirmacao_id) REFERENCES evento(id);
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uq_historico_conferencia_form1_evento_confirmacao'
            ) THEN
                ALTER TABLE historico_conferencia_form1_integral
                    ADD CONSTRAINT uq_historico_conferencia_form1_evento_confirmacao
                    UNIQUE (evento_confirmacao_id);
            END IF;
        END $$
    """))
    conexao.execute(text("""
        ALTER TABLE historico_conferencia_form1_integral
            DROP CONSTRAINT IF EXISTS ck_historico_conferencia_form1_situacao,
            DROP CONSTRAINT IF EXISTS ck_historico_conferencia_form1_devolucao_completa,
            DROP CONSTRAINT IF EXISTS ck_historico_conferencia_form1_decisao_completa,
            ADD CONSTRAINT ck_historico_conferencia_form1_situacao CHECK (
                situacao IN (
                    'aguardando_conferencia_interna_apa',
                    'devolvida_para_ajustes',
                    'conferencia_interna_confirmada'
                )
            ),
            ADD CONSTRAINT ck_historico_conferencia_form1_decisao_completa CHECK (
                (situacao = 'aguardando_conferencia_interna_apa'
                 AND devolvida_por_id IS NULL AND devolvida_em IS NULL
                 AND justificativa_devolucao IS NULL AND evento_devolucao_id IS NULL
                 AND confirmada_por_id IS NULL AND confirmada_em IS NULL
                 AND evento_confirmacao_id IS NULL)
                OR
                (situacao = 'devolvida_para_ajustes'
                 AND devolvida_por_id IS NOT NULL AND devolvida_em IS NOT NULL
                 AND justificativa_devolucao IS NOT NULL AND evento_devolucao_id IS NOT NULL
                 AND confirmada_por_id IS NULL AND confirmada_em IS NULL
                 AND evento_confirmacao_id IS NULL)
                OR
                (situacao = 'conferencia_interna_confirmada'
                 AND devolvida_por_id IS NULL AND devolvida_em IS NULL
                 AND justificativa_devolucao IS NULL AND evento_devolucao_id IS NULL
                 AND confirmada_por_id IS NOT NULL AND confirmada_em IS NOT NULL
                 AND evento_confirmacao_id IS NOT NULL)
            )
    """))


def reverter(sessao):
    """Reverte somente se nenhuma conferência confirmada seria perdida."""

    conexao = sessao.connection()
    if conexao.scalar(text("""
        SELECT EXISTS (
            SELECT 1 FROM historico_conferencia_form1_integral
            WHERE situacao = 'conferencia_interna_confirmada'
               OR confirmada_por_id IS NOT NULL
               OR confirmada_em IS NOT NULL
               OR evento_confirmacao_id IS NOT NULL
        )
    """)):
        raise RuntimeError(
            "reversão recusada: há confirmações internas preservadas"
        )
    conexao.execute(text("""
        ALTER TABLE historico_conferencia_form1_integral
            DROP CONSTRAINT IF EXISTS ck_historico_conferencia_form1_decisao_completa,
            DROP CONSTRAINT IF EXISTS ck_historico_conferencia_form1_situacao,
            DROP CONSTRAINT IF EXISTS uq_historico_conferencia_form1_evento_confirmacao,
            DROP CONSTRAINT IF EXISTS fk_historico_conferencia_form1_evento_confirmacao,
            DROP CONSTRAINT IF EXISTS fk_historico_conferencia_form1_confirmada_por,
            DROP COLUMN IF EXISTS evento_confirmacao_id,
            DROP COLUMN IF EXISTS confirmada_em,
            DROP COLUMN IF EXISTS confirmada_por_id,
            ADD CONSTRAINT ck_historico_conferencia_form1_situacao CHECK (
                situacao IN ('aguardando_conferencia_interna_apa', 'devolvida_para_ajustes')
            ),
            ADD CONSTRAINT ck_historico_conferencia_form1_devolucao_completa CHECK (
                (situacao = 'aguardando_conferencia_interna_apa'
                 AND devolvida_por_id IS NULL AND devolvida_em IS NULL
                 AND justificativa_devolucao IS NULL AND evento_devolucao_id IS NULL)
                OR
                (situacao = 'devolvida_para_ajustes'
                 AND devolvida_por_id IS NOT NULL AND devolvida_em IS NOT NULL
                 AND justificativa_devolucao IS NOT NULL AND evento_devolucao_id IS NOT NULL)
            )
    """))
