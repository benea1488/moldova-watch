"""OCCRP Aleph: entitati si documente din leak-uri/investigatii cu legatura MD."""
from __future__ import annotations

from ..config import env
from ..models import Item
from ..util import get
from .base import Source

API = "https://aleph.occrp.org/api/2/entities"


class Aleph(Source):
    name = "OCCRP Aleph"
    key = "aleph"

    def fetch(self) -> list[Item]:
        headers = {}
        api_key = env("ALEPH_API_KEY")
        if api_key:
            headers["Authorization"] = f"ApiKey {api_key}"

        out: list[Item] = []
        seen_ids: set[str] = set()

        # interogari nominale: oligarhii apar des in jurisdictii offshore
        queries = self.wl.all_aliases()[:25]
        for q in queries:
            params = {
                "q": q,
                "filter:schemata": "Thing",
                "limit": 5,
            }
            r = get(self.session, API, params=params, headers=headers)
            if r.status_code != 200:
                continue
            for res in r.json().get("results", []):
                rid = res.get("id")
                if not rid or rid in seen_ids:
                    continue
                seen_ids.add(rid)
                props = res.get("properties", {})
                caption = res.get("caption", q)
                collection = (res.get("collection") or {}).get("label", "")
                out.append(Item(
                    source=self.name,
                    title=f"{caption}",
                    url=f"https://aleph.occrp.org/entities/{rid}",
                    date=props.get("modifiedAt", [""])[0]
                        if isinstance(props.get("modifiedAt"), list) else "",
                    summary=f"Colectie: {collection}" if collection else "",
                    tags=["leak"],
                    meta={"schema": res.get("schema"), "query": q},
                ))
        return out
