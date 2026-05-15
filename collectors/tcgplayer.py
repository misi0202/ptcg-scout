import logging

from bs4 import BeautifulSoup

from .base import BaseCollector, CardData

logger = logging.getLogger(__name__)

TCGPLAYER_URL = "https://www.tcgplayer.com/search/pokemon/product"
TCGPLAYER_FALLBACK = "https://www.tcgplayer.com/search/pokemon/151"


class TCGPlayerCollector(BaseCollector):
    name = "tcgplayer"

    def __init__(self):
        super().__init__(min_delay=5.0, max_delay=10.0)
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def _try_page(self, url: str) -> list[CardData]:
        results = []
        resp = self.get(url)
        logger.info("[tcgplayer] Response size: %d, status: %d",
                   len(resp.text), resp.status_code)

        soup = BeautifulSoup(resp.text, "lxml")

        selectors = [
            "div.search-result",
            "div[class*=product]",
            "div[class*=search-result]",
            "div.product-listing",
            "a[class*=product]",
        ]
        cards = []
        for sel in selectors:
            cards = soup.select(sel)
            if cards:
                logger.info("[tcgplayer] Matched %d cards with: %s", len(cards), sel)
                break

        for card_el in cards:
            name_el = (
                card_el.select_one("[class*=title]")
                or card_el.select_one("[class*=name]")
                or card_el.select_one("h3")
            )
            price_el = (
                card_el.select_one("[class*=price]")
                or card_el.select_one("[class*=market]")
                or card_el.select_one("span[class*=price]")
            )
            set_el = (
                card_el.select_one("[class*=subtitle]")
                or card_el.select_one("[class*=set]")
            )

            if not name_el:
                continue

            name = name_el.get_text(strip=True)
            set_name = set_el.get_text(strip=True) if set_el else ""
            price = None
            if price_el:
                text = price_el.get_text(strip=True).replace("$", "").replace(",", "")
                try:
                    price = float(text)
                except ValueError:
                    pass

            results.append(CardData(
                name=name,
                set_name=set_name,
                price=price,
                source="tcgplayer",
            ))

        return results

    def collect(self) -> list[CardData]:
        results = []
        for url in (TCGPLAYER_URL, TCGPLAYER_FALLBACK):
            try:
                results = self._try_page(url)
                if results:
                    break
            except Exception as e:
                logger.error("[tcgplayer] %s failed: %s", url, e)
                continue

        logger.info("[tcgplayer] Collected %d cards", len(results))
        return results
