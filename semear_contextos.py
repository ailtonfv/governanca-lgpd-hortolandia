# Catálogo FICTÍCIO de contextos de atuação e suas famílias (DA-38; texto do Encarregado, 13/10/2026).
# Contexto de atuação NÃO é a finalidade da LGPD: é o recorte administrativo e funcional
# em que o tratamento de um objeto é descrito. O prefixo do código forma a família.
# Pode ser rodado mais de uma vez: só acrescenta o que ainda não existe.

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import FamiliaContexto, ContextoAtuacao

# (família, nome). Nenhuma família é mutuamente exclusiva por enquanto (DA-38, item 6).
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

with Session(motor) as sessao, sessao.begin():
    novas = novos = 0
    for fid, nome in FAMILIAS:
        if sessao.get(FamiliaContexto, fid) is None:
            sessao.add(FamiliaContexto(id=fid, nome=nome, mutuamente_exclusiva=False))
            novas += 1
    sessao.flush()
    for cid, nome, descricao in CONTEXTOS:
        if sessao.get(ContextoAtuacao, cid) is None:
            familia = cid.split("-")[1]              # CTX-TRIB-01 -> TRIB
            sessao.add(ContextoAtuacao(id=cid, familia_id=familia, nome=nome, descricao=descricao))
            novos += 1
print(f"Famílias novas: {novas}. Contextos novos: {novos}.\n")

with Session(motor) as sessao:
    for c in sessao.scalars(select(ContextoAtuacao).order_by(ContextoAtuacao.id)):
        print(f"  {c.id:<12} [{c.familia_id:<4}] {c.nome}")
