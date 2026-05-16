# APIs & Auth
Keys in `.env` → `os.getenv()` → GitHub Secrets → workflow env vars. `.env.example` tracks key names without values.

**No-auth APIs**: PokemonTCG (`api.pokemontcg.io/v2`): paginated `page`/`pageSize`, filter `q=field:value`, select fields. Reddit: `old.reddit.com/r/{sub}/hot.json` → `data.children[].data`.

**Auth APIs**: JustTCG (`x-api-key` header, 100 req/day): query `game=pokemon-japan`, filter variants by `language`/`condition` client-side. **Daily-cache Everything**: never repeat same query in one day.

**Scraping**: eBay: cookie-prime homepage → search `LH_Sold=1&LH_Complete=1` → parse `li.s-item`. IP-rate-limited — works on CI fresh IP, may 403 locally.

**Degradation**: Every collector checks `os.getenv("KEY")` first → missing key = `return []`. Wrap `collect()` in try/except → log warning, never throw. All sources return `list[CardData]` (standard fields + `extra: dict`).
