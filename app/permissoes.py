# Camada de domínio: quem pode fazer o quê (SAD 03) e a segregação de funções (ADR 000, O-66).
#
# Regra central: quem submeteu uma versão NÃO pode analisá-la, validá-la nem devolvê-la.
# A comparação é feita pela PESSOA, nunca pela conta: a Pessoa A não escapa da regra
# trocando da conta A1 para a A2.
#
# Toda tentativa negada vira um evento de AUDITORIA (DA-26), numa corrente mensal (DA-27).

from datetime import date
from sqlalchemy import select
from app.modelos import Conta, Designacao, Evento
from app.eventos import registrar_evento

# Qual papel é exigido para cada ação (provisório da PoC, a partir da matriz do SAD 03)
PAPEIS_EXIGIDOS = {
    "submeter": {"elaborador"},
    "analisar": {"analista"},
    "devolver": {"analista", "validador"},
    "validar": {"validador"},
}

# Ações sujeitas à segregação: o autor da submissão não pode praticá-las
ACOES_SEGREGADAS = {"analisar", "devolver", "validar"}


def obter_conta(sessao, conta_id):
    """Busca a conta; a pessoa dona dela está em conta.pessoa_id."""
    conta = sessao.get(Conta, conta_id)
    return conta


def tem_papel(sessao, pessoa_id, unidade_id, papeis):
    """A pessoa tem, nesta unidade, ao menos um dos papéis exigidos?"""
    encontrada = sessao.scalars(
        select(Designacao).where(
            Designacao.pessoa_id == pessoa_id,
            Designacao.unidade_id == unidade_id,
            Designacao.papel.in_(papeis),
            Designacao.ativa.is_(True),
        )
    ).first()
    return encontrada is not None


def autor_da_submissao(sessao, cadeia_id):
    """Quem submeteu a versão? Lido do próprio livro de atos (o último 'submeter' da corrente)."""
    evento = sessao.scalars(
        select(Evento)
        .where(Evento.cadeia_id == cadeia_id, Evento.codigo_evento == "submeter")
        .order_by(Evento.sequencia_cadeia.desc())
        .limit(1)
    ).first()
    return None if evento is None else evento.pessoa_id


def verificar_acao(sessao, conta_id, cadeia_id, unidade_id, acao):
    """Decide se a ação é permitida. Devolve (permitido, motivo, pessoa_id)."""
    conta = obter_conta(sessao, conta_id)
    if conta is None:
        return False, "conta inexistente", None
    if not conta.ativa:
        return False, "conta desativada", conta.pessoa_id

    pessoa_id = conta.pessoa_id
    if not tem_papel(sessao, pessoa_id, unidade_id, PAPEIS_EXIGIDOS[acao]):
        return False, f"a pessoa não tem papel para '{acao}' nesta unidade", pessoa_id

    if acao in ACOES_SEGREGADAS and autor_da_submissao(sessao, cadeia_id) == pessoa_id:
        return False, "segregação de funções: a pessoa é autora da submissão", pessoa_id

    return True, "permitido", pessoa_id


def executar_acao(sessao, conta_id, cadeia_id, unidade_id, acao, conteudo=None):
    """Verifica e, se permitido, registra a ação no livro de atos do objeto.
    Se negado, registra a tentativa na corrente de auditoria do mês."""
    permitido, motivo, pessoa_id = verificar_acao(sessao, conta_id, cadeia_id, unidade_id, acao)
    if permitido:
        registrar_evento(sessao, cadeia_id, acao, pessoa_id,
                         dict(conteudo or {}, conta_id=conta_id))
    else:
        cadeia_auditoria = f"AUDITORIA-{date.today():%Y-%m}"
        registrar_evento(sessao, cadeia_auditoria, "acesso_negado", pessoa_id or "DESCONHECIDA", {
            "acao_tentada": acao,
            "objeto": cadeia_id,
            "conta_id": conta_id,
            "motivo": motivo,
        })
    return permitido, motivo
