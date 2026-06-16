"""OpenSanctions: sanctiuni, PEPs, entitati linkate. Interogheaza bulk data (fara API key)."""
from __future__ import annotations

import csv
import io
import urllib.request
import datetime

from ..models import Item
from .base import Source

# Folosim setul de date 'default' care include sanctiuni, PEPs, etc. (la fel ca /search/default)
BULK_URL = "https://data.opensanctions.org/datasets/latest/default/targets.simple.csv"

class OpenSanctions(Source):
    name = "OpenSanctions"
    key = "opensanctions"

    def fetch(self) -> list[Item]:
        out: list[Item] = []
        seen_ids: set[str] = set()

        req = urllib.request.Request(BULK_URL)
        try:
            with urllib.request.urlopen(req) as response:
                wrapper = io.TextIOWrapper(response, encoding='utf-8', errors='replace')
                reader = csv.reader(wrapper)
                try:
                    headers = next(reader)
                except StopIteration:
                    return []
                
                try:
                    id_idx = headers.index("id")
                    schema_idx = headers.index("schema")
                    name_idx = headers.index("name")
                    aliases_idx = headers.index("aliases")
                    dataset_idx = headers.index("dataset")
                    sanctions_idx = headers.index("sanctions")
                    last_change_idx = headers.index("last_change")
                except ValueError:
                    raise RuntimeError("Formatul CSV OpenSanctions s-a modificat.")
                
                for row in reader:
                    if len(row) <= last_change_idx:
                        continue
                    
                    name = row[name_idx]
                    aliases = row[aliases_idx]
                    
                    # Verificam direct in watchlist (doar daca exista un nume)
                    if not name and not aliases:
                        continue
                        
                    hits = self.wl.match(name, aliases)
                    if not hits:
                        continue
                        
                    rid = row[id_idx]
                    if rid in seen_ids:
                        continue
                    seen_ids.add(rid)
                    
                    schema = row[schema_idx]
                    dataset = row[dataset_idx]
                    sanctions = row[sanctions_idx]
                    last_change = row[last_change_idx]
                    
                    tags = ["sanction"] if sanctions else []
                    summary = f"Datasets: {dataset}" if dataset else ""
                    
                    out.append(Item(
                        source=self.name,
                        title=f"{name} [{schema}]",
                        url=f"https://www.opensanctions.org/entities/{rid}/",
                        date=last_change or datetime.datetime.now().isoformat(),
                        summary=summary,
                        tags=tags,
                        meta={"datasets": dataset.split(";"), "query": [h.name for h in hits]},
                    ))
        except Exception as e:
            raise RuntimeError(f"Eroare la descarcarea bulk data OpenSanctions: {e}")
            
        return out
