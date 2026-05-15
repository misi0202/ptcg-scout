import time
import random
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


@dataclass
class CardData:
    name: str
    set_name: str
    card_number: str = ""
    pokemon_name: str = ""
    price: Optional[float] = None
    condition: str = ""
    sale_date: str = ""
    source: str = ""
    extra: dict = field(default_factory=dict)


class BaseCollector(ABC):
    name: str = "base"

    def __init__(self, min_delay: float = 3.0, max_delay: float = 7.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.session = self._build_session()

    def _build_session(self) -> requests.Session:
        s = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retries)
        s.mount("https://", adapter)
        s.mount("http://", adapter)
        s.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        return s

    def _rotate_ua(self):
        self.session.headers["User-Agent"] = random.choice(USER_AGENTS)

    def _delay(self):
        time.sleep(random.uniform(self.min_delay, self.max_delay))

    def get(self, url: str, **kwargs) -> requests.Response:
        self._rotate_ua()
        self._delay()
        logger.info("[%s] GET %s", self.name, url[:80])
        return self.session.get(url, timeout=30, **kwargs)

    @abstractmethod
    def collect(self) -> list[CardData]:
        ...
