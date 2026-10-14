# Atalhos usados pelos testes. Somente dados fictícios.

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import Registro, RegistroObjeto, Evento
from app.workflow import criar_registro

CADASTRO = "OBJ-ATV-020"        # Gerir e manter o Cadastro imobiliário (fictício)
LANCAMENTO = "OBJ-PRC-001"      # Lançamento e cobrança do IPTU (fictício)


def g1(cmd, principal, contexto, conta="CONTA-A1", unidade="UNID-NORTE",
       titulo="Registro de teste (fictício)", **extra):
    """Um pedido G1 numa transação própria, confirmada ao final."""
    with Session(motor, expire_on_commit=False) as s, s.begin():
        return criar_registro(s, comando_id=cmd, conta_id=conta, unidade_id=unidade,
                              contexto_id=contexto, titulo_objeto=titulo,
                              objeto_principal_id=principal, **extra)


def sem_reexecucao(resultado):
    """O resultado sem o indicador de reexecução, para comparar com o original."""
    return {k: v for k, v in resultado.items() if k != "reexecutado"}


def evento_g1(codigo):
    with Session(motor) as s:
        return s.scalars(select(Evento).where(Evento.cadeia_id == codigo, Evento.codigo_evento == "G1")).one()


def mudar_estado(codigo, estado, liberar_vinculos=False):
    """PROVISÓRIO ATÉ O M1b.1: prepara o estado direto no banco DE TESTE, porque os atos de
    suspender, concluir e cancelar ainda não existem. Testa a REGRA, não o ato."""
    with Session(motor) as s, s.begin():
        r = s.scalars(select(Registro).where(Registro.codigo_lgpd == codigo)).one()
        r.estado_atual = estado
        if liberar_vinculos:
            for v in s.scalars(select(RegistroObjeto).where(RegistroObjeto.registro_id == r.id)):
                v.ativo = False
