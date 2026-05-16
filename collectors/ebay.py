"""eBay sold listings collector — scrapes sold prices from eBay search.

Uses session cookies (prime homepage first) to avoid 403.
Rate-limited per IP; designed for once-daily use via GitHub Actions."""

import logging
import re
import time

from bs4 import BeautifulSoup

from .base import BaseCollector, CardData

logger = logging.getLogger(__name__)

EBAY_SEARCHES = [
    "pokemon+psa+10+sold",
    "pokemon+psa+9+sold",
    "pokemon+card+psa+graded",
]

BASE_URL = (
    "https://www.ebay.com/sch/i.html"
    "?_nkw={query}&LH_Sold=1&LH_Complete=1&_ipg=60&_sop=13"
)
BEAUTIFULSOUP_PARSER = "lxml"

POKEMON_NAMES = [
    "pikachu", "charizard", "gengar", "mewtwo", "mew",
    "umbreon", "espeon", "sylveon", "vaporeon", "jolteon", "flareon",
    "rayquaza", "lugia", "ho-oh", "eevee", "gyarados", "dragonite",
    "tyranitar", "gardevoir", "greninja", "mimikyu", "snorlax",
    "blaziken", "darkrai", "celebi", "jirachi", "arceus",
    "lucario", "garchomp", "metagross", "salamence", "zoroark",
    "magikarp", "latias", "latios", "giratina",
    "venusaur", "blastoise", "alakazam", "machamp",
    "scizor", "houndoom", "absol", "aegislash",
]


class EbayCollector(BaseCollector):
    name = "ebay"

    def __init__(self):
        super().__init__(min_delay=5.0, max_delay=10.0)
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
        })

    def _prime_cookies(self):
        try:
            self.session.get("https://www.ebay.com", timeout=10)
        except Exception:
            pass

    def _parse_price(self, text: str) -> float | None:
        text = text.replace("$", "").replace(",", "").strip()
        try:
            return float(text.split()[0])
        except (ValueError, IndexError):
            return None

    def _detect_pokemon(self, title: str) -> str:
        name_lower = title.lower()
        for pk in POKEMON_NAMES:
            if pk in name_lower:
                return pk.title()
        return ""

    def collect(self) -> list[CardData]:
        results = []

        self._prime_cookies()
        time.sleep(3)

        for query in EBAY_SEARCHES:
            try:
                self._rotate_ua()
                url = BASE_URL.format(query=query)
                resp = self.session.get(url, timeout=30)

                if resp.status_code == 403:
                    logger.warning("[ebay] 403 Forbidden on '%s' — IP rate-limited, trying next query", query)
                    time.sleep(10)
                    continue
                if resp.status_code != 200:
                    logger.warning("[ebay] %d for query='%s'", resp.status_code, query)
                    continue

                try:
                    soup = BeautifulSoup(resp.text, BEAUTIFULSOUP_PARSER)
                except Exception:
                    soup = BeautifulSoup(resp.text, "html.parser")

                items = soup.select("li.s-item")
                logger.info("[ebay] Query '%s': %d items", query, len(items))

                for item in items:
                    title_el = item.select_one(".s-item__title")
                    price_el = item.select_one(".s-item__price")
                    date_el = item.select_one(".s-item__title--tagblock__COMPLETED")

                    if not title_el or not price_el:
                        continue

                    title = title_el.get_text(strip=True)
                    if "Shop on eBay" in title:
                        continue

                    price = self._parse_price(price_el.get_text(strip=True))
                    if not price or price < 1:
                        continue

                    sale_date = ""
                    if date_el:
                        sale_date = date_el.get_text(strip=True)

                    pokemon_name = self._detect_pokemon(title)
                    if not pokemon_name:
                        continue

                    grade = ""
                    gm = re.search(r"PSA\s*(\d+)", title, re.IGNORECASE)
                    if gm:
                        grade = gm.group(1)

                    results.append(CardData(
                        name=title,
                        set_name="eBay Sold",
                        pokemon_name=pokemon_name,
                        price=price,
                        condition=f"PSA {grade}" if grade else "Graded",
                        sale_date=sale_date,
                        source="ebay",
                        extra={
                            "grade": grade,
                            "title": title,
                        },
                    ))

                time.sleep(5)

            except Exception as e:
                logger.error("[ebay] Query '%s' failed: %s", query, e)

        logger.info("[ebay] Collected %d sold listings", len(results))
        return results
