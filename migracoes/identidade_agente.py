"""Migração 8: matrícula funcional única para os agentes fictícios da PoC."""

from sqlalchemy import text


MATRICULAS_FICTICIAS = {
    "PESSOA-A": "MAT-FICT-0001",
    "PESSOA-B": "MAT-FICT-0002",
    "PESSOA-C": "MAT-FICT-0003",
    "PESSOA-D": "MAT-FICT-0004",
    "PESSOA-E": "MAT-FICT-0005",
    "PESSOA-F": "MAT-FICT-0006",
}


def aplicar(sessao):
    sessao.execute(text("ALTER TABLE pessoa ADD COLUMN IF NOT EXISTS matricula VARCHAR(30)"))
    for pessoa_id, matricula in MATRICULAS_FICTICIAS.items():
        sessao.execute(
            text("UPDATE pessoa SET matricula = :matricula WHERE id = :pessoa_id AND matricula IS NULL"),
            {"pessoa_id": pessoa_id, "matricula": matricula},
        )
    faltantes = sessao.execute(
        text("SELECT id FROM pessoa WHERE matricula IS NULL ORDER BY id")
    ).scalars().all()
    if faltantes:
        raise RuntimeError(
            "Migração de identidade encontrou pessoas sem matrícula definida: "
            + ", ".join(faltantes)
        )
    sessao.execute(text("ALTER TABLE pessoa ALTER COLUMN matricula SET NOT NULL"))
    sessao.execute(text(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_pessoa_matricula ON pessoa (matricula)"
    ))
