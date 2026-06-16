"""Triere editoriala optionala cu Claude API.

Activata DOAR daca exista secretul ANTHROPIC_API_KEY. Daca lipseste, se sare
peste (cost zero). Produce un brief editorial scurt + conexiuni cross-sursa +
unghiuri de investigatie, pe baza itemelor de top.
"""
from __future__ import annotations

from .config import env
from .models import Item
from .util import get, log, make_session, post

API = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-6"

SYSTEM = (
    "Esti asistent de documentare pentru un editor de investigatii cu acoperire "
    "pe Republica Moldova. Primesti o lista de semnale brute agregate azi din "
    "surse internationale si presa de investigatie. Sarcina ta: separa semnalul "
    "de zgomot. Raspunde in romana, concis, fara floricele. Format:\n"
    "1) BRIEF (max 5 puncte): ce conteaza azi si DE CE.\n"
    "2) CONEXIUNI: nume/entitati care apar in mai multe surse simultan.\n"
    "3) UNGHIURI: 2-3 piste concrete de verificat, fiecare cu primul pas.\n"
    "Nu inventa. Daca un semnal e slab, spune-o."
)


def brief(items: list[Item], max_items: int = 30) -> str | None:
    api_key = env("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    top = sorted(items, key=lambda i: i.score, reverse=True)[:max_items]
    if not top:
        return None

    lines = []
    for it in top:
        ents = ", ".join(it.entities) if it.entities else "-"
        lines.append(
            f"[{it.source}] {it.title} | entitati: {ents} | "
            f"scor: {it.score} | {it.date} | {it.url}"
        )
    user = "Semnale de azi:\n\n" + "\n".join(lines)

    session = make_session(timeout=60)
    try:
        r = post(session, API,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": MODEL,
                "max_tokens": 1200,
                "system": SYSTEM,
                "messages": [{"role": "user", "content": user}],
            },
        )
        if r.status_code != 200:
            log.warning("  triage Claude API status %s", r.status_code)
            return None
        data = r.json()
        parts = [b.get("text", "") for b in data.get("content", [])
                 if b.get("type") == "text"]
        return "\n".join(p for p in parts if p).strip() or None
    except Exception as exc:
        log.warning("  triage ESEC: %s", exc)
        return None
