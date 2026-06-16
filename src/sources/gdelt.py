"""GDELT 2.0: acoperirea presei internationale despre Moldova.

Filtram sa EXCLUDEM sursele RO/MD, ca sa vedem doar acoperirea externa
(complementar cu sursa mdpress, care aduce acoperirea interna).
"""
from __future__ import annotations

from ..models import Item
from ..util import get
from .base import Source

API = "https://api.gdeltproject.org/api/v2/doc/doc"


class Gdelt(Source):
    name = "GDELT"
    key = "gdelt"

    def fetch(self) -> list[Item]:
        exclude = self.cfg.get("exclude_source_countries", ["RO", "MD"])
        timespan = f"{max(self.settings.lookback_days, 1)}d"

        # query: Moldova + watchlist (numai nume core, latina), excludem RO/MD
        names = [e.name.split()[-1] for e in self.wl.entities if not e.is_theme][:8]
        names_q = " OR ".join(f'"{n}"' for n in names)
        query = f'(Moldova OR Moldovan) ({names_q})' if names_q else "Moldova"

        params = {
            "query": query,
            "mode": "ArtList",
            "maxrecords": 40,
            "timespan": timespan,
            "format": "json",
            "sort": "DateDesc",
        }
        r = get(self.session, API, params=params)
        if r.status_code != 200:
            return []
        try:
            articles = r.json().get("articles", [])
        except ValueError:
            return []

        out: list[Item] = []
        for a in articles:
            src_country = (a.get("sourcecountry") or "").upper()[:2]
            if src_country in {c.upper() for c in exclude}:
                continue
            out.append(Item(
                source=self.name,
                title=a.get("title", "(fara titlu)"),
                url=a.get("url", ""),
                date=a.get("seendate", ""),
                summary=f"Sursa: {a.get('domain', '')} ({a.get('sourcecountry', '')})",
                meta={"sourcecountry": a.get("sourcecountry"),
                      "language": a.get("language")},
            ))
        return out
