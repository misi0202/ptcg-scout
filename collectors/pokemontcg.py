import logging

import requests

from .base import BaseCollector, CardData

logger = logging.getLogger(__name__)

API_BASE = "https://api.pokemontcg.io/v2"

MODERN_SETS = [
    # Scarlet & Violet
    "sv1", "sv2", "sv2a", "sv3", "sv3pt5", "sv4", "sv4pt5",
    "sv5", "sv6", "sv6pt5", "sv7", "sv8", "sv8pt5", "sv9", "sv10",
    # Sword & Shield
    "swsh1", "swsh2", "swsh3", "swsh3pt5", "swsh4", "swsh4pt5",
    "swsh5", "swsh6", "swsh7", "swsh8", "swsh9", "swsh10",
    "swsh10pt5", "swsh11", "swsh12", "swsh12pt5",
]

POKEMON_NAMES = [
    "pikachu", "charizard", "gengar", "mewtwo", "mew",
    "umbreon", "espeon", "sylveon", "vaporeon", "jolteon", "flareon",
    "rayquaza", "lugia", "ho-oh", "eevee", "gyarados", "dragonite",
    "tyranitar", "gardevoir", "greninja", "mimikyu", "snorlax",
    "blaziken", "darkrai", "celebi", "jirachi", "arceus",
    "lucario", "zoroark", "garchomp", "metagross", "salamence",
]


class PokemonTCGCollector(BaseCollector):
    name = "pokemontcg"

    def __init__(self):
        super().__init__(min_delay=1.0, max_delay=2.0)
        self.session.headers.update({"Accept": "application/json"})

    def _fetch_cards(self, query: str, page_size: int = 50) -> list[dict]:
        url = f"{API_BASE}/cards"
        all_cards = []
        page = 1
        while True:
            params = {"q": query, "pageSize": page_size, "page": page,
                       "select": "id,name,supertype,subtypes,set,number,rarity,artist,nationalPokedexNumbers,tcgplayer,cardmarket"}
            resp = self.session.get(url, params=params, timeout=30)
            if resp.status_code != 200:
                logger.warning("[pokemontcg] %d for query=%s page=%d", resp.status_code, query[:50], page)
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
            # Fetch cards by set
            for set_id in MODERN_SETS:
                cards = self._fetch_cards(f"set.id:{set_id}")
                for card in cards:
                    card_id = card.get("id", "")
                    if card_id in seen:
                        continue
                    seen.add(card_id)

                    # Skip non-Pokemon cards
                    supertype = card.get("supertype", "")
                    if supertype in ("Trainer", "Energy"):
                        continue

                    name = card.get("name", "")
                    set_info = card.get("set", {})
                    set_name = set_info.get("name", "") if isinstance(set_info, dict) else ""

                    tcg = card.get("tcgplayer", {}) or {}
                    tcg_prices = tcg.get("prices", {}) or {}

                    # Use holofoil/reverseHolofoil market price, fallback to normal
                    price = None
                    for variant in ("reverseHolofoil", "holofoil", "normal"):
                        vp = tcg_prices.get(variant, {}) or {}
                        if vp.get("market"):
                            price = float(vp["market"])
                            break

                    # Pokemon name comes from the card name itself
                    # (API card names contain the Pokemon name directly)
                    pokemon_name = name

                    rarity = card.get("rarity", "") or ""
                    artist = card.get("artist", "") or ""

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
                            "tcgplayer_low": tcg_prices.get("normal", {}).get("low") if tcg_prices else None,
                            "tcgplayer_mid": tcg_prices.get("normal", {}).get("mid") if tcg_prices else None,
                            "tcgplayer_high": tcg_prices.get("normal", {}).get("high") if tcg_prices else None,
                        },
                    ))

                logger.info("[pokemontcg] Set %s: %d cards (total: %d)", set_id, len(cards), len(results))

            logger.info("[pokemontcg] Collected %d cards from %d sets", len(results), len(MODERN_SETS))

        except Exception as e:
            logger.error("[pokemontcg] Collection failed: %s", e)

        return results
