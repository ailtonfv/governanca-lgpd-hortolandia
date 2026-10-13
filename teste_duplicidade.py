# Teste da trava contra Registros duplicados (O-80). Somente dados fictícios.
# Requer o catálogo fictício (python semear_catalogo.py).
# Cada cenário compara o resultado ESPERADO com o OBTIDO.
# Roda uma vez: se o pedido CMD-DUP-01 já existir, apenas mostra o que está gravado.

import threading
import time
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import Comando, Registro, RegistroObjeto
from app.workflow import criar_registro


def mostrar(selo_ok, rotulo, registro, motivo, existente):
    selo = "✔" if selo_ok else "✘ FALHOU"
    resultado = f"CRIADO {registro.codigo_lgpd}" if registro else f"NEGADO ({motivo})"
    print(f"{selo} {rotulo:<48} -> {resultado}")
    if existente:
        print(f"      ↳ existente: {existente['registro_existente']} · {existente['objeto']} · "
              f"estado {existente['estado']} · unidade {existente['unidade']} · "
              f"responsável {existente['responsavel']}")
        print(f"      ↳ ações possíveis: {', '.join(existente['acoes_possiveis'])}")


def pedido(conta, unidade, objetos, titulo, cmd):
    """Um pedido numa transação própria (expire_on_commit=False: o resultado continua legível depois)."""
    with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
        return criar_registro(sessao, conta, unidade, objetos, titulo, cmd)


with Session(motor) as sessao:
    ja_existe = sessao.get(Comando, "CMD-DUP-01") is not None

if not ja_existe:
    print("=== Cenários de duplicidade (O-80) ===")

    # Preparo: um Registro com DOIS serviços de mesma finalidade (RF-PRC-13)
    r, m, e = pedido("CONTA-A1", "UNID-NORTE", ["OBJ-SRV-001", "OBJ-SRV-002"],
                     "Atendimento tributário (fictício)", "CMD-DUP-01")
    mostrar(r is not None, "Preparo: Registro com 2 serviços", r, m, e)

    # (2) mesmo objeto, título diferente -> bloqueado
    r, m, e = pedido("CONTA-A1", "UNID-NORTE", ["OBJ-SRV-001"], "IPTU", "CMD-DUP-02")
    mostrar(r is None, "(2) mesmo objeto, outro título ('IPTU')", r, m, e)

    # (2b) um dos objetos já está ocupado -> bloqueado
    r, m, e = pedido("CONTA-A1", "UNID-NORTE", ["OBJ-PRC-001", "OBJ-SRV-002"],
                     "Mistura", "CMD-DUP-03")
    mostrar(r is None, "(2b) um dos objetos já tem Registro", r, m, e)

    # (3) mesmo nome, tipos e identificadores diferentes -> ambos permitidos
    r, m, e = pedido("CONTA-A1", "UNID-NORTE", ["OBJ-SRV-010"],
                     "Atendimento ao contribuinte", "CMD-DUP-04")
    mostrar(r is not None, "(3) 'Atendimento…' como SERVIÇO", r, m, e)
    r, m, e = pedido("CONTA-A1", "UNID-NORTE", ["OBJ-PRC-010"],
                     "Atendimento ao contribuinte", "CMD-DUP-05")
    mostrar(r is not None, "(3) 'Atendimento…' como PROCESSO", r, m, e)

    # (7) clique duplo -> mesmo resultado, nada novo
    r, m, e = pedido("CONTA-A1", "UNID-NORTE", ["OBJ-SRV-001"], "IPTU", "CMD-DUP-02")
    mostrar(r is None and m == "pedido repetido", "(7) repetição do pedido CMD-DUP-02", r, m, e)

    # (1) dois servidores, ao MESMO tempo, para o mesmo objeto (OBJ-PRC-001)
    #     A grava e segura a transação aberta por 2 segundos; C pesquisa nesse intervalo,
    #     não vê nada (o de A ainda não foi confirmado) e tenta gravar: a trava do banco decide.
    resultados = {}
    a_gravou = threading.Event()

    def servidor_a():
        with Session(motor, expire_on_commit=False) as sessao, sessao.begin():
            resultados["A"] = criar_registro(sessao, "CONTA-A1", "UNID-NORTE", ["OBJ-PRC-001"],
                                             "Lançamento do IPTU", "CMD-DUP-06")
            a_gravou.set()
            time.sleep(2)            # transação ainda aberta: o Registro de A não é visível a C

    def servidor_c():
        a_gravou.wait()
        resultados["C"] = pedido("CONTA-C1", "UNID-SUL", ["OBJ-PRC-001"],
                                 "Lançamento do IPTU (2)", "CMD-DUP-07")

    t1, t2 = threading.Thread(target=servidor_a), threading.Thread(target=servidor_c)
    t1.start(); t2.start(); t1.join(); t2.join()
    ra, rc = resultados["A"], resultados["C"]
    mostrar(ra[0] is not None, "(1) simultâneo: servidor A", *ra)
    mostrar(rc[0] is None, "(1) simultâneo: servidor C", *rc)
else:
    print("Os cenários de duplicidade já foram executados. Veja o que está gravado.")

with Session(motor) as sessao:
    print("\n=== Objetos do catálogo ocupados (Registros não cancelados) ===")
    for v in sessao.scalars(select(RegistroObjeto).where(RegistroObjeto.ativo.is_(True))
                            .order_by(RegistroObjeto.objeto_id)):
        print(f"  {v.objeto_id:<12} -> {sessao.get(Registro, v.registro_id).codigo_lgpd}")
