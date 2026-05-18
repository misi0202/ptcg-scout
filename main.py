import json
import logging
import os
import sys
from datetime import date

from dotenv import load_dotenv

from collectors import EbayCollector, PokemonTCGCollector, RedditCollector, collect_jp_cards
from collectors.justtcg import enrich_top_cards
from db.models import get_connection, init_db, insert_card, insert_mention, insert_price
from analyzer.boxes import analyze_boxes, save_boxes
from analyzer.scoring import compute_scores
from analyzer.supply_demand import analyze as sd_analyze
from analyzer.trends import determine_signal, signal_label
from notifier.feishu import send_daily_report, send_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ptcg-scout")

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
HISTORY_DIR = os.path.join(DATA_DIR, "history")


def save_json(filename: str, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Saved %s", path)


def collect_all():
    collectors = [
        PokemonTCGCollector(),
        EbayCollector(),
        RedditCollector(),
    ]
    all_data = []
    for collector in collectors:
        try:
            data = collector.collect()
            all_data.extend(data)
            logger.info("Collector %s: %d items", collector.name, len(data))
        except Exception as e:
            logger.error("Collector %s failed: %s", collector.name, e)

    # JP card collector (function-based, uses JustTCG API when key available)
    try:
        jp_data = collect_jp_cards()
        all_data.extend(jp_data)
        logger.info("Collector justtcg_jp: %d items", len(jp_data))
    except Exception as e:
        logger.warning("Collector justtcg_jp failed: %s", e)

    return all_data


_jp_names: dict[int, str] = {}  # card_id -> Japanese name


def store_data(conn, all_data):
    for item in all_data:
        try:
            card_id = insert_card(
                conn,
                name=item.name,
                set_name=item.set_name,
                card_number=item.card_number,
                pokemon_name=item.pokemon_name,
                artist=item.extra.get("artist", ""),
                rarity=item.extra.get("rarity", ""),
                image_url=item.extra.get("image_url", ""),
                game=item.extra.get("game", "pokemon"),
            )
            if item.price is not None and item.price > 0:
                insert_price(
                    conn, card_id=card_id, source=item.source,
                    price=item.price, condition=item.condition,
                    sale_date=item.sale_date,
                )
            # Also store cardmarket price if available
            cm_price = item.extra.get("cardmarket_avg")
            if cm_price and cm_price > 0:
                try:
                    insert_price(
                        conn, card_id=card_id, source="cardmarket",
                        price=float(cm_price), condition=item.condition,
                        sale_date=item.sale_date,
                    )
                except (ValueError, TypeError):
                    pass
            # Track JP card names
            jp_name = item.extra.get("jp_name", "")
            if jp_name:
                _jp_names[card_id] = jp_name

            if item.source == "reddit" and item.pokemon_name:
                mention_count = item.extra.get("score") or item.extra.get("reactions") or 1
                mention_date = item.extra.get("created_utc") or item.extra.get("timestamp") or ""
                insert_mention(
                    conn, card_id=card_id, source=item.source,
                    keyword=item.pokemon_name,
                    mention_count=mention_count,
                    mention_date=mention_date,
                )
        except Exception as e:
            logger.error("Failed to store item %s: %s", item.name, e)
    conn.commit()


def run_scoring(conn) -> list[dict]:
    rows = conn.execute("""
        SELECT c.id, c.name, c.pokemon_name, c.set_name,
               c.psa10_pop, c.psa_total_pop, c.rarity, c.artist, c.image_url, c.game,
               c.card_number
        FROM cards c
        WHERE c.set_name NOT IN ('PokemonTCG', 'PokeInvesting', 'PokemonCardValue')
    """).fetchall()

    # Mention counts per card
    mention_rows = conn.execute(
        "SELECT card_id, SUM(mention_count) as total FROM mentions GROUP BY card_id"
    ).fetchall()
    card_mentions: dict[int, int] = {mr["card_id"]: mr["total"] for mr in mention_rows}

    # Price data by source
    price_rows = conn.execute(
        "SELECT card_id, source, AVG(price) as avg_p FROM prices GROUP BY card_id, source"
    ).fetchall()
    card_prices: dict[int, dict[str, float]] = {}
    for pr in price_rows:
        card_prices.setdefault(pr["card_id"], {})[pr["source"]] = round(pr["avg_p"], 2)

    # Load JP price trends from caches (JustTCG enrichment + JP card cache)
    import json as _json
    jp_trends: dict[str, dict] = {}
    for _cache_file in ("jp_cache.json", "jp_cards_cache.json"):
        _jp_cache_path = os.path.join(DATA_DIR, _cache_file)
        try:
            with open(_jp_cache_path, encoding="utf-8") as f:
                jp_cache = _json.load(f)
            if _cache_file == "jp_cache.json":
                for card_name, data in jp_cache.items():
                    if isinstance(data, dict) and data.get("jp_price"):
                        jp_trends[card_name] = {
                            "change_7d": data.get("jp_price_change_7d") or 0,
                            "change_30d": data.get("jp_price_change_30d") or 0,
                        }
            else:  # jp_cards_cache.json
                for card_data in jp_cache.get("cards", []):
                    name = card_data.get("name", "")
                    extra = card_data.get("extra", {})
                    if name and (extra.get("jp_price_change_7d") or extra.get("jp_price_change_30d")):
                        jp_trends[name] = {
                            "change_7d": extra.get("jp_price_change_7d") or 0,
                            "change_30d": extra.get("jp_price_change_30d") or 0,
                        }
        except Exception:
            pass

    # Build card inputs for compute_scores
    card_inputs = []
    for row in rows:
        cid = row["id"]
        prices = card_prices.get(cid, {})
        mention_total = card_mentions.get(cid, 0)
        sd = sd_analyze(conn, cid)

        # Look up JP price trends from cache
        name = row["name"] or ""
        jp_trend = jp_trends.get(name, {})

        card_inputs.append({
            "id": cid,
            "name": name,
            "pokemon": row["pokemon_name"] or "",
            "us_price": prices.get("pokemontcg", 0),
            "cm_price": prices.get("cardmarket", 0),
            "jp_price": prices.get("justtcg", 0),
            "mention_count": mention_total,
            "price_change_pct": sd.price_change_pct if sd else 0,
            "jp_price_change_7d": jp_trend.get("change_7d", 0),
            "jp_price_change_30d": jp_trend.get("change_30d", 0),
            "image_url": row["image_url"] or "",
            "rarity": row["rarity"] or "",
            "artist": row["artist"] or "",
            "set_name": row["set_name"] or "",
            "game": row["game"] or "pokemon",
        })

    scores = compute_scores(card_inputs)

    results = []
    for score in scores:
        cid = score.card_id
        row = next(r for r in rows if r["id"] == cid)
        prices = card_prices.get(cid, {})
        mention_total = card_mentions.get(cid, 0)
        sd = sd_analyze(conn, cid)
        signal = determine_signal(sd, mention_total)

        results.append({
            "id": score.card_id,
            "name": score.name,
            "pokemon": score.pokemon_name,
            "image_url": row["image_url"] or "",
            "rarity": row["rarity"] or "",
            "artist": row["artist"] or "",
            "set_name": row["set_name"] or "",
            "game": row["game"] or "pokemon",
            "composite": score.composite_score,
            "price_signal": score.price_signal,
            "ip_signal": score.ip_signal,
            "volume_signal": score.volume_signal,
            "momentum": score.momentum,
            "divergence_score": score.divergence_score,
            "signal": signal,
            "signal_label": signal_label(signal),
            "jp_name": _jp_names.get(cid, ""),
            "reason": score.reason,
            "us_price": prices.get("pokemontcg", 0),
            "cm_price": prices.get("cardmarket", 0),
            "jp_price": prices.get("justtcg", 0),
            "avg_price_30d": sd.avg_price_30d if sd else 0,
            "price_change_pct": sd.price_change_pct if sd else 0,
            "volume_30d": sd.volume_30d if sd else 0,
            "supply_demand_ratio": sd.supply_demand_ratio if sd else 0,
        })

    results.sort(key=lambda x: x["composite"], reverse=True)
    logger.info("Scored %d cards, TOP 5: %s", len(results),
                [f"{r['name'][:20]}({r['composite']})" for r in results[:5]])

    # Top 100 by score, plus all JP cards (ensures JP filter has data)
    output = results[:100]
    included_ids = {r["id"] for r in output}
    for r in results[100:]:
        if r.get("game") == "pokemon-jp" and r["id"] not in included_ids:
            output.append(r)
            included_ids.add(r["id"])
    return output


def save_history_snapshot(results: list[dict]):
    os.makedirs(HISTORY_DIR, exist_ok=True)
    today = date.today().isoformat()
    path = os.path.join(HISTORY_DIR, f"{today}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info("History snapshot saved: %s", path)


def main():
    logger.info("PTCG Scout starting...")

    init_db()
    conn = get_connection()

    all_data = collect_all()
    logger.info("Total items collected: %d", len(all_data))

    store_data(conn, all_data)

    top50 = run_scoring(conn)
    logger.info("TOP 50 scored, #1: %s (%.2f)", top50[0]["name"] if top50 else "N/A",
                top50[0]["composite"] if top50 else 0)

    # Enrich with JP market data
    top50 = enrich_top_cards(top50, max_lookups=30)

    save_json("cards.json", top50)
    save_history_snapshot(top50)

    boxes = analyze_boxes()
    save_boxes(boxes)
    logger.info("Box analysis: %d boxes", len(boxes))

    conn.close()

    top10 = top50[:10]
    send_daily_report(top10)

    alerts = [
        c for c in top50
        if abs(c["price_change_pct"]) > 10
    ]
    if alerts:
        for a in alerts:
            a["alert_reason"] = f"价格异动 {a['price_change_pct']:+.1f}%"
        send_alert(alerts)

    logger.info("PTCG Scout finished.")


if __name__ == "__main__":
    main()
