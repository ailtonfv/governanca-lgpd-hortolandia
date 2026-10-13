# Camada de domínio: o ciclo de vida do Registro (SAD 04 e SAD 05).
#
# Regra de ouro (DA-26, item 5): cada ato acontece numa transação só.
# O ato (evento), o pedido (comando) e os resumos (projeções) são gravados juntos, ou nada é gravado.

import uuid
from datetime import datetime, timezone
from sqlalchemy import select, func
from app.modelos import Comando, Conta, Registro, Ciclo, Instrumento
from app.eventos import registrar_evento, registrar_auditoria
from app.permissoes import tem_papel

TIPOS_OBJETO = {"processo", "atividade", "servico"}


def proximo_codigo_lgpd(sessao):
    """Gera o próximo código humano do ano. Ex.: LGPD-2026-00001 (formato ainda A VALIDAR, SAD 05, 5.1)."""
    ano = datetime.now(timezone.utc).year
    prefixo = f"LGPD-{ano}-"
    quantos = sessao.scalar(select(func.count()).select_from(Registro)
                            .where(Registro.codigo_lgpd.like(prefixo + "%")))
    return f"{prefixo}{quantos + 1:05d}"


def criar_registro(sessao, conta_id, unidade_id, tipo_objeto, titulo_objeto, comando_id=None):
    """Ato G1 — Criar Registro (SAD 04, seção 7).

    Quem pode: pessoa com papel de elaborador na unidade (provisório da PoC).
    O que nasce junto: o Registro, o ciclo 1, o FORM 1 (não iniciado) e o ato no livro.
    Devolve (registro ou None, motivo).
    """
    # 1. pedido repetido? devolve o mesmo resultado
    if comando_id is not None:
        anterior = sessao.get(Comando, comando_id)
        if anterior is not None:
            return sessao.get(Registro, anterior.resultado.get("registro_id")), "pedido repetido"

    # 2. portões
    conta = sessao.get(Conta, conta_id)
    motivo = None
    if conta is None or not conta.ativa:
        motivo = "conta inexistente ou desativada"
    elif tipo_objeto not in TIPOS_OBJETO:
        motivo = f"tipo de objeto inválido: {tipo_objeto}"
    elif not tem_papel(sessao, conta.pessoa_id, unidade_id, {"elaborador"}):
        motivo = "a pessoa não tem papel de elaborador nesta unidade"

    pessoa_id = conta.pessoa_id if conta is not None else None
    comando = Comando(id=comando_id or str(uuid.uuid4()), tipo="criar_registro",
                      ator_tipo="pessoa" if pessoa_id else "desconhecido",
                      ator_id=pessoa_id or conta_id, conta_id=conta_id)
    sessao.add(comando)
    sessao.flush()

    if motivo is not None:                       # negado: vai para a auditoria
        registrar_auditoria(sessao, "tentativa_negada", comando.ator_tipo, comando.ator_id,
                            {"acao_tentada": "criar_registro", "objeto": unidade_id,
                             "conta_id": conta_id, "motivo": motivo}, comando_id=comando.id)
        comando.resultado = {"permitido": False, "motivo": motivo}
        sessao.flush()
        return None, motivo

    # 3. nasce o Registro, com o ciclo 1 e o FORM 1
    registro = Registro(id=str(uuid.uuid4()), codigo_lgpd=proximo_codigo_lgpd(sessao),
                        tipo_objeto=tipo_objeto, titulo_objeto=titulo_objeto,
                        unidade_principal_atual_id=unidade_id, criado_por=pessoa_id,
                        ciclo_atual=1, estado_atual="em_andamento", sequencia_atual=0)
    sessao.add(registro)
    sessao.flush()
    ciclo = Ciclo(registro_id=registro.id, numero=1, situacao="ativo")
    sessao.add(ciclo)
    sessao.add(Instrumento(id=str(uuid.uuid4()), registro_id=registro.id,
                           tipo_instrumento="FORM1", estado_instrumento="nao_iniciado"))
    sessao.flush()

    # 4. o ato no livro (a corrente do Registro usa o codigo_lgpd como nome)
    evento = registrar_evento(sessao, comando, "registro", registro.codigo_lgpd, "criar_registro",
                              {"tipo_objeto": tipo_objeto, "titulo_objeto": titulo_objeto,
                               "unidade_principal": unidade_id, "conta_id": conta_id},
                              codigo_evento="G1", registro_id=registro.id, ciclo_id=ciclo.id)

    # 5. projeções atualizadas na mesma transação
    ciclo.evento_inicio_id = evento.id
    registro.sequencia_atual = evento.sequencia_cadeia
    comando.resultado = {"permitido": True, "motivo": "permitido", "registro_id": registro.id}
    sessao.flush()
    return registro, "permitido"
