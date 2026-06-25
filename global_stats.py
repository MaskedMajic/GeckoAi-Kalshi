import os
import uuid
import requests

import config


BOT_ID_PATH = os.path.join(
    "data",
    "bot_id.txt"
)

GLOBAL_STATS_URL = getattr(
    config,
    "GLOBAL_STATS_URL",
    "https://raspberrypi.tailfe26af.ts.net/trade"
)

GLOBAL_STATS_TOKEN = getattr(
    config,
    "GLOBAL_STATS_TOKEN",
    "gecko_mahk_kalshi"
)


def get_bot_id():
    os.makedirs(
        "data",
        exist_ok=True
    )

    if os.path.exists(BOT_ID_PATH):
        with open(BOT_ID_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()

    bot_id = str(uuid.uuid4())

    with open(BOT_ID_PATH, "w", encoding="utf-8") as f:
        f.write(bot_id)

    return bot_id


def enabled(trade=None):
    if not getattr(
        config,
        "GLOBAL_STATS_ENABLED",
        True
    ):
        return False

    if getattr(
        config,
        "GLOBAL_LIVE_ONLY",
        True
    ):
        if trade and not trade.get("live"):
            return False

    return True


def build_payload(trade, close_data):
    payload = {
        "bot_id": get_bot_id(),
        "bot_version": getattr(
            config,
            "BOT_VERSION",
            "0.1.0"
        ),
        "mode": "LIVE" if trade.get("live") else "PAPER",

        "ticker": trade.get("ticker"),
        "market": trade.get("market"),
        "side": trade.get("side"),

        "entry": trade.get("entry"),
        "avg_fill_price": trade.get("avg_fill_price"),
        "contracts": trade.get("contracts"),
        "time_left_minutes": trade.get("time_left"),

        "btc_entry_price": trade.get("btc_entry_price"),
        "btc_close_price": close_data.get("btc_close_price"),

        "winning_side": close_data.get("winning_side"),
        "result": close_data.get("result"),
        "pnl": close_data.get("pnl"),

        "closed_at": close_data.get("closed_at"),
    }

    if getattr(
        config,
        "SHARE_BALANCE",
        True
    ):
        payload["bankroll_before"] = trade.get("bankroll_before")
        payload["bankroll_after"] = close_data.get("bankroll_after")

    if getattr(
        config,
        "SHARE_TRADE_LOGS",
        True
    ):
        payload["contract_cost"] = trade.get("contract_cost")
        payload["fees"] = trade.get("fees")
        payload["limit_price"] = trade.get("limit_price")
        payload["raw_avg_fill_price"] = trade.get("raw_avg_fill_price")

        payload["lowest_seen"] = trade.get("lowest_seen")
        payload["highest_seen"] = trade.get("highest_seen")
        payload["worst_against_entry"] = trade.get("worst_against_entry")
        payload["best_in_favor_entry"] = trade.get("best_in_favor_entry")
        payload["price_path_points"] = trade.get("price_path_points")
        payload["price_path"] = trade.get("price_path")

    return payload


def send_trade(trade, close_data):
    if not enabled(trade):
        return False

    payload = build_payload(
        trade,
        close_data
    )

    try:
        response = requests.post(
            GLOBAL_STATS_URL,
            json=payload,
            headers={
                "X-GECKO-TOKEN": GLOBAL_STATS_TOKEN
            },
            timeout=10
        )

        if response.status_code not in [200, 201, 202]:
            print(
                f"[GLOBAL STATS ERROR] "
                f"{response.status_code} | {response.text}"
            )
            return False

        print("[GLOBAL STATS] Trade sent")
        return True

    except requests.exceptions.RequestException as e:
        print(f"[GLOBAL STATS ERROR] {e}")
        return False