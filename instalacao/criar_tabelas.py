# Instalação: cria as tabelas num banco VAZIO e registra a versão 1 do esquema.
#   python -m instalacao.criar_tabelas
# Num banco que já tem tabelas, não faz nada: a evolução é pelo aplicador de migrações.

import getpass
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import Base, VersaoEsquema

ESQUEMA_INICIAL = (1, "esquema inicial v2 (Etapa 2d: D1, D2, D4, idempotência estrita)")

existentes = inspect(motor).get_table_names()
if existentes:
    raise SystemExit(f"O banco '{motor.url.database}' já tem {len(existentes)} tabela(s). "
                     "Nada foi feito. Para evoluir o esquema: python -m migracoes.aplicar")

Base.metadata.create_all(motor)
with Session(motor) as sessao, sessao.begin():
    sessao.add(VersaoEsquema(numero=ESQUEMA_INICIAL[0], nome=ESQUEMA_INICIAL[1], aplicada_por=getpass.getuser()))
print(f"Banco '{motor.url.database}': {len(inspect(motor).get_table_names())} tabelas criadas; "
      f"versão {ESQUEMA_INICIAL[0]} registrada.")
