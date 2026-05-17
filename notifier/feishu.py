import json
import logging
import os
from datetime import date

import requests

logger = logging.getLogger(__name__)

WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")


def send_card(title: str, content: str, color: str = "blue"):
    if not WEBHOOK_URL:
        logger.warning("FEISHU_WEBHOOK_URL not set, skipping notification")
        return

    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": color,
            },
            "elements": [
                {"tag": "markdown", "content": content},
                {
                    "tag": "note",
                    "elements": [
                        {"tag": "plain_text", "content": f"PTCG Scout · {date.today().isoformat()}"}
                    ],
                },
            ],
        },
    }

    try:
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info("[feishu] Notification sent: %s", title[:50])
        else:
            logger.error("[feishu] Failed: %d %s", resp.status_code, resp.text)
    except Exception as e:
        logger.error("[feishu] Error: %s", e)


SIGNAL_EMOJI = {
    "bullish": "🟢",
    "cautious": "🟡",
    "bearish": "🔴",
    "watch": "🔵",
    "neutral": "⚪",
    "insufficient_data": "⚫",
}


def send_daily_report(top10: list[dict]):
    lines = []
    for i, card in enumerate(top10, 1):
        emoji = SIGNAL_EMOJI.get(card["signal"], "⚪")
        ps = card.get("price_signal", 0)
        vs = card.get("volume_signal", 0)
        mom = card.get("momentum", 0)
        lines.append(
            f"{i}. **{card['name']}** | Score **{card['composite']}** | {emoji} {card['signal_label']}\n"
            f"   Price: {ps:.0f} · Volume: {vs:.0f} · Momentum: {mom:+.0f}\n"
            f"   30d avg ${card['avg_price_30d']:.2f} "
            f"({card['price_change_pct']:+.1f}%) | {card['reason']}"
        )

    content = "\n\n".join(lines)
    send_card(
        title=f"PTCG 潜力卡日报 TOP {len(top10)}",
        content=content,
        color="blue",
    )


def send_alert(alert_items: list[dict]):
    if not alert_items:
        return

    lines = []
    for item in alert_items:
        emoji = SIGNAL_EMOJI.get(item.get("signal", ""), "")
        lines.append(f"- {emoji} **{item['name']}**: {item.get('alert_reason', '')}")

    content = "\n".join(lines)
    send_card(
        title="PTCG 异动提醒",
        content=content,
        color="red",
    )
