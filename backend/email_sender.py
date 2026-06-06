"""Email sending via Gmail SMTP using each user's own credentials.

Falls back to platform-wide GMAIL_USER / GMAIL_APP_PASSWORD env vars (or admin
config in DB) if the user has not configured their own.

Supports optional `cc` recipients — typically the user's `secondary_email`
(business address) so every outgoing document is also copied to the company.
"""
import os
import smtplib
from email.message import EmailMessage
from typing import List, Optional, Tuple


def send_email_with_attachment(
    gmail_user: str,
    gmail_password: str,
    recipients: List[str],
    subject: str,
    body: str,
    attachment_name: str,
    attachment_bytes: bytes,
    extra_attachments: Optional[List[Tuple[str, bytes, str]]] = None,
    cc: Optional[List[str]] = None,
    from_name_override: Optional[str] = None,
) -> dict:
    """Send an email with the generated DOCX attached.

    If per-user creds are empty, fall back to platform-wide env vars
    (GMAIL_USER + GMAIL_APP_PASSWORD).
    """
    if not gmail_user or not gmail_password:
        gmail_user = os.environ.get("GMAIL_USER", "").strip()
        gmail_password = os.environ.get("GMAIL_APP_PASSWORD", "").strip()

    if not gmail_user or not gmail_password:
        return {
            "ok": False,
            "error": "Adresa Gmail nu este configurată. Mergeți la Setări → Configurare email pentru a o adăuga.",
        }

    from_name = (from_name_override or os.environ.get("SMTP_FROM_NAME", "")).strip()
    from_header = f"{from_name} <{gmail_user}>" if from_name else gmail_user

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_header
    msg["To"] = ", ".join(recipients)
    cc_list = [c for c in (cc or []) if c and c.strip()]
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    msg.set_content(body or "")

    msg.add_attachment(
        attachment_bytes,
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=attachment_name,
    )

    for name, data, mime in (extra_attachments or []):
        maintype, subtype = mime.split("/", 1) if "/" in mime else ("application", "octet-stream")
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=name)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
            server.login(gmail_user, gmail_password)
            server.send_message(msg)
        return {"ok": True, "cc": cc_list}
    except smtplib.SMTPAuthenticationError:
        return {"ok": False, "error": "Autentificare Gmail eșuată. Verificați adresa și App Password-ul (16 caractere)."}
    except Exception as e:
        return {"ok": False, "error": f"Eroare SMTP: {str(e)}"}
