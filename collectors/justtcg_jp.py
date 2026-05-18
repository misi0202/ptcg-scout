"""Japanese market collector.

JustTCG remains the price source.
TCGdex is the primary JP card-image source.
pokemon-card.com is the fallback source for cards TCGdex does not cover.
"""

import json
import logging
import os
import re
import time
from datetime import date
from urllib.parse import urljoin

import requests

from .base import CardData

logger = logging.getLogger(__name__)

JUSTTCG_API_BASE = "https://api.justtcg.com/v1"
TCGDEX_API_BASE = "https://api.tcgdex.net/v2/ja"
POKEMON_CARD_BASE = "https://www.pokemon-card.com"
JUSTTCG_API_KEY = os.getenv("JUSTTCG_API_KEY", "")

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "jp_cards_cache.json")
CACHE_MAX_AGE_DAYS = 30

_JAPANESE_CHAR_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]")
_DETAIL_IMAGE_RE = re.compile(r'<img class="fit" src="(?P<src>/assets/images/card_images/large/[^"]+)"\s+alt="(?P<name>[^"]+)"')
_DETAIL_SET_RE = re.compile(r"/card/regulation_logo_1/(?P<set>[A-Za-z0-9-]+)\.gif")
_DETAIL_LOCAL_ID_RE = re.compile(r"&nbsp;\s*(?P<local>\d+)\s*&nbsp;/\s*&nbsp;")

_POKEMON_JP: dict[str, str] = {
    "pikachu": "ピカチュウ",
    "charizard": "リザードン",
    "mew": "ミュウ",
    "mewtwo": "ミュウツー",
    "gengar": "ゲンガー",
    "umbreon": "ブラッキー",
    "espeon": "エーフィ",
    "sylveon": "ニンフィア",
    "vaporeon": "シャワーズ",
    "jolteon": "サンダース",
    "flareon": "ブースター",
    "glaceon": "グレイシア",
    "leafeon": "リーフィア",
    "eevee": "イーブイ",
    "rayquaza": "レックウザ",
    "lugia": "ルギア",
    "ho-oh": "ホウオウ",
    "dragonite": "カイリュー",
    "gyarados": "ギャラドス",
    "tyranitar": "バンギラス",
    "gardevoir": "サーナイト",
    "lucario": "ルカリオ",
    "greninja": "ゲッコウガ",
    "mimikyu": "ミミッキュ",
    "snorlax": "カビゴン",
    "blaziken": "バシャーモ",
    "darkrai": "ダークライ",
    "celebi": "セレビィ",
    "jirachi": "ジラーチ",
    "arceus": "アルセウス",
    "giratina": "ギラティナ",
    "garchomp": "ガブリアス",
    "metagross": "メタグロス",
    "salamence": "ボーマンダ",
    "zoroark": "ゾロアーク",
    "latias": "ラティアス",
    "latios": "ラティオス",
    "scizor": "ハッサム",
    "blastoise": "カメックス",
    "venusaur": "フシギバナ",
    "alakazam": "フーディン",
    "machamp": "カイリキー",
    "magikarp": "コイキング",
    "absol": "アブソル",
    "reshiram": "レシラム",
    "iono": "イオノ",
    "erika": "エリカ",
    "misty": "カスミ",
}

_TOKEN_JP: dict[str, str] = {
    "ex": "ex",
    "gx": "GX",
    "v": "V",
    "vmax": "VMAX",
    "vstar": "VSTAR",
    "sar": "SAR",
    "ar": "AR",
    "sr": "SR",
    "ur": "UR",
    "chr": "CHR",
    "csr": "CSR",
    "tag": "TAG",
    "&": "&",
}

_SET_NAMES_JP = {
    "Eevee Heroes": "イーブイヒーローズ",
    "Shiny Treasure ex": "シャイニートレジャーex",
    "VSTAR Universe": "VSTARユニバース",
    "Ruler of the Black Flame": "黒炎の支配者",
    "151": "ポケモンカード151",
    "Snow Hazard": "スノーハザード",
    "Clay Burst": "クレイバースト",
    "Triplet Beat": "トリプレットビート",
    "Paradigm Trigger": "パラダイムトリガー",
    "Fusion Arts": "フュージョンアーツ",
    "Dark Phantasma": "ダークファンタズマ",
    "Lost Abyss": "ロストアビス",
    "Blue Sky Stream": "蒼空ストリーム",
    "VMAX Climax": "VMAXクライマックス",
    "Matchless Fighters": "双璧のファイター",
    "Tag All Stars": "タッグオールスターズ",
    "Crimson Haze": "クリムゾンヘイズ",
    "Wild Force": "ワイルドフォース",
    "Cyber Judge": "サイバージャッジ",
    "Star Birth": "スターバース",
    "Gym Challenge": "ジム拡張第2弾 闇からの挑戦",
    "SM-P: Sun & Moon Promos": "SM-P",
    "XY-P: XY Promos": "XY-P",
    "S-P: Sword & Shield Promos": "S-P",
    "S7R: Blue Sky Stream": "蒼空ストリーム",
    "Start Deck 100 Battle Collection": "スタートデッキ100",
    "SM9: Tag Bolt": "タッグボルト",
}

