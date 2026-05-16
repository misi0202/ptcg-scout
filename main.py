import json
import logging
import os
import sys
from datetime import date

from dotenv import load_dotenv

from collectors import DiscordCollector, PokemonTCGCollector, RedditCollector
from db.models import get_connection, init_db, insert_card, insert_mention, insert_price
from analyzer.boxes import analyze_boxes, save_boxes
from analyzer.scoring import calculate_score, CardScore
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
        RedditCollector(),
        DiscordCollector(),
    ]
    all_data = []
    for collector in collectors:
        try:
            data = collector.collect()
            all_data.extend(data)
            logger.info("Collector %s: %d items", collector.name, len(data))
        except Exception as e:
            logger.error("Collector %s failed: %s", collector.name, e)
    return all_data


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
            if item.source in ("reddit", "discord") and item.pokemon_name:
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
               c.psa10_pop, c.psa_total_pop, c.rarity, c.artist, c.image_url
        FROM cards c
    """).fetchall()

    results = []
    for row in rows:
        mention_data = conn.execute(
            "SELECT keyword, SUM(mention_count) as total FROM mentions WHERE card_id=?",
            (row["id"],),
        ).fetchone()

        keywords = []
        mention_total = 0
        if mention_data:
            keywords = [mention_data["keyword"]] if mention_data["keyword"] else []
            mention_total = mention_data["total"] or 0

        score = calculate_score(
            card_id=row["id"],
            name=row["name"],
            pokemon_name=row["pokemon_name"] or "",
            keywords=keywords,
            mention_count=mention_total,
            psa10_pop=row["psa10_pop"] or 0,
            set_name=row["set_name"] or "",
            rarity=row["rarity"] or "",
            artist=row["artist"] or "",
        )

        sd = sd_analyze(conn, row["id"])
        signal = determine_signal(sd, mention_total)

        results.append({
            "id": score.card_id,
            "name": score.name,
            "pokemon": score.pokemon_name,
            "image_url": row["image_url"] or "",
            "rarity": row["rarity"] or "",
            "artist": row["artist"] or "",
            "set_name": row["set_name"] or "",
            "aesthetic": score.aesthetic_score,
            "ip": score.ip_score,
            "narrative": score.narrative_score,
            "pop_mult": score.pop_multiplier,
            "composite": score.composite_score,
            "signal": signal,
            "signal_label": signal_label(signal),
            "reason": score.reason,
            "avg_price_30d": sd.avg_price_30d if sd else 0,
            "price_change_pct": sd.price_change_pct if sd else 0,
            "volume_30d": sd.volume_30d if sd else 0,
            "supply_demand_ratio": sd.supply_demand_ratio if sd else 0,
        })

    results.sort(key=lambda x: x["composite"], reverse=True)
    return results[:30]


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

    top30 = run_scoring(conn)
    logger.info("TOP 30 scored, #1: %s (%.2f)", top30[0]["name"] if top30 else "N/A",
                top30[0]["composite"] if top30 else 0)

    save_json("cards.json", top30)
    save_history_snapshot(top30)

    boxes = analyze_boxes()
    save_boxes(boxes)
    logger.info("Box analysis: %d boxes", len(boxes))

    conn.close()

    top10 = top30[:10]
    send_daily_report(top10)

    alerts = [
        c for c in top30
        if abs(c["price_change_pct"]) > 10
    ]
    if alerts:
        for a in alerts:
            a["alert_reason"] = f"价格异动 {a['price_change_pct']:+.1f}%"
        send_alert(alerts)

    logger.info("PTCG Scout finished.")


if __name__ == "__main__":
    main()
