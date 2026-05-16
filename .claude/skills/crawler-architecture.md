# Crawler Architecture Rules

## Base Collector Pattern
All data sources extend `collectors.base.BaseCollector`:
- `name: str` — unique identifier used in logging
- `__init__(min_delay, max_delay)` — sets up `requests.Session` with retry adapter
- `collect() -> list[CardData]` — abstract, implement per source
- `get(url)` — thin wrapper: rotates UA, sleeps random delay, logs, calls `session.get()`

## Session Setup (do not deviate)
```python
Retry(total=3, backoff_factor=1.0, status_forcelist=[429, 500, 502, 503, 504])
HTTPAdapter(max_retries=retries) → session.mount("https://", adapter)
```
- UA rotation pool: 4 browser-like User-Agent strings, pick via `random.choice`
- Default timeout: 30s for API calls, use longer (60s) for heavy pages

## When Adding a New Collector
1. Create `collectors/<source>.py` extending `BaseCollector`
2. Set `name` class attribute
3. Implement `collect()` returning `list[CardData]`
4. Add to `collectors/__init__.py` exports
5. Add instance to `collect_all()` list in `main.py`
6. If authenticated: check `os.getenv("KEY")` at top of `collect()`, return `[]` on missing
7. If scraping: handle 403/429 by returning `[]` after logging warning

## CardData Contract
```python
CardData(
    name=str,          # card title
    set_name=str,      # set/series name
    card_number=str,   # collector number
    pokemon_name=str,  # detected Pokemon (for IP scoring)
    price=float|None,  # market price
    condition=str,     # "PSA 10", "Near Mint", etc
    sale_date=str,     # ISO date of sale
    source=str,        # collector name ("pokemontcg", "ebay", "reddit")
    extra=dict,        # source-specific fields (rarity, artist, image_url, game, etc)
)
```

## Error Handling
- Always wrap `collect()` body in `try/except Exception`, log error, return `[]`
- Never let one collector failure stop the pipeline
- Log with `logger.info/warning/error` using module-level logger
- Prefix log messages with `[source_name]` for grep-ability

## Rate Limiting
- API collectors: 1-3s delay between paginated requests
- Web scrapers: 5-10s delay, cookie-prime before first request
- Use `time.sleep(random.uniform(min, max))` not fixed delays
- Respect HTTP 429: exponential backoff with Retry adapter
