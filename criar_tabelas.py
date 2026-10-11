# Cria no banco lgpd_poc as tabelas descritas em app/modelos.py.
# Pode ser rodado mais de uma vez: tabelas que já existem não são recriadas.

from sqlalchemy import inspect
from app.banco import motor
from app.modelos import Base

Base.metadata.create_all(motor)

inspetor = inspect(motor)
for tabela in inspetor.get_table_names():
    print(f"Tabela '{tabela}' pronta, com as colunas:")
    for coluna in inspetor.get_columns(tabela):
        print(f"   - {coluna['name']:<18} {coluna['type']}")
