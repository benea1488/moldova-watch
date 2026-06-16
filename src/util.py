"""Utilitare comune: sesiune HTTP cu retry, logging, normalizare text/URL."""
from __future__ import annotations

import logging
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit, urlunsplit

import requests
from requests.adapters import HTTPAdapter

try:
    from urllib3.util.retry import Retry
except Exception:  # pragma: no cover
    Retry = None

USER_AGENT = (
    "moldova-watch/2.0 (+https://github.com/) "
    "investigative documentation bot; contact via repo"
)

log = logging.getLogger("moldova-watch")


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )


def make_session(timeout: int = 25) -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"})
    if Retry is not None:
        retry = Retry(
            total=3,
            backoff_factor=1.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET", "POST"]),
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry)
        s.mount("https://", adapter)
        s.mount("http://", adapter)
    # atasam timeout-ul ca atribut; sursele il folosesc explicit
    s.request_timeout = timeout  # type: ignore[attr-defined]
    return s


def get(session: requests.Session, url: str, **kw):
    kw.setdefault("timeout", getattr(session, "request_timeout", 25))
    return session.get(url, **kw)


def post(session: requests.Session, url: str, **kw):
    kw.setdefault("timeout", getattr(session, "request_timeout", 25))
    return session.post(url, **kw)


# ---------- text ----------

def strip_diacritics(text: str) -> str:
    """Elimina diacriticele latine; pastreaza chirilicele intacte."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize_latin(text: str) -> str:
    """Lowercase + fara diacritice latine. Pentru matching tolerant."""
    return strip_diacritics(text).lower()


# ---------- URL ----------

def normalize_url(url: str) -> str:
    """Normalizeaza pentru dedup: fara fragment, fara trailing slash, lowercase host."""
    if not url:
        return ""
    try:
        parts = urlsplit(url)
        path = parts.path.rstrip("/")
        return urlunsplit((parts.scheme, parts.netloc.lower(), path, parts.query, ""))
    except Exception:
        return url


# ---------- date ----------

def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def cutoff(lookback_days: int) -> datetime:
    return now_utc() - timedelta(days=lookback_days)


def parse_date(value) -> datetime | None:
    """Incearca cateva formate uzuale; intoarce datetime aware (UTC) sau None."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    s = str(value).strip()
    if not s:
        return None
    fmts = (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
    )
    for f in fmts:
        try:
            dt = datetime.strptime(s, f)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None
