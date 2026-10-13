# Modelos: a descrição das tabelas do banco, escrita em Python.
# O SQLAlchemy traduz cada classe abaixo em uma tabela do PostgreSQL.

from sqlalchemy import (Column, BigInteger, Integer, String, Text, DateTime, JSON, Boolean,
                        ForeignKey, UniqueConstraint, func)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base comum de todas as tabelas da PoC."""


class Comando(Base):
    """Um pedido do servidor (ex.: "validar o REG-0003"). DA-26, item 3.

    Se o mesmo pedido chegar duas vezes (clique duplo, rede lenta), o sistema
    reconhece o comando_id repetido e devolve o resultado original, sem gravar de novo.
    Um comando pode gerar um ou mais eventos (ordem_no_comando).
    """
    __tablename__ = "comando"

    id = Column(String(64), primary_key=True)              # comando_id: identificador único do pedido
    tipo = Column(String(50), nullable=False)              # o que foi pedido (ex.: validar)
    ator_tipo = Column(String(20), nullable=False)         # pessoa, conta_servico, integracao ou sistema
    ator_id = Column(String(50), nullable=False)           # quem pediu (se pessoa: a PESSOA, não a conta)
    conta_id = Column(String(50))                          # a credencial usada (só informativo)
    recebido_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resultado = Column(JSON)                               # a resposta dada, para devolver na repetição


class Evento(Base):
    """Livro de atos do DOMÍNIO: os atos do workflow (submeter, analisar, validar...).
    DA-26 (modelo de eventos) e DA-27 (contrato de integridade).

    Regras desta tabela:
    - cada objeto tem sua própria corrente (cadeia_tipo + cadeia_id);
    - dentro de uma corrente, a sequência não se repete (1, 2, 3...);
    - cada evento guarda o hash do anterior; nada é apagado nem alterado;
    - o texto exato que foi lacrado (payload_canonico) fica guardado junto.
    Tentativas negadas e consultas NÃO entram aqui: vão para evento_auditoria.
    """
    __tablename__ = "evento"

    id = Column(BigInteger, primary_key=True)                  # número interno da linha
    # --- a corrente (DA-26, item 1)
    cadeia_tipo = Column(String(30), nullable=False)           # registro, relato, incidente...
    cadeia_id = Column(String(50), nullable=False)             # qual corrente (ex.: REG-0003)
    sequencia_cadeia = Column(Integer, nullable=False)         # posição na corrente: 1, 2, 3...
    registro_id = Column(String(50))                           # o Registro (ligação real na etapa 2)
    ciclo_id = Column(Integer)                                 # o ciclo do Registro (etapa 2)
    # --- o que aconteceu (DA-26, item 2)
    tipo_evento = Column(String(50), nullable=False)           # nome do ato (ex.: submeter)
    codigo_evento = Column(String(10))                         # código da transição no SAD 04 (ex.: I3)
    # --- o pedido que gerou o ato (DA-26, item 3)
    comando_id = Column(String(64), ForeignKey("comando.id"), nullable=False)
    ordem_no_comando = Column(Integer, nullable=False)         # 1º, 2º... evento do mesmo pedido
    # --- quem (DA-26, item 6)
    ator_tipo = Column(String(20), nullable=False)             # pessoa, conta_servico, integracao, sistema
    ator_id = Column(String(50), nullable=False)               # se pessoa: a PESSOA, nunca a conta
    em_nome_de = Column(String(50))                            # substituição (cenário d, mais adiante)
    # --- quando
    ocorrido_em = Column(DateTime(timezone=True), nullable=False)  # quando o ato aconteceu (entra no lacre)
    registrado_em = Column(DateTime(timezone=True),                # quando o banco gravou (fora do lacre)
                           nullable=False, server_default=func.now())
    # --- versões (DA-26, item 2; DA-27, item 4)
    versao_regra = Column(String(20), nullable=False)          # versão da configuração do workflow
    versao_esquema_evento = Column(Integer, nullable=False)    # versão do formato deste evento
    versao_algoritmo_hash = Column(String(30), nullable=False) # como o lacre foi calculado
    # --- conteúdo e lacre (DA-27)
    conteudo = Column(JSON, nullable=False)                    # os detalhes do ato
    payload_canonico = Column(Text, nullable=False)            # o texto exato que foi lacrado
    hash_anterior = Column(String(64), nullable=False)         # o lacre do evento anterior
    hash = Column(String(64), nullable=False, unique=True)     # o lacre deste evento

    __table_args__ = (
        UniqueConstraint("cadeia_id", "sequencia_cadeia", name="uq_evento_posicao_na_cadeia"),
        UniqueConstraint("comando_id", "ordem_no_comando", name="uq_evento_ordem_no_comando"),
    )


class EventoAuditoria(Base):
    """Livro de AUDITORIA: consultas, downloads, tentativas negadas, alterações de conta e papel.
    DA-26, item 4 (separado do domínio) e DA-27, item 1 (segmentos mensais).

    Não pertence a nenhum Registro. Cada mês forma um segmento (ex.: AUDITORIA-2026-10),
    com sua própria corrente de hash. O fechamento do segmento e a ligação entre meses
    ficam para um passo posterior.
    """
    __tablename__ = "evento_auditoria"

    id = Column(BigInteger, primary_key=True)
    segmento_id = Column(String(30), nullable=False)           # ex.: AUDITORIA-2026-10
    sequencia_segmento = Column(Integer, nullable=False)       # posição no segmento: 1, 2, 3...
    tipo_evento = Column(String(50), nullable=False)           # ex.: tentativa_negada
    comando_id = Column(String(64), ForeignKey("comando.id"))  # o pedido que foi negado (se houver)
    ator_tipo = Column(String(20), nullable=False)
    ator_id = Column(String(50), nullable=False)
    ocorrido_em = Column(DateTime(timezone=True), nullable=False)
    registrado_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    versao_esquema_evento = Column(Integer, nullable=False)
    versao_algoritmo_hash = Column(String(30), nullable=False)
    conteudo = Column(JSON, nullable=False)                    # ação tentada, objeto, conta, motivo
    payload_canonico = Column(Text, nullable=False)
    hash_anterior = Column(String(64), nullable=False)
    hash = Column(String(64), nullable=False, unique=True)

    __table_args__ = (
        UniqueConstraint("segmento_id", "sequencia_segmento", name="uq_auditoria_posicao_no_segmento"),
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


class Registro(Base):
    """O Registro LGPD: a "pasta" de um processo, atividade ou serviço que trata dados pessoais.
    SAD 05, seção 5. Criado pelo ato G1 (SAD 04, seção 7).

    Os campos marcados como PROJEÇÃO são um resumo para consulta rápida: a verdade está
    no livro de atos, e a projeção sempre pode ser reconstruída a partir dele (DA-26, item 5).
    """
    __tablename__ = "registro"

    id = Column(String(36), primary_key=True)                     # registro_id: identificador técnico (UUID)
    codigo_lgpd = Column(String(20), nullable=False, unique=True)  # identificador humano (ex.: LGPD-2026-00001)
    tipo_objeto = Column(String(20), nullable=False)              # processo, atividade ou servico
    titulo_objeto = Column(String(200), nullable=False)           # descrição curta, sem dados pessoais
    unidade_principal_atual_id = Column(String(50), ForeignKey("unidade.id"), nullable=False)
    criado_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    criado_por = Column(String(50), nullable=False)               # a PESSOA que criou
    # --- projeções (resumo reconstruível a partir do livro de atos)
    ciclo_atual = Column(Integer, nullable=False)                 # número do ciclo ativo
    estado_atual = Column(String(30), nullable=False)             # ex.: em_andamento
    sequencia_atual = Column(Integer, nullable=False)             # último número da corrente do Registro


class Ciclo(Base):
    """Um ciclo de vida do Registro. O ciclo 1 nasce com o Registro; a reabertura (fora da
    PoC nuclear) abriria o ciclo 2. SAD 05, seção 6."""
    __tablename__ = "ciclo"

    id = Column(Integer, primary_key=True)                        # ciclo_id: número interno
    registro_id = Column(String(36), ForeignKey("registro.id"), nullable=False)
    numero = Column(Integer, nullable=False)                      # 1, 2, 3... dentro do Registro
    iniciado_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    evento_inicio_id = Column(BigInteger, ForeignKey("evento.id"))  # o ato que abriu o ciclo
    motivo_inicio = Column(String(200))                           # obrigatório a partir do ciclo 2
    situacao = Column(String(20), nullable=False)                 # ativo, concluido ou cancelado (projeção)

    __table_args__ = (
        UniqueConstraint("registro_id", "numero", name="uq_ciclo_numero_no_registro"),
    )


class Instrumento(Base):
    """Um FORM dentro do Registro (FORM 1 a 4). Uma entidade só, com o tipo como atributo.
    No máximo um Instrumento de cada tipo por Registro. SAD 05, seção 7.1.
    Na PoC nuclear existe só o FORM 1 (simplificado)."""
    __tablename__ = "instrumento"

    id = Column(String(36), primary_key=True)                     # instrumento_id (UUID)
    registro_id = Column(String(36), ForeignKey("registro.id"), nullable=False)
    tipo_instrumento = Column(String(10), nullable=False)         # FORM1, FORM2, FORM3 ou FORM4
    estado_instrumento = Column(String(30), nullable=False)       # projeção: nao_iniciado, em_preenchimento...
    versao_vigente_id = Column(String(36))                        # projeção: última versão validada (etapa 2b)

    __table_args__ = (
        UniqueConstraint("registro_id", "tipo_instrumento", name="uq_instrumento_tipo_no_registro"),
    )
