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


def fmt_runtime(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"


def repaint(message):
    os.system("cls")
    print(message, end="", flush=True)


def safe_streak():
    try:
        streak = stats.get_streak()
        if streak["current_type"] == "WIN":
            return f"W{streak['current_count']}"
        if streak["current_type"] == "LOSS":
            return f"L{streak['current_count']}"
    except Exception:
        pass

    return "-"


def get_starting_balance():
    if config.MODE == "live_test":
        return strategy.get_live_balance()

    return stats.get_latest_bankroll(config.STARTING_BANKROLL)


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


def dashboard_header():
    summary = stats.get_summary()

    runtime = fmt_runtime(
        int(time.time() - session_started_at)
    )

    session_trades = (
        summary["total_trades"]
        -
        start_summary["total_trades"]
    )

    session_wins = (
        summary["wins"]
        -
        start_summary["wins"]
    )

    session_losses = (
        summary["losses"]
        -
        start_summary["losses"]
    )

    session_pnl = (
        summary["total_pnl"]
        -
        start_summary["total_pnl"]
    )

    current_balance = (
        summary["latest_bankroll"]
        if summary["latest_bankroll"] > 0
        else starting_balance
    )

    current_contracts = risk.get_contracts(
        current_balance,
        0.90
    )

    total_pnl = (
        current_balance
        -
        config.STARTING_BANKROLL
    )

    return (
        f"{GREEN}=============================={RESET}\n"
        f"{GREEN}       GECKOAI KALSHI{RESET}\n"
        f"{GREEN}=============================={RESET}\n\n"

        f"Mode: {display_mode}\n"
        f"Start Balance: ${starting_balance:.2f}\n"
        f"Balance: ${current_balance:.2f}\n"
        f"Contracts: {current_contracts}\n"
        f"Sizing: {config.SIZING_MODE}\n\n"

        f"Record: {summary['wins']}W / {summary['losses']}L\n"
        f"Win Rate: {summary['win_rate']:.2f}%\n"
        f"Total PnL: ${total_pnl:+.2f}\n"
        f"Streak: {safe_streak()}\n\n"

        f"Session Runtime: {runtime}\n"
        f"Session Trades: {session_trades}\n"
        f"Session W/L: {session_wins}W / {session_losses}L\n"
        f"Session PnL: ${session_pnl:+.2f}\n\n"
    )


stats.init_db()

session_started_at = time.time()

starting_balance = get_starting_balance()
start_summary = stats.get_summary()

display_mode = (
    "LIVE"
    if config.MODE == "live_test"
    else config.MODE.upper()
)

startup = (
    "📡 BOT STARTED\n"
    f"Mode: {display_mode}\n"
    f"Balance: ${starting_balance:.2f}\n"
    f"Contracts: {risk.get_contracts(starting_balance, 0.90)}\n"
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
                dashboard_header()
                +
                f"{YELLOW}🟡 ACTIVE TRADE{RESET}\n\n"
                f"Ticker: {open_trade['ticker']}\n"
                f"Side: {open_trade['side']}\n"
                f"Entry: {open_trade['entry']:.2f}\n"
                f"Now: {current:.2f}\n"
                f"Time Left: {mm:02}:{ss:02}\n"
                f"Source: {live['source']}\n"
            )

        time.sleep(1)
        continue

    market = kalshi_client.get_market()

    if not market:

        repaint(
            dashboard_header()
            +
            f"{RED}🔴 WAITING FOR MARKET{RESET}\n"
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
            dashboard_header()
            +
            f"{PURPLE}🟣 STREAM ROLLOVER{RESET}\n\n"
            f"Ticker: {stream_ticker}\n"
            f"Waiting for stream ticks...\n"
        )

        time.sleep(2)
        continue

    live_price = get_price(market)

    if not live_price:

        repaint(
            dashboard_header()
            +
            f"{BLUE}🔵 WAITING FOR PRICE{RESET}\n\n"
            f"Ticker: {market['ticker']}\n"
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
        dashboard_header()
        +
        f"{GREEN}🟢 WATCH{RESET}\n\n"
        f"Ticker: {market['ticker']}\n"
        f"YES: {yes:.2f}\n"
        f"NO: {no:.2f}\n"
        f"Time Left: {mm:02}:{ss:02}\n"
        f"Side: {side}\n"
        f"Status: {decision}\n"
        f"Reason: {reason}\n"
        f"Source: {live_price['source']}\n"
    )

    if entry and allowed:

        repaint(
            dashboard_header()
            +
            f"{BLUE}⚡ ENTRY SIGNAL{RESET}\n\n"
            f"Ticker: {market['ticker']}\n"
            f"Side: {side}\n"
            f"Entry: {entry:.2f}\n"
            f"Time Left: {mm:02}:{ss:02}\n"
        )

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