# Modelos: a descrição das tabelas do banco, escrita em Python.
# O SQLAlchemy traduz cada classe abaixo em uma tabela do PostgreSQL.

from sqlalchemy import (Column, BigInteger, Integer, String, DateTime, JSON, Boolean,
                        ForeignKey, UniqueConstraint, func)
from sqlalchemy.orm import DeclarativeBase, relationship


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


class Pessoa(Base):
    """Uma pessoa (servidor). É a PESSOA que a segregação de funções compara (SAD 03, O-66).
    Na PoC, somente pessoas fictícias. Nenhum CPF, matrícula ou dado real.
    """
    __tablename__ = "pessoa"

    id = Column(String(50), primary_key=True)          # identificador fictício (ex.: PESSOA-A)
    nome = Column(String(100), nullable=False)          # nome fictício
    ativa = Column(Boolean, nullable=False, default=True)

    contas = relationship("Conta", back_populates="pessoa")  # uma pessoa pode ter várias contas


class Conta(Base):
    """Uma conta de acesso. Pertence a exatamente uma pessoa.
    A mesma pessoa pode ter mais de uma conta (ex.: A1 e A2): por isso a regra
    de segregação nunca compara contas, e sim as pessoas por trás delas.
    """
    __tablename__ = "conta"

    id = Column(String(50), primary_key=True)                              # ex.: CONTA-A1
    pessoa_id = Column(String(50), ForeignKey("pessoa.id"), nullable=False)  # a quem pertence
    ativa = Column(Boolean, nullable=False, default=True)

    pessoa = relationship("Pessoa", back_populates="contas")


class Unidade(Base):
    """Uma unidade administrativa (Secretaria, departamento...). Na PoC, unidades fictícias."""
    __tablename__ = "unidade"

    id = Column(String(50), primary_key=True)        # ex.: UNID-NORTE
    nome = Column(String(150), nullable=False)        # nome fictício
    ativa = Column(Boolean, nullable=False, default=True)


class Designacao(Base):
    """Quem exerce qual papel, em qual unidade (SAD 03).
    O papel é dado à PESSOA (não à conta). Uma pessoa pode ter vários papéis.
    Papéis usados na PoC nuclear: elaborador, analista, validador.
    """
    __tablename__ = "designacao"

    id = Column(Integer, primary_key=True)                                     # número interno
    pessoa_id = Column(String(50), ForeignKey("pessoa.id"), nullable=False)    # quem
    unidade_id = Column(String(50), ForeignKey("unidade.id"), nullable=False)  # onde
    papel = Column(String(30), nullable=False)                                 # qual papel
    ativa = Column(Boolean, nullable=False, default=True)

    pessoa = relationship("Pessoa")
    unidade = relationship("Unidade")

    __table_args__ = (
        # a mesma pessoa não recebe o mesmo papel duas vezes na mesma unidade
        UniqueConstraint("pessoa_id", "unidade_id", "papel", name="uq_designacao"),
    )
