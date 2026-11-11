"""Reversão explícita de infraestrutura vazia, sem CASCADE ou commit próprio."""
from sqlalchemy import inspect, text


def reverter_tabelas_vazias(sessao, nomes):
    conexao = sessao.connection()
    inspector = inspect(conexao)
    existentes = set(inspector.get_table_names())
    alvos = [n for n in nomes if n in existentes]
    quote = conexao.dialect.identifier_preparer.quote
    if not alvos:
        return
    # Impede inserções entre a verificação de vazio e o DDL.
    conexao.execute(text('LOCK TABLE '+', '.join(quote(n) for n in sorted(alvos))+' IN ACCESS EXCLUSIVE MODE'))
    ocupadas = [n for n in alvos if conexao.scalar(text('SELECT EXISTS (SELECT 1 FROM '+quote(n)+')'))]
    if ocupadas:
        raise RuntimeError('reversão recusada: contém snapshots ou outros dados em '+', '.join(ocupadas))
    dependentes = []
    for nome in sorted(existentes-set(alvos)):
        if any(fk['referred_table'] in alvos for fk in inspector.get_foreign_keys(nome)):
            dependentes.append(nome)
    if dependentes:
        raise RuntimeError('reversão recusada: reverta primeiro as migrações dependentes ('+', '.join(dependentes)+'). Nenhuma tabela foi removida.')
    for nome in alvos:
        conexao.execute(text('DROP TABLE '+quote(nome)))