_OFFICIAL_SET_CODES = {
    "Eevee Heroes": "S6a",
    "Shiny Treasure ex": "SV4a",
    "VSTAR Universe": "S12a",
    "Ruler of the Black Flame": "SV3",
    "151": "SV2a",
    "Snow Hazard": "SV2P",
    "Clay Burst": "SV2D",
    "Triplet Beat": "SV1a",
    "Paradigm Trigger": "S12",
    "Fusion Arts": "S8",
    "Dark Phantasma": "S10a",
    "Lost Abyss": "S11",
    "Blue Sky Stream": "S7R",
    "VMAX Climax": "S8b",
    "Matchless Fighters": "S5a",
    "Tag All Stars": "SM12a",
    "Crimson Haze": "SV5a",
    "Wild Force": "SV5K",
    "Cyber Judge": "SV5M",
    "Star Birth": "S9",
    "SM-P: Sun & Moon Promos": "SM-P",
    "XY-P: XY Promos": "XY-P",
    "S-P: Sword & Shield Promos": "S-P",
    "S7R: Blue Sky Stream": "S7R",
    "SM9: Tag Bolt": "SM9",
}

_TCGDEX_SET_IDS = dict(_OFFICIAL_SET_CODES)

JP_SEARCH_QUERIES = [
    "pikachu", "charizard", "mew", "mewtwo", "eevee", "umbreon", "gengar", "rayquaza",
    "lugia", "ho-oh", "espeon", "sylveon", "vaporeon", "jolteon", "flareon", "gyarados",
    "dragonite", "tyranitar", "gardevoir", "lucario", "greninja", "mimikyu", "snorlax",
    "blaziken", "darkrai", "celebi", "jirachi", "arceus", "garchomp", "metagross",
    "salamence", "zoroark", "latias", "latios", "giratina", "scizor", "blastoise",
    "venusaur", "alakazam", "machamp",
]

_tcgdex_set_cache: dict[str, str | None] = {}
_tcgdex_cards_cache: dict[str, list[dict]] = {}
_official_search_cache: dict[str, list[dict]] = {}
_official_detail_cache: dict[str, dict] = {}
_tcgdex_name_cache: dict[str, list[dict]] = {}


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


def _has_japanese(text: str) -> bool:
    return bool(_JAPANESE_CHAR_RE.search(text or ""))


