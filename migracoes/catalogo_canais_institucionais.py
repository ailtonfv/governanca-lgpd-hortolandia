"""Migração 19: consolida as modalidades institucionais do catálogo de canais.

A migração altera somente o catálogo geral. Não cria vínculos ``ObjetoCanal`` e
não reescreve os nomes preservados nos retratos históricos dos Registros.
"""

from sqlalchemy import text


CANAIS = (
    ("CNL-001", "Presencial / balcão de atendimento", None),
    ("CNL-002", "Portal da Prefeitura", None),
    ("CNL-003", "Telefone", None),
    ("CNL-004", "Ouvidoria", "Ouvidoria"),
    ("CNL-005", "e-SIC", "e-SIC"),
    ("CNL-006", "Central 156", None),
    ("CNL-007", "WhatsApp corporativo", None),
    ("CNL-008", "E-mail institucional", None),
)


def aplicar(sessao):
    for canal_id, nome, classificacao_form1 in CANAIS:
        sessao.execute(text("""
            INSERT INTO canal (id, nome_canonico, classificacao_form1, ativo)
            VALUES (:canal_id, :nome, :classificacao_form1, TRUE)
            ON CONFLICT (id) DO UPDATE
               SET nome_canonico = EXCLUDED.nome_canonico,
                   classificacao_form1 = EXCLUDED.classificacao_form1
        """), {
            "canal_id": canal_id,
            "nome": nome,
            "classificacao_form1": classificacao_form1,
        })
