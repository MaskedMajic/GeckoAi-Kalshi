import os
import sys
import time
from pathlib import Path
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
HOME = "\033[H"
CLEAR_FROM_CURSOR = "\033[J"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"

TIMING_LOG_PATH = Path("data/timing.log")


def ms_now():
    return int(time.time() * 1000)


def log_timing(stage, started_ms, extra=""):
    elapsed = ms_now() - started_ms
    suffix = f" | {extra}" if extra else ""
    TIMING_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TIMING_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"[TIMING] {stage} | {elapsed}ms{suffix}\n")
    return elapsed


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
    if sys.stdout.isatty():
        if not _display_snapshot.get("initialized"):
            sys.stdout.write(HIDE_CURSOR)
            sys.stdout.write(message)
            _display_snapshot["initialized"] = True
        else:
            sys.stdout.write(HOME)
            sys.stdout.write(CLEAR_FROM_CURSOR)
            sys.stdout.write(message)
        sys.stdout.flush()
    else:
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
    started_ms = ms_now()
    latest = kalshi_stream.get_latest()

    if latest and latest.get("ticker") == market["ticker"]:
        log_timing("price.stream", started_ms, market["ticker"])
        return {
            "yes": latest["yes"],
            "no": latest["no"],
            "source": "STREAM",
        }

    fallback = kalshi_client.get_market_prices(market["ticker"])

    if fallback:
        log_timing("price.rest", started_ms, market["ticker"])
        return {
            "yes": fallback["yes"],
            "no": fallback["no"],
            "source": "REST",
        }

    log_timing("price.none", started_ms, market["ticker"])
    return None


def track_trade_price(trade, current):
    current = round(float(current), 4)

    if "price_path" not in trade:
        trade["price_path"] = []

    if "lowest_seen" not in trade:
        trade["lowest_seen"] = current

    if "highest_seen" not in trade:
        trade["highest_seen"] = current

    trade["price_path"].append(current)

    trade["lowest_seen"] = min(
        trade["lowest_seen"],
        current
    )

    trade["highest_seen"] = max(
        trade["highest_seen"],
        current
    )

    trade["worst_against_entry"] = round(
        trade["entry"] - trade["lowest_seen"],
        4
    )

    trade["best_in_favor_entry"] = round(
        trade["highest_seen"] - trade["entry"],
        4
    )

    trade["price_path_points"] = len(
        trade["price_path"]
    )


def should_stop_loss(current):
    return (
        config.MODE == "live_test"
        and getattr(config, "ENABLE_STOP_LOSS", False)
        and current <= getattr(config, "STOP_LOSS_PRICE", 0)
    )


DASHBOARD_REFRESH_MS = 1000
REPAINT_INTERVAL_MS = 500

_display_snapshot = {
    "summary": None,
    "streak_label": "-",
    "header": "",
    "last_refresh_ms": 0,
    "last_render_ms": 0,
    "last_render_text": None,
    "initialized": False,
}


