# Camada de domínio: quem pode fazer o quê (SAD 03) e a segregação de funções (ADR 000, O-66).
#
# Regra central: quem submeteu uma versão NÃO pode analisá-la, validá-la nem devolvê-la.
# A comparação é feita pela PESSOA, nunca pela conta: a Pessoa A não escapa da regra
# trocando da conta A1 para a A2.
#
# Todo pedido vira um COMANDO (DA-26, item 3): se o mesmo pedido chegar duas vezes,
# o sistema devolve a resposta original e não grava nada de novo.
# Ato permitido -> livro de atos do domínio. Tentativa negada -> livro de auditoria do mês (DA-26, item 4).

import uuid
from sqlalchemy import select
from app.modelos import Comando, Conta, Designacao, Evento
from app.eventos import registrar_evento, registrar_auditoria

# Qual papel é exigido para cada ação (provisório da PoC, a partir da matriz do SAD 03)
PAPEIS_EXIGIDOS = {
    "submeter": {"elaborador"},
    "analisar": {"analista"},
    "devolver": {"analista", "validador"},
    "validar": {"validador"},
}

# Ações sujeitas à segregação: o autor da submissão não pode praticá-las
ACOES_SEGREGADAS = {"analisar", "devolver", "validar"}

# Como cada ação aparece no livro de atos: nome do evento e código da transição (catálogo do SAD 05 / SAD 04)
EVENTO_DA_ACAO = {
    "submeter": ("submeter", "I3"),
    "analisar": ("iniciar_analise", "I13"),
    "devolver": ("devolver", "I6"),
    "validar": ("validar", "I5"),
}


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
        .where(Evento.cadeia_id == cadeia_id, Evento.tipo_evento == "submeter")
        .order_by(Evento.sequencia_cadeia.desc())
        .limit(1)
    ).first()
    return None if evento is None else evento.ator_id


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


def executar_acao(sessao, conta_id, cadeia_id, unidade_id, acao, conteudo=None, comando_id=None):
    """Recebe um pedido, decide e registra. Devolve (permitido, motivo, repetido).

    - Pedido repetido (mesmo comando_id): devolve a resposta original, sem gravar nada.
    - Permitido: grava o ato no livro de atos do objeto.
    - Negado: grava a tentativa no livro de auditoria do mês.
    """
    # 1. o pedido já foi atendido antes?
    if comando_id is not None:
        anterior = sessao.get(Comando, comando_id)
        if anterior is not None:
            return anterior.resultado["permitido"], anterior.resultado["motivo"], True

    # 2. decide
    permitido, motivo, pessoa_id = verificar_acao(sessao, conta_id, cadeia_id, unidade_id, acao)

    # 3. registra o pedido (quem pediu é a PESSOA; a conta fica só como informação)
    if pessoa_id is None:
        ator_tipo, ator_id = "desconhecido", conta_id   # conta inexistente: não há pessoa a apontar
    else:
        ator_tipo, ator_id = "pessoa", pessoa_id
    comando = Comando(id=comando_id or str(uuid.uuid4()), tipo=acao,
                      ator_tipo=ator_tipo, ator_id=ator_id, conta_id=conta_id)
    sessao.add(comando)
    sessao.flush()

    # 4. grava no livro certo
    if permitido:
        tipo_evento, codigo = EVENTO_DA_ACAO[acao]
        registrar_evento(sessao, comando, "registro", cadeia_id, tipo_evento,
                         dict(conteudo or {}, conta_id=conta_id), codigo_evento=codigo)
    else:
        registrar_auditoria(sessao, "tentativa_negada", ator_tipo, ator_id, {
            "acao_tentada": acao,
            "objeto": cadeia_id,
            "conta_id": conta_id,
            "motivo": motivo,
        }, comando_id=comando.id)

    # 5. guarda a resposta, para devolver igual se o pedido se repetir
    comando.resultado = {"permitido": permitido, "motivo": motivo}
    sessao.flush()
    return permitido, motivo, False
