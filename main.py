import time
from datetime import datetime, timezone

import config
import discord_alerts
import kalshi_client
import live_broker
import paper_broker
import risk
import stats
import strategy


LIVE_MODE = "live_test"


def minutes_until_close(close_time: str) -> int:
    close_dt = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
    seconds_left = (close_dt - datetime.now(timezone.utc)).total_seconds()
    return max(0, int(seconds_left / 60))


def is_closed(close_time: str) -> bool:
    close_dt = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
    return datetime.now(timezone.utc) >= close_dt


def is_live_mode() -> bool:
    return config.MODE == LIVE_MODE


def get_starting_balance() -> float:
    if is_live_mode():
        return strategy.get_live_balance()

    summary = stats.get_summary()
    return summary["latest_bankroll"]


def send_startup_alert(balance: float) -> None:
    preview_contracts = risk.get_contracts(balance, 0.90)
    display_mode = "LIVE" if is_live_mode() else config.MODE.upper()

    startup = (
        "📡 BOT STARTED\n"
        f"Mode: {display_mode}\n"
        f"Balance: ${balance:.2f}\n"
        f"Contracts: {preview_contracts}\n"
        f"Sizing: {config.SIZING_MODE}"
    )

    print()
    print(startup)
    discord_alerts.send_message(startup)


def settle_open_trade(open_trade):
    if not is_closed(open_trade["close"]):
        return open_trade

    settled = paper_broker.close_paper_trade(open_trade)

    if settled:
        return None

    return open_trade


def track_open_trade(open_trade, last_move):
    live = kalshi_client.get_market_prices(open_trade["ticker"])

    if not live:
        time.sleep(5)
        return open_trade, last_move

    current = live["yes"] if open_trade["side"] == "YES" else live["no"]

    print(
        f"[TRACK] {open_trade['side']} | "
        f"ENTRY={open_trade['entry']:.2f} | "
        f"NOW={current:.2f}"
    )

    move = round(abs(current - open_trade["entry"]), 2)

    if move >= 0.10 and move != last_move:
        discord_alerts.send_message(
            f"📊 UPDATE | "
            f"{open_trade['side']} | "
            f"{open_trade['entry']:.2f} → {current:.2f}"
        )
        last_move = move

    time.sleep(5)
    return open_trade, last_move


def pick_side(market):
    yes = market["yes_entry"]
    no = market["no_entry"]

    if 0.88 <= yes <= 0.95:
        return "YES", yes

    if 0.88 <= no <= 0.95:
        return "NO", no

    return None, None


def open_new_trade(market, side, entry, time_left):
    if is_live_mode():
        return live_broker.place_live_order(market, side, entry, time_left)

    return paper_broker.open_paper_trade(market, side, entry, time_left)


def main():
    stats.init_db()

    starting_balance = get_starting_balance()
    send_startup_alert(starting_balance)

    open_trade = None
    last_move = None

    while True:
        if open_trade:
            open_trade = settle_open_trade(open_trade)

            if open_trade is None:
                last_move = None
                time.sleep(10)
                continue

            open_trade, last_move = track_open_trade(open_trade, last_move)
            continue

        market = kalshi_client.get_market()

        if not market:
            print("[WAIT]")
            time.sleep(10)
            continue

        yes = market["yes_entry"]
        no = market["no_entry"]
        time_left = minutes_until_close(market["close"])

        side, entry = pick_side(market)

        print(
            f"[WATCH] YES={yes:.2f} | "
            f"NO={no:.2f} | "
            f"TIME={time_left}m | "
            f"SIDE={side or '-'}"
        )

        if side:
            allowed, reason = strategy.should_trade(entry, time_left)
            print(f"[DECISION] {allowed} | {reason}")

            if allowed:
                open_trade = open_new_trade(market, side, entry, time_left)

        time.sleep(5 if time_left <= 5 else 30)


if __name__ == "__main__":
    main()