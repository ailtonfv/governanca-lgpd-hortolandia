# Carga FICTÍCIA dos catálogos (O-80, DA-36, DA-38):
#   operacional (serviço, processo, atividade), canais, contextos de atuação e famílias,
#   bases e conjuntos de dados, com as relações "atendido por" e "utiliza".
# O identificador canônico (id) é o que define a equivalência; o nome é só para leitura.

from sqlalchemy import select
from app.modelos import (ObjetoCatalogo, UnidadeObjetoCatalogo, ObjetoContextoCatalogo,
                         Canal, ServicoCanal, FamiliaContexto, ContextoAtuacao,
                         BaseDados, ObjetoBase)
from carga_ficticia.seguranca import validar_ausencia_de_identificadores

OBJETOS = [
    # (id canônico,   tipo,        nome canônico)
    ("OBJ-SRV-001", "servico",   "2ª via do IPTU (fictício)"),
    ("OBJ-SRV-002", "servico",   "Certidão de débitos (fictício)"),
    ("OBJ-PRC-001", "processo",  "Lançamento e cobrança do IPTU (fictício)"),
    ("OBJ-ATV-001", "atividade", "Cálculo do valor venal (fictício)"),
    ("OBJ-ATV-002", "atividade", "Emissão dos carnês (fictício)"),
    ("OBJ-SRV-010", "servico",   "Atendimento ao contribuinte (fictício)"),   # mesmo nome,
    ("OBJ-PRC-010", "processo",  "Atendimento ao contribuinte (fictício)"),   # tipo diferente
    ("OBJ-ATV-020", "atividade", "Gerir e manter o Cadastro imobiliário (fictício)"),
    ("OBJ-SRV-900", "servico",   "Serviço fictício de demonstração"),
    ("OBJ-SRV-901", "servico",   "Outro serviço fictício de demonstração"),
    ("OBJ-SRV-902", "servico",   "Serviço financeiro fictício de demonstração"),
    ("OBJ-SRV-020", "servico",   "Fornecimento de medicamento de alto custo (fictício)"),
]

# Relações estritamente demonstrativas da PoC. Não afirmam a competência real das
# Secretarias: o catálogo definitivo virá dos FORMs e das fontes oficiais, com curadoria.
# (unidade, objeto, papel)
OBJETOS_POR_UNIDADE = [
    *(("UNID-NORTE", oid, "RESPONSAVEL") for oid, _, _ in OBJETOS if oid not in {"OBJ-SRV-902", "OBJ-SRV-020"}),
    ("UNID-SUL", "OBJ-ATV-020", "RESPONSAVEL"),
    ("UNID-SUL", "OBJ-PRC-001", "RESPONSAVEL"),
    ("UNID-SUL", "OBJ-SRV-902", "RESPONSAVEL"),
    ("SEC-SAUDE", "OBJ-SRV-020", "RESPONSAVEL"),
]

CANAIS = [
    ("CNL-001", "Balcão de atendimento (fictício)"),
    ("CNL-002", "Portal da Prefeitura (fictício)"),
    ("CNL-003", "Telefone (fictício)"),
]

# (serviço, canal): o serviço é atendido pelo canal
ATENDIMENTOS = [
    ("OBJ-SRV-001", "CNL-001"),   # 2ª via do IPTU — balcão
    ("OBJ-SRV-001", "CNL-002"),   # 2ª via do IPTU — portal
    ("OBJ-SRV-002", "CNL-001"),   # Certidão de débitos — balcão
]

# Nenhuma família é mutuamente exclusiva por enquanto (DA-38, item 6)
FAMILIAS = [
    ("TRIB", "Tributação"), ("URB", "Urbanismo e território"), ("ATD", "Atendimento ao cidadão"),
    ("TRA", "Transparência"), ("RH", "Gestão de pessoas"), ("EDU", "Educação"), ("SAU", "Saúde"),
    ("SOC", "Assistência social"), ("FIS", "Fiscalização"), ("COM", "Contratações"),
    ("MOB", "Mobilidade"), ("AMB", "Meio ambiente"), ("SEG", "Segurança patrimonial"),
    ("JUR", "Jurídico"),
]

