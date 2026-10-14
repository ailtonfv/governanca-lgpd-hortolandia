# Camada de domínio: os dois livros com cadeia de hash (DA-26, DA-27).
#
#   Livro de atos do DOMÍNIO (tabela evento)      -> uma corrente por objeto  (ex.: REG-0003)
#   Livro de AUDITORIA (tabela evento_auditoria)  -> uma corrente por mês     (ex.: AUDITORIA-2026-10)
#
# Os dois usam o mesmo lacre: SHA-256 sobre um texto JSON canônico.
# O texto exato que foi lacrado fica guardado no próprio evento (payload_canonico).

import hashlib
import json
from datetime import datetime, timezone
from sqlalchemy import select
from app.modelos import Evento, EventoAuditoria

HASH_INICIAL = "0" * 64                            # o "elo zero": o primeiro evento não tem anterior
VERSAO_ESQUEMA_EVENTO = 1                          # formato dos eventos (DA-27, item 4)
VERSAO_ALGORITMO_HASH = "sha256-json-canonico-v1"  # como o lacre é calculado (DA-27, item 4)
VERSAO_REGRA_POC = "POC-1"                         # provisório: a tabela versao_regra chega na etapa 2

# Lista FECHADA dos campos que entram no lacre (DA-27, item 2).
CAMPOS_LACRADOS_DOMINIO = (
    "cadeia_tipo", "cadeia_id", "sequencia_cadeia", "registro_id", "ciclo_id",
    "tipo_evento", "codigo_evento", "comando_id", "ordem_no_comando",
    "ator_tipo", "ator_id", "em_nome_de", "ocorrido_em",
    "versao_regra", "versao_esquema_evento", "versao_algoritmo_hash",
    "conteudo", "hash_anterior",
)
CAMPOS_LACRADOS_AUDITORIA = (
    "segmento_id", "sequencia_segmento", "tipo_evento", "comando_id",
    "ator_tipo", "ator_id", "ocorrido_em",
    "versao_esquema_evento", "versao_algoritmo_hash",
    "conteudo", "hash_anterior",
)


# ---------------------------------------------------------------- ferramentas do lacre

def agora_utc():
    """Agora, no horário universal (UTC)."""
    return datetime.now(timezone.utc)


