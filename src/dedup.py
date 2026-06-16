"""Deduplicare + istoric rulant pentru detectia de momentum pe entitati."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from .models import Item
from .util import now_utc, parse_date

ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = ROOT / "data" / "seen.json"

# cate zile de istoric pastram pentru momentum
HISTORY_DAYS = 30


class SeenStore:
    """
    Persistat in data/seen.json (commitat inapoi in repo).
    Structura:
      {
        "seen": { uid: "YYYY-MM-DD" },          # cand am vazut prima data
        "entity_log": [ ["YYYY-MM-DD", "Nume"], ... ]   # pt. momentum
      }
    """

    def __init__(self, seen: dict, entity_log: list):
        self.seen = seen
        self.entity_log = entity_log

    @classmethod
    def load(cls) -> "SeenStore":
        if STATE_PATH.exists():
            try:
                data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
                return cls(data.get("seen", {}), data.get("entity_log", []))
            except Exception:
                pass
        return cls({}, [])

    def is_new(self, item: Item) -> bool:
        return item.uid not in self.seen

    def record(self, items: list[Item]) -> None:
        today = now_utc().strftime("%Y-%m-%d")
        for it in items:
            self.seen.setdefault(it.uid, today)
            for ent in it.entities:
                self.entity_log.append([today, ent])

    def prune(self) -> None:
        cut = now_utc().timestamp() - HISTORY_DAYS * 86400
        kept = []
        for day, ent in self.entity_log:
            dt = parse_date(day)
            if dt and dt.timestamp() >= cut:
                kept.append([day, ent])
        self.entity_log = kept

    def momentum(self, days: int = 14, min_count: int = 3) -> list[tuple[str, int]]:
        """Entitati cu cele mai multe aparitii in ultimele `days` zile."""
        cut = now_utc().timestamp() - days * 86400
        c: Counter = Counter()
        for day, ent in self.entity_log:
            dt = parse_date(day)
            if dt and dt.timestamp() >= cut:
                c[ent] += 1
        return [(e, n) for e, n in c.most_common() if n >= min_count]

    def save(self) -> None:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {"seen": self.seen, "entity_log": self.entity_log}
        STATE_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=0), encoding="utf-8"
        )


def filter_new(items: list[Item], store: SeenStore) -> list[Item]:
    out, batch_seen = [], set()
    for it in items:
        if it.uid in batch_seen:
            continue
        batch_seen.add(it.uid)
        if store.is_new(it):
            out.append(it)
    return out