CONTEXTOS = [
    ("CTX-TRIB-01", "Gestão cadastral tributária", "Manutenção de cadastros utilizados na constituição e administração de tributos municipais"),
    ("CTX-TRIB-02", "Lançamento tributário", "Apuração e constituição de créditos tributários municipais"),
    ("CTX-TRIB-03", "Arrecadação e cobrança tributária", "Emissão de guias, pagamentos, parcelamentos e cobrança administrativa de tributos"),
    ("CTX-URB-01", "Planejamento territorial", "Uso de informações para planejamento urbano, territorial e definição de políticas de ocupação"),
    ("CTX-URB-02", "Licenciamento de obras", "Análise, autorização e acompanhamento de obras e edificações"),
    ("CTX-URB-03", "Regularização fundiária", "Identificação e regularização jurídica, urbanística e social de imóveis e ocupações"),
    ("CTX-ATD-01", "Gestão do atendimento ao cidadão", "Organização de filas, senhas, agendamentos, protocolos e histórico do atendimento"),
    ("CTX-ATD-02", "Gestão de manifestações", "Recebimento e tratamento de reclamações, sugestões, elogios, denúncias e solicitações"),
    ("CTX-TRA-01", "Transparência e acesso à informação", "Atendimento de pedidos de acesso à informação e acompanhamento de respostas"),
    ("CTX-RH-01", "Administração funcional", "Gestão de vínculos, lotações, frequência, férias, remuneração e demais informações funcionais"),
    ("CTX-RH-02", "Saúde ocupacional", "Acompanhamento da saúde, segurança e aptidão laboral dos agentes públicos"),
    ("CTX-EDU-01", "Gestão da vida escolar", "Matrícula, frequência, avaliação, transferência e histórico de estudantes"),
    ("CTX-SAU-01", "Assistência à saúde", "Prestação e acompanhamento de atendimentos e cuidados de saúde"),
    ("CTX-SOC-01", "Proteção e assistência social", "Atendimento, acompanhamento e concessão de benefícios socioassistenciais"),
    ("CTX-FIS-01", "Fiscalização administrativa", "Planejamento, execução e registro de ações de fiscalização municipal"),
    ("CTX-COM-01", "Contratações públicas", "Planejamento, seleção de fornecedores, contratação e gestão contratual"),
    ("CTX-MOB-01", "Mobilidade e trânsito", "Gestão da circulação, transporte, fiscalização e segurança viária"),
    ("CTX-AMB-01", "Gestão e fiscalização ambiental", "Licenciamento, monitoramento e fiscalização de atividades com impacto ambiental"),
    ("CTX-SEG-01", "Segurança patrimonial", "Controle de acesso, vigilância e proteção de instalações e bens municipais"),
    ("CTX-JUR-01", "Representação e defesa jurídica", "Gestão de processos judiciais, administrativos e atividades de representação do Município"),
]

# Relações de demonstração necessárias aos percursos da PoC. Não representam
# competência ou classificação oficial da Prefeitura.
CONTEXTOS_POR_OBJETO = [
    ("OBJ-ATV-020", "CTX-TRIB-01"),
    ("OBJ-ATV-020", "CTX-TRIB-03"),
    ("OBJ-ATV-020", "CTX-URB-01"),
    ("OBJ-ATV-020", "CTX-URB-02"),
    ("OBJ-ATV-020", "CTX-URB-03"),
    ("OBJ-PRC-001", "CTX-TRIB-02"),
    ("OBJ-SRV-001", "CTX-TRIB-03"),
    ("OBJ-SRV-002", "CTX-TRIB-03"),
    ("OBJ-SRV-010", "CTX-TRIB-03"),
    ("OBJ-PRC-010", "CTX-TRIB-03"),
    ("OBJ-ATV-001", "CTX-TRIB-02"),
    ("OBJ-ATV-001", "CTX-TRIB-03"),
    ("OBJ-ATV-002", "CTX-TRIB-03"),
    ("OBJ-SRV-900", "CTX-TRIB-01"),
    ("OBJ-SRV-900", "CTX-TRIB-03"),
    ("OBJ-SRV-900", "CTX-URB-01"),
    ("OBJ-SRV-901", "CTX-ATD-01"),
    ("OBJ-SRV-902", "CTX-COM-01"),
    ("OBJ-SRV-020", "CTX-SAU-01"),
]

BASES = [
    # (id,       nome,                                         suporte)
    ("BAS-001", "Cadastro imobiliário (fictício)",            "sistema"),
    ("BAS-002", "Cadastro funcional de servidores (fictício)", "banco de dados"),
]

