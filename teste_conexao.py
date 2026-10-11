# Teste de conexão: o Python consegue falar com o banco lgpd_poc?
# A senha NÃO está aqui: ela é lida do arquivo .env (que não vai para o GitHub).

import os
from dotenv import load_dotenv           # lê o arquivo .env
from sqlalchemy import URL, create_engine, text  # a "ponte" entre Python e PostgreSQL

load_dotenv()  # carrega as variáveis do .env para a memória do programa

# Monta o endereço do banco a partir das informações do .env.
# URL.create cuida sozinho de senhas com caracteres especiais (@, #, /, :, etc.).
endereco = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("BANCO_USUARIO"),
    password=os.getenv("BANCO_SENHA"),
    host=os.getenv("BANCO_HOST"),
    port=int(os.getenv("BANCO_PORTA")),
    database=os.getenv("BANCO_NOME"),
)

motor = create_engine(endereco)  # prepara a conexão (ainda não conecta)

with motor.connect() as conexao:  # agora sim conecta; ao final, fecha sozinho
    usuario = conexao.execute(text("SELECT current_user")).scalar()
    base = conexao.execute(text("SELECT current_database()")).scalar()
    print("Conexão estabelecida!")
    print("Usuário conectado:", usuario)
    print("Base de dados:   ", base)
