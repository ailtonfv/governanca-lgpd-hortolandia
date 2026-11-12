"""Saída de e-mails com entrega explícita e tratamento conservador de falha SMTP."""
import os
import ssl
import smtplib
from email.message import EmailMessage
from sqlalchemy import select
from app.modelos import AvisoDpo
from app.fila_form2 import agora


def montar_aviso(aviso, base_url):
    dados = aviso.metadados
    mensagem = EmailMessage()
    mensagem["To"] = os.getenv("LGPD_EMAIL_DPO", "lgpd@hortolandia.sp.gov.br")
    mensagem["From"] = os.getenv("LGPD_SMTP_REMETENTE", "poc@localhost")
    titulo = "Manifestação solicitada" if aviso.tipo == "manifestacao" else "Para ciência"
    mensagem["Subject"] = f"[LGPD] {titulo} — {dados['identificador_lgpd']}"
    mensagem["Message-ID"] = f"<lgpd-aviso-{aviso.id}@hortolandia.sp.gov.br>"
    mensagem.set_content(
        f"Processo: {dados['identificador_lgpd']}\n"
        f"Secretaria de origem: {dados['secretaria_id']}\n"
        f"Fila destinatária: {dados['fila_id']}\n"
        f"Entrada: {dados['entrada_em']}\n"
        f"Situação no encaminhamento: {titulo}\n"
        + (f"Complemento de manifestação: {dados['manifestacao_anterior_id']}\n" if dados.get("complemento") else "")
        +
        f"Acesso institucional: {base_url.rstrip('/')}/form2/filas\n")
    return mensagem


def enviar_smtp(mensagem):
    host = os.environ["LGPD_SMTP_HOST"]
    porta = int(os.environ["LGPD_SMTP_PORTA"])
    seguranca = os.environ["LGPD_SMTP_SEGURANCA"]
    if seguranca not in {"SSL", "STARTTLS"}:
        raise ValueError("Configure SSL ou STARTTLS para o serviço institucional.")
    if not os.getenv("LGPD_SMTP_REMETENTE"):
        raise ValueError("Configure o remetente autorizado.")
    contexto = ssl.create_default_context()
    if seguranca == "SSL":
        cliente = smtplib.SMTP_SSL(host, porta, context=contexto, timeout=30)
    else:
        cliente = smtplib.SMTP(host, porta, timeout=30)
    with cliente:
        if seguranca == "STARTTLS":
            cliente.starttls(context=contexto)
        usuario = os.getenv("LGPD_SMTP_USUARIO")
        if usuario:
            cliente.login(usuario, os.environ["LGPD_SMTP_SENHA"])
        recusados = cliente.send_message(mensagem)
        if recusados:
            raise RuntimeError("Destinatário recusado pelo serviço de envio.")


def entregar_pendentes(sessao, transporte, *, ciencia_individual=True, base_url):
    """A marca 'enviando' exige conferência após interrupção; evita reenvio cego."""
    enviados = 0
    while True:
        consulta = select(AvisoDpo).where(AvisoDpo.estado == "pendente")
        if not ciencia_individual:
            consulta = consulta.where(AvisoDpo.tipo == "manifestacao")
        aviso = sessao.scalar(consulta.order_by(AvisoDpo.criado_em).with_for_update(skip_locked=True).limit(1))
        if aviso is None:
            return enviados
        mensagem = montar_aviso(aviso, base_url)
        aviso.estado = "enviando"
        sessao.commit()
        try:
            transporte(mensagem)
        except Exception:
            aviso.estado = "conferir_entrega"
            aviso.erro = "Falha de transporte. Conferir a entrega antes de autorizar nova tentativa."
            sessao.commit()
            raise
        aviso.estado = "enviado"
        aviso.enviado_em = agora()
        sessao.commit()
        enviados += 1


def resumo_quinzenal(sessao, inicio, fim):
    """Intervalo semiaberto explícito para a execução agendada."""
    if inicio.tzinfo is None or fim.tzinfo is None or fim <= inicio:
        raise ValueError("Período inválido.")
    avisos = sessao.scalars(select(AvisoDpo).where(
        AvisoDpo.tipo == "ciencia", AvisoDpo.criado_em >= inicio,
        AvisoDpo.criado_em < fim).order_by(AvisoDpo.criado_em)).all()
    mensagem = EmailMessage()
    mensagem["To"] = os.getenv("LGPD_EMAIL_DPO", "lgpd@hortolandia.sp.gov.br")
    mensagem["From"] = os.getenv("LGPD_SMTP_REMETENTE", "poc@localhost")
    mensagem["Subject"] = f"[LGPD] Resumo quinzenal — {inicio.date()} a {fim.date()}"
    mensagem["Message-ID"] = f"<lgpd-resumo-{inicio.date()}-{fim.date()}@hortolandia.sp.gov.br>"
    linhas = [f"Período de {inicio.isoformat()} até {fim.isoformat()} (fim exclusivo).",
              f"Total de ingressos: {len(avisos)}"]
    linhas += [f"{a.metadados['identificador_lgpd']} | {a.metadados['secretaria_id']} | "
               f"{a.metadados['fila_id']} | {a.metadados['entrada_em']}" for a in avisos]
    mensagem.set_content("\n".join(linhas))
    return mensagem
