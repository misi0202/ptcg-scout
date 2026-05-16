"""JustTCG collector — Japanese Pokemon card pricing.

Free tier: 1,000 calls/month, 100/day.
Daily cache prevents redundant API calls within the same day."""

import json
import logging
import os
import time
from datetime import date

import requests

logger = logging.getLogger(__name__)

API_BASE = "https://api.justtcg.com/v1"
API_KEY = os.getenv("JUSTTCG_API_KEY", "")

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CACHE_FILE = os.path.join(CACHE_DIR, "jp_cache.json")


def _load_cache() -> dict:
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_cache(cache: dict):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def lookup_jp_card(name: str) -> dict | None:
    """Look up JP card data, using daily cache to save API quota."""
    if not API_KEY:
        return None

    today = date.today().isoformat()

    cache = _load_cache()
    cached = cache.get(name)
    if cached and cached.get("fetched_at") == today:
        logger.debug("[justtcg] Cache hit: %s", name[:40])
        cached.pop("fetched_at", None)
        return cached

    headers = {"x-api-key": API_KEY, "Accept": "application/json"}
    params = {"game": "pokemon-japan", "name": name, "limit": 5}

    for attempt in range(3):
        try:
            resp = requests.get(f"{API_BASE}/cards", headers=headers, params=params, timeout=20)
            if resp.status_code == 429:
                time.sleep(5 + attempt * 5)
                continue
            if resp.status_code != 200:
                logger.warning("[justtcg] %d for '%s'", resp.status_code, name[:40])
                return None

            data = resp.json()
            cards = data.get("data", [])
            if not cards:
                cache[name] = {"fetched_at": today}  # cache miss too
                _save_cache(cache)
                return None

            for card in cards:
                for v in card.get("variants", []):
                    if v.get("language") != "Japanese":
                        continue
                    if v.get("condition") not in ("Near Mint", "Lightly Played"):
                        continue

                    jp_data = {
                        "jp_price": v.get("price"),
                        "jp_price_change_7d": v.get("priceChange7d"),
                        "jp_price_change_30d": v.get("priceChange30d"),
                        "jp_condition": v.get("condition"),
                        "jp_printing": v.get("printing"),
                        "jp_name": card.get("name", ""),
                        "jp_set": card.get("set_name", ""),
                        "jp_rarity": card.get("rarity", ""),
                        "jp_number": card.get("number", ""),
                        "fetched_at": today,
                    }
                    cache[name] = jp_data
                    _save_cache(cache)
                    jp_data.pop("fetched_at", None)
                    logger.debug("[justtcg] Fetched: %s → ¥%s", name[:40], jp_data["jp_price"])
                    return jp_data

            cache[name] = {"fetched_at": today}
            _save_cache(cache)
            return None

        except Exception as e:
            logger.error("[justtcg] %s", e)
            time.sleep(2)

    return None


def enrich_top_cards(cards: list[dict], max_lookups: int = 50) -> list[dict]:
    """Add JP market data to top-scored cards using daily cache."""
    if not API_KEY:
        logger.info("[justtcg] No API key, skipping JP enrichment")
        return cards

    today = date.today().isoformat()
    cache = _load_cache()
    cached_today = sum(1 for v in cache.values() if v.get("fetched_at") == today)
    api_calls = 0

    for card in cards[:max_lookups]:
        name = card.get("name", "")
        if not name or card.get("jp_price"):
            continue
        if "mention" in name.lower():
            continue

        # Check if we already have today's data cached
        cached = cache.get(name)
        if cached and cached.get("fetched_at") == today:
            cached.pop("fetched_at", None)
            if cached.get("jp_price"):
                card.update(cached)
            continue

        # Only call API if cache miss AND we have quota (max 50 new lookups/day)
        if api_calls >= 50:
            logger.debug("[justtcg] Daily API quota reached (50 new lookups)")
            break

        jp = lookup_jp_card(name)
        api_calls += 1

        if jp:
            card["jp_price"] = jp["jp_price"]
            card["jp_price_change_7d"] = jp.get("jp_price_change_7d")
            card["jp_price_change_30d"] = jp.get("jp_price_change_30d")
            card["jp_name"] = jp["jp_name"]
            card["jp_set"] = jp["jp_set"]
            card["jp_rarity"] = jp.get("jp_rarity", "")
            card["jp_number"] = jp.get("jp_number", "")

        time.sleep(0.75)

    logger.info("[justtcg] JP enriched: %d API calls (%d cached today)",
               api_calls, cached_today)
    return cards