# (objeto, base): o objeto UTILIZA a base
USOS = [
    ("OBJ-ATV-020", "BAS-001"),   # Gerir e manter o Cadastro imobiliário
    ("OBJ-PRC-001", "BAS-001"),   # Lançamento do IPTU
]


def semear(sessao):
    """Acrescenta o que ainda não existe. Devolve quantos itens novos foram criados."""
    # Os catálogos podem conter nomes públicos de órgãos e descrições funcionais,
    # mas nunca identificadores de pessoas. A barreira roda antes do primeiro INSERT.
    validar_ausencia_de_identificadores(
        "catálogos",
        {
            "objetos": OBJETOS,
            "objetos_por_unidade": OBJETOS_POR_UNIDADE,
            "canais": CANAIS,
            "atendimentos": ATENDIMENTOS,
            "familias": FAMILIAS,
            "contextos": CONTEXTOS,
            "contextos_por_objeto": CONTEXTOS_POR_OBJETO,
            "bases": BASES,
            "usos": USOS,
        },
    )
    novos = 0
    for oid, tipo, nome in OBJETOS:
        if sessao.get(ObjetoCatalogo, oid) is None:
            sessao.add(ObjetoCatalogo(id=oid, tipo_objeto=tipo, nome_canonico=nome)); novos += 1
    sessao.flush()
    for unidade_id, objeto_id, papel in OBJETOS_POR_UNIDADE:
        existe = sessao.scalars(select(UnidadeObjetoCatalogo).where(
            UnidadeObjetoCatalogo.unidade_id == unidade_id,
            UnidadeObjetoCatalogo.objeto_id == objeto_id,
            UnidadeObjetoCatalogo.vigente_ate.is_(None),
        )).first()
        if existe is None:
            sessao.add(UnidadeObjetoCatalogo(
                unidade_id=unidade_id,
                objeto_id=objeto_id,
                papel=papel,
                fonte="carga fictícia da PoC",
            ))
            novos += 1
    for cid, nome in CANAIS:
        if sessao.get(Canal, cid) is None:
            sessao.add(Canal(id=cid, nome_canonico=nome)); novos += 1
    for fid, nome in FAMILIAS:
        if sessao.get(FamiliaContexto, fid) is None:
            sessao.add(FamiliaContexto(id=fid, nome=nome, mutuamente_exclusiva=False)); novos += 1
    for bid, nome, suporte in BASES:
        if sessao.get(BaseDados, bid) is None:
            sessao.add(BaseDados(id=bid, nome_canonico=nome, suporte=suporte)); novos += 1
    sessao.flush()
    for cid, nome, descricao in CONTEXTOS:
        if sessao.get(ContextoAtuacao, cid) is None:
            sessao.add(ContextoAtuacao(id=cid, familia_id=cid.split("-")[1], nome=nome,
                                       descricao=descricao)); novos += 1
    sessao.flush()
    for objeto_id, contexto_id in CONTEXTOS_POR_OBJETO:
        existe = sessao.scalars(select(ObjetoContextoCatalogo).where(
            ObjetoContextoCatalogo.objeto_id == objeto_id,
            ObjetoContextoCatalogo.contexto_id == contexto_id,
            ObjetoContextoCatalogo.vigente_ate.is_(None),
        )).first()
        if existe is None:
            sessao.add(ObjetoContextoCatalogo(
                objeto_id=objeto_id,
                contexto_id=contexto_id,
                fonte="carga fictícia da PoC",
            ))
            novos += 1
    for sid, cid in ATENDIMENTOS:
        if sessao.scalars(select(ServicoCanal).where(ServicoCanal.servico_id == sid, ServicoCanal.canal_id == cid,
                                                     ServicoCanal.vigente_ate.is_(None))).first() is None:
            sessao.add(ServicoCanal(servico_id=sid, canal_id=cid)); novos += 1
    for oid, bid in USOS:
        if sessao.scalars(select(ObjetoBase).where(ObjetoBase.objeto_id == oid, ObjetoBase.base_id == bid,
                                                   ObjetoBase.vigente_ate.is_(None))).first() is None:
            sessao.add(ObjetoBase(objeto_id=oid, base_id=bid)); novos += 1
    sessao.flush()
    return novos
