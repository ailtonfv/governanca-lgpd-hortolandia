# Camada de domínio: o PEDIDO IDEMPOTENTE (DA-26, item 3), em versão estrita (Etapa 2d).
#
# Todo ato que altera dados chega com uma chave (comando_id) escolhida por quem pede.
#   - sem chave                          -> recusado
#   - chave nova                         -> o pedido é processado
#   - mesma chave + mesmos parâmetros    -> devolve o RESULTADO ORIGINAL, idêntico, com reexecutado = True
#   - mesma chave + parâmetros diferentes -> recusado como reutilização indevida da chave
#   - dois pedidos com a mesma chave ao mesmo tempo -> o banco aceita só um (chave primária);
#     o outro relê o comando gravado e responde como reexecução
#
# Para saber se os parâmetros são "os mesmos", eles são lacrados com o mesmo método dos eventos
# (JSON canônico + SHA-256, DA-27) e o lacre fica guardado no comando (hash_parametros).

import hashlib
import json
from sqlalchemy.exc import IntegrityError
from app.modelos import Comando
from app.eventos import registrar_auditoria


class ErroDeIntegridadeInesperado(Exception):
    """Uma recusa do banco que o código não sabe interpretar: é defeito, não decisão de negócio."""


def nome_da_restricao(erro):
    """Qual regra do banco recusou a gravação? (o nome vem do próprio PostgreSQL)"""
    diag = getattr(getattr(erro, "orig", None), "diag", None)
    return getattr(diag, "constraint_name", None)


def lacre_dos_parametros(tipo, parametros):
    """Lacre (SHA-256) do texto canônico do pedido: tipo + parâmetros, chaves em ordem, sem espaços."""
    texto = json.dumps({"tipo": tipo, "parametros": parametros},
                       sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _resposta_a_repeticao(sessao, existente, tipo, lacre, ator_tipo, ator_id):
    """O comando já existe: devolve o resultado original ou recusa a reutilização da chave."""
    if existente.hash_parametros is not None and existente.hash_parametros != lacre:
        motivo = "reutilização indevida da chave do pedido: mesmo comando_id com conteúdo diferente"
        registrar_auditoria(sessao, "tentativa_negada", ator_tipo, ator_id,
                            {"acao_tentada": tipo, "motivo": motivo}, comando_id=existente.id)
        return {"permitido": False, "motivo": motivo, "reexecutado": False}
    # mesmos parâmetros (ou comando antigo, sem lacre: legado, aceito sem conferência)
    return dict(existente.resultado or {}, reexecutado=True)


def abrir_comando(sessao, comando_id, tipo, parametros, ator_tipo, ator_id, conta_id=None):
    """Registra o pedido. Devolve (comando, None) se for novo, ou (None, resposta) se não deve ser
    processado de novo (reexecução, reutilização indevida ou falta de chave)."""
    if not comando_id or not str(comando_id).strip():
        motivo = "pedido sem comando_id: todo ato que altera dados exige a chave do pedido"
        registrar_auditoria(sessao, "tentativa_negada", ator_tipo, ator_id,
                            {"acao_tentada": tipo, "motivo": motivo})
        return None, {"permitido": False, "motivo": motivo, "reexecutado": False}

    lacre = lacre_dos_parametros(tipo, parametros)
    existente = sessao.get(Comando, comando_id)
    if existente is not None:
        return None, _resposta_a_repeticao(sessao, existente, tipo, lacre, ator_tipo, ator_id)

    comando = Comando(id=comando_id, tipo=tipo, ator_tipo=ator_tipo, ator_id=ator_id,
                      conta_id=conta_id, hash_parametros=lacre)
    try:
        with sessao.begin_nested():                 # se o banco recusar, só isto é desfeito
            sessao.add(comando)
            sessao.flush()
    except IntegrityError as erro:
        if nome_da_restricao(erro) != "comando_pkey":
            raise
        # outro pedido com a mesma chave foi gravado primeiro: relê e responde como repetição
        existente = sessao.get(Comando, comando_id, populate_existing=True)
        if existente is None:
            raise ErroDeIntegridadeInesperado("comando_pkey recusou, mas o comando não foi encontrado")
        return None, _resposta_a_repeticao(sessao, existente, tipo, lacre, ator_tipo, ator_id)
    return comando, None


def fechar_comando(comando, resultado):
    """Guarda o resultado original do pedido e devolve-o, marcado como não reexecutado."""
    comando.resultado = resultado
    return dict(resultado, reexecutado=False)
