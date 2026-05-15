import logging
import os
from datetime import datetime

import requests

from .base import BaseCollector, CardData

logger = logging.getLogger(__name__)

DISCORD_API = "https://discord.com/api/v10"

# US/EU community keywords — English only for Discord
KEYWORDS = [
    "psa10", "psa 10", "graded", "gem mint", "chase card",
    "undervalued", "sleeper", "potential", "invest", "pickup",
    "art", "beautiful", "fire", "stunning", "alt art",
    "charizard", "pikachu", "gengar", "mewtwo", "mew",
    "umbreon", "espeon", "sylveon", "rayquaza", "lugia",
    "greninja", "giratina", "eevee", "snorlax", "dragonite",
    "karp", "magikarp", "gyarados", "tyranitar", "gardevoir",
    "moonbreon", "bubble mew", "latias", "latios",
]

POKEMON_HOT_LIST = [
    "charizard", "pikachu", "gengar", "mewtwo", "mew",
    "umbreon", "espeon", "sylveon", "rayquaza", "lugia",
    "greninja", "giratina", "eevee", "snorlax", "dragonite",
    "gyarados", "tyranitar", "gardevoir", "mimikyu",
]


class DiscordCollector(BaseCollector):
    name = "discord"

    def __init__(self):
        super().__init__(min_delay=1.0, max_delay=2.0)
        self.token = os.getenv("DISCORD_BOT_TOKEN", "")
        self.channel_ids = [
            cid.strip()
            for cid in os.getenv("DISCORD_CHANNEL_IDS", "").split(",")
            if cid.strip()
        ]

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json",
        }

    def _fetch_messages(self, channel_id: str, limit: int = 100) -> list[dict]:
        url = f"{DISCORD_API}/channels/{channel_id}/messages"
        resp = requests.get(
            url,
            headers=self._headers(),
            params={"limit": limit},
            timeout=30,
        )
        if resp.status_code == 401:
            logger.error("[discord] Unauthorized — check DISCORD_BOT_TOKEN")
            return []
        if resp.status_code == 404:
            logger.error("[discord] Channel %s not found — bot may not have access", channel_id)
            return []
        if resp.status_code == 429:
            retry_after = resp.json().get("retry_after", 5)
            logger.warning("[discord] Rate limited, retry-after %.1fs", retry_after)
            return []
        resp.raise_for_status()
        return resp.json()

    def collect(self) -> list[CardData]:
        results = []

        if not self.token:
            logger.warning("[discord] No DISCORD_BOT_TOKEN, skipping")
            return results

        if not self.channel_ids:
            logger.warning("[discord] No DISCORD_CHANNEL_IDS configured, skipping")
            return results

        for channel_id in self.channel_ids:
            try:
                messages = self._fetch_messages(channel_id)
                for msg in messages:
                    content = msg.get("content", "")
                    if not content:
                        continue

                    text_lower = content.lower()
                    matched_keywords = [kw for kw in KEYWORDS if kw in text_lower]
                    matched_pokemon = [pk for pk in POKEMON_HOT_LIST if pk in text_lower]

                    if not matched_pokemon:
                        continue

                    for pokemon in set(matched_pokemon):
                        results.append(CardData(
                            name=f"{pokemon.title()} Discord mention",
                            set_name=channel_id,
                            pokemon_name=pokemon,
                            source="discord",
                            extra={
                                "keywords": matched_keywords,
                                "channel_id": channel_id,
                                "message_id": msg.get("id", ""),
                                "author_id": msg.get("author", {}).get("id", ""),
                                "timestamp": msg.get("timestamp", ""),
                                "reactions": sum(
                                    r.get("count", 0)
                                    for r in msg.get("reactions", [])
                                ),
                            },
                        ))

                logger.info("[discord] Channel %s: scanned messages, found %d pokemon mentions",
                           channel_id, len(results))

            except Exception as e:
                logger.error("[discord] Channel %s failed: %s", channel_id, e)

        logger.info("[discord] Total mentions collected: %d", len(results))
        return results
