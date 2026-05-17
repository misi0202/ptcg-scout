"""JustTCG Japanese card collector — fetches JP cards with prices.

Uses JustTCG API (pokemon-japan game) to discover JP-market cards.
Caches results daily; preserves data from previous runs when API key is missing."""

import json
import logging
import os
import time
from datetime import date

import requests

from .base import CardData

logger = logging.getLogger(__name__)

API_BASE = "https://api.justtcg.com/v1"
API_KEY = os.getenv("JUSTTCG_API_KEY", "")

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "jp_cards_cache.json")
CACHE_MAX_AGE_DAYS = 30  # Use cache up to 30 days old if API key unavailable

# Popular JP-exclusive or JP-primary cards to discover
JP_SEARCH_QUERIES = [
    "pikachu",
    "charizard",
    "mew",
    "mewtwo",
    "eevee",
    "umbreon",
    "gengar",
    "rayquaza",
    "lugia",
    "ho-oh",
]


def _load_cache() -> dict:
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"cards": [], "fetched_at": ""}


def _save_cache(data: dict):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def collect_jp_cards() -> list[CardData]:
    """Collect JP cards from JustTCG. Uses cache if API key is missing."""
    today = date.today().isoformat()

    if not API_KEY:
        cache = _load_cache()
        cached_date = cache.get("fetched_at", "")
        if cached_date:
            days_old = (date.today() - date.fromisoformat(cached_date)).days
            if days_old <= CACHE_MAX_AGE_DAYS and cache.get("cards"):
                logger.info("[justtcg_jp] Using cached JP data (%d cards, %d days old)",
                            len(cache["cards"]), days_old)
                return [_dict_to_carddata(d) for d in cache["cards"]]
        logger.info("[justtcg_jp] No API key and no fresh cache — returning empty")
        return []

    headers = {"x-api-key": API_KEY, "Accept": "application/json"}
    collected = []
    seen_names = set()

    for query in JP_SEARCH_QUERIES:
        try:
            params = {"game": "pokemon-japan", "name": query, "limit": 5}
            resp = requests.get(f"{API_BASE}/cards", headers=headers, params=params, timeout=20)

            if resp.status_code == 429:
                logger.warning("[justtcg_jp] Rate limited, stopping JP collection")
                time.sleep(10)
                break
            if resp.status_code != 200:
                logger.warning("[justtcg_jp] %d for query='%s'", resp.status_code, query)
                continue

            cards = resp.json().get("data", [])
            for card in cards:
                name = card.get("name", "")
                if name in seen_names:
                    continue
                seen_names.add(name)

                # Find best Japanese variant
                for v in card.get("variants", []):
                    if v.get("language") != "Japanese":
                        continue
                    if v.get("condition") not in ("Near Mint", "Lightly Played"):
                        continue

                    collected.append(CardData(
                        name=name,
                        set_name=card.get("set_name", ""),
                        card_number=card.get("number", "") or "",
                        pokemon_name=name,
                        price=float(v.get("price", 0)) if v.get("price") else None,
                        source="justtcg",
                        extra={
                            "game": "pokemon-jp",
                            "rarity": card.get("rarity", ""),
                            "image_url": card.get("image_url", ""),
                            "jp_condition": v.get("condition"),
                            "jp_printing": v.get("printing"),
                            "jp_price_change_7d": v.get("priceChange7d"),
                            "jp_price_change_30d": v.get("priceChange30d"),
                        },
                    ))
                    break

            time.sleep(1.0)

        except Exception as e:
            logger.error("[justtcg_jp] Query '%s' failed: %s", query, e)

    logger.info("[justtcg_jp] Collected %d JP cards", len(collected))

    # Update cache
    cache_data = {
        "cards": [_carddata_to_dict(c) for c in collected],
        "fetched_at": today,
    }
    _save_cache(cache_data)

    return collected


def _carddata_to_dict(c: CardData) -> dict:
    return {
        "name": c.name,
        "set_name": c.set_name,
        "card_number": c.card_number,
        "pokemon_name": c.pokemon_name,
        "price": c.price,
        "source": c.source,
        "extra": c.extra,
    }


def _dict_to_carddata(d: dict) -> CardData:
    return CardData(
        name=d.get("name", ""),
        set_name=d.get("set_name", ""),
        card_number=d.get("card_number", ""),
        pokemon_name=d.get("pokemon_name", ""),
        price=d.get("price"),
        source=d.get("source", "justtcg"),
        extra=d.get("extra", {}),
    )
