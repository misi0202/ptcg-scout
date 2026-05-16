# API Conventions

## Authentication
- All API keys live in `.env` → loaded via `python-dotenv` → accessed via `os.getenv("KEY_NAME")`
- Keys passed to GitHub Actions via `secrets.*` → injected as env vars in workflow
- `.env.example` tracks required keys without values

## External API Patterns

### Free / No-Auth APIs
- **Pokemon TCG API** (`api.pokemontcg.io/v2`): no key, JSON responses, paginated with `page`/`pageSize`. Filter with `q=` parameter using field:value syntax (`set.id:sv1`, `rarity:"Illustration Rare"`). Select specific fields with `select=id,name,set,tcgplayer`.
- **Reddit public JSON** (`old.reddit.com/r/{sub}/hot.json`): no key, returns nested `data.children[].data`. Rate limit: ~2s between requests.

### Authenticated APIs
- **JustTCG** (`api.justtcg.com/v1`): `x-api-key` header. Free tier: 100 req/day. Query `game=pokemon-japan` for JP cards. Variants embedded in response, filter by `language`/`condition` client-side. **Must daily-cache results** — never make the same query twice in one day.

### Web Scraping
- **eBay sold listings**: cookie-prime homepage first, then search `LH_Sold=1&LH_Complete=1`. Parse with BeautifulSoup+lxml, selector `li.s-item`. **IP-rate-limited** — works on GitHub Actions (fresh IP), may 403 locally after repeated requests.

## Graceful Degradation
- All collectors return `[]` when API key missing, 403, or rate-limited
- Log warning never throw on API failure
- `os.getenv("KEY")` check at top of `collect()` method, return early if missing

## Data Model
- Unified output: `CardData` dataclass (`collectors/base.py`)
- Standard fields: name, set_name, card_number, pokemon_name, price, condition, sale_date, source
- Extended fields in `extra: dict` (artist, rarity, image_url, jp_*, grade, keywords)
