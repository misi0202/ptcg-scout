# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Commands

```bash
# Python env
conda activate ptcg-scout

# Run full pipeline (collect → score → notify → save JSON)
python main.py

# Frontend dev
cd web && npm run dev

# Frontend build & static export
cd web && npx next build
```

## Architecture

```
main.py                  # Pipeline orchestrator: collect → store → score → enrich → notify
collectors/              # Data sources, each extends BaseCollector → returns list[CardData]
  base.py                #   ABC: requests.Session + Retry adapter, UA pool (4), delay between requests
  pokemontcg.py          #   EN cards + TCGPlayer/Cardmarket prices (api.pokemontcg.io/v2, no auth)
  reddit.py              #   r/PokemonTCG via old.reddit.com/.json (no auth needed)
  ebay.py                #   eBay sold listings via HTML scrape (cookie-prime, IP-rate-limited)
  justtcg.py             #   JP prices via JustTCG API (x-api-key header, 100 req/day)
analyzer/
  scoring.py             #   Hybrid: Price×0.4 + IP×0.3 + Volume×0.2 + Momentum×0.1
  supply_demand.py       #   30-day volume-price analysis from prices table
  trends.py              #   Signal: bullish/cautious/bearish/watch based on SD + mentions
  boxes.py               #   Booster box low-point detection (post-release window rules)
notifier/feishu.py       #   Feishu webhook: daily TOP 10 report + price spike alerts
db/
  schema.sql             #   SQLite: cards, prices, mentions, scores, boxes
  models.py              #   insert_card/insert_price/insert_mention helpers
config/pokemon_tiers.json # IP tiers (T1=100 to T4=50), narrative tags, artist list
web/                     #   Next.js 14 static export (output:"export") + Tailwind 3 + Recharts
data/                    #   Output: cards.json, boxes.json, history/YYYY-MM-DD.json
```

## Pipeline Flow

1. `collect_all()` — Run all collectors in sequence; each returns `list[CardData]`
2. `store_data()` — Write to SQLite (`cards`, `prices`, `mentions` tables)
3. `run_scoring()` — Score all cards, return TOP 50 sorted by composite
4. `enrich_top_cards()` — Add JP prices via JustTCG (cached per day)
5. `save_json()` / `save_history_snapshot()` — Output to `data/cards.json`
6. `send_daily_report()` — Push TOP 10 + price alerts to Feishu

## Collectors

All collectors extend `collectors.base.BaseCollector` and implement `collect() -> list[CardData]`.

**Base infrastructure**: `requests.Session` + `HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1, status_forcelist=[429,500,502,503,504]))`. UA pool of 4, rotated per request. `time.sleep(random.uniform(min,max))` before each `self.get()`.

**CardData contract**: `name, set_name, card_number, pokemon_name, price|None, condition, sale_date, source, extra:dict`. Use `extra` for source-specific fields (rarity, artist, image_url, game, grade, jp_*).

**Error handling**: `collect()` wrapped in try/except → `logger.error` → `return []`. One collector failure never blocks the pipeline. Log prefix: `[source_name]`.

**API auth pattern**: `os.getenv("KEY")` at top of `collect()` → missing key = `return []` and log warning. Keys in `.env.example` → `os.getenv()` → GitHub Secrets → workflow env vars.

**Adding a collector**: (1) `collectors/<name>.py` extends BaseCollector, set `name` attr, implement `collect()` (2) auth check at top (3) export in `__init__.py` (4) add instance to `collect_all()` in main.py.

### Rate Limits by Source

| Source | Rate | Mechanism |
|---|---|---|
| PokemonTCG | ~1-3s between pages | Page-based pagination, filter `q=field:value`, select fields |
| Reddit | 2-5s between requests | `old.reddit.com/r/{sub}/hot.json` → `data.children[].data`, 50 posts/page |
| JustTCG | 100 req/day | `x-api-key` header, daily cache to `data/jp_cache.json` |
| eBay (scrape) | 5-10s between requests | Cookie-prime homepage → search `LH_Sold=1&LH_Complete=1` → parse `li.s-item`. IP-rate-limited (works on CI fresh IP, may 403 locally) |

