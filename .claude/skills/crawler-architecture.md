# Crawlers
All collectors extend `collectors.base.BaseCollector` → implement `collect() -> list[CardData]`.

**Session**: `requests.Session` + `HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1, status_forcelist=[429,500,502,503,504]))`. UA pool of 4, rotated per request. Delay: `time.sleep(random.uniform(min,max))` before each `self.get()`.

**Adding a collector**: 1) `collectors/<name>.py` extends BaseCollector 2) set `name` attr 3) implement `collect()` 4) export in `__init__.py` 5) add instance to `collect_all()` in main.py 6) auth check: `os.getenv("KEY")` at top, `return []` if missing.

**CardData contract**: `name, set_name, card_number, pokemon_name, price|None, condition, sale_date, source, extra:dict`. Use `extra` for source-specific fields (rarity, artist, image_url, game, grade, jp_*).

**Error handling**: `collect()` wrapped in `try/except Exception → logger.error → return []`. One collector failure never blocks pipeline. Log prefix: `[source_name]` for grep.

**Rate limits**: APIs: 1-3s between pages. Scrapers: 5-10s, cookie-prime first. 429: exponential backoff via Retry adapter. Daily cache for authenticated APIs to preserve quota.
