"""Envio de email via SMTP, com fallback de desenvolvimento.

Se as variáveis SMTP_* não estiverem configuradas, o email é apenas
impresso no console (modo dev) em vez de falhar — assim o fluxo funciona
localmente sem precisar de um servidor SMTP real.
"""
import os
import smtplib
from email.message import EmailMessage


def _smtp_config():
    return {
        "host": os.environ.get("SMTP_HOST"),
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": os.environ.get("SMTP_USER"),
        "password": os.environ.get("SMTP_PASSWORD"),
        "from": os.environ.get("SMTP_FROM", os.environ.get("SMTP_USER", "no-reply@tubify.local")),
    }


def send_email(to, subject, body):
    """Envia um email. Retorna True se enviado via SMTP, False se só logado (dev)."""
    cfg = _smtp_config()
    if not cfg["host"] or not cfg["user"] or not cfg["password"]:
        # Fallback de desenvolvimento: loga no console
        print("=" * 60)
        print("[EMAIL - modo dev, SMTP não configurado]")
        print(f"Para: {to}")
        print(f"Assunto: {subject}")
        print(body)
        print("=" * 60)
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg["from"]
    msg["To"] = to
    msg.set_content(body)

    with smtplib.SMTP(cfg["host"], cfg["port"]) as server:
        server.starttls()
        server.login(cfg["user"], cfg["password"])
        server.send_message(msg)
    return True
