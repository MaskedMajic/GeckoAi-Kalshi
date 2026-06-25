import os
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
import kalshi_stream


GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[96m"
PURPLE = "\033[95m"
RED = "\033[91m"
RESET = "\033[0m"


def time_left(close):
    dt = datetime.fromisoformat(close.replace("Z", "+00:00"))
    seconds = max(0, int((dt - datetime.now(timezone.utc)).total_seconds()))
    return seconds // 60, seconds % 60, seconds


def closed(close):
    _, _, seconds = time_left(close)
    return seconds <= 0


def repaint(message):
    os.system("cls")
    print(message, end="", flush=True)


def get_starting_balance():
    if config.MODE == "live_test":
        return strategy.get_live_balance()

    summary = stats.get_summary()
    return summary["latest_bankroll"]


def get_price(market):
    latest = kalshi_stream.get_latest()

    if latest and latest.get("ticker") == market["ticker"]:
        return {
            "yes": latest["yes"],
            "no": latest["no"],
            "source": "STREAM",
        }

    fallback = kalshi_client.get_market_prices(market["ticker"])

    if fallback:
        return {
            "yes": fallback["yes"],
            "no": fallback["no"],
            "source": "REST",
        }

    return None


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

discord_alerts.send_message(startup)

open_trade = None
stream_ticker = None


while True:

    if open_trade:

        if closed(open_trade["close"]):

            settled = paper_broker.close_paper_trade(open_trade)

            if settled:
                open_trade = None

            time.sleep(5)
            continue

        live = get_price(open_trade)

        if live:

            current = (
                live["yes"]
                if open_trade["side"] == "YES"
                else live["no"]
            )

            mm, ss, _ = time_left(open_trade["close"])

            repaint(
                f"{YELLOW}🟡 ACTIVE TRADE{RESET}\n\n"
                f"Mode: {display_mode}\n"
                f"Ticker: {open_trade['ticker']}\n"
                f"Side: {open_trade['side']}\n"
                f"Entry: {open_trade['entry']:.2f}\n"
                f"Now: {current:.2f}\n"
                f"Time: {mm:02}:{ss:02}\n"
                f"Source: {live['source']}\n"
            )

        time.sleep(1)
        continue

    market = kalshi_client.get_market()

    if not market:

        repaint(
            f"{RED}🔴 WAITING MARKET{RESET}\n"
        )

        kalshi_stream.stop()
        stream_ticker = None

        time.sleep(5)
        continue

    if stream_ticker != market["ticker"]:

        stream_ticker = market["ticker"]

        kalshi_stream.stop()
        kalshi_stream.start(stream_ticker)

        repaint(
            f"{PURPLE}🟣 STREAM ROLLOVER{RESET}\n\n"
            f"Ticker: {stream_ticker}\n"
            f"Waiting for stream ticks...\n"
        )

        time.sleep(2)
        continue

    live_price = get_price(market)

    if not live_price:

        repaint(
            f"{BLUE}🔵 WAITING PRICE{RESET}\n\n"
            f"Ticker: {market['ticker']}\n"
            f"Waiting for ticks...\n"
        )

        time.sleep(2)
        continue

    yes = live_price["yes"]
    no = live_price["no"]

    mm, ss, seconds_left = time_left(market["close"])

    side = "-"
    entry = None

    if config.ENTRY_MIN <= yes <= config.ENTRY_MAX:
        side = "YES"
        entry = yes

    elif config.ENTRY_MIN <= no <= config.ENTRY_MAX:
        side = "NO"
        entry = no

    allowed = False
    reason = "-"

    if entry:
        allowed, reason = strategy.should_trade(
            entry,
            seconds_left / 60
        )

    decision = "ENTER" if allowed else "WAIT"

    repaint(
        f"{GREEN}🟢 GECKOAI LIVE{RESET}\n\n"
        f"Mode: {display_mode}\n"
        f"Balance: ${starting_balance:.2f}\n"
        f"Contracts: {preview_contracts}\n"
        f"Sizing: {config.SIZING_MODE}\n\n"
        f"Ticker: {market['ticker']}\n"
        f"YES: {yes:.2f}\n"
        f"NO: {no:.2f}\n"
        f"Time: {mm:02}:{ss:02}\n"
        f"Side: {side}\n"
        f"Status: {decision}\n"
        f"Reason: {reason}\n"
        f"Source: {live_price['source']}\n"
    )

    if entry and allowed:

        if config.MODE == "live_test":

            open_trade = live_broker.place_live_order(
                market,
                side,
                entry,
                seconds_left / 60,
            )

        else:

            open_trade = paper_broker.open_paper_trade(
                market,
                side,
                entry,
                seconds_left / 60,
            )

    time.sleep(1)