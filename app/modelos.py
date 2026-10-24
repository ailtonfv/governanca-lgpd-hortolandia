# Modelos: a descrição das tabelas do banco, escrita em Python.
# O SQLAlchemy traduz cada classe abaixo em uma tabela do PostgreSQL.

from sqlalchemy import (Column, BigInteger, Integer, String, Text, DateTime, JSON, Boolean,
                        ForeignKey, ForeignKeyConstraint, UniqueConstraint, CheckConstraint, Index, func)
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
    hash_parametros = Column(String(64))                   # lacre dos parâmetros do pedido: a mesma chave
                                                           # com outro conteúdo é recusada (Etapa 2d)


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
    matricula = Column(String(30), nullable=False)      # matrícula funcional única; fictícia na PoC
    nome = Column(String(100), nullable=False)          # nome fictício
    ativa = Column(Boolean, nullable=False, default=True)

    contas = relationship("Conta", back_populates="pessoa")  # uma pessoa pode ter várias contas

    __table_args__ = (UniqueConstraint("matricula", name="uq_pessoa_matricula"),)


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
    """Uma unidade administrativa. A PoC usa nomes públicos reais das Secretarias, mas agentes,
    designações, Registros e conteúdos continuam fictícios."""
    __tablename__ = "unidade"

    id = Column(String(50), primary_key=True)        # ex.: UNID-NORTE
    nome = Column(String(150), nullable=False)        # nome fictício
    ativa = Column(Boolean, nullable=False, default=True)


