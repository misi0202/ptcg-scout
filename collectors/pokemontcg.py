import logging

import requests

from .base import BaseCollector, CardData

logger = logging.getLogger(__name__)

API_BASE = "https://api.pokemontcg.io/v2"

# Rarities to collect (IR/AR level and above)
TARGET_RARITIES = [
    "Illustration Rare",
    "Special Illustration Rare",
    "Art Rare",
    "Ultra Rare",
    "Hyper Rare",
    "Secret Rare",
    "Amazing Rare",
    "Radiant Rare",
    "Shiny Rare",
    "Shiny Ultra Rare",
    "ACE SPEC Rare",
    "Master Ball",
    "Promo",
]


class PokemonTCGCollector(BaseCollector):
    name = "pokemontcg"

    def __init__(self):
        super().__init__(min_delay=1.0, max_delay=2.0)
        self.session.headers.update({"Accept": "application/json"})

    def _get_all_sets(self) -> list[dict]:
        """Fetch all set IDs with series info from the API."""
        try:
            resp = self.session.get(f"{API_BASE}/sets", params={"select": "id,series"}, timeout=30)
            data = resp.json()
            return data.get("data", [])
        except Exception as e:
            logger.error("[pokemontcg] Failed to fetch sets: %s", e)
            return []

    def _fetch_cards(self, query: str, page_size: int = 50) -> list[dict]:
        url = f"{API_BASE}/cards"
        all_cards = []
        page = 1
        while page <= 10:  # safety limit
            params = {
                "q": query,
                "pageSize": page_size,
                "page": page,
                "select": "id,name,supertype,subtypes,set,number,rarity,artist,images,tcgplayer,cardmarket",
            }
            resp = self.session.get(url, params=params, timeout=30)
            if resp.status_code != 200:
                logger.warning("[pokemontcg] %d for query=%s page=%d", resp.status_code, query[:60], page)
                break

            data = resp.json()
            cards = data.get("data", [])
            all_cards.extend(cards)
            if len(cards) < page_size:
                break
            page += 1
            self._delay()

        return all_cards

    def collect(self) -> list[CardData]:
        results = []
        seen = set()

        try:
            all_sets = self._get_all_sets()
            logger.info("[pokemontcg] Found %d sets total", len(all_sets))

            rarity_query = " OR ".join(f'rarity:"{r}"' for r in TARGET_RARITIES)

            for s in all_sets:
                set_id = s.get("id", "")
                series = (s.get("series", "") or "").lower()
                is_jp = any(kw in series for kw in ("japan", "japanese", "jp"))
                game = "pokemon-jp" if is_jp else "pokemon"

                query = f'set.id:{set_id} ({rarity_query})'
                cards = self._fetch_cards(query)

                for card in cards:
                    card_id = card.get("id", "")
                    if card_id in seen:
                        continue
                    seen.add(card_id)

                    supertype = card.get("supertype", "")
                    if supertype in ("Trainer", "Energy"):
                        continue

                    name = card.get("name", "")
                    set_info = card.get("set", {})
                    set_name = set_info.get("name", "") if isinstance(set_info, dict) else ""

                    tcg = card.get("tcgplayer", {}) or {}
                    tcg_prices = tcg.get("prices", {}) or {}

                    price = None
                    for variant in ("reverseHolofoil", "holofoil", "normal"):
                        vp = tcg_prices.get(variant, {}) or {}
                        if vp.get("market"):
                            price = float(vp["market"])
                            break

                    rarity = card.get("rarity", "") or ""
                    artist = card.get("artist", "") or ""
                    images = card.get("images", {}) or {}
                    image_url = images.get("large") or images.get("small") or ""

                    pokemon_name = name

                    cm = card.get("cardmarket", {}) or {}
                    cm_prices = cm.get("prices", {}) or {}
                    cm_price = cm_prices.get("trendPrice") or cm_prices.get("averageSellPrice")

                    results.append(CardData(
                        name=name,
                        set_name=set_name,
                        card_number=card.get("number", "") or "",
                        pokemon_name=pokemon_name,
                        price=price,
                        source="pokemontcg",
                        extra={
                            "rarity": rarity,
                            "artist": artist,
                            "image_url": image_url,
                            "game": game,
                            "tcgplayer_low": (tcg_prices.get("normal", {}) or {}).get("low"),
                            "tcgplayer_mid": (tcg_prices.get("normal", {}) or {}).get("mid"),
                            "tcgplayer_high": (tcg_prices.get("normal", {}) or {}).get("high"),
                            "cardmarket_trend": cm_prices.get("trendPrice"),
                            "cardmarket_avg": cm_price,
                        },
                    ))

                if cards:
                    logger.info("[pokemontcg] Set %s (%s): %d cards (total: %d)", set_id, game, len(cards), len(results))

            logger.info("[pokemontcg] Collected %d high-rarity cards from %d sets", len(results), len(all_sets))

        except Exception as e:
            logger.error("[pokemontcg] Collection failed: %s", e)

        return results
