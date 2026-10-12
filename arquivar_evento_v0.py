# Arquiva a primeira versão do livro de atos antes de criar a nova (alinhada à DA-26 e à DA-27).
#
# Princípio: o livro de atos não se apaga. Em vez de excluir a tabela antiga,
# ela é RENOMEADA para evento_v0 e fica somente para leitura, como histórico da PoC.
# Roda uma vez só: se evento_v0 já existir, não faz nada.

from sqlalchemy import inspect, text
from app.banco import motor

tabelas = inspect(motor).get_table_names()

if "evento_v0" in tabelas:
    print("Nada a fazer: a tabela evento_v0 já existe (arquivamento feito antes).")
elif "evento" not in tabelas:
    print("Nada a fazer: não existe tabela evento para arquivar.")
else:
    with motor.begin() as con:  # tudo ou nada: uma única transação
        # 1. troca o nome da tabela
        con.execute(text('ALTER TABLE evento RENAME TO evento_v0'))

        # 2. troca o nome das regras da tabela (chave, hash único, posição na cadeia),
        #    para não colidirem com as da tabela nova
        regras = con.execute(text(
            "SELECT conname FROM pg_constraint WHERE conrelid = 'evento_v0'::regclass"
        )).scalars().all()
        for nome in regras:
            novo = nome.replace("evento", "evento_v0", 1)
            con.execute(text(f'ALTER TABLE evento_v0 RENAME CONSTRAINT "{nome}" TO "{novo}"'))

        # 3. troca o nome do contador de números internos (id)
        contador = con.execute(text("SELECT pg_get_serial_sequence('evento_v0', 'id')")).scalar()
        if contador:
            con.execute(text(f"ALTER SEQUENCE {contador} RENAME TO evento_v0_id_seq"))

        # 4. etiqueta e trava: a tabela antiga passa a ser somente leitura
        con.execute(text(
            "COMMENT ON TABLE evento_v0 IS "
            "'Livro de atos da 1a versao da PoC, arquivado em 12/10/2026. Somente leitura.'"
        ))
        con.execute(text("REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON evento_v0 FROM CURRENT_USER"))

    with motor.connect() as con:
        total = con.execute(text("SELECT count(*) FROM evento_v0")).scalar()
        regras = con.execute(text(
            "SELECT conname FROM pg_constraint WHERE conrelid = 'evento_v0'::regclass ORDER BY 1"
        )).scalars().all()
    print(f"Arquivado: tabela evento_v0 com {total} eventos, somente leitura.")
    print("Regras renomeadas:", ", ".join(regras))
