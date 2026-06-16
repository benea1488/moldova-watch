"""Randare output: Markdown (digest), JSON (feed masina), RSS (reader)."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from .models import Item
from .util import now_utc

ROOT = Path(__file__).resolve().parent.parent
DIGEST_DIR = ROOT / "digests"


def _group_by_source(items: list[Item]) -> dict[str, list[Item]]:
    g: dict[str, list[Item]] = {}
    for it in items:
        g.setdefault(it.source, []).append(it)
    return g


def _group_by_entity(items: list[Item]) -> dict[str, list[Item]]:
    g: dict[str, list[Item]] = {}
    for it in items:
        for ent in it.entities:
            g.setdefault(ent, []).append(it)
    return dict(sorted(g.items(), key=lambda kv: -len(kv[1])))


def render_markdown(items: list[Item], *, priority_top_n: int,
                    momentum: list[tuple[str, int]],
                    triage: str | None, errors: list[str]) -> str:
    today = now_utc().strftime("%Y-%m-%d")
    L = [f"# Moldova Watch — {today}", ""]
    L.append(f"*{len(items)} semnale noi din {len(_group_by_source(items))} surse.*")
    L.append("")

    if triage:
        L += ["## 🧭 Brief editorial (Claude)", "", triage, ""]

    if momentum:
        L.append("## 📈 Momentum (ultimele 14 zile)")
        L.append("")
        for ent, n in momentum:
            L.append(f"- **{ent}** — {n} aparitii")
        L.append("")

    # Priority
    ranked = sorted(items, key=lambda i: i.score, reverse=True)
    L.append("## ⭐ Priority")
    L.append("")
    if not ranked:
        L.append("_Nimic nou azi._")
    for it in ranked[:priority_top_n]:
        L.append(_md_line(it, show_score=True))
    L.append("")

    # Pe entitate
    by_ent = _group_by_entity(items)
    if by_ent:
        L.append("## 👤 Pe entitate")
        L.append("")
        for ent, its in by_ent.items():
            L.append(f"### {ent} ({len(its)})")
            for it in sorted(its, key=lambda i: i.score, reverse=True):
                L.append(_md_line(it))
            L.append("")

    # Pe sursa (complet)
    L.append("## 🗂️ Toate, pe sursa")
    L.append("")
    for src, its in sorted(_group_by_source(items).items()):
        L.append(f"### {src} ({len(its)})")
        for it in sorted(its, key=lambda i: i.score, reverse=True):
            L.append(_md_line(it))
        L.append("")

    if errors:
        L.append("## ⚠️ Erori la fetch")
        L.append("")
        for e in errors:
            L.append(f"- {e}")
        L.append("")

    L.append("---")
    L.append(f"_Generat automat de moldova-watch la {now_utc().isoformat()}._")
    return "\n".join(L)


def _md_line(it: Item, show_score: bool = False) -> str:
    tags = "".join(f" `{t}`" for t in it.tags)
    ents = f" — {', '.join(it.entities)}" if it.entities else ""
    date = f" ({it.date[:10]})" if it.date else ""
    score = f" **[{it.score}]**" if show_score else ""
    title = it.title.replace("\n", " ").strip()
    link = f"[{title}]({it.url})" if it.url else title
    return f"- {link}{date}{ents}{tags}{score}"


def write_outputs(items: list[Item], *, priority_top_n: int,
                  momentum, triage, errors) -> Path:
    DIGEST_DIR.mkdir(parents=True, exist_ok=True)
    today = now_utc().strftime("%Y-%m-%d")

    md = render_markdown(items, priority_top_n=priority_top_n,
                         momentum=momentum, triage=triage, errors=errors)
    (DIGEST_DIR / f"{today}.md").write_text(md, encoding="utf-8")
    (DIGEST_DIR / "latest.md").write_text(md, encoding="utf-8")

    # JSON feed
    payload = {
        "generated": now_utc().isoformat(),
        "count": len(items),
        "items": [i.to_dict() for i in sorted(items, key=lambda x: -x.score)],
        "momentum": momentum,
        "errors": errors,
    }
    (DIGEST_DIR / "latest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # RSS
    (DIGEST_DIR / "feed.xml").write_text(_render_rss(items), encoding="utf-8")

    return DIGEST_DIR / f"{today}.md"


def _render_rss(items: list[Item]) -> str:
    now = now_utc().strftime("%a, %d %b %Y %H:%M:%S +0000")
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0"><channel>',
        "<title>Moldova Watch</title>",
        "<link>https://github.com/</link>",
        "<description>Semnale de investigatie, Republica Moldova</description>",
        f"<lastBuildDate>{now}</lastBuildDate>",
    ]
    for it in sorted(items, key=lambda x: -x.score)[:60]:
        title = escape(f"[{it.source}] {it.title}")
        desc = escape((it.summary or "") + f" (scor {it.score})")
        link = escape(it.url or "https://github.com/")
        parts.append(
            f"<item><title>{title}</title><link>{link}</link>"
            f"<guid isPermaLink='false'>{it.uid}</guid>"
            f"<description>{desc}</description></item>"
        )
    parts.append("</channel></rss>")
    return "".join(parts)
