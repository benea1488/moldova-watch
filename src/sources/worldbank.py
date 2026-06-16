"""World Bank: proiecte active + documente recente pentru Moldova."""
from __future__ import annotations

from ..models import Item
from ..util import cutoff, get, parse_date
from .base import Source

PROJECTS = "https://search.worldbank.org/api/v2/projects"
DOCS = "https://search.worldbank.org/api/v2/wds"


class WorldBank(Source):
    name = "World Bank"
    key = "worldbank"

    def fetch(self) -> list[Item]:
        country = self.cfg.get("country", "MD")
        cut = cutoff(self.settings.lookback_days)
        out: list[Item] = []

        # 1) proiecte
        r = get(self.session, PROJECTS, params={
            "format": "json", "countrycode_exact": country,
            "rows": 20, "os": 0, "fl": "id,project_name,boardapprovaldate,url",
        })
        if r.status_code == 200:
            projects = r.json().get("projects", {})
            for pid, p in projects.items():
                date = p.get("boardapprovaldate", "")
                dt = parse_date(date)
                if dt and dt < cut:
                    continue
                out.append(Item(
                    source=self.name,
                    title=f"Proiect: {p.get('project_name', pid)}",
                    url=p.get("url", f"https://projects.worldbank.org/en/projects-operations/project-detail/{pid}"),
                    date=date,
                    summary=f"ID proiect {pid}",
                    meta={"type": "project"},
                ))

        # 2) documente recente
        r = get(self.session, DOCS, params={
            "format": "json", "countrycode": country,
            "rows": 15, "strdate": cut.strftime("%Y-%m-%d"),
            "fl": "docdt,display_title,pdfurl,url",
        })
        if r.status_code == 200:
            docs = r.json().get("documents", {})
            for did, d in docs.items():
                if did == "facets":
                    continue
                out.append(Item(
                    source=self.name,
                    title=f"Document: {d.get('display_title', did)}",
                    url=d.get("pdfurl") or d.get("url", ""),
                    date=d.get("docdt", ""),
                    summary="Document Banca Mondiala",
                    meta={"type": "document"},
                ))
        return out
