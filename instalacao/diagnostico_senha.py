# Diagnóstico: a senha do .env é a mesma que o banco espera?
# Nada aqui mostra a senha na tela: só o tamanho e uma "impressão digital" curta (hash).

import os, hashlib, getpass
from dotenv import load_dotenv
import psycopg

load_dotenv()

def digital(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:8]

def tenta(senha):
    try:
        psycopg.connect(host="localhost", port=5432, dbname="lgpd_poc",
                        user="lgpd_poc_app", password=senha).close()
        return "CONECTOU"
    except Exception:
        return "falhou"

do_env = os.getenv("BANCO_SENHA") or ""
print(f"Senha do .env      -> tamanho {len(do_env)}, digital {digital(do_env)}, teste: {tenta(do_env)}")

digitada = getpass.getpass("Digite a senha do lgpd_poc_app (nada aparece na tela) e Enter: ")
print(f"Senha digitada     -> tamanho {len(digitada)}, digital {digital(digitada)}, teste: {tenta(digitada)}")
print("As duas são iguais?", do_env == digitada)
