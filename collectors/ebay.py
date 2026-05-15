import logging
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

from .base import BaseCollector, CardData

logger = logging.getLogger(__name__)

EBAY_SOLD_URL = "https://www.ebay.com/sch/i.html?_nkw=pokemon+psa+10&_sop=10&LH_Sold=1&LH_Complete=1&_ipg=120"


class EbayCollector(BaseCollector):
    name = "ebay"

    def __init__(self, min_delay: float = 5.0, max_delay: float = 10.0):
        super().__init__(min_delay, max_delay)

    def collect(self) -> list[CardData]:
        results = []
        try:
            resp = self.get(EBAY_SOLD_URL)
            soup = BeautifulSoup(resp.text, "lxml")
            items = soup.select("li.s-item")

            for item in items:
                title_el = item.select_one(".s-item__title")
                price_el = item.select_one(".s-item__price")
                date_el = item.select_one(".s-item__title--tagblock__COMPLETED")

                if not title_el or not price_el:
                    continue

                title = title_el.text.strip()
                price_text = price_el.text.strip().replace("$", "").replace(",", "")

                try:
                    price = float(price_text.split()[0])
                except (ValueError, IndexError):
                    continue

                sale_date = ""
                if date_el:
                    sale_date = date_el.text.strip()

                card = CardData(
                    name=title,
                    set_name="",
                    price=price,
                    condition="PSA 10",
                    sale_date=sale_date,
                    source="ebay",
                )
                results.append(card)

            logger.info("[ebay] Collected %d sold listings", len(results))
        except Exception as e:
            logger.error("[ebay] Collection failed: %s", e)

        return results
