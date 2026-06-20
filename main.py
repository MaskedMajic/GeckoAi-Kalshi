import time
from datetime import datetime, timezone

import config
import stats
import strategy
import risk
import paper_broker
import live_broker
import discord_alerts
import kalshi_client


def mins(close):
    dt = datetime.fromisoformat(close.replace("Z", "+00:00"))
    return max(
        0,
        int((dt - datetime.now(timezone.utc)).total_seconds() / 60),
    )


def closed(close):
    dt = datetime.fromisoformat(close.replace("Z", "+00:00"))
    return datetime.now(timezone.utc) >= dt


def get_starting_balance():
    if config.MODE == "live_test":
        return strategy.get_live_balance()

    summary = stats.get_summary()
    return summary["latest_bankroll"]


stats.init_db()

starting_balance = get_starting_balance()
preview_contracts = risk.get_contracts(starting_balance, 0.90)

display_mode = "LIVE" if config.MODE == "live_test" else config.MODE.upper()

startup = (
    "📡 BOT STARTED\n"
    f"Mode: {display_mode}\n"
    f"Balance: ${starting_balance:.2f}\n"
    f"Contracts: {preview_contracts}\n"
    f"Sizing: {config.SIZING_MODE}"
)

print()
print(startup)
discord_alerts.send_message(startup)

open_trade = None
last_move = None

while True:
    if open_trade:
        if closed(open_trade["close"]):
            settled = paper_broker.close_paper_trade(open_trade)

            if settled:
                open_trade = None
                last_move = None

            time.sleep(10)
            continue

        live = kalshi_client.get_market_prices(open_trade["ticker"])

        if live:
            current = (
                live["yes"]
                if open_trade["side"] == "YES"
                else live["no"]
            )

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
        continue

    market = kalshi_client.get_market()

    if not market:
        print("[WAIT]")
        time.sleep(10)
        continue

    yes = market["yes_entry"]
    no = market["no_entry"]
    time_left = mins(market["close"])

    side = None
    entry = None

    if 0.88 <= yes <= 0.95:
        side = "YES"
        entry = yes
    elif 0.88 <= no <= 0.95:
        side = "NO"
        entry = no

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
            if config.MODE == "live_test":
                open_trade = live_broker.place_live_order(
                    market,
                    side,
                    entry,
                    time_left,
                )
            else:
                open_trade = paper_broker.open_paper_trade(
                    market,
                    side,
                    entry,
                    time_left,
                )

    time.sleep(5 if time_left <= 5 else 30)