def data_em_texto(momento):
    """Data e hora em formato fixo, sempre UTC e com microssegundos. Ex.: 2026-10-12T18:05:03.123456Z"""
    return momento.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def texto_canonico(evento, campos):
    """Monta o texto que será lacrado: só os campos da lista, chaves em ordem, sem espaços."""
    pacote = {}
    for campo in campos:
        valor = getattr(evento, campo)
        if campo == "ocorrido_em":
            valor = data_em_texto(valor)
        pacote[campo] = valor
    return json.dumps(pacote, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def lacre(texto):
    """O lacre (hash SHA-256) de um texto."""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def selar_e_gravar(sessao, evento, campos):
    """Guarda o texto canônico, calcula o lacre e envia ao banco (dentro da transação)."""
    evento.payload_canonico = texto_canonico(evento, campos)
    evento.hash = lacre(evento.payload_canonico)
    sessao.add(evento)
    sessao.flush()
    return evento


# ---------------------------------------------------------------- livro de atos (domínio)

def registrar_evento(sessao, comando, cadeia_tipo, cadeia_id, tipo_evento, conteudo,
                     codigo_evento=None, ordem_no_comando=1, registro_id=None, ciclo_id=None,
                     em_nome_de=None, versao_regra=VERSAO_REGRA_POC,
                     versao_esquema_evento=VERSAO_ESQUEMA_EVENTO):
    """Acrescenta um ato ao fim da corrente do objeto. Quem praticou é quem fez o pedido (comando)."""
    ultimo = sessao.scalars(
        select(Evento)
        .where(Evento.cadeia_id == cadeia_id)
        .order_by(Evento.sequencia_cadeia.desc())
        .limit(1)
    ).first()

    evento = Evento(
        cadeia_tipo=cadeia_tipo,
        cadeia_id=cadeia_id,
        sequencia_cadeia=1 if ultimo is None else ultimo.sequencia_cadeia + 1,
        registro_id=registro_id,
        ciclo_id=ciclo_id,
        tipo_evento=tipo_evento,
        codigo_evento=codigo_evento,
        comando_id=comando.id,
        ordem_no_comando=ordem_no_comando,
        ator_tipo=comando.ator_tipo,
        ator_id=comando.ator_id,
        em_nome_de=em_nome_de,
        ocorrido_em=agora_utc(),
        versao_regra=versao_regra,
        versao_esquema_evento=versao_esquema_evento,
        versao_algoritmo_hash=VERSAO_ALGORITMO_HASH,
        conteudo=conteudo,
        hash_anterior=HASH_INICIAL if ultimo is None else ultimo.hash,
    )
    return selar_e_gravar(sessao, evento, CAMPOS_LACRADOS_DOMINIO)


# ---------------------------------------------------------------- livro de auditoria

def segmento_do_mes(momento):
    """Nome do segmento mensal de auditoria (mês em UTC). Ex.: AUDITORIA-2026-10"""
    return f"AUDITORIA-{momento.astimezone(timezone.utc):%Y-%m}"


def registrar_auditoria(sessao, tipo_evento, ator_tipo, ator_id, conteudo, comando_id=None):
    """Acrescenta um evento ao segmento de auditoria do mês (consulta, tentativa negada...)."""
    momento = agora_utc()
    segmento = segmento_do_mes(momento)
    ultimo = sessao.scalars(
        select(EventoAuditoria)
        .where(EventoAuditoria.segmento_id == segmento)
        .order_by(EventoAuditoria.sequencia_segmento.desc())
        .limit(1)
    ).first()

    evento = EventoAuditoria(
        segmento_id=segmento,
        sequencia_segmento=1 if ultimo is None else ultimo.sequencia_segmento + 1,
        tipo_evento=tipo_evento,
        comando_id=comando_id,
        ator_tipo=ator_tipo,
        ator_id=ator_id,
        ocorrido_em=momento,
        versao_esquema_evento=VERSAO_ESQUEMA_EVENTO,
        versao_algoritmo_hash=VERSAO_ALGORITMO_HASH,
        conteudo=conteudo,
        hash_anterior=HASH_INICIAL if ultimo is None else ultimo.hash,
    )
    return selar_e_gravar(sessao, evento, CAMPOS_LACRADOS_AUDITORIA)


# ---------------------------------------------------------------- verificação

def conferir(eventos, campos, nome_posicao):
    """Confere uma corrente, evento por evento, com quatro perguntas."""
    anterior = HASH_INICIAL
    for esperado, ev in enumerate(eventos, start=1):
        n = getattr(ev, nome_posicao)
        if n != esperado:                                    # 1. a numeração está completa?
            return False, f"SEQUÊNCIA INTERROMPIDA: esperado {esperado}, encontrado {n}"
        if ev.hash_anterior != anterior:                     # 2. o elo com o anterior está certo?
            return False, f"ELO QUEBRADO antes do evento {n}"
        if texto_canonico(ev, campos) != ev.payload_canonico:  # 3. os campos batem com o texto lacrado?
            return False, f"CAMPOS ALTERADOS no evento {n}: não conferem com o texto lacrado"
        if lacre(ev.payload_canonico) != ev.hash:            # 4. o lacre bate com o texto?
            return False, f"LACRE VIOLADO no evento {n}"
        anterior = ev.hash
    return True, f"corrente íntegra ({len(eventos)} eventos)"


def verificar_cadeia(sessao, cadeia_id):
    """Relê do banco a corrente de um objeto e confere."""
    eventos = sessao.scalars(
        select(Evento).where(Evento.cadeia_id == cadeia_id).order_by(Evento.sequencia_cadeia)
    ).all()
    return conferir(eventos, CAMPOS_LACRADOS_DOMINIO, "sequencia_cadeia")


def verificar_segmento(sessao, segmento_id):
    """Relê do banco um segmento mensal de auditoria e confere."""
    eventos = sessao.scalars(
        select(EventoAuditoria)
        .where(EventoAuditoria.segmento_id == segmento_id)
        .order_by(EventoAuditoria.sequencia_segmento)
    ).all()
    return conferir(eventos, CAMPOS_LACRADOS_AUDITORIA, "sequencia_segmento")
