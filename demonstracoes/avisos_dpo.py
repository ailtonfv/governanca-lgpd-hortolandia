"""Executar periodicamente pelo agendador institucional após configurar o SMTP."""
import argparse
import os
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.banco import motor
from app.modelos import ResumoDpo
from app.avisos_dpo import entregar_pendentes, enviar_smtp, resumo_quinzenal
from app.fila_form2 import agora

def executar():
    parser=argparse.ArgumentParser()
    parser.add_argument("--enviar",action="store_true",help="Entregar pelo SMTP configurado")
    parser.add_argument("--resumo-inicio",help="Data ISO inicial de período de 15 dias")
    args=parser.parse_args()
    pasta=Path("evidencias/avisos_dpo")
    def capturar(mensagem):
        pasta.mkdir(parents=True,exist_ok=True)
        identificador=mensagem["Message-ID"].strip("<>").replace("@","_")
        (pasta/(identificador+".eml")).write_bytes(mensagem.as_bytes())
    transporte=enviar_smtp if args.enviar else capturar
    if args.enviar:
        for chave in ("LGPD_SMTP_HOST","LGPD_SMTP_PORTA","LGPD_SMTP_SEGURANCA","LGPD_SMTP_REMETENTE","LGPD_BASE_URL"):
            if not os.getenv(chave):
                parser.error("Configuração ausente: "+chave)
    with Session(motor) as sessao:
        if args.resumo_inicio:
            inicio=datetime.fromisoformat(args.resumo_inicio).replace(tzinfo=ZoneInfo("America/Sao_Paulo"))
            fim=inicio+timedelta(days=15)
            mensagem=resumo_quinzenal(sessao,inicio,fim)
            if not args.enviar:
                capturar(mensagem)
                return
            if fim > agora():
                parser.error("O período do resumo ainda está em andamento.")
            periodo=sessao.get(ResumoDpo,args.resumo_inicio,with_for_update=True)
            if periodo is not None:
                parser.error("Período já registrado. Conferir estado antes de repetir.")
            sessao.add(ResumoDpo(periodo=args.resumo_inicio,estado="enviando"))
            sessao.commit()
            transporte(mensagem)
            periodo=sessao.get(ResumoDpo,args.resumo_inicio)
            periodo.estado="enviado";periodo.enviado_em=agora();sessao.commit()
        elif args.enviar:
            print(entregar_pendentes(sessao,transporte,
                ciencia_individual=os.getenv("LGPD_DPO_CIENCIA_INDIVIDUAL","1") == "1",
                base_url=os.environ["LGPD_BASE_URL"]))
        else:
            from app.modelos import AvisoDpo
            from app.avisos_dpo import montar_aviso
            for aviso in sessao.scalars(select(AvisoDpo)):
                capturar(montar_aviso(aviso,os.getenv("LGPD_BASE_URL","http://127.0.0.2:8001")))
            print("Mensagens de teste gravadas em evidencias/avisos_dpo.")
if __name__=="__main__":
    executar()
