"""SURSA NOUA: presa de investigatie din Moldova (acoperire interna).

Agregheaza feed-uri RSS de la redactiile de investigatie (ZdG, RISE,
Anticoruptie.md, Mold-street, NewsMaker, IPN). Pentru redactiile pur de
investigatie (always_include) pastram TOT; pentru restul, doar hit-urile pe
watchlist (filtrarea efectiva se face in main, prin scoring).

Feed-urile sunt config-driven (config/sources.yaml). Daca unul moare, il scoti
de acolo, nu din cod. Esecul unui feed nu rupe restul.
"""
from __future__ import annotations

import feedparser

from ..config import Watchlist
from ..models import Item
from ..util import cutoff, log, make_session, parse_date
from .base import Source


class MdPress(Source):
    name = "MD Press"
    key = "mdpress"

    def fetch(self) -> list[Item]:
        feeds = self.cfg.get("feeds", [])
        always = set(self.cfg.get("always_include", []))
        cut = cutoff(self.settings.lookback_days)
        out: list[Item] = []

        for f in feeds:
            fname, furl = f.get("name", "?"), f.get("url", "")
            if not furl:
                continue
            try:
                parsed = feedparser.parse(furl, agent="moldova-watch/2.0")
            except Exception as exc:
                log.warning("    feed %s ESEC: %s", fname, exc)
                continue
            if getattr(parsed, "bozo", 0) and not parsed.entries:
                log.warning("    feed %s gol/invalid", fname)
                continue

            outlet_always = fname in always
            for e in parsed.entries[:30]:
                date = e.get("published", "") or e.get("updated", "")
                dt = parse_date(date)
                if dt and dt < cut:
                    continue
                title = e.get("title", "(fara titlu)")
                summary = _clean(e.get("summary", ""))[:300]
                matched = self.wl.match(title, summary)
                if not outlet_always and not matched:
                    continue
                tags = ["leak"] if outlet_always else []
                out.append(Item(
                    source=self.name,
                    title=f"[{fname}] {title}",
                    url=e.get("link", ""),
                    date=date,
                    summary=summary,
                    entities=[m.name for m in matched],
                    tags=tags,
                    meta={"outlet": fname},
                ))
        return out


def _clean(html: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", html or "").strip()
