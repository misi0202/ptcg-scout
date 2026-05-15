import logging
import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta

logger = logging.getLogger(__name__)


@dataclass
class SupplyDemand:
    card_id: int
    avg_price_30d: float
    price_change_pct: float
    volume_30d: int
    volume_change_pct: float
    in_stock_count: int
    sold_count: int
    supply_demand_ratio: float


def analyze(conn: sqlite3.Connection, card_id: int) -> SupplyDemand | None:
    today = date.today()
    d30 = today - timedelta(days=30)
    d60 = today - timedelta(days=60)

    current = conn.execute(
        """SELECT AVG(price) as avg_p, COUNT(*) as cnt
           FROM prices WHERE card_id = ? AND sale_date >= ?""",
        (card_id, d30.isoformat()),
    ).fetchone()

    previous = conn.execute(
        """SELECT AVG(price) as avg_p, COUNT(*) as cnt
           FROM prices WHERE card_id = ? AND sale_date >= ? AND sale_date < ?""",
        (card_id, d60.isoformat(), d30.isoformat()),
    ).fetchone()

    if not current or current["cnt"] == 0:
        return None

    avg_price = current["avg_p"] or 0
    prev_avg = previous["avg_p"] or avg_price
    price_change = ((avg_price - prev_avg) / prev_avg * 100) if prev_avg > 0 else 0

    volume = current["cnt"] or 0
    prev_volume = previous["cnt"] or volume
    volume_change = ((volume - prev_volume) / prev_volume * 100) if prev_volume > 0 else 0

    sold = conn.execute(
        "SELECT COUNT(*) as cnt FROM prices WHERE card_id = ? AND sale_date >= ?",
        (card_id, d30.isoformat()),
    ).fetchone()

    inventory = conn.execute(
        "SELECT COUNT(*) as cnt FROM prices WHERE card_id = ? AND price > 0",
        (card_id,),
    ).fetchone()

    sold_count = sold["cnt"] if sold else 0
    in_stock = inventory["cnt"] if inventory else 0
    ratio = sold_count / in_stock if in_stock > 0 else 0

    sd = SupplyDemand(
        card_id=card_id,
        avg_price_30d=round(avg_price, 2),
        price_change_pct=round(price_change, 2),
        volume_30d=volume,
        volume_change_pct=round(volume_change, 2),
        in_stock_count=in_stock,
        sold_count=sold_count,
        supply_demand_ratio=round(ratio, 3),
    )
    logger.debug("SupplyDemand card %d: avg=%.2f change=%.2f%% ratio=%.3f",
                 card_id, avg_price, price_change, ratio)
    return sd
