"""TCG Price Lookup collector — JP price lookup for top-scored cards.

The free tier has tight rate limits (~10 req/min). This collector is designed
to supplement existing English card data by looking up Japanese market prices
for cards that have already been scored by the main pipeline.

It's NOT used during initial collection. Call enrich_jp_prices() after scoring."""

import logging
import os
import time

import requests

logger = logging.getLogger(__name__)

API_BASE = "https://api.tcgpricelookup.com/v1"
API_KEY = os.getenv("TCGPRICELOOKUP_API_KEY", "")


def lookup_jp_card(name: str) -> dict | None:
    """Look up a single card's JP market price by name."""
    if not API_KEY:
        return None

    headers = {"x-api-key": API_KEY, "Accept": "application/json"}
    url = f"{API_BASE}/cards/search"
    params = {"game": "pokemon-jp", "q": name, "limit": 3}

    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=20)
            if resp.status_code == 429:
                time.sleep(5 + attempt * 5)
                continue
            if resp.status_code != 200:
                logger.warning("[tcgpricelookup] %d for '%s'", resp.status_code, name[:40])
                return None

            data = resp.json()
            cards = data.get("data", [])
            if not cards:
                return None

            # Return first matching card with price
            for card in cards:
                prices = card.get("prices", {}) or {}
                raw = (prices.get("raw", {}) or {}).get("near_mint", {}) or {}
                tcg = raw.get("tcgplayer", {}) or {}
                price = tcg.get("market") or tcg.get("mid")
                if price:
                    return {
                        "jp_price": float(price),
                        "jp_name": card.get("name", ""),
                        "jp_set": (card.get("set", {}) or {}).get("name", ""),
                        "jp_rarity": card.get("rarity", ""),
                        "jp_image_url": card.get("image_url", ""),
                        "jp_tcgplayer_low": tcg.get("low"),
                        "jp_tcgplayer_mid": tcg.get("mid"),
                        "jp_tcgplayer_market": tcg.get("market"),
                    }
            return None
        except Exception as e:
            logger.error("[tcgpricelookup] %s", e)
            time.sleep(2)

    return None


def enrich_top_cards(cards: list[dict], max_lookups: int = 30) -> list[dict]:
    """Add JP market data to the top N cards."""
    if not API_KEY:
        logger.info("[tcgpricelookup] No API key, skipping JP enrichment")
        return cards

    enriched = 0
    for card in cards[:max_lookups]:
        name = card.get("name", "")
        if not name:
            continue

        jp = lookup_jp_card(name)
        if jp:
            card["jp_price"] = jp["jp_price"]
            card["jp_name"] = jp["jp_name"]
            card["jp_set"] = jp["jp_set"]
            card["jp_rarity"] = jp["jp_rarity"]
            card["jp_image_url"] = jp["jp_image_url"]
            enriched += 1

        time.sleep(1.0)  # respectful rate limit

    logger.info("[tcgpricelookup] Enriched %d/%d cards with JP data", enriched, min(len(cards), max_lookups))
    return cards
