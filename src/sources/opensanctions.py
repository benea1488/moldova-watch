"""OpenSanctions: sanctiuni, PEPs, entitati linkate. Interogheaza per alias + tara MD."""
from __future__ import annotations

from ..config import env
from ..models import Item
from ..util import get
from .base import Source

API = "https://api.opensanctions.org/search/default"


class OpenSanctions(Source):
    name = "OpenSanctions"
    key = "opensanctions"

    def fetch(self) -> list[Item]:
        api_key = env("OPENSANCTIONS_API_KEY")
        if not api_key:
            raise RuntimeError("lipseste OPENSANCTIONS_API_KEY (sursa dezactivata)")

        headers = {"Authorization": f"ApiKey {api_key}"}
        out: list[Item] = []
        seen_ids: set[str] = set()

        queries = self.wl.all_aliases() if self.cfg.get("per_alias", True) else ["Moldova"]
        for q in queries:
            params = {"q": q, "limit": 8, "countries": "md"}
            r = get(self.session, API, params=params, headers=headers)
            if r.status_code == 403:
                raise RuntimeError("cheie respinsa (403)")
            if r.status_code != 200:
                continue
            for res in r.json().get("results", []):
                rid = res.get("id")
                if rid in seen_ids:
                    continue
                seen_ids.add(rid)
                props = res.get("properties", {})
                topics = props.get("topics", []) or []
                tags = ["sanction"] if "sanction" in topics else []
                caption = res.get("caption", "(fara nume)")
                schema = res.get("schema", "")
                out.append(Item(
                    source=self.name,
                    title=f"{caption} [{schema}]",
                    url=f"https://www.opensanctions.org/entities/{rid}/",
                    date=res.get("last_change", "") or res.get("last_seen", ""),
                    summary="Topics: " + ", ".join(topics) if topics else "",
                    tags=tags,
                    meta={"datasets": res.get("datasets", []), "query": q},
                ))
        return out
