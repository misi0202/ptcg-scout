"""JustTCG Japanese card collector — fetches JP cards with prices.

Uses JustTCG API (pokemon-japan game) to discover JP-market cards.
Caches results daily; preserves data from previous runs when API key is missing."""

import json
import logging
import os
import time
from datetime import date

import requests

from .base import CardData

logger = logging.getLogger(__name__)

API_BASE = "https://api.justtcg.com/v1"
POKEMONTCG_API = "https://api.pokemontcg.io/v2"
API_KEY = os.getenv("JUSTTCG_API_KEY", "")

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "jp_cards_cache.json")

# Japanese Pokemon name mapping
_POKEMON_JP: dict[str, str] = {
    "pikachu": "ピカチュウ", "charizard": "リザードン", "mew": "ミュウ",
    "mewtwo": "ミュウツー", "gengar": "ゲンガー", "umbreon": "ブラッキー",
    "espeon": "エーフィ", "sylveon": "ニンフィア", "vaporeon": "シャワーズ",
    "jolteon": "サンダース", "flareon": "ブースター", "glaceon": "グレイシア",
    "leafeon": "リーフィア", "eevee": "イーブイ", "rayquaza": "レックウザ",
    "lugia": "ルギア", "ho-oh": "ホウオウ", "dragonite": "カイリュー",
    "gyarados": "ギャラドス", "tyranitar": "バンギラス", "gardevoir": "サーナイト",
    "lucario": "ルカリオ", "greninja": "ゲッコウガ", "mimikyu": "ミミッキュ",
    "snorlax": "カビゴン", "blaziken": "バシャーモ", "darkrai": "ダークライ",
    "celebi": "セレビィ", "jirachi": "ジラーチ", "arceus": "アルセウス",
    "giratina": "ギラティナ", "garchomp": "ガブリアス", "metagross": "メタグロス",
    "salamence": "ボーマンダ", "zoroark": "ゾロアーク", "latias": "ラティアス",
    "latios": "ラティオス", "scizor": "ハッサム", "blastoise": "カメックス",
    "venusaur": "フシギバナ", "alakazam": "フーディン", "machamp": "カイリキー",
    "magikarp": "コイキング", "absol": "アブソル", "reshiram": "レシラム",
    "iono": "イオネ", "erika": "エリカ", "misty": "カスミ",
    "poncho-wearing": "ポンチョ", "pretend": "なりきり", "team": "団",
    "skull": "スカル", "magikarp": "コイキング",
}

def _make_jp_name(en_name: str) -> str:
    """Convert English card name to Japanese display name."""
    words = en_name.lower().replace("-", " ").replace("  ", " ").split()
    out = []
    for w in words:
        clean = w.rstrip(".,;:")
        jp = _POKEMON_JP.get(clean)
        if jp:
            out.append(jp)
        else:
            out.append(w.upper() if w.isupper() else w.title())
    return "".join(out)

# Japanese set name mapping
_SET_NAMES_JP = {
    "Eevee Heroes": "イーブイヒーローズ",
    "Shiny Treasure ex": "シャイニートレジャーex",
    "VSTAR Universe": "VSTARユニバース",
    "Ruler of the Black Flame": "黒炎の支配者",
    "151": "151",
    "Snow Hazard": "スノーハザード",
    "Clay Burst": "クレイバースト",
    "Triplet Beat": "トリプレットビート",
    "Paradigm Trigger": "パラダイムトリガー",
    "Fusion Arts": "フュージョンアーツ",
    "Dark Phantasma": "ダークファンタズマ",
    "Lost Abyss": "ロストアビス",
    "Blue Sky Stream": "蒼空ストリーム",
    "VMAX Climax": "VMAXクライマックス",
    "Matchless Fighters": "無双ファイターズ",
    "Tag All Stars": "タッグオールスターズ",
    "Crimson Haze": "クリムゾンヘイズ",
    "Wild Force": "ワイルドフォース",
    "Cyber Judge": "サイバージャッジ",
    "Star Birth": "スターバース",
    "Gym Challenge": "ジムチャレンジ",
    "SM-P: Sun & Moon Promos": "SM-P プロモ",
    "XY-P: XY Promos": "XY-P プロモ",
    "S7R: Blue Sky Stream": "蒼空ストリーム",
}
CACHE_MAX_AGE_DAYS = 30  # Use cache up to 30 days old if API key unavailable

