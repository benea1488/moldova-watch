"""HUDOC (CEDO): hotarari, decizii, cazuri comunicate cu Moldova ca stat parat.

COMMUNICATEDCASES = semnal timpuriu: o speta e comunicata cu 1-2 ani inainte
sa devina hotarare publica. Le marcam 'early-signal'.
"""
from __future__ import annotations

import json

from ..models import Item
from ..util import cutoff, get, parse_date
from .base import Source

# endpoint-ul public folosit de interfata HUDOC
API = "https://hudoc.echr.coe.int/app/query/results"

COLLECTION_FLAGS = {
    "JUDGMENTS": "sort=kpdate Descending&select=itemid,docname,kpdate,respondent",
}


class Hudoc(Source):
    name = "HUDOC"
    key = "hudoc"

    def fetch(self) -> list[Item]:
        respondent = self.cfg.get("respondent", "MDA")
        collections = self.cfg.get(
            "collections", ["JUDGMENTS", "DECISIONS", "COMMUNICATEDCASES", "CLIN"]
        )
        cut = cutoff(self.settings.lookback_days)
        out: list[Item] = []

        for coll in collections:
            query = (
                f"contentsitehudoc=ECHR AND "
                f"(NOT (doctype:PR OR doctype:HFCOMOLD OR doctype:HFCOMFOLD)) AND "
                f"respondent:\"{respondent}\" AND collection:\"{coll}\""
            )
            params = {
                "query": query,
                "select": "itemid,docname,kpdate,respondent,doctypebranch",
                "sort": "kpdate Descending",
                "start": 0,
                "length": 20,
            }
            r = get(self.session, API, params=params)
            if r.status_code != 200:
                continue
            try:
                results = r.json().get("results", [])
            except json.JSONDecodeError:
                continue

            for res in results:
                col = res.get("columns", res)
                itemid = col.get("itemid", "")
                name = col.get("docname", "(fara titlu)")
                kpdate = col.get("kpdate", "")
                dt = parse_date(kpdate)
                if dt and dt < cut:
                    continue
                tags = ["court"]
                if coll == "COMMUNICATEDCASES":
                    tags.append("early-signal")
                out.append(Item(
                    source=self.name,
                    title=f"{name}",
                    url=f"https://hudoc.echr.coe.int/eng?i={itemid}",
                    date=kpdate,
                    summary=f"Colectie CEDO: {coll}; parat: {respondent}",
                    tags=tags,
                    meta={"collection": coll},
                ))
        return out
