"""Hybrid scoring engine — market data + Pokemon IP tiers + price trends.

Formula: Price×0.4 + IP×0.3 + Volume×0.2 + Momentum×0.1
- Price: normalized best available market price (US/EU/JP)
- IP: Pokemon popularity tier (T1=100, T2=85, T3=70, T4=50, default 30)
- Volume: normalized Reddit mention frequency
- Momentum: price trend from JustTCG 30d/7d change or supply_demand history"""

import json
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")

# Load Pokemon IP tiers
with open(os.path.join(CONFIG_DIR, "pokemon_tiers.json"), encoding="utf-8") as f:
    TIER_CONFIG = json.load(f)

TIER_MAP: dict[str, int] = {}
for tier_data in TIER_CONFIG.values():
    if isinstance(tier_data, dict) and "score" in tier_data and "pokemon" in tier_data:
        for pokemon in tier_data["pokemon"]:
            TIER_MAP[pokemon.lower()] = tier_data["score"]


def get_ip_score(pokemon_name: str) -> float:
    """Look up Pokemon IP popularity tier (T1=100 → T4=50, default 30)."""
    if not pokemon_name:
        return 30.0
    name_lower = pokemon_name.lower()
    for key, score in sorted(TIER_MAP.items(), key=lambda x: -len(x[0])):
        if key in name_lower:
            return float(score)
    return 30.0


@dataclass
class CardScore:
    card_id: int
    name: str
    pokemon_name: str
    price_signal: float
    ip_signal: float
    volume_signal: float
    momentum: float
    composite_score: float
    reason: str = ""


def compute_scores(cards: list[dict]) -> list[CardScore]:
    """Score all cards. Returns sorted by composite desc."""

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

        # 1) Price signal (0-100)
        price_signal = min(100.0, round((price / max_price) * 100, 1)) if price > 0 else 30.0

        # 2) IP tier signal (0-100)
        pokemon = c.get("pokemon", "")
        ip_signal = get_ip_score(pokemon)

        # 3) Volume signal (0-100)
        volume_signal = min(100.0, round((mention / max_mentions) * 100, 1)) if mention > 0 else 30.0

        # 4) Momentum from multiple sources
        momentum = _calc_momentum(c)

        # Composite: Price×0.4 + IP×0.3 + Volume×0.2 + Momentum×0.1
        composite = round(
            price_signal * 0.4 + ip_signal * 0.3 + volume_signal * 0.2 + momentum * 0.1,
            1,
        )
        composite = max(5.0, min(100.0, composite))

        # Build reason
        parts = []
        best_price_src = ""
        if c.get("jp_price"):
            best_price_src = f"¥{c['jp_price']:,.0f} JP"
        elif c.get("us_price"):
            best_price_src = f"${c['us_price']:.2f} US"
        elif c.get("cm_price"):
            best_price_src = f"€{c['cm_price']:.2f} EU"
        if best_price_src:
            parts.append(f"price={best_price_src}")
        if ip_signal >= 85:
            parts.append(f"IP T{_tier_label(ip_signal)}")
        elif ip_signal >= 70:
            parts.append(f"IP T{_tier_label(ip_signal)}")
        if mention > 0:
            parts.append(f"mentions={mention}")
        if momentum != 0:
            parts.append(f"momentum={momentum:+.0f}")

        results.append(CardScore(
            card_id=c["id"],
            name=c.get("name", ""),
            pokemon_name=pokemon,
            price_signal=price_signal,
            ip_signal=ip_signal,
            volume_signal=volume_signal,
            momentum=momentum,
            composite_score=composite,
            reason="; ".join(parts) if parts else "no market data yet",
        ))

    results.sort(key=lambda s: s.composite_score, reverse=True)
    logger.info("Scored %d cards: top=%.1f bottom=%.1f",
                len(results), results[0].composite_score, results[-1].composite_score)
    return results


def _calc_momentum(card: dict) -> float:
    """Calculate price trend momentum from available sources.

    Priority: JustTCG 30d change > JustTCG 7d change > supply_demand 30d change.
    Returns value in 0-100 range (50 = neutral).
    """
    jp_price = card.get("jp_price", 0) or 0
    is_jp = card.get("game") == "pokemon-jp" or jp_price > 0

    # JustTCG price changes (JP cards only — prevent name-collision with EN cards)
    if is_jp:
        jp30 = card.get("jp_price_change_30d")
        jp7 = card.get("jp_price_change_7d")
        for raw_val in (jp30, jp7):
            if raw_val is None or raw_val == 0:
                continue
            try:
                val = float(raw_val)
            except (ValueError, TypeError):
                continue

            # Convert to percentage: if |val| > 50 treat as absolute yen change
            if abs(val) > 50 and jp_price > 0:
                pct = (val / jp_price) * 100
            else:
                pct = val

            return _pct_to_momentum(pct)

    # Supply-demand 30-day price change (from accumulated history, all markets)
    sd_pct = float(card.get("price_change_pct", 0) or 0)
    if sd_pct != 0:
        return _pct_to_momentum(sd_pct)

    return 50.0  # neutral — no trend data


def _pct_to_momentum(pct: float) -> float:
    """Map price change % to momentum (0-100 scale, 50 = neutral)."""
    # Positive = bullish, negative = bearish
    # Map roughly: +30% → 100, 0% → 50, -30% → 0
    momentum = 50.0 + pct * 1.67
    return max(0.0, min(100.0, round(momentum, 1)))


def _tier_label(score: float) -> str:
    if score >= 100:
        return "1"
    if score >= 85:
        return "2"
    if score >= 70:
        return "3"
    if score >= 50:
        return "4"
    return "?"
