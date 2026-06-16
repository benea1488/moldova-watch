"""Notificari: Telegram (pentru priority) si Email (pentru tot digest-ul)."""
from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
import markdown

from .config import Settings, env
from .models import Item
from .util import log, make_session, post

API = "https://api.telegram.org/bot{token}/sendMessage"


def notify(items: list[Item], settings: Settings) -> None:
    # 1. Telegram
    token = env("TELEGRAM_BOT_TOKEN")
    chat_id = env("TELEGRAM_CHAT_ID")
    if token and chat_id:
        top = [i for i in items if i.score >= settings.telegram_min_score]
        top.sort(key=lambda i: i.score, reverse=True)
        top = top[:10]
        if top:
            lines = ["*Moldova Watch — semnale priority azi*", ""]
            for it in top:
                ents = f" — {', '.join(it.entities)}" if it.entities else ""
                title = _esc(it.title[:140])
                lines.append(f"\u2022 [{title}]({it.url}) `{it.score}`{_esc(ents)}")
            text = "\n".join(lines)
            
            session = make_session()
            try:
                r = post(session, API.format(token=token), json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True,
                })
                if r.status_code != 200:
                    log.warning("  Telegram status %s: %s", r.status_code, r.text[:200])
            except Exception as exc:
                log.warning("  Telegram ESEC: %s", exc)

def send_email_digest(md_path: Path) -> None:
    """Trimite tot digest-ul prin email, transformat in HTML."""
    email_user = env("EMAIL_USER")
    email_pass = env("EMAIL_PASS")
    
    if not email_user or not email_pass:
        return
        
    try:
        md_text = md_path.read_text(encoding="utf-8")
        
        lines = md_text.splitlines()
        subject = "Moldova Watch Digest"
        if lines and lines[0].startswith("# "):
            subject = lines[0].replace("# ", "")
        
        html_body = markdown.markdown(md_text)
        html_content = f'''
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                    h2 {{ color: #2980b9; margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
                    h3 {{ color: #e67e22; margin-top: 20px; }}
                    a {{ color: #3498db; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                </style>
            </head>
            <body>
                {html_body}
            </body>
        </html>
        '''
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = email_user
        msg['To'] = email_user
        
        part = MIMEText(html_content, 'html')
        msg.attach(part)
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_user, email_pass)
        server.sendmail(email_user, email_user, msg.as_string())
        server.quit()
        
        log.info("Email trimis cu succes catre %s", email_user)
    except Exception as e:
        log.warning("Eroare la trimiterea emailului: %s", e)

def _esc(s: str) -> str:
    for ch in ("[", "]", "`"):
        s = s.replace(ch, " ")
    return s
