"""Teste pentru matching de alias-uri (latina + chirilic) si dedup."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import Watchlist            # noqa: E402
from src.dedup import filter_new, SeenStore  # noqa: E402
from src.models import Item                  # noqa: E402


def _wl():
    return Watchlist.load()


def test_latin_alias_match():
    wl = _wl()
    hits = [e.name for e in wl.match("Curtea a respins cererea lui Plahotniuc")]
    assert "Vladimir Plahotniuc" in hits


def test_cyrillic_alias_match():
    wl = _wl()
    hits = [e.name for e in wl.match("Суд рассмотрел дело Шор и Плахотнюк")]
    assert "Ilan Shor" in hits
    assert "Vladimir Plahotniuc" in hits


def test_diacritics_insensitive():
    wl = _wl()
    # "Guțul" cu diacritice trebuie sa prinda entitatea
    hits = [e.name for e in wl.match("Evghenia Guțul a declarat")]
    assert "Evghenia Gutul" in hits


def test_no_false_positive_short_alias():
    wl = _wl()
    # "sandu" nu trebuie sa apara intr-un cuvant mai mare aleatoriu
    hits = [e.name for e in wl.match("nisip si sandugherie oarecare")]
    assert "Maia Sandu" not in hits


def test_dedup_within_batch():
    a = Item(source="X", title="t", url="http://e.com/1")
    b = Item(source="X", title="t", url="http://e.com/1")
    store = SeenStore({}, [])
    out = filter_new([a, b], store)
    assert len(out) == 1


def test_dedup_against_history():
    a = Item(source="X", title="t", url="http://e.com/1")
    store = SeenStore({a.uid: "2026-01-01"}, [])
    out = filter_new([a], store)
    assert out == []


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("PASS", fn.__name__)
    print(f"\n{len(fns)} teste trecute.")
