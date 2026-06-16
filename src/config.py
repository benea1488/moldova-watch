"""Incarcare configurari + Watchlist cu matching pe alias-uri multilingv."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .util import normalize_latin

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"


@dataclass
class Entity:
    name: str
    weight: int = 3
    tags: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    is_theme: bool = False
    # compilat: lista de (alias_normalizat, e_chirilic)
    _norm: list[tuple[str, bool]] = field(default_factory=list, repr=False)


_CYRILLIC = re.compile(r"[\u0400-\u04FF]")


def _has_cyrillic(s: str) -> bool:
    return bool(_CYRILLIC.search(s))


@dataclass
class Watchlist:
    entities: list[Entity]

    @classmethod
    def load(cls, path: Path | None = None) -> "Watchlist":
        path = path or (CONFIG_DIR / "watchlist.yaml")
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        ents: list[Entity] = []
        for block, is_theme in (("entities", False), ("themes", True)):
            for raw in data.get(block, []) or []:
                aliases = list(raw.get("aliases", []))
                # numele canonic e si el un alias implicit
                if raw["name"] not in aliases:
                    aliases.append(raw["name"])
                e = Entity(
                    name=raw["name"],
                    weight=int(raw.get("weight", 3)),
                    tags=list(raw.get("tags", [])),
                    aliases=aliases,
                    is_theme=is_theme,
                )
                e._norm = cls._compile(aliases)
                ents.append(e)
        return cls(ents)

    @staticmethod
    def _compile(aliases: list[str]) -> list[tuple[str, bool]]:
        out = []
        for a in aliases:
            a = a.strip()
            if not a:
                continue
            if _has_cyrillic(a):
                out.append((a.lower(), True))
            else:
                out.append((normalize_latin(a), False))
        # alias-uri mai lungi intai (match mai specific)
        return sorted(set(out), key=lambda t: -len(t[0]))

    def all_aliases(self) -> list[str]:
        """Pentru sursele care interogheaza API-ul per nume."""
        seen, out = set(), []
        for e in self.entities:
            for a in e.aliases:
                if a not in seen:
                    seen.add(a)
                    out.append(a)
        return out

    def match(self, *texts: str) -> list[Entity]:
        """Intoarce entitatile ale caror alias-uri apar in textele date."""
        blob_latin = normalize_latin(" \n ".join(t for t in texts if t))
        blob_raw = " \n ".join(t for t in texts if t).lower()
        hits: list[Entity] = []
        for e in self.entities:
            for alias_norm, is_cyr in e._norm:
                haystack = blob_raw if is_cyr else blob_latin
                if _word_present(alias_norm, haystack):
                    hits.append(e)
                    break
        return hits


def _word_present(needle: str, haystack: str) -> bool:
    """Match pe granita de cuvant pentru alias-uri scurte; substring pt. fraze."""
    if not needle:
        return False
    if " " in needle or len(needle) > 12:
        return needle in haystack
    # alias scurt (un nume): cere granita ca sa evitam fals-pozitive
    return re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", haystack) is not None


@dataclass
class Settings:
    lookback_days: int
    priority_top_n: int
    telegram_min_score: float
    sources: dict

    @classmethod
    def load(cls, path: Path | None = None) -> "Settings":
        path = path or (CONFIG_DIR / "sources.yaml")
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        lookback = int(os.environ.get("LOOKBACK_DAYS", data.get("lookback_days", 7)))
        return cls(
            lookback_days=lookback,
            priority_top_n=int(data.get("priority_top_n", 15)),
            telegram_min_score=float(data.get("telegram_min_score", 6.0)),
            sources=data.get("sources", {}),
        )

    def src(self, name: str) -> dict:
        return self.sources.get(name, {}) or {}

    def enabled(self, name: str) -> bool:
        return bool(self.src(name).get("enabled", False))


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()
