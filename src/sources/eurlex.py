"""EUR-Lex: acte juridice UE care mentioneaza Moldova (CFSP, sanctiuni, asociere).

Folosim cautarea web EUR-Lex (rezultate Atom). Daca formatul se schimba,
fallback pe zero iteme, fara sa rupem digestul.
"""
from __future__ import annotations

import feedparser

from ..models import Item
from ..util import cutoff, parse_date
from .base import Source

# RSS de cautare full-text EUR-Lex (Moldova)
FEED = (
    "https://eur-lex.europa.eu/EN/display-feed.rss"
    "?myRssId=ZmldbGQ9RE4mdHlwZT1xdWlja19zZWFyY2gmdGV4dD1Nb2xkb3Zh"
)


class EurLex(Source):
    name = "EUR-Lex"
    key = "eurlex"

    def fetch(self) -> list[Item]:
        cut = cutoff(self.settings.lookback_days)
        out: list[Item] = []
        feed = feedparser.parse(FEED)
        for e in feed.entries[:40]:
            date = e.get("published", "") or e.get("updated", "")
            dt = parse_date(date)
            if dt and dt < cut:
                continue
            title = e.get("title", "(fara titlu)")
            out.append(Item(
                source=self.name,
                title=title,
                url=e.get("link", ""),
                date=date,
                summary=e.get("summary", "")[:300],
                tags=["sanction"] if "restrictive" in title.lower()
                    or "sanction" in title.lower() else [],
            ))
        return out
