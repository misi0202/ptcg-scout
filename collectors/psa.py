import logging

from bs4 import BeautifulSoup

from .base import BaseCollector, CardData

logger = logging.getLogger(__name__)

PSA_POP_URL = "https://www.psacard.com/pop/tcg-cards/pokemon/"


class PSACollector(BaseCollector):
    name = "psa"

    def __init__(self):
        super().__init__(min_delay=4.0, max_delay=8.0)
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def collect(self) -> list[CardData]:
        results = []
        try:
            resp = self.get(PSA_POP_URL)
            logger.info("[psa] Response size: %d, status: %d",
                       len(resp.text), resp.status_code)

            soup = BeautifulSoup(resp.text, "lxml")

            row_selectors = [
                "table.pop-report-table tbody tr",
                "table[class*=pop] tbody tr",
                "table tbody tr",
                "div[class*=table] div[class*=row]",
            ]

            rows = []
            for sel in row_selectors:
                rows = soup.select(sel)
                if rows:
                    logger.info("[psa] Matched %d rows with: %s", len(rows), sel)
                    break

            for row in rows:
                cells = row.select("td") or row.select("div[class*=cell]")
                if len(cells) < 4:
                    continue

                card_name = cells[0].get_text(strip=True)
                if not card_name or len(card_name) < 3:
                    continue

                total_pop = 0
                psa10_pop = 0
                for i, cell in enumerate(cells):
                    text = cell.get_text(strip=True).replace(",", "")
                    if "10" in card_name and i == 0:
                        continue
                    if text.isdigit():
                        val = int(text)
                        if i == len(cells) - 1 or psa10_pop == 0:
                            psa10_pop = val
                        else:
                            total_pop = val if val > total_pop else total_pop

                results.append(CardData(
                    name=card_name,
                    set_name="",
                    source="psa",
                    extra={
                        "psa10_pop": psa10_pop,
                        "psa_total_pop": total_pop or psa10_pop,
                    },
                ))

            logger.info("[psa] Collected %d cards from Pop Report", len(results))
        except Exception as e:
            logger.error("[psa] Collection failed: %s", e)

        return results
