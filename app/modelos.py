# Modelos: a descrição das tabelas do banco, escrita em Python.
# O SQLAlchemy traduz cada classe abaixo em uma tabela do PostgreSQL.

from sqlalchemy import (Column, BigInteger, Integer, String, DateTime, JSON,
                        UniqueConstraint, func)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base comum de todas as tabelas da PoC."""


class Evento(Base):
    """Livro de atos: cada linha é um acontecimento, selado com hash (DA-26, DA-27).

    Regras desta tabela:
    - cada objeto (ex.: um Registro) tem sua própria corrente (cadeia_id);
    - dentro de uma corrente, a sequência não se repete (1, 2, 3...);
    - cada evento guarda o hash do anterior; nada é apagado nem alterado.
    """
    __tablename__ = "evento"

    id = Column(BigInteger, primary_key=True)              # número interno da linha
    cadeia_id = Column(String(50), nullable=False)         # a qual corrente pertence (ex.: REG-0001)
    sequencia_cadeia = Column(Integer, nullable=False)     # posição na corrente: 1, 2, 3...
    codigo_evento = Column(String(50), nullable=False)     # o que aconteceu (ex.: submeter, analisar)
    pessoa_id = Column(String(50), nullable=False)         # quem fez (a pessoa, não a conta)
    registrado_em = Column(DateTime(timezone=True),        # quando o sistema registrou
                           nullable=False, server_default=func.now())
    conteudo = Column(JSON, nullable=False)                # os detalhes do evento
    hash_anterior = Column(String(64), nullable=False)     # o lacre do evento anterior
    hash = Column(String(64), nullable=False, unique=True)  # o lacre deste evento

    __table_args__ = (
        # Garante que não existam dois eventos na mesma posição da mesma corrente
        UniqueConstraint("cadeia_id", "sequencia_cadeia", name="uq_evento_posicao_na_cadeia"),
    )
