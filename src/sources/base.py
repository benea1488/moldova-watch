"""Contract comun pentru surse. Fiecare sursa e izolata: daca pica, nu rupe restul."""
from __future__ import annotations

import requests

from ..config import Settings, Watchlist
from ..models import Item
from ..util import log, make_session


class Source:
    name: str = "base"
    key: str = "base"   # cheia din sources.yaml

    def __init__(self, settings: Settings, wl: Watchlist,
                 session: requests.Session | None = None):
        self.settings = settings
        self.wl = wl
        self.cfg = settings.src(self.key)
        self.session = session or make_session()

    def fetch(self) -> list[Item]:
        raise NotImplementedError

    def run(self) -> tuple[list[Item], str | None]:
        """Returneaza (items, eroare). Erorile sunt prinse, nu propagate."""
        try:
            items = self.fetch()
            log.info("  %-14s -> %d iteme", self.name, len(items))
            return items, None
        except Exception as exc:  # izolare per-sursa
            log.warning("  %-14s ESEC: %s", self.name, exc)
            return [], f"{self.name}: {exc}"
