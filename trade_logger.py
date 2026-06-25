import json
import os
import uuid
from datetime import datetime, timezone

import config


TRADE_LOG_PATH = getattr(
    config,
    "TRADE_JSON_PATH",
    os.path.join("data", "trades.json")
)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def _read_log():
    if not os.path.exists(TRADE_LOG_PATH):
        return []

    with open(TRADE_LOG_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return []

    if isinstance(data, list):
        return data

    return []


def _write_log(records):
    directory = os.path.dirname(TRADE_LOG_PATH)

    if directory:
        os.makedirs(directory, exist_ok=True)

    temp_path = f"{TRADE_LOG_PATH}.tmp"

    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
        f.write("\n")

    os.replace(temp_path, TRADE_LOG_PATH)


def _trade_movement_fields(trade):
    entry = trade.get("entry")
    lowest_seen = trade.get("lowest_seen")
    highest_seen = trade.get("highest_seen")
    price_path = trade.get("price_path", [])

    worst_against_entry = None
    best_in_favor_entry = None

    if entry is not None and lowest_seen is not None:
        worst_against_entry = round(
            entry - lowest_seen,
            4
        )

    if entry is not None and highest_seen is not None:
        best_in_favor_entry = round(
            highest_seen - entry,
            4
        )

    return {
        "lowest_seen": lowest_seen,
        "highest_seen": highest_seen,
        "worst_against_entry": worst_against_entry,
        "best_in_favor_entry": best_in_favor_entry,
        "price_path": price_path,
        "price_path_points": len(price_path),
    }


def log_trade_open(trade):
    trade_id = trade.get("trade_id") or str(uuid.uuid4())
    trade["trade_id"] = trade_id

    movement = _trade_movement_fields(trade)

    records = _read_log()
    records.append({
        "trade_id": trade_id,
        "status": "OPEN",
        "mode": "LIVE" if trade.get("live") else "PAPER",
        "market": trade.get("market"),
        "ticker": trade.get("ticker"),
        "side": trade.get("side"),
        "opened_at": trade.get("opened_at") or now_iso(),
        "market_close_time": trade.get("close"),
        "time_left_minutes": trade.get("time_left"),
        "btc_entry_price": trade.get("btc_entry_price"),
        "entry_contract_price": trade.get("entry"),
        "avg_fill_price": trade.get("avg_fill_price"),
        "limit_price": trade.get("limit_price"),
        "contracts": trade.get("contracts"),
        "contract_cost": trade.get("contract_cost"),
        "fees": trade.get("fees"),
        "bankroll_before": trade.get("bankroll_before"),
        "bankroll_after": None,
        "btc_close_price": None,
        "exit_contract_value": None,
        "winning_side": None,
        "result": None,
        "pnl": None,
        "closed_at": None,

        "lowest_seen": movement["lowest_seen"],
        "highest_seen": movement["highest_seen"],
        "worst_against_entry": movement["worst_against_entry"],
        "best_in_favor_entry": movement["best_in_favor_entry"],
        "price_path": movement["price_path"],
        "price_path_points": movement["price_path_points"],
    })

    _write_log(records)
    return trade_id


def log_trade_close(trade, close_data):
    trade_id = trade.get("trade_id") or str(uuid.uuid4())
    records = _read_log()

    movement = _trade_movement_fields(trade)

    close_data = {
        **close_data,
        "lowest_seen": movement["lowest_seen"],
        "highest_seen": movement["highest_seen"],
        "worst_against_entry": movement["worst_against_entry"],
        "best_in_favor_entry": movement["best_in_favor_entry"],
        "price_path": movement["price_path"],
        "price_path_points": movement["price_path_points"],
    }

    for record in reversed(records):
        if record.get("trade_id") == trade_id:
            record.update(close_data)
            record["status"] = "CLOSED"
            _write_log(records)
            return trade_id

    records.append({
        "trade_id": trade_id,
        "status": "CLOSED",
        "mode": "LIVE" if trade.get("live") else "PAPER",
        "market": trade.get("market"),
        "ticker": trade.get("ticker"),
        "side": trade.get("side"),
        "opened_at": trade.get("opened_at"),
        "market_close_time": trade.get("close"),
        "time_left_minutes": trade.get("time_left"),
        "btc_entry_price": trade.get("btc_entry_price"),
        "entry_contract_price": trade.get("entry"),
        "avg_fill_price": trade.get("avg_fill_price"),
        "limit_price": trade.get("limit_price"),
        "contracts": trade.get("contracts"),
        "contract_cost": trade.get("contract_cost"),
        "fees": trade.get("fees"),
        "bankroll_before": trade.get("bankroll_before"),
        **close_data,
    })

    _write_log(records)
    return trade_id