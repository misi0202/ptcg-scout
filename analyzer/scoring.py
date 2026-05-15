import json
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")

with open(os.path.join(CONFIG_DIR, "pokemon_tiers.json"), encoding="utf-8") as f:
    TIER_CONFIG = json.load(f)

TIER_MAP: dict[str, int] = {}
for tier_data in TIER_CONFIG.values():
    if isinstance(tier_data, dict) and "score" in tier_data and "pokemon" in tier_data:
        for pokemon in tier_data["pokemon"]:
            TIER_MAP[pokemon.lower()] = tier_data["score"]

NARRATIVE_TAGS = TIER_CONFIG.get("narrative_tags", {})

ART_KEYWORDS = [
    "art", "beautiful", "fire", "stunning", "gorgeous",
    "amazing art", "best art", "illustration", "full art",
    "alternate art", "special art",
]


@dataclass
class CardScore:
    card_id: int
    name: str
    pokemon_name: str
    aesthetic_score: float
    ip_score: float
    narrative_score: float
    pop_multiplier: float
    composite_score: float
    trend_signal: str = ""
    reason: str = ""


def get_ip_score(pokemon_name: str) -> float:
    if not pokemon_name:
        return 30.0
    return float(TIER_MAP.get(pokemon_name.lower(), 30.0))


def get_aesthetic_score(keywords: list[str], mention_count: int) -> float:
    if not keywords:
        return 30.0
    art_hits = sum(1 for kw in keywords if any(ak in kw.lower() for ak in ART_KEYWORDS))
    score = min(100.0, 20.0 + (art_hits * 15.0) + (mention_count * 0.5))
    return score


def get_narrative_score(name: str, set_name: str, extra_info: str = "") -> float:
    text = f"{name} {set_name} {extra_info}".lower()
    best = 0.0
    for tag_info in NARRATIVE_TAGS.values():
        if not isinstance(tag_info, dict):
            continue
        tag_score = tag_info.get("score", 0)
        for kw in tag_info.get("keywords", []):
            if kw.lower() in text:
                best = max(best, float(tag_score))
    return best if best > 0 else 10.0


def get_pop_multiplier(psa10_pop: int) -> float:
    if psa10_pop <= 0:
        return 1.0
    if psa10_pop < 100:
        return 1.15
    if psa10_pop <= 500:
        return 1.10
    if psa10_pop <= 2000:
        return 1.00
    if psa10_pop <= 5000:
        return 0.93
    return 0.85


def calculate_score(
    card_id: int,
    name: str,
    pokemon_name: str,
    keywords: list[str],
    mention_count: int,
    psa10_pop: int,
    set_name: str = "",
    extra_info: str = "",
) -> CardScore:
    aesthetic = get_aesthetic_score(keywords, mention_count)
    ip = get_ip_score(pokemon_name)
    narrative = get_narrative_score(name, set_name, extra_info)
    pop_mult = get_pop_multiplier(psa10_pop)

    base = aesthetic * 0.35 + ip * 0.40 + narrative * 0.25
    composite = round(base * pop_mult, 2)

    reasons = []
    if ip >= 85:
        reasons.append(f"{pokemon_name} is a top-tier Pokemon")
    if aesthetic >= 70:
        reasons.append("strong art appeal")
    if narrative >= 50:
        reasons.append("narrative value detected")
    if pop_mult >= 1.10:
        reasons.append(f"PSA10 pop={psa10_pop}, very scarce")

    score = CardScore(
        card_id=card_id,
        name=name,
        pokemon_name=pokemon_name,
        aesthetic_score=round(aesthetic, 2),
        ip_score=round(ip, 2),
        narrative_score=round(narrative, 2),
        pop_multiplier=pop_mult,
        composite_score=composite,
        reason="; ".join(reasons) if reasons else "standard card",
    )

    logger.debug("Scored %s: composite=%.2f (base=%.2f × %.2f)", name, composite, base, pop_mult)
    return score
