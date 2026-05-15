import logging

from bs4 import BeautifulSoup

from .base import BaseCollector, CardData

logger = logging.getLogger(__name__)

TCGPLAYER_URL = "https://www.tcgplayer.com/search/pokemon/product"


class TCGPlayerCollector(BaseCollector):
    name = "tcgplayer"

    def __init__(self):
        super().__init__(min_delay=5.0, max_delay=10.0)

    def collect(self) -> list[CardData]:
        results = []
        try:
            resp = self.get(TCGPLAYER_URL)
            soup = BeautifulSoup(resp.text, "lxml")

            cards = soup.select("div.search-result")
            for card_el in cards:
                name_el = card_el.select_one(".search-result__title")
                price_el = card_el.select_one(".search-result__market-price")
                set_el = card_el.select_one(".search-result__subtitle")

                if not name_el:
                    continue

                name = name_el.get_text(strip=True)
                set_name = set_el.get_text(strip=True) if set_el else ""

                price = None
                if price_el:
                    price_text = price_el.get_text(strip=True).replace("$", "").replace(",", "")
                    try:
                        price = float(price_text)
                    except ValueError:
                        pass

                results.append(CardData(
                    name=name,
                    set_name=set_name,
                    price=price,
                    source="tcgplayer",
                ))

            logger.info("[tcgplayer] Collected %d cards", len(results))
        except Exception as e:
            logger.error("[tcgplayer] Collection failed: %s", e)

        return results
