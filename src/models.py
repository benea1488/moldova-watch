"""Modelul de date central: un Item = un semnal dintr-o sursa."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Item:
    source: str                      # "HUDOC", "OpenSanctions", ...
    title: str
    url: str
    date: str = ""                   # ISO 8601 daca e disponibil
    summary: str = ""
    entities: list[str] = field(default_factory=list)   # nume canonice din watchlist
    tags: list[str] = field(default_factory=list)       # "early-signal", "sanction", ...
    score: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def uid(self) -> str:
        """Identitate stabila pentru deduplicare: sursa + url (sau titlu)."""
        basis = f"{self.source}|{self.url or self.title}".strip().lower()
        return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["uid"] = self.uid
        return d
