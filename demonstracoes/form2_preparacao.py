"""Executor local de habilitações aprovadas, individualizadas por pessoa/Registro.

Não decide competências; não cria pessoas/Registros/snapshots nem aplica migrações.
O manifesto deve ser conferido e aprovado pelo responsável funcional, fora da web.
"""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path


def ler_manifesto(caminho):
    dados = json.loads(Path(caminho).read_text(encoding="utf-8-sig"))
    if set(dados) != {"politica", "somente_dados_ficticios", "habilitacoes"}:
        raise ValueError("Manifesto com campos ausentes ou desconhecidos.")
    if dados["politica"] != "F2-DEMO-05-v1" or dados["somente_dados_ficticios"] is not True:
        raise ValueError("Somente política demonstrativa e dados fictícios são permitidos.")
    campos = {"comando_id", "registro_id", "pessoa_id", "finalidade", "vigente_de",
              "vigente_ate", "aprovacao_referencia", "fundamento", "ativa"}
    if not isinstance(dados["habilitacoes"], list) or not dados["habilitacoes"]:
        raise ValueError("Informe as habilitações individualmente aprovadas.")
    vistos = set()
    for item in dados["habilitacoes"]:
        if not isinstance(item, dict) or set(item) != campos:
            raise ValueError("Habilitação incompleta ou com campos extras.")
        if not item["pessoa_id"].startswith("PESSOA-"):
            raise ValueError("Utilize somente a identidade técnica da massa fictícia.")
        chave = (item["registro_id"], item["pessoa_id"])
        if chave in vistos:
            raise ValueError("Pessoa/Registro duplicados no manifesto.")
        vistos.add(chave)
        item["vigente_de"] = datetime.fromisoformat(item["vigente_de"])
        item["vigente_ate"] = datetime.fromisoformat(item["vigente_ate"])
    return dados["habilitacoes"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifesto", required=True)
    parser.add_argument("--banco", required=True)
    parser.add_argument("--executar", action="store_true")
    args = parser.parse_args()
    if not (args.banco.endswith("_teste") or args.banco == "lgpd_poc_v2"):
        raise SystemExit("Recusado: somente banco de teste ou demonstração local conhecida.")
    itens = ler_manifesto(args.manifesto)
    if not args.executar:
        print(f"Manifesto lido: {len(itens)} habilitações. Nenhuma gravação. Confira a aprovação individual antes de --executar.")
        return
    os.environ["BANCO_NOME"] = args.banco
    from sqlalchemy.orm import Session
    from app.banco import motor
    from app.form2_preparacao import registrar_habilitacao_controlada
    if motor.url.database != args.banco or motor.url.host not in {"localhost", "127.0.0.1", "::1"}:
        raise SystemExit("Destino divergente ou não local; nenhuma gravação autorizada.")
    with Session(motor) as sessao, sessao.begin():
        for item in itens:
            resultado = registrar_habilitacao_controlada(sessao, **item)
            if not resultado["permitido"]:
                raise RuntimeError(resultado["motivo"])
    print(f"{len(itens)} habilitações processadas com auditoria; nenhuma designação automática.")


if __name__ == "__main__":
    main()
