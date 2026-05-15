import logging

from bs4 import BeautifulSoup

from .base import BaseCollector, CardData

logger = logging.getLogger(__name__)

EBAY_SOLD_URL = (
    "https://www.ebay.com/sch/i.html"
    "?_nkw=pokemon+psa+10&_sop=10&LH_Sold=1&LH_Complete=1&_ipg=60"
)


class EbayCollector(BaseCollector):
    name = "ebay"

    def __init__(self, min_delay: float = 5.0, max_delay: float = 10.0):
        super().__init__(min_delay, max_delay)
        self.session.headers.update({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        })

    def _parse_price(self, text: str) -> float | None:
        text = text.replace("$", "").replace(",", "").strip()
        try:
            return float(text.split()[0])
        except (ValueError, IndexError):
            return None

    def collect(self) -> list[CardData]:
        results = []
        try:
            resp = self.get(EBAY_SOLD_URL)
            logger.info("[ebay] Response size: %d bytes, status: %d",
                       len(resp.text), resp.status_code)

            soup = BeautifulSoup(resp.text, "lxml")

            selectors = [
                "li.s-item",
                "div.s-item",
                "div.srp-results li",
                "li.srp-results__item",
            ]

            items = []
            for sel in selectors:
                items = soup.select(sel)
                if items:
                    logger.info("[ebay] Matched %d items with selector: %s", len(items), sel)
                    break

            for item in items:
                title_el = None
                for t_sel in [".s-item__title", "h3.s-item__title", "a.s-item__link"]:
                    title_el = item.select_one(t_sel)
                    if title_el:
                        break

                price_el = None
                for p_sel in [".s-item__price", ".s-item__detail--price", "span.ITALIC"]:
                    price_el = item.select_one(p_sel)
                    if price_el:
                        break

                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                if not title or "Shop on eBay" in title:
                    continue

                price = None
                if price_el:
                    price = self._parse_price(price_el.get_text(strip=True))

                results.append(CardData(
                    name=title,
                    set_name="",
                    price=price,
                    condition="PSA 10",
                    source="ebay",
                ))

            logger.info("[ebay] Parsed %d sold listings", len(results))
        except Exception as e:
            logger.error("[ebay] Collection failed: %s", e)

        return results
