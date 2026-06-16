"""Scoring de relevanta: combina greutatea entitatilor, sursa, recenta si tag-uri."""
from __future__ import annotations

from .config import Entity, Watchlist
from .models import Item
from .util import now_utc, parse_date

# Greutate de baza per sursa (cat de "tare" e un semnal de acolo by default)
SOURCE_WEIGHT = {
    "OpenSanctions": 4.0,
    "HUDOC": 3.5,
    "OCCRP Aleph": 4.0,
    "EUR-Lex": 2.5,
    "World Bank": 2.0,
    "GDELT": 1.5,
    "MD Press": 2.5,
}

# Bonus pentru tag-uri de tip "semnal timpuriu" sau eveniment juridic dur
TAG_BONUS = {
    "early-signal": 2.5,     # ex: HUDOC COMMUNICATEDCASES
    "sanction": 2.0,
    "new-designation": 2.5,
    "leak": 1.5,
    "court": 1.0,
}


def score_item(item: Item, matched: list[Entity]) -> float:
    score = SOURCE_WEIGHT.get(item.source, 1.0)

    # contributia entitatilor (max 3 ca sa nu explodeze)
    ent_weights = sorted((e.weight for e in matched), reverse=True)[:3]
    score += sum(ent_weights) * 0.8

    # entitate "core" (non-tema) mareste increderea
    if any(not e.is_theme for e in matched):
        score += 1.0

    # tag-uri
    for t in item.tags:
        score += TAG_BONUS.get(t, 0.0)

    # recenta: bonus liniar pentru ultimele 14 zile
    dt = parse_date(item.date)
    if dt:
        age_days = max((now_utc() - dt).days, 0)
        score += max(0.0, 2.0 - age_days / 7.0)

    return round(score, 2)


def apply(items: list[Item], wl: Watchlist) -> list[Item]:
    """Imbogateste fiecare item cu entitati + scor. Pastreaza ordinea originala."""
    for it in items:
        if not it.entities:
            matched = wl.match(it.title, it.summary)
            it.entities = [e.name for e in matched]
        else:
            matched = [e for e in wl.entities if e.name in it.entities]
        it.score = score_item(it, matched)
    return items