# Broad search for JP cards across all popular Pokemon
JP_SEARCH_QUERIES = [
    # T1 (highest demand)
    "pikachu", "charizard", "mew", "mewtwo", "eevee",
    "umbreon", "gengar", "rayquaza",
    # T2
    "lugia", "ho-oh", "espeon", "sylveon", "vaporeon",
    "jolteon", "flareon", "gyarados", "dragonite",
    "tyranitar", "gardevoir", "lucario", "greninja",
    "mimikyu", "snorlax", "blaziken", "darkrai",
    "celebi", "jirachi", "arceus",
    # T3-T4 (popular but lower tier)
    "garchomp", "metagross", "salamence", "zoroark",
    "latias", "latios", "giratina", "scizor",
    "blastoise", "venusaur", "alakazam", "machamp",
]


def _load_cache() -> dict:
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"cards": [], "fetched_at": ""}


def _save_cache(data: dict):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _fetch_pokemontcg_image(name: str) -> str:
    """Try to get card image from Pokemon TCG API (free, no auth needed).
    Tries multiple search strategies for cards not in the English API."""
    import re

    # Build search candidates: exact → stripped → first word → Pokemon name match
    queries = [name]
    base = re.sub(r"\s*[-–]\s*\d+[\s/].*$", "", name).strip()
    if base != name:
        queries.append(base)

    first_word = name.split()[0]
    if first_word not in queries:
        queries.append(first_word)

    # Match against known Pokemon names for JP-exclusive promos
    _POKEMON_NAMES = [
        "pikachu", "charizard", "mewtwo", "mew", "eevee", "umbreon",
        "espeon", "sylveon", "vaporeon", "jolteon", "flareon", "gengar",
        "rayquaza", "lugia", "ho-oh", "gyarados", "dragonite", "tyranitar",
        "gardevoir", "lucario", "greninja", "mimikyu", "snorlax",
        "blaziken", "darkrai", "celebi", "jirachi", "arceus",
        "garchomp", "metagross", "salamence", "zoroark",
        "latias", "latios", "giratina", "scizor", "blastoise",
        "venusaur", "alakazam", "machamp", "magikarp", "absol",
    ]
    name_lower = name.lower()
    for pk in _POKEMON_NAMES:
        if pk in name_lower and pk not in queries:
            queries.append(pk)
            break

    for q in queries[:4]:
        try:
            resp = requests.get(
                f"{POKEMONTCG_API}/cards",
                params={"q": f'name:"{q}"', "select": "images", "pageSize": 1},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if data:
                    images = data[0].get("images", {}) or {}
                    img = images.get("large") or images.get("small") or ""
                    if img:
                        return img
        except Exception:
            pass
    return ""


def _fill_missing_images(cards: list[CardData]) -> list[CardData]:
    """Backfill image_url and jp_name for cards missing them."""
    for c in cards:
        if not c.extra.get("image_url"):
            img = _fetch_pokemontcg_image(c.name)
            if img:
                c.extra["image_url"] = img
                time.sleep(0.3)
        if not c.extra.get("jp_name"):
            c.extra["jp_name"] = _make_jp_name(c.name)
        if not c.extra.get("jp_set_name"):
            c.extra["jp_set_name"] = _SET_NAMES_JP.get(c.set_name, c.set_name)
    return cards


def collect_jp_cards() -> list[CardData]:
    """Collect JP cards from JustTCG. Uses cache if API key is missing."""
    today = date.today().isoformat()

    if not API_KEY:
        cache = _load_cache()
        cached_date = cache.get("fetched_at", "")
        if cached_date:
            days_old = (date.today() - date.fromisoformat(cached_date)).days
            if days_old <= CACHE_MAX_AGE_DAYS and cache.get("cards"):
                logger.info("[justtcg_jp] Using cached JP data (%d cards, %d days old)",
                            len(cache["cards"]), days_old)
                cards = [_dict_to_carddata(d) for d in cache["cards"]]
                cards = _fill_missing_images(cards)
                return cards
        logger.info("[justtcg_jp] No API key and no fresh cache — returning empty")
        return []

    headers = {"x-api-key": API_KEY, "Accept": "application/json"}
    collected = []
    seen_names = set()

    for query in JP_SEARCH_QUERIES:
        try:
            params = {"game": "pokemon-japan", "name": query, "limit": 10}
            resp = requests.get(f"{API_BASE}/cards", headers=headers, params=params, timeout=20)

            if resp.status_code == 429:
                logger.warning("[justtcg_jp] Rate limited, stopping JP collection")
                time.sleep(10)
                break
            if resp.status_code != 200:
                logger.warning("[justtcg_jp] %d for query='%s'", resp.status_code, query)
                continue

            cards = resp.json().get("data", [])
            for card in cards:
                name = card.get("name", "")
                if name in seen_names:
                    continue
                seen_names.add(name)

                # Find best Japanese variant
                for v in card.get("variants", []):
                    if v.get("language") != "Japanese":
                        continue
                    if v.get("condition") not in ("Near Mint", "Lightly Played"):
                        continue

                    # Try all possible image URL fields from JustTCG API
                    image_url = (
                        card.get("image_url") or card.get("image") or
                        card.get("img_url") or card.get("picture") or ""
                    )
                    if not image_url:
                        image_url = _fetch_pokemontcg_image(name)
                        time.sleep(0.3)

                    jp_name = _make_jp_name(name)
                    set_name_en = card.get("set_name", "")
                    jp_set = _SET_NAMES_JP.get(set_name_en, set_name_en)

                    collected.append(CardData(
                        name=name,
                        set_name=set_name_en,
                        card_number=card.get("number", "") or "",
                        pokemon_name=name,
                        price=float(v.get("price", 0)) if v.get("price") else None,
                        source="justtcg",
                        extra={
                            "game": "pokemon-jp",
                            "rarity": card.get("rarity", ""),
                            "image_url": image_url,
                            "jp_name": jp_name,
                            "jp_set_name": jp_set,
                            "jp_condition": v.get("condition"),
                            "jp_printing": v.get("printing"),
                            "jp_price_change_7d": v.get("priceChange7d"),
                            "jp_price_change_30d": v.get("priceChange30d"),
                        },
                    ))
                    break

            time.sleep(1.0)

        except Exception as e:
            logger.error("[justtcg_jp] Query '%s' failed: %s", query, e)

    logger.info("[justtcg_jp] Collected %d JP cards from API", len(collected))

    # Merge with existing cache (keep old cards, add/update new ones)
    old_cache = _load_cache()
    old_cards = old_cache.get("cards", [])
    old_by_name = {c["name"]: c for c in old_cards}
    new_by_name = {c.name: _carddata_to_dict(c) for c in collected}

    # Update old cards with fresh API data, keep cards not in API results
    merged = {**old_by_name, **new_by_name}
    cache_data = {
        "cards": list(merged.values()),
        "fetched_at": today,
    }
    _save_cache(cache_data)
    logger.info("[justtcg_jp] Cache merged: %d old + %d new = %d total",
                len(old_cards), len(collected), len(cache_data["cards"]))

    return collected


def _carddata_to_dict(c: CardData) -> dict:
    return {
        "name": c.name,
        "set_name": c.set_name,
        "card_number": c.card_number,
        "pokemon_name": c.pokemon_name,
        "price": c.price,
        "source": c.source,
        "extra": c.extra,
    }


def _dict_to_carddata(d: dict) -> CardData:
    return CardData(
        name=d.get("name", ""),
        set_name=d.get("set_name", ""),
        card_number=d.get("card_number", ""),
        pokemon_name=d.get("pokemon_name", ""),
        price=d.get("price"),
        source=d.get("source", "justtcg"),
        extra=d.get("extra", {}),
    )