## Database

SQLite at `data/ptcg.db`. Schema: `db/schema.sql` with `CREATE TABLE IF NOT EXISTS`. No migration framework.

**Tables**: `cards` (UNIQUE on `name, set_name, card_number`), `prices` (FK→cards, `source+price+sale_date`), `mentions` (FK→cards, `source+keyword+date`), `scores`, `boxes`.

**Patterns**: `INSERT OR IGNORE` for idempotency. Return inserted/ existing id via `SELECT id FROM cards WHERE name=? AND set_name=?`. `conn.row_factory = sqlite3.Row`. Batch commit after loop, not per-row. Index FK and date columns.

**Adding columns**: (1) Add to `schema.sql` CREATE TABLE (2) Add param to `insert_*()` in `models.py` (3) Delete `data/ptcg.db` to rebuild. For retroactive: ALTER TABLE before `init_db()`.

**Storage**: `*.db` in `.gitignore`. `data/` JSON files are committed, the DB file is NOT.

## Frontend

Next.js 14 static export (`output: "export"`) → GitHub Pages. Tailwind 3 + Recharts for charts.

**Data flow**: `getStaticProps` reads `path.join(cwd, "..", "data", "cards.json")` at build time. Dynamic routes via `getStaticPaths` from same file. No runtime API calls.

**Visual system**: Light warm-gradient bg. Glass cards: `backdrop-blur(20px) bg-white/60 border-white/80`. Fonts: Playfair Display (headings) + DM Sans (body). Gold gradient on high scores, indigo on mid, rose on negative. Floating radial-gradient orbs.

**Layout**: `repeat(5, 1fr)` grid → 4→3→2 responsive breakpoints. Hero card with animated gradient border above grid. `max-w-[1600px]`. Card images: `aspect-[2.5/3.5]`.

**Components**: `.glass-card` with `hover:translateY(-2px)`. Filter pills in `bg-white/60` container, active=`bg-stone-800 text-white`. `.stagger-item` + `animation-delay` from index. Images: `object-contain`, `hover:scale-110`.

## Scoring Formula

```
Score = Price_Signal × 0.4 + IP_Heat × 0.3 + Volume_Signal × 0.2 + Momentum × 0.1

Price_Signal: normalized best market price (US/EU/JP). Default 30.
IP_Heat: Pokemon popularity tier from config/pokemon_tiers.json (T1=100, T2=85, T3=70, T4=50, default 30).
Volume_Signal: normalized Reddit mention count. Default 30.
Momentum: price trend 0-100 (50=neutral). Priority: JustTCG 30d → 7d → supply_demand history. +30% → 100, -30% → 0.
All sub-scores and final composite capped to 5-100 range.
```

## Key Design Rules

- **Collectors degrade gracefully**: When API key missing or rate-limited, return `[]` and log warning — never crash
- **Daily-cache authenticated APIs**: Never repeat same API call within one day. `data/jp_cache.json` for JustTCG
- **eBay collector is IP-rate-limited**: 403 after consecutive requests. Works on GitHub Actions (fresh IP each run) but may fail locally
- **First run has no history**: All signals show "insufficient_data" until 30 days of price data accumulate
- **Card DB UNIQUE constraint**: `(name, set_name, card_number)` — same card from different sets/variants gets separate rows
- **Reddit collector uses public JSON**: No API key needed. old.reddit.com/hot.json returns 50 posts per request
- **Frontend reads static JSON**: Next.js getStaticProps reads from `../data/cards.json` at build time
- **`extra` dict for source-specific fields**: Never add collector-specific columns to the core CardData contract — use `extra` dict

## GitHub Actions

- `.github/workflows/daily.yml` — Runs UTC 22:00 (BJT 06:00), also manual trigger
- `scout` job runs Python pipeline, commits `data/` back
- `deploy` job builds Next.js and deploys to GitHub Pages
- Secrets needed: `FEISHU_WEBHOOK_URL`, `JUSTTCG_API_KEY`

## Network Rules

Avoid using WebFetch when possible.
Prefer:
- curl
- wget
- Invoke-WebRequest
- local scripts

Reason:
Fetch domain verification is unreliable in this environment.
