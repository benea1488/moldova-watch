"""Orchestrator Moldova Watch.

Flux:
  1. incarca watchlist + settings
  2. ruleaza fiecare sursa (izolat)
  3. imbogateste cu entitati + scor
  4. deduplica fata de istoric
  5. (optional) triere Claude API
  6. scrie output (md/json/rss) + notifica Telegram
  7. inregistreaza + salveaza state-ul
"""
from __future__ import annotations

import sys

from . import notify, render, triage
from .config import Settings, Watchlist
from .dedup import SeenStore, filter_new
from .scoring import apply as apply_scores
from .sources import ALL
from .util import log, make_session, setup_logging


def main() -> int:
    setup_logging()
    log.info("== Moldova Watch ==")

    wl = Watchlist.load()
    settings = Settings.load()
    log.info("Watchlist: %d entitati | lookback: %d zile",
             len(wl.entities), settings.lookback_days)

    session = make_session()
    all_items, errors = [], []

    log.info("Surse:")
    for SourceCls in ALL:
        inst = SourceCls(settings, wl, session)
        if not settings.enabled(inst.key):
            log.info("  %-14s (dezactivat)", inst.name)
            continue
        items, err = inst.run()
        all_items.extend(items)
        if err:
            errors.append(err)

    log.info("Total brut: %d iteme", len(all_items))

    # scoring + entitati
    apply_scores(all_items, wl)

    # dedup fata de istoric
    store = SeenStore.load()
    fresh = filter_new(all_items, store)
    log.info("Noi (dupa dedup): %d", len(fresh))

    # triere editoriala optionala
    brief = triage.brief(fresh)
    if brief:
        log.info("Brief Claude generat (%d caractere)", len(brief))

    # momentum din istoric (inclusiv ce adaugam acum)
    store.record(fresh)
    store.prune()
    momentum = store.momentum(days=14, min_count=3)

    # output
    path = render.write_outputs(
        fresh,
        priority_top_n=settings.priority_top_n,
        momentum=momentum,
        triage=brief,
        errors=errors,
    )
    log.info("Digest scris: %s", path)

    # telegram
    notify.notify(fresh, settings)

    # email
    notify.send_email_digest(path)

    store.save()
    log.info("State salvat. Gata.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
