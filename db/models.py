import sqlite3
import os
from datetime import date

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ptcg.db")

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(os.path.abspath(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def insert_card(conn: sqlite3.Connection, name: str, set_name: str,
                card_number: str = "", pokemon_name: str = "",
                artist: str = "", rarity: str = "", image_url: str = "") -> int:
    conn.execute(
        """INSERT OR IGNORE INTO cards (name, set_name, card_number, pokemon_name, artist, rarity, image_url)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (name, set_name, card_number, pokemon_name, artist, rarity, image_url),
    )
    row = conn.execute(
        "SELECT id FROM cards WHERE name=? AND set_name=?",
        (name, set_name),
    ).fetchone()
    return row["id"] if row else -1


def insert_price(conn: sqlite3.Connection, card_id: int, source: str,
                 price: float, condition: str = "", sale_date: str = ""):
    conn.execute(
        """INSERT INTO prices (card_id, source, price, condition, sale_date)
           VALUES (?, ?, ?, ?, ?)""",
        (card_id, source, price, condition, sale_date or None),
    )


def insert_mention(conn: sqlite3.Connection, card_id: int, source: str,
                   keyword: str, mention_count: int, mention_date: str):
    conn.execute(
        """INSERT INTO mentions (card_id, source, keyword, mention_count, mention_date)
           VALUES (?, ?, ?, ?, ?)""",
        (card_id, source, keyword, mention_count, mention_date),
    )


def get_prices_30d(conn: sqlite3.Connection, card_id: int) -> list[dict]:
    rows = conn.execute(
        """SELECT price, sale_date FROM prices
           WHERE card_id = ? AND sale_date >= date('now', '-30 days')
           ORDER BY sale_date""",
        (card_id,),
    ).fetchall()
    return [dict(r) for r in rows]
