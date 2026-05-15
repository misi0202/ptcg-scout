import logging

from .supply_demand import SupplyDemand

logger = logging.getLogger(__name__)

# Thresholds
HEAT_THRESHOLD = 50
PRICE_CHANGE_THRESHOLD = 5.0
VOLUME_CHANGE_THRESHOLD = 10.0


def determine_signal(sd: SupplyDemand | None, mention_count: int = 0) -> str:
    if sd is None:
        return "insufficient_data"

    price_up = sd.price_change_pct > PRICE_CHANGE_THRESHOLD
    price_down = sd.price_change_pct < -PRICE_CHANGE_THRESHOLD
    volume_up = sd.volume_change_pct > VOLUME_CHANGE_THRESHOLD
    volume_down = sd.volume_change_pct < -VOLUME_CHANGE_THRESHOLD
    demand_strong = sd.supply_demand_ratio > 0.5
    demand_weak = sd.supply_demand_ratio < 0.2
    hot = mention_count > HEAT_THRESHOLD

    if volume_up and price_up and demand_strong:
        return "bullish"       # 放量上涨 + 供需缺口大
    if volume_up and price_up and hot:
        return "bullish"
    if volume_down and price_up and demand_weak:
        return "cautious"      # 缩量上涨，需求弱
    if price_down and volume_down and not hot:
        return "bearish"       # 量价齐跌
    if not price_up and not price_down and volume_up and not hot:
        return "watch"         # 价稳量增，关注
    if hot and price_up:
        return "bullish"
    if hot and not price_down:
        return "watch"

    return "neutral"


SIGNAL_LABELS = {
    "bullish": "🟢 强烈看涨",
    "cautious": "🟡 谨慎观望",
    "bearish": "🔴 规避",
    "watch": "🔵 关注（可能低点）",
    "neutral": "⚪ 中性",
    "insufficient_data": "⚫ 数据不足",
}


def signal_label(signal: str) -> str:
    return SIGNAL_LABELS.get(signal, signal)
