"""Notificare Telegram optionala: doar itemele de priority (scor >= prag)."""
from __future__ import annotations

from .config import Settings, env
from .models import Item
from .util import log, make_session, post

API = "https://api.telegram.org/bot{token}/sendMessage"


def notify(items: list[Item], settings: Settings) -> None:
    token = env("TELEGRAM_BOT_TOKEN")
    chat_id = env("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return

    top = [i for i in items if i.score >= settings.telegram_min_score]
    top.sort(key=lambda i: i.score, reverse=True)
    top = top[:10]
    if not top:
        return

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


def _esc(s: str) -> str:
    # escapam doar caracterele care strica Markdown-ul Telegram in link/text
    for ch in ("[", "]", "`"):
        s = s.replace(ch, " ")
    return s
