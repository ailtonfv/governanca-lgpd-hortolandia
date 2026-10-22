"""POC-TS-009: ensaio de volume, integridade e reconstrução.

Este programa recria EXCLUSIVAMENTE o banco cujo nome termina em ``_teste``.
Ele gera 1.000 Registros sintéticos com 50 eventos cada, verifica todas as
cadeias e reconstrói uma amostra a partir do livro de atos.
"""

import argparse
import json
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from app.banco import motor
from app.eventos import (CAMPOS_LACRADOS_DOMINIO, HASH_INICIAL,
                         VERSAO_ALGORITMO_HASH, conferir, lacre,
                         texto_canonico)
from app.modelos import Base, Comando, Evento, Registro
from carga_ficticia import catalogos, pessoas


TOTAL_PADRAO_REGISTROS = 1_000
EVENTOS_PADRAO_POR_REGISTRO = 50
TAMANHO_PADRAO_AMOSTRA = 25


def argumentos():
    parser = argparse.ArgumentParser(description="Executa o ensaio formal POC-TS-009.")
    parser.add_argument("--executar", action="store_true",
                        help="confirma a recriação do banco exclusivo de testes")
    parser.add_argument("--registros", type=int, default=TOTAL_PADRAO_REGISTROS)
    parser.add_argument("--eventos-por-registro", type=int,
                        default=EVENTOS_PADRAO_POR_REGISTRO)
    parser.add_argument("--amostra", type=int, default=TAMANHO_PADRAO_AMOSTRA)
    return parser.parse_args()


def validar_parametros(opcoes):
    banco = motor.url.database or ""
    if not banco.endswith("_teste"):
        raise SystemExit("Recusado: POC-TS-009 só pode usar banco terminado em '_teste'.")
    if not opcoes.executar:
        raise SystemExit("Recusado: informe --executar para recriar o banco de testes.")
    if opcoes.registros < 1 or opcoes.eventos_por_registro < 1:
        raise SystemExit("Recusado: as quantidades precisam ser positivas.")
    if not 1 <= opcoes.amostra <= opcoes.registros:
        raise SystemExit("Recusado: a amostra deve estar entre 1 e o total de Registros.")
    return banco


def id_registro(numero):
    return f"VOL-{numero:032d}"


def estado_do_evento(sequencia, total):
    if sequencia == 1:
        return "em_andamento"
    if sequencia == total:
        return "concluido"
    return "em_validacao" if sequencia % 2 == 0 else "em_andamento"


def montar_lote(inicio, fim, eventos_por_registro, momento_base):
    comandos = []
    registros = []
    eventos = []

    for numero in range(inicio, fim + 1):
        registro_id = id_registro(numero)
        comando_id = f"CMD-VOL-{numero:06d}"
        comandos.append({
            "id": comando_id,
            "tipo": "ensaio_volume_poc_ts_009",
            "ator_tipo": "sistema",
            "ator_id": "POC-TS-009",
            "conta_id": None,
            "resultado": {"eventos_gerados": eventos_por_registro},
            "hash_parametros": None,
        })
        registros.append({
            "id": registro_id,
            "codigo_lgpd": f"LGPD-2099-{numero:05d}",
            "tipo_objeto": "atividade",
            "titulo_objeto": f"Atividade sintética de volume {numero:05d}",
            "unidade_principal_atual_id": "UNID-NORTE",
            "contexto_atuacao_id": "CTX-TRIB-01",
            "ano_codigo": 2099,
            "numero_codigo": numero,
            "criado_por": "PESSOA-A",
            "ciclo_atual": 1,
            "estado_atual": estado_do_evento(eventos_por_registro, eventos_por_registro),
            "sequencia_atual": eventos_por_registro,
        })

        hash_anterior = HASH_INICIAL
        for sequencia in range(1, eventos_por_registro + 1):
            estado = estado_do_evento(sequencia, eventos_por_registro)
            evento = Evento(
                cadeia_tipo="registro",
                cadeia_id=registro_id,
                sequencia_cadeia=sequencia,
                registro_id=registro_id,
                ciclo_id=None,
                tipo_evento="passo_sintetico_volume",
                codigo_evento="VOLUME",
                comando_id=comando_id,
                ordem_no_comando=sequencia,
                ator_tipo="sistema",
                ator_id="POC-TS-009",
                em_nome_de=None,
                ocorrido_em=momento_base + timedelta(
                    microseconds=(numero * eventos_por_registro) + sequencia
                ),
                versao_regra="POC-1",
                versao_esquema_evento=1,
                versao_algoritmo_hash=VERSAO_ALGORITMO_HASH,
                conteudo={"estado_projetado": estado, "passo": sequencia},
                hash_anterior=hash_anterior,
            )
            evento.payload_canonico = texto_canonico(evento, CAMPOS_LACRADOS_DOMINIO)
            evento.hash = lacre(evento.payload_canonico)
            hash_anterior = evento.hash
            eventos.append({
                campo.name: getattr(evento, campo.name)
                for campo in Evento.__table__.columns
                if campo.name not in {"id", "registrado_em"}
            })
    return comandos, registros, eventos


