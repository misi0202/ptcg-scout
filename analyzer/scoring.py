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

NARRATIVE_TAGS: list[tuple[float, list[str]]] = []
for tag_info in TIER_CONFIG.get("narrative_tags", {}).values():
    if isinstance(tag_info, dict):
        tag_score = float(tag_info.get("score", 0))
        keywords = tag_info.get("keywords", [])
        NARRATIVE_TAGS.append((tag_score, keywords))

# Per-card narrative scores (name-level + special case overrides)
NARRATIVE_SCORES: dict[str, dict] = {}
NARRATIVE_SPECIAL: list[dict] = []
_narrative_path = os.path.join(CONFIG_DIR, "narrative_scores.json")
try:
    with open(_narrative_path, encoding="utf-8") as f:
        ns_data = json.load(f)
    NARRATIVE_SCORES = ns_data.get("scores", {})
    NARRATIVE_SPECIAL = ns_data.get("special_cases", [])
    logger.info("Loaded %d per-card narrative scores + %d special cases",
                len(NARRATIVE_SCORES), len(NARRATIVE_SPECIAL))
except Exception:
    logger.warning("narrative_scores.json not found, using keyword matching only")

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
    name_lower = pokemon_name.lower()
    for key, score in TIER_MAP.items():
        if key in name_lower:
            return float(score)
    return 30.0


def get_aesthetic_score(keywords: list[str], mention_count: int) -> float:
    if not keywords:
        return 30.0
    art_hits = sum(1 for kw in keywords if any(ak in kw.lower() for ak in ART_KEYWORDS))
    score = min(100.0, 20.0 + (art_hits * 15.0) + (mention_count * 0.5))
    return score


def get_narrative_score(name: str, set_name: str, rarity: str = "", artist: str = "", card_number: str = "") -> float:
    # 1) Check special case overrides (name + set + artist/card_number)
    for case in NARRATIVE_SPECIAL:
        if case.get("name") == name and case.get("set_name") == set_name:
            if case.get("artist") == artist:
                return float(case["score"])
            if case.get("card_number") and case.get("card_number") == card_number:
                return float(case["score"])

    # 2) Check name-level score
    if name in NARRATIVE_SCORES:
        return float(NARRATIVE_SCORES[name]["score"])

    # 3) Keyword fallback
    text = f"{name} {set_name} {rarity} {artist}".lower()
    best = 0.0
    for tag_score, keywords in NARRATIVE_TAGS:
        for kw in keywords:
            if kw.lower() in text:
                best = max(best, tag_score)

    if best > 0:
        logger.debug("Narrative keyword match for '%s': %.0f", name, best)
    else:
        logger.debug("Narrative unscored: '%s' (artist=%s) — using default 10", name, artist)

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
    rarity: str = "",
    artist: str = "",
    card_number: str = "",
) -> CardScore:
    aesthetic = get_aesthetic_score(keywords, mention_count)
    ip = get_ip_score(pokemon_name)
    narrative = get_narrative_score(name, set_name, rarity, artist, card_number)
    pop_mult = get_pop_multiplier(psa10_pop)

    base = aesthetic * 0.35 + ip * 0.40 + narrative * 0.25
    composite = round(base * pop_mult, 2)

    reasons = []
    if ip >= 85:
        reasons.append(f"{pokemon_name} is a top-tier Pokemon")
    if aesthetic >= 70:
        reasons.append("strong art appeal")
    if narrative >= 30:
        reasons.append(f"narrative value: {narrative:.0f}")
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

    logger.debug("Scored %s: composite=%.2f (base=%.2f x %.2f)", name, composite, base, pop_mult)
    return score