def refresh_display_snapshot(force=False):
    started_ms = ms_now()
    now_ms = started_ms

    if (
        not force
        and _display_snapshot["summary"] is not None
        and now_ms - _display_snapshot["last_refresh_ms"] < DASHBOARD_REFRESH_MS
    ):
        return _display_snapshot

    summary = stats.get_summary()
    streak_label = safe_streak()

    current_balance = (
        summary["latest_bankroll"]
        if summary["latest_bankroll"] > 0
        else starting_balance
    )

    current_contracts = risk.get_contracts(
        current_balance,
        0.90
    )

    session_trades = summary["total_trades"] - start_summary["total_trades"]
    session_wins = summary["wins"] - start_summary["wins"]
    session_losses = summary["losses"] - start_summary["losses"]
    session_pnl = summary["total_pnl"] - start_summary["total_pnl"]
    total_pnl = current_balance - config.STARTING_BANKROLL
    runtime = fmt_runtime(int(time.time() - session_started_at))

    header = (
        f"{GREEN}=============================={RESET}\n"
        f"{GREEN}       GECKOAI KALSHI{RESET}\n"
        f"{GREEN}=============================={RESET}\n\n"
        f"{'Mode:':<10}"
        f"{display_mode:<14}"
        f"{'Record:':<10}"
        f"{summary['wins']}W / {summary['losses']}L\n"
        f"{'Balance:':<10}"
        f"${current_balance:<13.2f}"
        f"{'Win Rate:':<10}"
        f"{summary['win_rate']:.2f}%\n"
        f"{'Contracts:':<10}"
        f"{current_contracts:<13}"
        f"{'Streak:':<10}"
        f"{streak_label}\n\n"
        f"{'Sizing:':<10}"
        f"{config.SIZING_MODE}\n"
        f"{'PnL:':<10}"
        f"${total_pnl:+.2f}\n"
        f"{'Start:':<10}"
        f"${starting_balance:.2f}\n\n"
        f"Session Runtime: {runtime}\n"
        f"Session Trades: {session_trades}\n"
        f"Session W/L: {session_wins}W / {session_losses}L\n"
        f"Session PnL: ${session_pnl:+.2f}\n\n"
    )

    _display_snapshot.update({
        "summary": summary,
        "streak_label": streak_label,
        "header": header,
        "last_refresh_ms": now_ms,
    })

    log_timing("dashboard.refresh", started_ms)
    return _display_snapshot


def dashboard_header(force=False):
    snapshot = refresh_display_snapshot(force=force)
    return snapshot["header"]


def repaint_throttled(message, force=False):
    now_ms = ms_now()

    if not force:
        if message == _display_snapshot["last_render_text"]:
            return
        if now_ms - _display_snapshot["last_render_ms"] < REPAINT_INTERVAL_MS:
            return

    started_ms = now_ms
    repaint(message)
    _display_snapshot["last_render_ms"] = now_ms
    _display_snapshot["last_render_text"] = message
    log_timing("dashboard.repaint", started_ms)


stats.init_db()

session_started_at = time.time()
starting_balance = get_starting_balance()
start_summary = stats.get_summary()

display_mode = (
    "LIVE"
    if config.MODE == "live_test"
    else config.MODE.upper()
)

refresh_display_snapshot(force=True)

startup = (
    "📡 BOT STARTED\n"
    f"Mode: {display_mode}\n"
    f"Balance: ${starting_balance:.2f}\n"
    f"Contracts: {risk.get_contracts(starting_balance, 0.90)}\n"
    f"Sizing: {config.SIZING_MODE}\n"
    f"Stop Loss: {'ON' if getattr(config, 'ENABLE_STOP_LOSS', False) else 'OFF'}"
)

if getattr(config, "ENABLE_STOP_LOSS", False):
    startup += f" @ {config.STOP_LOSS_PRICE:.2f}"

discord_alerts.send_message(startup)