def carregar_volume(sessao, total_registros, eventos_por_registro, tamanho_lote=100):
    momento_base = datetime(2099, 1, 1, tzinfo=timezone.utc)
    for inicio in range(1, total_registros + 1, tamanho_lote):
        fim = min(total_registros, inicio + tamanho_lote - 1)
        comandos, registros, eventos = montar_lote(
            inicio, fim, eventos_por_registro, momento_base
        )
        sessao.execute(insert(Comando), comandos)
        sessao.execute(insert(Registro), registros)
        sessao.execute(insert(Evento), eventos)
        sessao.flush()


def verificar_integridade(sessao, total_registros):
    por_cadeia = defaultdict(list)
    consulta = select(Evento).where(
        Evento.cadeia_id.like("VOL-%")
    ).order_by(Evento.cadeia_id, Evento.sequencia_cadeia)
    for evento in sessao.scalars(consulta):
        por_cadeia[evento.cadeia_id].append(evento)

    if len(por_cadeia) != total_registros:
        raise AssertionError(
            f"esperadas {total_registros} cadeias; encontradas {len(por_cadeia)}"
        )
    for cadeia_id, eventos in por_cadeia.items():
        integra, motivo = conferir(
            eventos, CAMPOS_LACRADOS_DOMINIO, "sequencia_cadeia"
        )
        if not integra:
            raise AssertionError(f"cadeia {cadeia_id}: {motivo}")
    return por_cadeia


def verificar_reconstrucao(sessao, por_cadeia, tamanho_amostra):
    ids_amostra = sorted(por_cadeia)[:tamanho_amostra]
    registros = {
        registro.id: registro
        for registro in sessao.scalars(
            select(Registro).where(Registro.id.in_(ids_amostra))
        )
    }
    for registro_id in ids_amostra:
        eventos = por_cadeia[registro_id]
        estado_reconstruido = eventos[-1].conteudo["estado_projetado"]
        sequencia_reconstruida = eventos[-1].sequencia_cadeia
        projecao = registros[registro_id]
        if (estado_reconstruido, sequencia_reconstruida) != (
                projecao.estado_atual, projecao.sequencia_atual):
            raise AssertionError(f"reconstrução divergiu da projeção em {registro_id}")
    return ids_amostra


def executar(opcoes):
    banco = validar_parametros(opcoes)
    inicio_total = time.perf_counter()

    Base.metadata.drop_all(motor)
    Base.metadata.create_all(motor)
    with Session(motor) as sessao, sessao.begin():
        pessoas.semear(sessao)
        catalogos.semear(sessao)
        inicio_carga = time.perf_counter()
        carregar_volume(sessao, opcoes.registros, opcoes.eventos_por_registro)
        segundos_carga = time.perf_counter() - inicio_carga

    with Session(motor) as sessao:
        inicio_verificacao = time.perf_counter()
        por_cadeia = verificar_integridade(sessao, opcoes.registros)
        ids_amostra = verificar_reconstrucao(sessao, por_cadeia, opcoes.amostra)
        segundos_verificacao = time.perf_counter() - inicio_verificacao

    total_eventos = sum(len(eventos) for eventos in por_cadeia.values())
    return {
        "teste": "POC-TS-009",
        "resultado": "aprovado",
        "banco_exclusivo_de_teste": banco,
        "registros": opcoes.registros,
        "eventos": total_eventos,
        "cadeias_verificadas": len(por_cadeia),
        "eventos_por_cadeia": opcoes.eventos_por_registro,
        "amostra_reconstruida": len(ids_amostra),
        "projecoes_coincidentes": len(ids_amostra),
        "segundos_carga": round(segundos_carga, 3),
        "segundos_verificacao": round(segundos_verificacao, 3),
        "segundos_total": round(time.perf_counter() - inicio_total, 3),
        "executado_em_utc": datetime.now(timezone.utc).isoformat(),
        "dados_pessoais_reais": False,
    }


if __name__ == "__main__":
    print(json.dumps(executar(argumentos()), ensure_ascii=False, indent=2))