def _normalize_text(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[\s\-_/.:,'\"()&+]+", "", text)
    return text


def _normalize_local_id(card_number: str) -> str:
    card_number = (card_number or "").strip()
    if not card_number:
        return ""
    local = card_number.split("/")[0]
    local = re.sub(r"[^0-9A-Za-z]", "", local)
    return local.lstrip("0") or "0"


def _tcgdex_high_image(base_url: str) -> str:
    return f"{base_url}/high.webp" if base_url else ""


def _is_verified_jp_image(url: str) -> bool:
    url = url or ""
    return (
        "assets.tcgdex.net/ja/" in url
        or "pokemon-card.com/assets/images/card_images/large/" in url
    )


def _make_jp_name(en_name: str) -> str:
    if _has_japanese(en_name):
        return en_name

    words = re.split(r"[\s\-]+", en_name.strip())
    out: list[str] = []
    for word in words:
        if not word:
            continue
        clean = word.strip(".,;:()").lower()
        if clean in _POKEMON_JP:
            out.append(_POKEMON_JP[clean])
            continue
        if clean in _TOKEN_JP:
            out.append(_TOKEN_JP[clean])
            continue
        if clean.isdigit() or "/" in clean:
            out.append(word)
            continue
        # Skip decorative English descriptor fragments that hurt lookup quality.
        if clean in {"special", "art", "pretend", "poncho", "wearing", "team", "skull"}:
            continue
    return "".join(out) or en_name


def _jp_lookup_keyword(card_name: str, jp_name: str) -> str:
    if _has_japanese(jp_name):
        base = re.sub(r"\d+/\d+[A-Za-z-]*$", "", jp_name)
        base = re.sub(r"(ex|GX|VMAX|VSTAR|AR|SAR|SR|UR|CHR|CSR)$", "", base, flags=re.I)
        return base or jp_name

    name_lower = card_name.lower()
    for key, value in _POKEMON_JP.items():
        if key in name_lower:
            return value
    return jp_name or card_name


def _fetch_json(url: str, params: dict | None = None, headers: dict | None = None) -> dict | list | None:
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=20)
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception:
        return None


def _fetch_text(url: str, params: dict | None = None) -> str:
    try:
        resp = requests.get(url, params=params, timeout=20)
        if resp.status_code != 200:
            return ""
        return resp.text
    except Exception:
        return ""


def _tcgdex_set_id(jp_set_name: str) -> str:
    key = jp_set_name.strip()
    if key in _tcgdex_set_cache:
        return _tcgdex_set_cache[key] or ""

    data = _fetch_json(f"{TCGDEX_API_BASE}/sets", params={"name": key})
    set_id = ""
    if isinstance(data, list) and data:
        set_id = data[0].get("id", "")
    _tcgdex_set_cache[key] = set_id or None
    return set_id


def _tcgdex_name_search(jp_name: str) -> list[dict]:
    key = jp_name.strip()
    if key in _tcgdex_name_cache:
        return _tcgdex_name_cache[key]

    data = _fetch_json(f"{TCGDEX_API_BASE}/cards", params={"name": key})
    cards = data if isinstance(data, list) else []
    _tcgdex_name_cache[key] = cards
    return cards


def _tcgdex_set_cards(set_id: str) -> list[dict]:
    if set_id in _tcgdex_cards_cache:
        return _tcgdex_cards_cache[set_id]

    data = _fetch_json(f"{TCGDEX_API_BASE}/sets/{set_id}")
    cards = []
    if isinstance(data, dict):
        cards = data.get("cards", []) or []
    _tcgdex_cards_cache[set_id] = cards
    return cards


def _match_tcgdex_card(cards: list[dict], jp_name: str, card_number: str) -> dict | None:
    local_id = _normalize_local_id(card_number)
    normalized_name = _normalize_text(jp_name)

    if local_id:
        exact_local = [
            card for card in cards
            if _normalize_local_id(card.get("localId", "")) == local_id
        ]
        if len(exact_local) == 1:
            return exact_local[0]
        for card in exact_local:
            if _normalize_text(card.get("name", "")) == normalized_name:
                return card
        if exact_local:
            return exact_local[0]

    for card in cards:
        if _normalize_text(card.get("name", "")) == normalized_name:
            return card

    return None


def _find_tcgdex_image(card_name: str, jp_name: str, jp_set_name: str, card_number: str, set_name: str) -> str:
    set_id = _tcgdex_set_id(jp_set_name)
    if not set_id:
        set_id = _TCGDEX_SET_IDS.get(set_name, "") or ""

    cards = _tcgdex_set_cards(set_id)
    if cards:
        match = _match_tcgdex_card(cards, jp_name, card_number)
        if not match and card_name:
            match = _match_tcgdex_card(cards, _jp_lookup_keyword(card_name, jp_name), card_number)
        if match:
            return _tcgdex_high_image(match.get("image", ""))

    # Older sets sometimes have empty set card lists in TCGdex, but name search
    # can still return an image-bearing entry.
    expected_set_id = _TCGDEX_SET_IDS.get(set_name, "") or set_id
    search_terms = [jp_name]
    keyword = _jp_lookup_keyword(card_name, jp_name)
    if keyword and keyword not in search_terms:
        search_terms.append(keyword)

    local_id = _normalize_local_id(card_number)
    for term in search_terms:
        for item in _tcgdex_name_search(term):
            item_id = item.get("id", "")
            item_set_id = item_id.split("-")[0] if "-" in item_id else ""
            item_local_id = _normalize_local_id(item.get("localId", ""))
            if expected_set_id and item_set_id != expected_set_id:
                continue
            if local_id and item_local_id and item_local_id != local_id:
                continue
            image = item.get("image", "")
            if image:
                return _tcgdex_high_image(image)

    return ""


def _official_search(keyword: str) -> list[dict]:
    key = keyword.strip()
    if key in _official_search_cache:
        return _official_search_cache[key]

    data = _fetch_json(
        f"{POKEMON_CARD_BASE}/card-search/resultAPI.php",
        params={
            "pokemon": key,
            "keyword": key,
            "sm_and_keyword": "true",
            "regulation_sidebar_form": "all",
            "regulation": "all",
            "se_ta": "pokemon",
            "page": 1,
        },
    )
    cards = []
    if isinstance(data, dict) and data.get("result") == 1:
        cards = data.get("cardList", []) or []
    _official_search_cache[key] = cards
    return cards


def _official_detail(card_id: str, regulation: str = "all") -> dict:
    cache_key = f"{card_id}:{regulation}"
    if cache_key in _official_detail_cache:
        return _official_detail_cache[cache_key]

    html = _fetch_text(f"{POKEMON_CARD_BASE}/card-search/details.php/card/{card_id}/regu/{regulation}")
    if not html:
        _official_detail_cache[cache_key] = {}
        return {}

    image_match = _DETAIL_IMAGE_RE.search(html)
    set_match = _DETAIL_SET_RE.search(html)
    local_match = _DETAIL_LOCAL_ID_RE.search(html)

    detail = {
        "image_url": urljoin(POKEMON_CARD_BASE, image_match.group("src")) if image_match else "",
        "set_code": set_match.group("set") if set_match else "",
        "local_id": local_match.group("local") if local_match else "",
        "name": image_match.group("name") if image_match else "",
    }
    _official_detail_cache[cache_key] = detail
    return detail


def _find_official_image(card_name: str, jp_name: str, card_number: str, set_name: str) -> str:
    keyword = _jp_lookup_keyword(card_name, jp_name)
    results = _official_search(keyword)
    if not results:
        return ""

    local_id = _normalize_local_id(card_number)
    normalized_name = _normalize_text(jp_name)
    expected_set_code = _OFFICIAL_SET_CODES.get(set_name, "")

    best_url = ""
    best_score = -1
    matched_strongly = False
    for item in results[:12]:
        detail = _official_detail(str(item.get("cardID", "")))
        if not detail.get("image_url"):
            continue

        score = 0
        item_name = _normalize_text(item.get("cardNameAltText", ""))
        detail_name = _normalize_text(detail.get("name", ""))
        detail_local = _normalize_local_id(detail.get("local_id", ""))
        detail_set_code = detail.get("set_code", "")
        strong_match = False

        if local_id and detail_local == local_id:
            score += 4
            strong_match = True
        if expected_set_code and detail_set_code == expected_set_code:
            score += 4
            strong_match = True
        if normalized_name and item_name == normalized_name:
            score += 3
        if normalized_name and detail_name == normalized_name:
            score += 2
        if keyword and keyword in (item.get("cardNameAltText", "") or ""):
            score += 1

        if score > best_score:
            best_score = score
            best_url = detail["image_url"]
            matched_strongly = strong_match

    return best_url if best_score > 0 and matched_strongly else ""


def _resolve_jp_image(
    card_name: str,
    jp_name: str,
    jp_set_name: str,
    set_name: str,
    card_number: str,
) -> tuple[str, str]:
    tcgdex_url = _find_tcgdex_image(card_name, jp_name, jp_set_name, card_number, set_name)
    if tcgdex_url:
        return tcgdex_url, "tcgdex"

    official_url = _find_official_image(card_name, jp_name, card_number, set_name)
    if official_url:
        return official_url, "pokemon-card.com"

    return "", "missing_jp_scan"


def _fill_missing_images(cards: list[CardData]) -> tuple[list[CardData], bool]:
    changed = False
    for card in cards:
        extra = card.extra
        if not extra.get("jp_name"):
            extra["jp_name"] = _make_jp_name(card.name)
            changed = True
        if not extra.get("jp_set_name"):
            extra["jp_set_name"] = _SET_NAMES_JP.get(card.set_name, card.set_name)
            changed = True

        image_url = extra.get("image_url", "")
        if not _is_verified_jp_image(image_url):
            resolved_url, source = _resolve_jp_image(
                card.name,
                extra.get("jp_name", ""),
                extra.get("jp_set_name", ""),
                card.set_name,
                card.card_number,
            )
            if resolved_url != image_url:
                extra["image_url"] = resolved_url
                changed = True
            if extra.get("image_source") != source:
                extra["image_source"] = source
                changed = True
            if resolved_url:
                time.sleep(0.2)
        elif not extra.get("image_source"):
            extra["image_source"] = "cache"
            changed = True

    return cards, changed


def collect_jp_cards() -> list[CardData]:
    """Collect JP cards from JustTCG and enrich them with JP card images."""
    today = date.today().isoformat()

    if not JUSTTCG_API_KEY:
        cache = _load_cache()
        cached_date = cache.get("fetched_at", "")
        if cached_date:
            days_old = (date.today() - date.fromisoformat(cached_date)).days
            if days_old <= CACHE_MAX_AGE_DAYS and cache.get("cards"):
                logger.info(
                    "[justtcg_jp] Using cached JP data (%d cards, %d days old)",
                    len(cache["cards"]),
                    days_old,
                )
                cards = [_dict_to_carddata(item) for item in cache["cards"]]
                try:
                    cards, changed = _fill_missing_images(cards)
                    if changed:
                        _save_cache({"cards": [_carddata_to_dict(card) for card in cards], "fetched_at": cached_date})
                except Exception as exc:
                    logger.warning("[justtcg_jp] Image resolution failed for cached data: %s", exc)
                return cards
        logger.info("[justtcg_jp] No API key and no fresh cache, returning empty")
        return []

    headers = {"x-api-key": JUSTTCG_API_KEY, "Accept": "application/json"}
    collected: list[CardData] = []
    seen_names: set[str] = set()

    for query in JP_SEARCH_QUERIES:
        try:
            params = {"game": "pokemon-japan", "name": query, "limit": 10}
            resp = requests.get(f"{JUSTTCG_API_BASE}/cards", headers=headers, params=params, timeout=20)

            if resp.status_code == 429:
                logger.warning("[justtcg_jp] Rate limited, stopping JP collection")
                time.sleep(10)
                break
            if resp.status_code != 200:
                logger.warning("[justtcg_jp] %d for query='%s'", resp.status_code, query)
                continue

            data = resp.json().get("data", [])
            for item in data:
                name = item.get("name", "")
                if name in seen_names:
                    continue
                seen_names.add(name)

                for variant in item.get("variants", []):
                    if variant.get("language") != "Japanese":
                        continue
                    if variant.get("condition") not in ("Near Mint", "Lightly Played"):
                        continue

                    set_name_en = item.get("set_name", "") or ""
                    jp_set_name = _SET_NAMES_JP.get(set_name_en, set_name_en)
                    image_url = ""
                    raw_image = (
                        item.get("image_url") or item.get("image") or item.get("img_url") or item.get("picture") or ""
                    )
                    if _is_verified_jp_image(raw_image):
                        image_url = raw_image

                    raw_number = item.get("number", "") or ""
                    card_number = raw_number.split("/")[0] if "/" in raw_number else raw_number

                    collected.append(
                        CardData(
                            name=name,
                            set_name=set_name_en,
                            card_number=card_number,
                            pokemon_name=name,
                            price=float(variant.get("price", 0)) if variant.get("price") else None,
                            source="justtcg",
                            extra={
                                "game": "pokemon-jp",
                                "rarity": item.get("rarity", ""),
                                "image_url": image_url,
                                "image_source": "justtcg" if image_url else "missing_jp_scan",
                                "jp_name": _make_jp_name(name),
                                "jp_set_name": jp_set_name,
                                "jp_condition": variant.get("condition"),
                                "jp_printing": variant.get("printing"),
                                "jp_price_change_7d": variant.get("priceChange7d"),
                                "jp_price_change_30d": variant.get("priceChange30d"),
                            },
                        )
                    )
                    break

            time.sleep(1.0)
        except Exception as exc:
            logger.error("[justtcg_jp] Query '%s' failed: %s", query, exc)

    collected, _ = _fill_missing_images(collected)
    logger.info("[justtcg_jp] Collected %d JP cards from API", len(collected))

    old_cache = _load_cache()
    old_cards = old_cache.get("cards", [])
    old_by_name = {card["name"]: card for card in old_cards}
    new_by_name = {card.name: _carddata_to_dict(card) for card in collected}
    merged = {**old_by_name, **new_by_name}

    cache_data = {"cards": list(merged.values()), "fetched_at": today}
    _save_cache(cache_data)
    logger.info(
        "[justtcg_jp] Cache merged: %d old + %d new = %d total",
        len(old_cards),
        len(collected),
        len(cache_data["cards"]),
    )

    return collected


def _carddata_to_dict(card: CardData) -> dict:
    return {
        "name": card.name,
        "set_name": card.set_name,
        "card_number": card.card_number,
        "pokemon_name": card.pokemon_name,
        "price": card.price,
        "source": card.source,
        "extra": card.extra,
    }


def _dict_to_carddata(data: dict) -> CardData:
    raw_number = data.get("card_number", "") or ""
    card_number = raw_number.split("/")[0] if "/" in raw_number else raw_number
    return CardData(
        name=data.get("name", ""),
        set_name=data.get("set_name", ""),
        card_number=card_number,
        pokemon_name=data.get("pokemon_name", ""),
        price=data.get("price"),
        source=data.get("source", "justtcg"),
        extra=data.get("extra", {}),
    )
