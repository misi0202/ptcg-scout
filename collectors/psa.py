import logging

from bs4 import BeautifulSoup

from .base import BaseCollector, CardData

logger = logging.getLogger(__name__)

PSA_POP_URL = "https://www.psacard.com/pop/tcg-cards/pokemon/"
PSA_CERT_URL = "https://www.psacard.com/cert/"


class PSACollector(BaseCollector):
    name = "psa"

    def __init__(self):
        super().__init__(min_delay=4.0, max_delay=8.0)

    def collect(self) -> list[CardData]:
        results = []
        try:
            resp = self.get(PSA_POP_URL)
            soup = BeautifulSoup(resp.text, "lxml")

            rows = soup.select("table.pop-report-table tbody tr")
            for row in rows:
                cells = row.select("td")
                if len(cells) < 5:
                    continue

                card_name = cells[0].get_text(strip=True)
                total_pop_text = cells[2].get_text(strip=True)
                psa10_text = cells[4].get_text(strip=True) if len(cells) > 4 else "0"

                try:
                    total_pop = int(total_pop_text.replace(",", ""))
                    psa10_pop = int(psa10_text.replace(",", ""))
                except ValueError:
                    total_pop = 0
                    psa10_pop = 0

                results.append(CardData(
                    name=card_name,
                    set_name="",
                    source="psa",
                    extra={
                        "psa10_pop": psa10_pop,
                        "psa_total_pop": total_pop,
                    },
                ))

            logger.info("[psa] Collected %d cards from Pop Report", len(results))
        except Exception as e:
            logger.error("[psa] Collection failed: %s", e)

        return results
