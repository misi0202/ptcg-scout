import json
import logging
import os
from datetime import date, timedelta

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# Known box release dates and reprint info (manually maintained)
KNOWN_BOXES = [
    {"name": "SV2a 151", "set_name": "Scarlet & Violet 151", "release_date": "2023-09-22", "reprint_cycle_months": 6},
    {"name": "SV10 Rocket", "set_name": "Scarlet & Violet 10: Rocket", "release_date": "2025-04-18", "reprint_cycle_months": 4},
    {"name": "VSTAR Universe", "set_name": "VSTAR Universe", "release_date": "2022-12-02", "reprint_cycle_months": 3},
    {"name": "Shiny Treasure ex", "set_name": "Shiny Treasure ex", "release_date": "2023-12-01", "reprint_cycle_months": 3},
    {"name": "Ruler of the Black Flame", "set_name": "Ruler of the Black Flame", "release_date": "2023-07-28", "reprint_cycle_months": 3},
    {"name": "Future Flash", "set_name": "Future Flash", "release_date": "2023-10-27", "reprint_cycle_months": 3},
    {"name": "Wild Force", "set_name": "Wild Force", "release_date": "2024-01-26", "reprint_cycle_months": 3},
]


def analyze_boxes() -> list[dict]:
    today = date.today()
    results = []

    for box in KNOWN_BOXES:
        try:
            release = date.fromisoformat(box["release_date"])
        except (ValueError, KeyError):
            release = today - timedelta(days=365)

        months_since_release = (today - release).days / 30.0
        reprint_cycle = box.get("reprint_cycle_months", 4)

        low_point = False
        reprint_status = "正常"
        if 3 <= months_since_release <= 5:
            reprint_status = "观察窗口期"
            low_point = True
        elif months_since_release > 5 and months_since_release > reprint_cycle:
            reprint_status = "等待再贩信号"
            low_point = True
        elif months_since_release < 1:
            reprint_status = "新品期"

        results.append({
            "id": box["name"].replace(" ", "_").lower(),
            "name": box["name"],
            "set_name": box["set_name"],
            "release_date": box["release_date"],
            "reprint_status": reprint_status,
            "current_price": 0,  # populated by price collectors
            "months_since_release": round(months_since_release, 1),
            "reprint_cycle_months": reprint_cycle,
            "low_point_alert": 1 if low_point else 0,
        })

    logger.info("Box analysis: %d boxes, %d with low-point alert",
                len(results), sum(1 for r in results if r["low_point_alert"]))
    return results


def save_boxes(boxes: list[dict]):
    path = os.path.join(DATA_DIR, "boxes.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(boxes, f, ensure_ascii=False, indent=2)
    logger.info("Saved boxes.json")