class Designacao(Base):
    """Quem exerce qual papel, em qual unidade (SAD 03).
    O papel é dado à PESSOA (não à conta). Uma pessoa pode ter vários papéis.
    Papéis usados na PoC nuclear: responsavel_registro, preenchedor, analista,
    validador, concluidor e agente_pendencia (designação provisória para atuar
    na fila institucional).
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
    contexto_atuacao_id = Column(String(20), ForeignKey("contexto_atuacao.id"), nullable=False)  # D1: um por Registro
    ano_codigo = Column(Integer, nullable=False)                  # D4: ano da criação (America/Sao_Paulo)
    numero_codigo = Column(Integer, nullable=False)               # D4: número dentro do ano (recomeça a cada ano)
    criado_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    criado_por = Column(String(50), nullable=False)               # a PESSOA que criou
    # --- projeções (resumo reconstruível a partir do livro de atos)
    ciclo_atual = Column(Integer, nullable=False)                 # número do ciclo ativo
    estado_atual = Column(String(30), nullable=False)             # ex.: em_andamento
    sequencia_atual = Column(Integer, nullable=False)             # último número da corrente do Registro

    __table_args__ = (
        UniqueConstraint("ano_codigo", "numero_codigo", name="uq_registro_ano_numero"),
        # permite que os vínculos apontem para (Registro, contexto): garante contexto único por Registro (D1)
        UniqueConstraint("id", "contexto_atuacao_id", name="uq_registro_id_contexto"),
    )


class ContadorRegistro(Base):
    """Contador anual do código LGPD (D4): LGPD-2026-00041, depois LGPD-2027-00001.
    Atualizado na mesma transação do G1, com INSERT ... ON CONFLICT ... RETURNING:
    dois pedidos simultâneos nunca recebem o mesmo número."""
    __tablename__ = "contador_registro"

    ano = Column(Integer, primary_key=True)
    ultimo_numero = Column(Integer, nullable=False)


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


class RascunhoInstrumento(Base):
    """O RASCUNHO de um Instrumento: a folha de trabalho, que pode ser rasurada (Incremento 1).
    Uma linha por Instrumento. Nasce no I1 (Iniciar preenchimento); é reescrita a cada I2 (Salvar).

    Controle otimista (POC-TS-004, A9): quem salva informa o número do salvamento que LEU.
    Se outra pessoa salvou nesse meio-tempo, o número já subiu e a gravação é recusada,
    para que ninguém apague o trabalho alheio sem ver."""
    __tablename__ = "rascunho_instrumento"

    instrumento_id = Column(String(36), ForeignKey("instrumento.id"), primary_key=True)
    conteudo = Column(JSON, nullable=False)                   # o que está preenchido (só dados fictícios)
    versao_rascunho = Column(Integer, nullable=False)         # nº do salvamento: 1 no I1, +1 a cada I2
    salvo_por = Column(String(50), nullable=False)            # a PESSOA que salvou por último
    salvo_em = Column(DateTime(timezone=True), nullable=False)
    lacre_conteudo = Column(String(64), nullable=False)       # lacre do conteúdo atual (usado no P3/P4)

    __table_args__ = (
        CheckConstraint("versao_rascunho >= 1", name="ck_rascunho_versao_positiva"),
    )


class VersaoInstrumento(Base):
    """Uma VERSÃO N do Instrumento: a cópia protocolada no I3 (Submeter). Nunca é alterada.
    Uma retirada (I4) não apaga a versão; a próxima submissão cria a Versão N+1 (cenário A11).
    O lacre é o SHA-256 do texto canônico do conteúdo, pelo mesmo método dos eventos (DA-27)."""
    __tablename__ = "versao_instrumento"

    id = Column(String(36), primary_key=True)                 # UUID da versão
    instrumento_id = Column(String(36), ForeignKey("instrumento.id"), nullable=False)
    numero = Column(Integer, nullable=False)                  # 1, 2, 3... dentro do Instrumento
    versao_contrato = Column(Integer, nullable=False, server_default="1")  # formato do conteúdo
    conteudo = Column(JSON, nullable=False)                   # o conteúdo congelado
    conteudo_canonico = Column(Text, nullable=False)          # o texto exato que foi lacrado
    lacre = Column(String(64), nullable=False)                # SHA-256 do conteudo_canonico
    submetida_por = Column(String(50), nullable=False)        # a PESSOA que submeteu
    submetida_em = Column(DateTime(timezone=True), nullable=False)
    evento_submissao_id = Column(BigInteger, ForeignKey("evento.id"), nullable=False)  # o ato I3

    __table_args__ = (
        UniqueConstraint("instrumento_id", "numero", name="uq_versao_numero_no_instrumento"),
    )


class AnaliseInstrumento(Base):
    """A análise aberta pelo I13 para uma versão submetida do Instrumento.

    Há uma única análise por versão. I14 poderá trocar o responsável atual sem
    apagar o autor do início nem os eventos anteriores da cadeia do Instrumento.
    """
    __tablename__ = "analise_instrumento"

    id = Column(String(36), primary_key=True)
    versao_id = Column(String(36), ForeignKey("versao_instrumento.id"), nullable=False)
    instrumento_id = Column(String(36), ForeignKey("instrumento.id"), nullable=False)
    responsavel_atual_id = Column(String(50), ForeignKey("pessoa.id"), nullable=False)
    iniciada_por = Column(String(50), ForeignKey("pessoa.id"), nullable=False)
    iniciada_em = Column(DateTime(timezone=True), nullable=False)
    atualizada_em = Column(DateTime(timezone=True), nullable=False)
    situacao = Column(String(20), nullable=False)              # ativa ou encerrada
    evento_inicio_id = Column(BigInteger, ForeignKey("evento.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("versao_id", name="uq_analise_por_versao"),
        CheckConstraint("situacao IN ('ativa', 'encerrada')", name="ck_analise_situacao"),
    )


class AcaoObrigatoria(Base):
    """Ação sintética mínima usada para provar o percurso com medidas no M1a.

    O FORM 4 completo está fora desta etapa. Aqui fica apenas o necessário para
    o G4 saber se o Registro deve permanecer em execução e para o G6 comprovar
    a conclusão ou o encerramento formal da medida.
    """
    __tablename__ = "acao_obrigatoria"

    id = Column(String(36), primary_key=True)
    registro_id = Column(String(36), ForeignKey("registro.id"), nullable=False)
    ciclo_id = Column(Integer, ForeignKey("ciclo.id"), nullable=False)
    instrumento_id = Column(String(36), ForeignKey("instrumento.id"), nullable=False)
    estado = Column(String(20), nullable=False)                 # aberta, concluida ou encerrada
    responsavel_id = Column(String(50), ForeignKey("pessoa.id"), nullable=False)
    evidencia = Column(JSON)                                    # sintética e sem dados pessoais reais
    criada_em = Column(DateTime(timezone=True), nullable=False)
    atualizada_em = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "estado IN ('aberta', 'concluida', 'encerrada')",
            name="ck_acao_obrigatoria_estado",
        ),
    )


class Pendencia(Base):
    """Providência rastreável; no M1a, começa pela devolução automática do I6.

    A pendência pertence ao Registro e ao ciclo em que nasceu. Quando decorre
    de um Instrumento, mantém também esse vínculo e aponta para o evento que a
    originou. O destino inicial é uma unidade, nunca uma pessoa específica.
    """
    __tablename__ = "pendencia"

    id = Column(String(36), primary_key=True)
    tipo_pendencia = Column(String(30), nullable=False)       # devolucao, providencia...
    registro_id = Column(String(36), ForeignKey("registro.id"), nullable=False)
    ciclo_origem_id = Column(Integer, ForeignKey("ciclo.id"), nullable=False)
    ciclo_contexto_atual_id = Column(Integer, ForeignKey("ciclo.id"), nullable=False)
    instrumento_id = Column(String(36), ForeignKey("instrumento.id"))
    evento_origem_id = Column(BigInteger, ForeignKey("evento.id"), nullable=False, unique=True)
    unidade_origem_id = Column(String(50), ForeignKey("unidade.id"), nullable=False)
    unidade_destino_id = Column(String(50), ForeignKey("unidade.id"), nullable=False)
    responsavel_atual_id = Column(String(50), ForeignKey("pessoa.id"))
    estado = Column(String(40), nullable=False)
    bloqueante = Column(Boolean, nullable=False)
    gate_bloqueado = Column(String(30))                        # ex.: submissao
    motivo = Column(Text, nullable=False)
    lacre_resposta = Column(String(64))                        # preenchido no futuro P3
    lacre_aceito = Column(String(64))                          # preenchido no futuro P4
    criada_em = Column(DateTime(timezone=True), nullable=False)
    atualizada_em = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "tipo_pendencia IN ('devolucao', 'providencia', 'participacao', "
            "'avaliacao_ripd', 'inconsistencia_ingestao')",
            name="ck_pendencia_tipo",
        ),
        CheckConstraint(
            "estado IN ('aberta', 'em_atendimento', 'respondida', 'encerrada', "
            "'devolvida_para_complementacao', 'cancelada')",
            name="ck_pendencia_estado",
        ),
        CheckConstraint(
            "(bloqueante AND gate_bloqueado IS NOT NULL) OR "
            "(NOT bloqueante AND gate_bloqueado IS NULL)",
            name="ck_pendencia_gate_bloqueante",
        ),
    )


# Numerador dos códigos LGPD. Um contador do próprio banco: dois pedidos simultâneos
# nunca recebem o mesmo número (pode haver "pulos" na numeração, o que é aceitável).


class ObjetoCatalogo(Base):
    """Um objeto da Jornada no catálogo: serviço, processo ou atividade (O-80).
    O identificador canônico (id) é o que define a equivalência, nunca o nome digitado.
    Na PoC, somente objetos fictícios."""
    __tablename__ = "objeto_catalogo"

    id = Column(String(50), primary_key=True)                 # identificador canônico (ex.: OBJ-SRV-001)
    tipo_objeto = Column(String(20), nullable=False)          # servico, processo ou atividade
    nome_canonico = Column(String(200), nullable=False)       # nome oficial no catálogo
    referencia = Column(String(100))                          # item da Carta de Serviços ou do Plano de Classificação
    ativo = Column(Boolean, nullable=False, default=True)


class UnidadeObjetoCatalogo(Base):
    """Vínculo curado entre uma Secretaria e um item do catálogo operacional.

    Na carga da PoC, vínculos e objetos são fictícios. Em produção, a fonte e a
    vigência permitirão saber por que o item aparece para determinada Secretaria.
    """
    __tablename__ = "unidade_objeto_catalogo"

    id = Column(Integer, primary_key=True)
    unidade_id = Column(String(50), ForeignKey("unidade.id"), nullable=False)
    objeto_id = Column(String(50), ForeignKey("objeto_catalogo.id"), nullable=False)
    papel = Column(String(20), nullable=False, default="RESPONSAVEL")
    fonte = Column(String(150), nullable=False)
    vigente_de = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    vigente_ate = Column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "papel IN ('RESPONSAVEL', 'PARTICIPANTE')",
            name="ck_unidade_objeto_papel",
        ),
        Index(
            "uq_unidade_objeto_vigente",
            "unidade_id",
            "objeto_id",
            unique=True,
            postgresql_where=(vigente_ate.is_(None)),
        ),
    )


class ObjetoContextoCatalogo(Base):
    """Contexto em que um item do catálogo pode iniciar um Registro.

    A relação é curada e versionável. Na PoC, todos os vínculos são fictícios;
    em produção, a fonte permite rastrear a decisão institucional.
    """
    __tablename__ = "objeto_contexto_catalogo"

    id = Column(Integer, primary_key=True)
    objeto_id = Column(String(50), ForeignKey("objeto_catalogo.id"), nullable=False)
    contexto_id = Column(String(20), ForeignKey("contexto_atuacao.id"), nullable=False)
    fonte = Column(String(150), nullable=False)
    vigente_de = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    vigente_ate = Column(DateTime(timezone=True))

    __table_args__ = (
        Index(
            "uq_objeto_contexto_catalogo_vigente",
            "objeto_id",
            "contexto_id",
            unique=True,
            postgresql_where=(vigente_ate.is_(None)),
        ),
    )


class FamiliaContexto(Base):
    """Família de contextos de atuação: o prefixo do código (TRIB, URB, RH...). DA-38, item 6.
    O mesmo objeto em dois contextos da MESMA família gera advertência (pede justificativa).
    Se a família estiver configurada como mutuamente exclusiva, em vez de advertência há bloqueio."""
    __tablename__ = "familia_contexto"

    id = Column(String(10), primary_key=True)                 # ex.: TRIB
    nome = Column(String(100), nullable=False)                # ex.: Tributação
    mutuamente_exclusiva = Column(Boolean, nullable=False, default=False)


class ContextoAtuacao(Base):
    """Catálogo de CONTEXTOS DE ATUAÇÃO (DA-38; antes chamado "de finalidades").
    Recorte administrativo e funcional em que o tratamento de um objeto é descrito.
    NÃO é a finalidade da LGPD (art. 6º, I), que é declarada no FORM 1.
    Na PoC, somente contextos fictícios."""
    __tablename__ = "contexto_atuacao"

    id = Column(String(20), primary_key=True)                 # ex.: CTX-TRIB-01
    familia_id = Column(String(10), ForeignKey("familia_contexto.id"), nullable=False)
    nome = Column(String(150), nullable=False)                # ex.: Gestão cadastral tributária
    descricao = Column(Text)
    ativo = Column(Boolean, nullable=False, default=True)     # desativado, nunca apagado


# Papéis de um objeto no Registro (DA-36, item 3). Os dois primeiros são o ASSUNTO e entram na trava.
PAPEIS_ASSUNTO = ("PRINCIPAL", "ABRANGIDO")
PAPEIS_CITADOS = ("APOIO", "RELACIONADO")


class RegistroObjeto(Base):
    """Vínculo entre um Registro e os objetos do catálogo (RF-PRC-13), com PAPEL.

    D1 — um contexto por Registro: o contexto aparece aqui só para a trava funcionar, e o banco
    garante que ele é SEMPRE o mesmo do Registro (chave estrangeira composta).
      - ASSUNTO (PRINCIPAL, ABRANGIDO): contexto obrigatório, igual ao do Registro;
      - CITADO (APOIO, RELACIONADO): contexto vazio — não ganha contexto naquele Registro.

    A TRAVA (DA-36 e DA-38), garantida pelo próprio banco:
      1. o mesmo objeto, no mesmo contexto, só pode ser ASSUNTO de UM Registro não cancelado;
      2. cada Registro tem exatamente UM objeto PRINCIPAL."""
    __tablename__ = "registro_objeto"

    id = Column(Integer, primary_key=True)
    registro_id = Column(String(36), ForeignKey("registro.id"), nullable=False)
    objeto_id = Column(String(50), ForeignKey("objeto_catalogo.id"), nullable=False)
    papel = Column(String(20), nullable=False)                # PRINCIPAL, ABRANGIDO, APOIO ou RELACIONADO
    contexto_atuacao_id = Column(String(20))                  # só para ASSUNTO; vazio para CITADO
    vinculado_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ativo = Column(Boolean, nullable=False, default=True)     # vira False quando o Registro é cancelado

    __table_args__ = (
        ForeignKeyConstraint(["registro_id", "contexto_atuacao_id"],
                             ["registro.id", "registro.contexto_atuacao_id"],
                             name="fk_vinculo_contexto_do_registro"),
        CheckConstraint(
            "(papel IN ('PRINCIPAL','ABRANGIDO') AND contexto_atuacao_id IS NOT NULL) OR "
            "(papel IN ('APOIO','RELACIONADO') AND contexto_atuacao_id IS NULL)",
            name="ck_papel_e_contexto"),
        Index("uq_objeto_contexto_assunto_ativo", "objeto_id", "contexto_atuacao_id", unique=True,
              postgresql_where=(ativo.is_(True) & papel.in_(PAPEIS_ASSUNTO))),
        Index("uq_um_principal_por_registro", "registro_id", unique=True,
              postgresql_where=(ativo.is_(True) & (papel == "PRINCIPAL"))),
    )


class Transversalidade(Base):
    """Declaração de transversalidade de um objeto DENTRO de uma família de contextos (D2).
    Alcance: objeto + família (não é global). Só a governança de proteção de dados (na PoC,
    o Encarregado) declara ou revoga. Enquanto vigente, resolve as advertências de família
    daquele objeto naquela família — sem afastar a trava nem os alertas.
    Encerrar é preencher vigente_ate; nunca apagar."""
    __tablename__ = "transversalidade"

    id = Column(Integer, primary_key=True)
    objeto_id = Column(String(50), ForeignKey("objeto_catalogo.id"), nullable=False)
    familia_id = Column(String(10), ForeignKey("familia_contexto.id"), nullable=False)
    fundamento = Column(Text, nullable=False)
    decidido_por = Column(String(50), nullable=False)         # a PESSOA com papel de governança
    vigente_de = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    vigente_ate = Column(DateTime(timezone=True))
    comando_id = Column(String(64), ForeignKey("comando.id"), nullable=False)  # o pedido que a declarou

    __table_args__ = (
        Index("uq_transversalidade_vigente", "objeto_id", "familia_id", unique=True,
              postgresql_where=(vigente_ate.is_(None))),
    )


class VersaoEsquema(Base):
    """Migrações já aplicadas a este banco (Etapa 2d): número, nome, quando e por quem.
    O aplicador (python -m migracoes.aplicar) só roda as que não estiverem aqui."""
    __tablename__ = "versao_esquema"

    numero = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    aplicada_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    aplicada_por = Column(String(50), nullable=False)


class BaseDados(Base):
    """Catálogo de BASES E CONJUNTOS DE DADOS: o terceiro eixo transversal (DA-38, item 7).
    Banco de dados, planilha, arquivo físico ou sistema. A base, enquanto ativo informacional,
    NÃO é assunto de Registro: as atividades que a criam, mantêm ou utilizam é que podem ser.
    Na PoC, somente bases fictícias."""
    __tablename__ = "base_dados"

    id = Column(String(20), primary_key=True)                 # ex.: BAS-001
    nome_canonico = Column(String(200), nullable=False)       # ex.: Cadastro imobiliário
    suporte = Column(String(30), nullable=False)              # banco, planilha, arquivo físico ou sistema
    ativo = Column(Boolean, nullable=False, default=True)


class ObjetoBase(Base):
    """Relação "utiliza" (muitos para muitos): a atividade ou o processo UTILIZA a base (DA-38, item 7).
    Com vigência: encerrar é preencher vigente_ate, nunca apagar."""
    __tablename__ = "objeto_base"

    id = Column(Integer, primary_key=True)
    objeto_id = Column(String(50), ForeignKey("objeto_catalogo.id"), nullable=False)
    base_id = Column(String(20), ForeignKey("base_dados.id"), nullable=False)
    vigente_de = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    vigente_ate = Column(DateTime(timezone=True))

    __table_args__ = (
        Index("uq_objeto_base_vigente", "objeto_id", "base_id", unique=True,
              postgresql_where=(vigente_ate.is_(None))),
    )


class Canal(Base):
    """Catálogo de CANAIS: as portas por onde o cidadão chega aos serviços (DA-36, item 6).
    O canal não faz parte da hierarquia serviço → processo → atividade: é uma dimensão transversal.
    Na PoC, somente canais fictícios."""
    __tablename__ = "canal"

    id = Column(String(50), primary_key=True)                 # identificador canônico (ex.: CNL-001)
    nome_canonico = Column(String(200), nullable=False)       # ex.: Balcão de atendimento
    ativo = Column(Boolean, nullable=False, default=True)     # desativado, nunca apagado


class ServicoCanal(Base):
    """Relação muitos para muitos entre serviço e canal (DA-36, item 6).
    Lida de um lado: o serviço É ATENDIDO PELO canal. Do outro: o canal ATENDE o serviço.
    Uma única relação, com vigência: encerrar é preencher vigente_ate, nunca apagar."""
    __tablename__ = "servico_canal"

    id = Column(Integer, primary_key=True)
    servico_id = Column(String(50), ForeignKey("objeto_catalogo.id"), nullable=False)
    canal_id = Column(String(50), ForeignKey("canal.id"), nullable=False)
    vigente_de = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    vigente_ate = Column(DateTime(timezone=True))             # vazio = ainda vigente
    observacao = Column(String(200))

    __table_args__ = (
        # o mesmo par serviço–canal não pode estar vigente duas vezes
        Index("uq_servico_canal_vigente", "servico_id", "canal_id", unique=True,
              postgresql_where=(vigente_ate.is_(None))),
    )
