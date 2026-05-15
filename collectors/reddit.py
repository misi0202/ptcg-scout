import logging
import os
from datetime import datetime

import praw

from .base import BaseCollector, CardData

logger = logging.getLogger(__name__)

SUBREDDITS = ["PokemonTCG", "PokeInvesting", "PokemonCardValue"]
KEYWORDS = [
    "psa10", "psa 10", "graded", "gem mint", "chase card",
    "undervalued", "sleeper", "potential", "invest",
    "art", "beautiful", "fire", "stunning",
]
POKEMON_HOT_LIST = [
    "charizard", "pikachu", "gengar", "mewtwo", "mew",
    "umbreon", "espeon", "sylveon", "rayquaza", "lugia",
    "greninja", "giratina", "eevee", "snorlax", "dragonite",
]


class RedditCollector(BaseCollector):
    name = "reddit"

    def __init__(self):
        super().__init__(min_delay=1.0, max_delay=2.0)
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID", ""),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
            user_agent="ptcg-scout/1.0 (by u/card_analyst)",
        )

    def collect(self) -> list[CardData]:
        results = []
        if not os.getenv("REDDIT_CLIENT_ID"):
            logger.warning("[reddit] No API credentials, skipping Reddit collection")
            return results

        try:
            for subreddit_name in SUBREDDITS:
                subreddit = self.reddit.subreddit(subreddit_name)
                for post in subreddit.hot(limit=50):
                    text = (post.title + " " + post.selftext).lower()

                    matched_keywords = [kw for kw in KEYWORDS if kw in text]
                    matched_pokemon = [pk for pk in POKEMON_HOT_LIST if pk in text]

                    if matched_pokemon:
                        for pokemon in matched_pokemon:
                            card = CardData(
                                name=f"{pokemon.title()} mention",
                                set_name=subreddit_name,
                                pokemon_name=pokemon,
                                source="reddit",
                                extra={
                                    "keywords": matched_keywords,
                                    "score": post.score,
                                    "comments": post.num_comments,
                                    "url": post.url,
                                    "created_utc": datetime.fromtimestamp(post.created_utc).isoformat(),
                                },
                            )
                            results.append(card)

                logger.info("[reddit] r/%s: collected %d mentions", subreddit_name, len(results))

        except Exception as e:
            logger.error("[reddit] Collection failed: %s", e)

        return results
