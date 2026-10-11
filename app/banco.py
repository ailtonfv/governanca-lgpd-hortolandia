# Camada de persistência: a conexão com o PostgreSQL.
# A senha vem do .env (nunca do código).

import os
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine

load_dotenv()

endereco = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("BANCO_USUARIO"),
    password=os.getenv("BANCO_SENHA"),
    host=os.getenv("BANCO_HOST"),
    port=int(os.getenv("BANCO_PORTA")),
    database=os.getenv("BANCO_NOME"),
)

motor = create_engine(endereco)
