"""JustTCG collector — Japanese Pokemon card pricing.

Free tier: 1,000 calls/month, 100/day.
Used to enrich TOP cards with JP market prices via pokemon-japan game."""

import logging
import os
import time

import requests

logger = logging.getLogger(__name__)

API_BASE = "https://api.justtcg.com/v1"
API_KEY = os.getenv("JUSTTCG_API_KEY", "")


def lookup_jp_card(name: str) -> dict | None:
    """Look up a single card's JP market data. Returns best NM variant."""
    if not API_KEY:
        return None

    headers = {"x-api-key": API_KEY, "Accept": "application/json"}
    url = f"{API_BASE}/cards"
    params = {"game": "pokemon-japan", "name": name, "limit": 5}

    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=20)
            if resp.status_code == 429:
                time.sleep(5 + attempt * 5)
                continue
            if resp.status_code != 200:
                logger.warning("[justtcg] %d for '%s'", resp.status_code, name[:40])
                return None

            data = resp.json()
            cards = data.get("data", [])
            if not cards:
                return None

            # Find best NM Japanese variant
            for card in cards:
                for v in card.get("variants", []):
                    if v.get("language") != "Japanese":
                        continue
                    if v.get("condition") not in ("Near Mint", "Lightly Played"):
                        continue

                    return {
                        "jp_price": v.get("price"),
                        "jp_price_change_7d": v.get("priceChange7d"),
                        "jp_price_change_30d": v.get("priceChange30d"),
                        "jp_condition": v.get("condition"),
                        "jp_printing": v.get("printing"),
                        "jp_name": card.get("name", ""),
                        "jp_set": card.get("set_name", ""),
                        "jp_rarity": card.get("rarity", ""),
                        "jp_number": card.get("number", ""),
                    }
            return None
        except Exception as e:
            logger.error("[justtcg] %s", e)
            time.sleep(2)

    return None


def enrich_top_cards(cards: list[dict], max_lookups: int = 50) -> list[dict]:
    """Add JP market data to top-scored cards."""
    if not API_KEY:
        logger.info("[justtcg] No API key, skipping JP enrichment")
        return cards

    enriched = 0
    for card in cards[:max_lookups]:
        name = card.get("name", "")
        if not name or card.get("jp_price"):
            continue

        # Skip cards that are just mentions (no real card data)
        if "mention" in name.lower():
            continue

        jp = lookup_jp_card(name)
        if jp:
            card["jp_price"] = jp["jp_price"]
            card["jp_price_change_7d"] = jp.get("jp_price_change_7d")
            card["jp_price_change_30d"] = jp.get("jp_price_change_30d")
            card["jp_name"] = jp["jp_name"]
            card["jp_set"] = jp["jp_set"]
            card["jp_rarity"] = jp.get("jp_rarity", "")
            card["jp_number"] = jp.get("jp_number", "")
            enriched += 1
            logger.debug("[justtcg] Enriched: %s → ¥%s", name[:40], jp["jp_price"])

        time.sleep(0.75)  # stay under rate limit

    logger.info("[justtcg] Enriched %d/%d cards with JP data", enriched, min(len(cards), max_lookups))
    return cards
