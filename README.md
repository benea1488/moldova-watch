# Moldova Watch

**Asistent zilnic de documentare pentru jurnaliști de investigații cu acoperire pe Republica Moldova.**

Rulează automat în GitHub Actions, agregă semnale din baze internaționale + presa de investigație locală, le punctează după relevanță și produce un digest zilnic (Markdown + JSON + RSS). Toată infrastructura e gratuită.

---

## Ce monitorizează

| Sursă | Ce captează | Cheie API |
|---|---|---|
| **OpenSanctions** | Sancțiuni, PEPs, entități linkate — interogat per alias din watchlist + țara MD | Da, gratuit non-comercial |
| **HUDOC (CEDO)** | Hotărâri, decizii, cazuri comunicate (early-signal) cu Moldova stat pârât | Nu |
| **OCCRP Aleph** | Entități din leak-uri/investigații cu legătură MD (inclusiv offshore) | Opțional |
| **EUR-Lex** | Acte UE care menționează Moldova (CFSP, sancțiuni, asociere) | Nu |
| **World Bank** | Proiecte active + documente recente | Nu |
| **GDELT 2.0** | Presa **internațională** (exclude RO/MD ca să vezi acoperirea externă) | Nu |
| **MD Press** *(nou)* | Presa **internă** de investigație: ZdG, RISE, Anticorupție, Mold-street, NewsMaker, IPN (RSS) | Nu |

## Ce e nou față de v1

- **Alias-uri multilingv** în watchlist (latină / română cu diacritice / **chirilic-rusă**). Numele apar des în rusă în surse — fără asta ratai jumătate din HUDOC/GDELT/Aleph.
- **Scoring de relevanță** + secțiune **Priority** în capul digestului. Nu mai e un perete plat.
- **Vedere pe entitate**: tot ce a apărut azi, grupat per persoană, cross-sursă.
- **Momentum**: cine „urcă" în ultimele 14 zile (din istoricul `seen.json`).
- **Triere editorială cu Claude** (opțional, vezi mai jos): brief + conexiuni + unghiuri.
- **Output triplu**: `digests/latest.md`, `latest.json`, `feed.xml` (RSS pentru reader).
- **Robustețe**: retry/backoff, timeouts, dedup pe hash + URL normalizat, izolare per-sursă.

---

## Setup (5 minute)

### 1. Fork / clonează repo-ul în contul tău

Public e mai eficient (minute nelimitate la Actions). Privat are limita de 2000 min/lună pe planul Free.

### 2. Obține cheia OpenSanctions (gratuit)

https://www.opensanctions.org/api/ → Sign up → cheie API. Pentru jurnalism non-comercial e gratuit.

### 3. Adaugă secretele

`Settings` → `Secrets and variables` → `Actions` → `New repository secret`:

```
OPENSANCTIONS_API_KEY   (obligatoriu — fără ea, sursa e dezactivată)
ANTHROPIC_API_KEY       (opțional — activează brief-ul editorial Claude)
ALEPH_API_KEY           (opțional — rate limit mai bun; cere la support@occrp.org)
TELEGRAM_BOT_TOKEN      (opțional)
TELEGRAM_CHAT_ID        (opțional)
```

### 4. Activează workflow-ul

Tab `Actions` → `Daily digest` → `Enable workflow`. Prima rulare manuală: `Run workflow` cu `lookback_days: 30` ca să prinzi backlog-ul.

Rulează implicit la **06:30 UTC**. Modifică `cron` în `.github/workflows/daily-digest.yml` pentru alt orar.

### 5. (Opțional) Telegram

1. `@BotFather` → `/newbot` → primești token.
2. Scrie-i botului într-un chat/grup.
3. `https://api.telegram.org/bot<TOKEN>/getUpdates` → ia `chat.id`.
4. Pune `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` ca secrete.

Pe Telegram ajung doar itemele **priority** (scor ≥ prag, configurabil în `sources.yaml`).

---

## Configurare (fără cod)

- **`config/watchlist.yaml`** — entitățile urmărite, cu greutate, tag-uri și alias-uri. Adaugă/șterge liber. Pentru fiecare nume nou, pune și varianta **chirilică** — crește recall-ul considerabil.
- **`config/sources.yaml`** — pornește/oprește surse, ajustează `lookback_days`, `priority_top_n`, pragul Telegram și lista de feed-uri RSS. Dacă un feed moare, îl scoți de aici, nu din cod.

## Rulare locală

```bash
pip install -r requirements.txt
export OPENSANCTIONS_API_KEY=...    # opțional pentru test
python -m src.main
python tests/test_core.py           # teste
```

Output în `digests/`.

---

## Roadmap (module de îmbogățire, la cerere)

Surse de tip *lookup* (nu „ce-i nou azi"), utile la enrichment punctual, nu în bucla zilnică:
- **GLEIF** (gratuit, fără cheie) — structuri corporative, relații parent/child via LEI.
- **OpenCorporates** — registre corporative (necesită cheie; free tier limitat).
- **TED (EU)** — licitații UE care menționează Moldova.

Spune-mi dacă vrei vreunul wired și ca modul activ.

## Arhitectură

```
src/
  main.py          orchestrator
  config.py        watchlist + alias matching + settings
  models.py        Item
  scoring.py       relevanță
  dedup.py         seen.json + momentum
  render.py        markdown / json / rss
  triage.py        brief Claude (opțional)
  notify.py        Telegram
  util.py          http retry, logging, normalizare
  sources/         o sursă = un modul izolat
```

Fiecare sursă rulează izolat: dacă pică, apare la „Erori la fetch" și restul digestului merge mai departe.
