"""Reddit collector using public JSON endpoints (no API key needed)."""

import logging
import json
import os
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime

from .base import BaseCollector, CardData

logger = logging.getLogger(__name__)

SUBREDDITS = ["PokemonTCG", "PokeInvesting", "PokemonCardValue"]
CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "reddit_cache.json")
CACHE_MAX_AGE_DAYS = 7

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
                "PTCGScout/0.1 personal market research "
                "(by u/misi0202; contact: https://github.com/misi0202/ptcg-scout)"
            ),
            "Accept": "application/json, application/xml, text/xml, */*",
            "Cookie": "over18=1",
        })

    def _load_cache(self) -> dict:
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_cache(self, cache: dict):
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

    def _cache_key(self, subreddit: str, sort: str) -> str:
        return f"{subreddit}:{sort}"

    def _cache_posts(self, subreddit: str, sort: str, posts: list[dict]):
        if not posts:
            return
        cache = self._load_cache()
        cache[self._cache_key(subreddit, sort)] = {
            "fetched_at": date.today().isoformat(),
            "posts": posts,
        }
        self._save_cache(cache)

    def _cached_posts(self, subreddit: str, sort: str) -> list[dict]:
        entry = self._load_cache().get(self._cache_key(subreddit, sort), {})
        fetched_at = entry.get("fetched_at")
        posts = entry.get("posts", [])
        if not fetched_at or not posts:
            return []
        try:
            days_old = (date.today() - date.fromisoformat(fetched_at)).days
        except ValueError:
            return []
        if days_old <= CACHE_MAX_AGE_DAYS:
            logger.info("[reddit] r/%s %s: using cached posts (%d, %d days old)",
                        subreddit, sort, len(posts), days_old)
            return posts
        return []

    def _parse_rss_posts(self, text: str) -> list[dict]:
        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            return []

        ns = {
            "atom": "http://www.w3.org/2005/Atom",
        }
        posts = []
        for entry in root.findall("atom:entry", ns):
            title = entry.findtext("atom:title", default="", namespaces=ns)
            content = entry.findtext("atom:content", default="", namespaces=ns)
            updated = entry.findtext("atom:updated", default="", namespaces=ns)
            link_el = entry.find("atom:link", ns)
            url = link_el.get("href", "") if link_el is not None else ""
            posts.append({
                "title": title,
                "selftext": content,
                "score": 1,
                "num_comments": 0,
                "created_utc": 0,
                "permalink": url.replace("https://www.reddit.com", ""),
                "updated": updated,
            })
        return posts

    def _fetch_subreddit(self, subreddit: str, sort: str = "hot", limit: int = 50) -> list[dict]:
        urls = [
            f"https://www.reddit.com/r/{subreddit}/{sort}.json?raw_json=1&limit={limit}",
            f"https://old.reddit.com/r/{subreddit}/{sort}.json?raw_json=1&limit={limit}",
            f"https://www.reddit.com/r/{subreddit}/{sort}/.rss?limit={limit}",
        ]
        saw_block = False

        for url in urls:
            for attempt in range(2):
                try:
                    resp = self.session.get(url, timeout=20)

                    if resp.status_code == 200:
                        if url.endswith(".rss") or "/.rss" in url:
                            posts = self._parse_rss_posts(resp.text)
                        else:
                            data = resp.json()
                            children = data.get("data", {}).get("children", [])
                            posts = [p["data"] for p in children if p.get("kind") == "t3"]
                        if posts:
                            self._cache_posts(subreddit, sort, posts)
                            return posts

                    if resp.status_code in (403, 429):
                        saw_block = True
                        wait = (attempt + 1) * 5
                        logger.warning("[reddit] r/%s %s: %d from %s (retry in %ds)",
                                       subreddit, sort, resp.status_code, url.split("/")[2], wait)
                        time.sleep(wait)
                        continue

                    logger.warning("[reddit] r/%s %s: %d from %s",
                                   subreddit, sort, resp.status_code, url.split("/")[2])
                    break

                except Exception as e:
                    logger.warning("[reddit] r/%s %s fetch error from %s: %s",
                                   subreddit, sort, url.split("/")[2], e)
                    if attempt < 1:
                        time.sleep(3)

        cached = self._cached_posts(subreddit, sort)
        if cached:
            return cached
        if saw_block:
            logger.warning("[reddit] r/%s %s: all public endpoints blocked and no cache available", subreddit, sort)
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
