"""Reddit collector using public JSON endpoints (no API key needed)."""

import logging
import time
from datetime import datetime

from .base import BaseCollector, CardData

logger = logging.getLogger(__name__)

SUBREDDITS = ["PokemonTCG", "PokeInvesting", "PokemonCardValue"]

KEYWORDS = [
    "psa10", "psa 10", "graded", "gem mint", "chase card",
    "undervalued", "sleeper", "potential", "invest", "pickup",
    "art", "beautiful", "fire", "stunning",
]

POKEMON_HOT_LIST = [
    "charizard", "pikachu", "gengar", "mewtwo", "mew",
    "umbreon", "espeon", "sylveon", "vaporeon", "jolteon", "flareon",
    "rayquaza", "lugia", "ho-oh", "eevee", "gyarados", "dragonite",
    "tyranitar", "gardevoir", "greninja", "mimikyu", "snorlax",
    "blaziken", "darkrai", "celebi", "jirachi", "arceus",
    "lucario", "garchomp", "metagross", "salamence", "zoroark",
    "magikarp", "latias", "latios", "giratina",
]


class RedditCollector(BaseCollector):
    name = "reddit"

    def __init__(self):
        super().__init__(min_delay=3.0, max_delay=5.0)
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
        })

    def _fetch_subreddit(self, subreddit: str, sort: str = "hot", limit: int = 50) -> list[dict]:
        url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit={limit}"
        for attempt in range(3):
            try:
                resp = self.session.get(url, timeout=20)

                if resp.status_code == 200:
                    data = resp.json()
                    posts = data.get("data", {}).get("children", [])
                    return [p["data"] for p in posts if p.get("kind") == "t3"]

                if resp.status_code in (403, 429):
                    wait = (attempt + 1) * 5
                    logger.warning("[reddit] r/%s %s: %d (retry in %ds)", subreddit, sort, resp.status_code, wait)
                    time.sleep(wait)
                    continue

                logger.warning("[reddit] r/%s %s: %d", subreddit, sort, resp.status_code)
                return []

            except Exception as e:
                logger.error("[reddit] r/%s fetch error: %s", subreddit, e)
                if attempt < 2:
                    time.sleep(3)
                else:
                    return []

        return []

    def collect(self) -> list[CardData]:
        results = []

        for subreddit in SUBREDDITS:
            try:
                posts = self._fetch_subreddit(subreddit, "hot", 50)
                posts += self._fetch_subreddit(subreddit, "new", 25)

                for post in posts:
                    title = post.get("title", "")
                    selftext = post.get("selftext", "")
                    text = (title + " " + selftext).lower()

                    matched_keywords = [kw for kw in KEYWORDS if kw in text]
                    matched_pokemon = [pk for pk in POKEMON_HOT_LIST if pk in text]

                    if not matched_pokemon:
                        continue

                    created = post.get("created_utc", 0)
                    created_str = datetime.fromtimestamp(created).isoformat() if created else ""

                    for pokemon in matched_pokemon:
                        results.append(CardData(
                            name=f"{pokemon.title()} Reddit mention",
                            set_name=subreddit,
                            pokemon_name=pokemon,
                            source="reddit",
                            extra={
                                "keywords": matched_keywords,
                                "score": post.get("score", 1),
                                "comments": post.get("num_comments", 0),
                                "url": f"https://reddit.com{post.get('permalink', '')}",
                                "created_utc": created_str,
                                "title": title,
                            },
                        ))

                logger.info("[reddit] r/%s: %d posts, %d pokemon mentions",
                           subreddit, len(posts), len(results))

                time.sleep(3.0)

            except Exception as e:
                logger.error("[reddit] r/%s failed: %s", subreddit, e)

        logger.info("[reddit] Collected %d mentions from %d subreddits",
                   len(results), len(SUBREDDITS))
        return results
