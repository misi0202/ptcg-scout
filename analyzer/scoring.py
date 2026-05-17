"""Data-driven scoring engine — scores cards based on real market data from APIs.

Sources: PokemonTCG (US prices), Cardmarket (EU), JustTCG (JP), Reddit (mentions), eBay (sold).
No subjective tiers, no keyword matching — purely market signals."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CardScore:
    card_id: int
    name: str
    pokemon_name: str
    # Data-driven signals (0-100)
    price_signal: float      # normalized market price
    volume_signal: float     # normalized mention/demand volume
    momentum: float          # price trend bonus (-10 to +10)
    composite_score: float   # final score (0-100)
    reason: str = ""


def compute_scores(cards: list[dict]) -> list[CardScore]:
    """Score all cards based purely on market data. Returns sorted by composite desc."""

    if not cards:
        return []

    # Extract raw values
    prices = []
    mentions = []
    for c in cards:
        best_price = c.get("us_price", 0) or c.get("cm_price", 0) or c.get("jp_price", 0) or 0
        prices.append(float(best_price))
        mentions.append(int(c.get("mention_count", 0) or 0))

    max_price = max(prices) if max(prices) > 0 else 1
    max_mentions = max(mentions) if max(mentions) > 0 else 1

    results = []
    for i, c in enumerate(cards):
        price = prices[i]
        mention = mentions[i]

        # Normalize to 0-100
        price_signal = min(100.0, round((price / max_price) * 100, 1)) if price > 0 else 30.0
        volume_signal = min(100.0, round((mention / max_mentions) * 100, 1)) if mention > 0 else 30.0

        # Momentum bonus: recent price change
        pct = float(c.get("price_change_pct", 0) or 0)
        if pct > 20:
            momentum = 10.0
        elif pct > 10:
            momentum = 7.0
        elif pct > 5:
            momentum = 4.0
        elif pct > 0:
            momentum = 2.0
        elif pct < -15:
            momentum = -8.0
        elif pct < -5:
            momentum = -4.0
        else:
            momentum = 0.0

        composite = round(price_signal * 0.6 + volume_signal * 0.4 + momentum, 1)
        composite = max(5.0, min(100.0, composite))

        # Build reason string from data
        parts = []
        best_price_src = ""
        if c.get("us_price"):
            best_price_src = f"${c['us_price']:.2f} US"
        elif c.get("cm_price"):
            best_price_src = f"€{c['cm_price']:.2f} EU"
        elif c.get("jp_price"):
            best_price_src = f"¥{c['jp_price']:,.0f} JP"
        if best_price_src:
            parts.append(f"price={best_price_src}")
        if mention > 0:
            parts.append(f"mentions={mention}")
        if momentum != 0:
            parts.append(f"momentum={momentum:+.0f}")

        results.append(CardScore(
            card_id=c["id"],
            name=c.get("name", ""),
            pokemon_name=c.get("pokemon", ""),
            price_signal=price_signal,
            volume_signal=volume_signal,
            momentum=momentum,
            composite_score=composite,
            reason="; ".join(parts) if parts else "no market data yet",
        ))

    results.sort(key=lambda s: s.composite_score, reverse=True)
    logger.info("Scored %d cards: top=%.1f, bottom=%.1f",
                len(results), results[0].composite_score, results[-1].composite_score)
    return results