open_trade = None
stream_ticker = None
stopped_out_ticker = None
current_market = None


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

            track_trade_price(
                open_trade,
                current
            )

            mm, ss, _ = time_left(open_trade["close"])

            if should_stop_loss(current):

                repaint_throttled(
                    dashboard_header(force=True)
                    +
                    f"{RED}🛑 STOP LOSS TRIGGERED{RESET}\n\n"
                    f"Ticker: {open_trade['ticker']}\n"
                    f"Side: {open_trade['side']}\n"
                    f"Entry: {open_trade['entry']:.2f}\n"
                    f"Now: {current:.2f}\n"
                    f"Stop: {config.STOP_LOSS_PRICE:.2f}\n"
                    f"Time Left: {mm:02}:{ss:02}\n"
                )

                exited = live_broker.exit_live_position(
                    open_trade,
                    current
                )

                if exited:
                    stopped_out_ticker = open_trade["ticker"]
                    open_trade = None
                    time.sleep(5)
                    continue

            repaint_throttled(
                dashboard_header()
                +
                f"{YELLOW}🟡 ACTIVE TRADE{RESET}\n\n"
                f"Ticker: {open_trade['ticker']}\n"
                f"Side: {open_trade['side']}\n"
                f"Entry: {open_trade['entry']:.2f}\n"
                f"Now: {current:.2f}\n"
                f"Stop Loss: {config.STOP_LOSS_PRICE:.2f}\n"
                f"Lowest Seen: {open_trade['lowest_seen']:.2f}\n"
                f"Highest Seen: {open_trade['highest_seen']:.2f}\n"
                f"Worst Against: {open_trade['worst_against_entry']:.2f}\n"
                f"Path Points: {open_trade['price_path_points']}\n"
                f"Time Left: {mm:02}:{ss:02}\n"
                f"Source: {live['source']}\n"
            )

        time.sleep(1)
        continue

    market_started_ms = ms_now()

    refresh_market = (
        current_market is None
        or closed(current_market["close"])
    )

    if refresh_market:
        market = kalshi_client.get_market(force_refresh=True)
        current_market = market
        log_timing("market.fetch.full", market_started_ms)
    else:
        market = current_market
        log_timing("market.fetch.cached", market_started_ms, market["ticker"])

    if not market:
        repaint_throttled(
            dashboard_header()
            +
            f"{RED}🔴 WAITING FOR MARKET{RESET}\n"
        )

        kalshi_stream.stop()
        stream_ticker = None
        current_market = None

        time.sleep(5)
        continue

    if stream_ticker != market["ticker"]:
        stream_ticker = market["ticker"]
        stopped_out_ticker = None

        kalshi_stream.stop()
        kalshi_stream.start(stream_ticker)

        repaint_throttled(
            dashboard_header(force=True)
            +
            f"{PURPLE}🟣 STREAM ROLLOVER{RESET}\n\n"
            f"Ticker: {stream_ticker}\n"
            f"Waiting for stream ticks...\n"
        )

        time.sleep(2)
        continue

    live_price = get_price(market)

    if not live_price:
        repaint_throttled(
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

    if stopped_out_ticker == market["ticker"]:
        repaint_throttled(
            dashboard_header(force=True)
            +
            f"{RED}🔒 MARKET LOCKED AFTER STOP{RESET}\n\n"
            f"Ticker: {market['ticker']}\n"
            f"Reason: Stop loss already triggered on this market\n"
            f"Time Left: {mm:02}:{ss:02}\n"
            f"YES: {yes:.2f}\n"
            f"NO: {no:.2f}\n"
            f"Source: {live_price['source']}\n"
        )

        time.sleep(1)
        continue

    if config.ENTRY_MIN <= yes <= config.ENTRY_MAX:
        side = "YES"
        entry = yes

    elif config.ENTRY_MIN <= no <= config.ENTRY_MAX:
        side = "NO"
        entry = no

    allowed = False
    reason = "-"

    if entry:
        decision_started_ms = ms_now()
        allowed, reason = strategy.should_trade(
            entry,
            seconds_left / 60
        )
        log_timing(
            "decision.should_trade",
            decision_started_ms,
            f"side={side} entry={entry:.2f}"
        )

    decision = "ENTER" if allowed else "WAIT"

    repaint_throttled(
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
        repaint_throttled(
            dashboard_header(force=True)
            +
            f"{BLUE}⚡ ENTRY SIGNAL{RESET}\n\n"
            f"Ticker: {market['ticker']}\n"
            f"Side: {side}\n"
            f"Entry: {entry:.2f}\n"
            f"Time Left: {mm:02}:{ss:02}\n"
        )

        entry_started_ms = ms_now()

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

        log_timing(
            "entry.execute",
            entry_started_ms,
            f"mode={config.MODE} side={side} ticker={market['ticker']}"
        )

        if open_trade and open_trade.get("refresh_dashboard"):
            refresh_display_snapshot(force=True)

    time.sleep(1)