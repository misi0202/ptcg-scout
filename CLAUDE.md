# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Commands

```bash
# Python env
conda activate ptcg-scout

# Run full pipeline (collect -> score -> notify -> save JSON)
python main.py

# Frontend dev
cd web && npm run dev

# Frontend build & export
cd web && npx next build
```

## Architecture

```
main.py                  # Pipeline orchestrator: collect → store → score → enrich → notify
collectors/              # Data sources, each returns list[CardData]
  pokemontcg.py          #   EN cards + TCGPlayer/Cardmarket prices (free API, no auth)
  reddit.py              #   r/PokemonTCG etc via old.reddit.com/.json (no API key needed)
  ebay.py                #   eBay sold listings via HTML scrape (cookie-prime approach)
  justtcg.py             #   JP prices via JustTCG API ($JUSTTCG_API_KEY), daily cached
  base.py                #   BaseCollector ABC with rate-limiting, UA rotation, retries
analyzer/
  scoring.py             #   Data-driven: Price×0.6 + Volume×0.4 + Momentum — no subjective tiers
  supply_demand.py       #   30-day volume-price analysis from prices table
  trends.py              #   Signal: bullish/cautious/bearish/watch based on SD + mentions
  boxes.py               #   Booster box low-point detection (post-release window rules)
notifier/feishu.py       #   Feishu webhook: daily TOP 10 report + price spike alerts
db/
  schema.sql             #   SQLite: cards, prices, mentions, scores, boxes
  models.py              #   insert_card/insert_price/insert_mention helpers
config/pokemon_tiers.json # IP tiers (T1=100 to T4=50), narrative tags, artist list
web/                     #   Next.js static export → GitHub Pages
data/                    #   Output: cards.json, boxes.json, history/YYYY-MM-DD.json
```

## Pipeline Flow

1. `collect_all()` — Run all collectors in sequence; each returns `list[CardData]`
2. `store_data()` — Write to SQLite (`cards`, `prices`, `mentions` tables)
3. `run_scoring()` — Score all cards, return TOP 50 sorted by composite
4. `enrich_top_cards()` — Add JP prices via JustTCG (cached per day)
5. `save_json()` / `save_history_snapshot()` — Output to `data/cards.json`
6. `send_daily_report()` — Push TOP 10 + price alerts to Feishu

## Key Design Rules

- **Collectors degrade gracefully**: When API key missing or rate-limited, return `[]` and log warning — never crash
- **The Pop Multiplier is an amplifier, not a score dimension**: It multiplies the base score (0.85–1.15), not weighted into the sum
- **eBay collector is IP-rate-limited**: 403 after consecutive requests. It works on GitHub Actions (fresh IP each run) but may fail locally
- **JustTCG daily cache**: `data/jp_cache.json` prevents redundant API calls within same day
- **First run has no history**: All signals show "insufficient_data" until 30 days of price data accumulate
- **Card DB UNIQUE constraint**: `(name, set_name, card_number)` — same card from different sets/variants gets separate rows
- **Reddit collector uses public JSON**: No API key needed. old.reddit.com/hot.json returns 50 posts per request
- **Frontend reads static JSON**: Next.js getStaticProps reads from `../data/cards.json` at build time

## Scoring Formula

```
Score = Price_Signal × 0.4 + IP_Heat × 0.3 + Volume_Signal × 0.2 + Momentum × 0.1

Price_Signal: normalized best market price (US/EU/JP). Default 30.
IP_Heat: Pokemon popularity tier from config/pokemon_tiers.json (T1=100 to T4=50, default 30).
Volume_Signal: normalized Reddit mention count. Default 30.
Momentum: price trend 0-100 (50=neutral). From JustTCG 30d/7d change or supply_demand history.
All scores capped to 5-100 range.
```

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
