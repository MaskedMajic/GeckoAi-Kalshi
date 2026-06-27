import sys
import time
import uuid
import base64
import requests

import config
import risk
import discord_alerts
import kalshi_client
import trade_logger
import stats
import global_stats

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.asymmetric import padding


HOST = "https://external-api.kalshi.com"

ORDER_PATH = "/trade-api/v2/portfolio/events/orders"
BALANCE_PATH = "/trade-api/v2/portfolio/balance"

MAX_FILL_ATTEMPTS = 5
BALANCE_CACHE_TTL_SECONDS = 2.0

_session = requests.Session()
_key_cache = None
_balance_cache = {"value": None, "expires_at": 0.0}


def repaint(message):
    sys.stdout.write("\r" + message + " " * 140)
    sys.stdout.flush()


def ms_now():
    return int(time.time() * 1000)


def log_timing(stage, started_ms, extra=""):
    elapsed = ms_now() - started_ms
    suffix = f" | {extra}" if extra else ""
    print(f"[TIMING] {stage} | {elapsed}ms{suffix}")
    return elapsed


def post_trade_side_effects(trade=None, close_data=None, messages=None):
    messages = messages or []

    for message in messages:
        discord_alerts.send_message(message)

    if trade and close_data:
        global_stats.send_trade(trade, close_data)


def load_key():
    global _key_cache

    if _key_cache is None:
        with open(config.KALSHI_PRIVATE_KEY_PATH, "rb") as f:
            _key_cache = load_pem_private_key(
                f.read(),
                password=None
            )

    return _key_cache


def sign_request(method, path):
    started_ms = ms_now()
    timestamp = str(int(time.time() * 1000))

    message = f"{timestamp}{method}{path}".encode()

    signature = load_key().sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH
        ),
        hashes.SHA256()
    )

    encoded = base64.b64encode(signature).decode()
    log_timing("live.sign_request", started_ms, f"{method} {path}")
    return timestamp, encoded


def headers(method, path):
    started_ms = ms_now()
    timestamp, signature = sign_request(method, path)

    header_map = {
        "KALSHI-ACCESS-KEY": config.KALSHI_KEY_ID,
        "KALSHI-ACCESS-TIMESTAMP": timestamp,
        "KALSHI-ACCESS-SIGNATURE": signature,
        "Content-Type": "application/json",
    }

    log_timing("live.headers", started_ms, f"{method} {path}")
    return header_map


def get_live_balance(force_refresh=False):
    started_ms = ms_now()
    now_ts = time.time()

    if (
        not force_refresh
        and _balance_cache["value"] is not None
        and _balance_cache["expires_at"] > now_ts
    ):
        log_timing("live.balance.cached", started_ms)
        return _balance_cache["value"]

    try:
        response = _session.get(
            HOST + BALANCE_PATH,
            headers=headers("GET", BALANCE_PATH),
            timeout=10
        )

        if response.status_code != 200:
            repaint(
                f"🔴 [BALANCE ERROR] Status={response.status_code}"
            )
            return 0

        data = response.json()

        value = float(
            data.get(
                "balance_dollars",
                0
            )
        )

        _balance_cache["value"] = value
        _balance_cache["expires_at"] = now_ts + BALANCE_CACHE_TTL_SECONDS
        log_timing("live.balance.fetch", started_ms)
        return value

    except requests.exceptions.RequestException as e:
        repaint(f"🔴 [BALANCE ERROR] {e}")
        return 0



def calc_price(side, entry):
    if side == "YES":
        return (
            "bid",
            min(
                0.99,
                round(entry + 0.01, 2)
            )
        )

    return (
        "ask",
        max(
            0.01,
            round((1 - entry) - 0.01, 2)
        )
    )


def normalize_fill_price(side, raw_avg_fill):
    if side == "YES":
        return raw_avg_fill

    return round(
        1 - raw_avg_fill,
        4
    )


def calc_exit_order(side, current_price):
    if side == "YES":
        return (
            "ask",
            max(
                0.01,
                round(current_price - 0.01, 2)
            )
        )

    return (
        "bid",
        min(
            0.99,
            round((1 - current_price) + 0.01, 2)
        )
    )


def place_live_order(market, side, entry, time_left):
    order_total_started_ms = ms_now()
    balance = get_live_balance()

    contracts = risk.get_contracts(
        balance,
        entry
    )

    if contracts < 1:
        discord_alerts.send_message(
            f"⛔ **NO TRADE** | Balance `${balance:.2f}` too low | "
            f"{side} @ `{entry:.2f}`"
        )
        return None

    for attempt in range(1, MAX_FILL_ATTEMPTS + 1):

        order_side, price = calc_price(
            side,
            entry
        )

        body_started_ms = ms_now()
        body = {
            "ticker": market["ticker"],
            "client_order_id": str(uuid.uuid4()),
            "side": order_side,
            "count": str(contracts),
            "price": f"{price:.4f}",
            "time_in_force": "immediate_or_cancel",
            "self_trade_prevention_type": "taker_at_cross",
        }
        log_timing("live.order.body", body_started_ms, f"attempt={attempt} ticker={market['ticker']}")

        repaint(
            f"⚡ [ORDER] "
            f"{attempt}/{MAX_FILL_ATTEMPTS} | "
            f"{side} | "
            f"Entry={entry:.2f} | "
            f"Limit={price:.2f} | "
            f"Contracts={contracts}"
        )

        request_started_ms = ms_now()
        request_headers = headers("POST", ORDER_PATH)

        try:
            response = _session.post(
                HOST + ORDER_PATH,
                headers=request_headers,
                json=body,
                timeout=10
            )
            log_timing("live.order.post", request_started_ms, f"attempt={attempt} status={response.status_code}")

        except requests.exceptions.RequestException as e:
            repaint(f"🔴 [ORDER ERROR] {e}")

            post_trade_side_effects(
                messages=[
                    f"❌ **ORDER ERROR {attempt}/{MAX_FILL_ATTEMPTS}** | "
                    f"`{market['ticker']}` | {side} @ `{entry:.2f}` | "
                    f"`{contracts}`ct | `{e}`"
                ]
            )

            time.sleep(1)
            continue

        if response.status_code not in [200, 201]:
            repaint(
                f"🔴 [LIVE FAILED] "
                f"{attempt}/{MAX_FILL_ATTEMPTS} | "
                f"Status={response.status_code}"
            )

            post_trade_side_effects(
                messages=[
                    f"❌ **LIVE FAILED {attempt}/{MAX_FILL_ATTEMPTS}** | "
                    f"`{market['ticker']}` | {side} @ `{entry:.2f}` | "
                    f"Limit `{price:.2f}` | Status `{response.status_code}`"
                ]
            )

            time.sleep(1)
            continue

        data = response.json()

        fill = float(
            data.get(
                "fill_count",
                "0"
            )
        )

        if fill > 0:
            raw_avg_fill = float(
                data.get(
                    "average_fill_price",
                    f"{price:.4f}"
                )
            )

            avg_fill = normalize_fill_price(
                side,
                raw_avg_fill
            )

            fee = float(
                data.get(
                    "average_fee_paid",
                    "0"
                )
            )

            contract_cost = round(
                avg_fill * fill,
                2
            )

            avg_fill_display = f"{avg_fill:.4f}"

            fee_display = data.get(
                "average_fee_paid",
                "0"
            )

            repaint(
                f"✅ [FILL] "
                f"{side} | "
                f"Avg={avg_fill:.4f} | "
                f"Contracts={fill:.0f} | "
                f"Cost=${contract_cost:.2f} | "
                f"Fee={fee_display}"
            )

            fill_message = (
                f"✅ **FILL {attempt}/{MAX_FILL_ATTEMPTS}** | "
                f"`{market['ticker']}` | {side} @ `{entry:.2f}` | "
                f"`{fill:.0f}`ct | Limit `{price:.2f}` | "
                f"Avg `{avg_fill_display}` | Fee `{fee_display}`"
            )

            trade = {
                "market": market["market"],
                "ticker": market["ticker"],
                "side": side,
                "entry": entry,
                "close": market["close"],
                "time_left": time_left,
                "position": contract_cost,
                "contracts": fill,
                "contract_cost": contract_cost,
                "avg_fill_price": avg_fill,
                "raw_avg_fill_price": raw_avg_fill,
                "limit_price": price,
                "fees": fee,
                "btc_entry_price": None,
                "opened_at": trade_logger.now_iso(),
                "bankroll_before": balance,
                "live": True,
                "order_response": data,
            }

            trade_logger.log_trade_open(
                trade
            )

            btc_started_ms = ms_now()
            trade["btc_entry_price"] = kalshi_client.get_btc_price()
            log_timing("live.btc_entry_price", btc_started_ms, market["ticker"])

            _balance_cache["value"] = round(balance - contract_cost - fee, 2)
            _balance_cache["expires_at"] = time.time() + BALANCE_CACHE_TTL_SECONDS

            post_trade_side_effects(
                messages=[fill_message]
            )
            log_timing(
                "live.order.total",
                order_total_started_ms,
                f"attempt={attempt} fill={fill:.0f} ticker={market['ticker']}"
            )

            trade["refresh_dashboard"] = True
            return trade

        repaint(
            f"⚪ [NO FILL] "
            f"{attempt}/{MAX_FILL_ATTEMPTS} | "
            f"{side} | "
            f"Limit={price:.2f}"
        )

        post_trade_side_effects(
            messages=[
                f"⚪ **NO FILL {attempt}/{MAX_FILL_ATTEMPTS}** | "
                f"`{market['ticker']}` | {side} @ `{entry:.2f}` | "
                f"`{contracts}`ct | Limit `{price:.2f}`"
            ]
        )

        latest = kalshi_client.get_market_prices(
            market["ticker"]
        )

        if latest:
            entry = (
                latest["yes"]
                if side == "YES"
                else latest["no"]
            )

        time.sleep(1)

    post_trade_side_effects(
        messages=[
            f"⚪ **FAILED AFTER {MAX_FILL_ATTEMPTS}** | "
            f"`{market['ticker']}` | {side}"
        ]
    )

    repaint(
        f"⚪ [FAILED] "
        f"No fill after {MAX_FILL_ATTEMPTS} attempts | "
        f"{side}"
    )

    return None


def exit_live_position(trade, current_price):
    exit_total_started_ms = ms_now()
    contracts = int(
        trade.get(
            "contracts",
            0
        )
    )

    if contracts < 1:
        return False

    side = trade.get("side")
    ticker = trade.get("ticker")

    order_side, exit_limit = calc_exit_order(
        side,
        current_price
    )

    body_started_ms = ms_now()
    body = {
        "ticker": ticker,
        "client_order_id": str(uuid.uuid4()),
        "side": order_side,
        "count": str(contracts),
        "price": f"{exit_limit:.4f}",
        "time_in_force": "immediate_or_cancel",
        "self_trade_prevention_type": "taker_at_cross",
    }
    log_timing("live.exit.body", body_started_ms, f"ticker={ticker}")

    repaint(
        f"🛑 [STOP EXIT] "
        f"{side} | "
        f"Now={current_price:.2f} | "
        f"Limit={exit_limit:.2f} | "
        f"Contracts={contracts}"
    )

    request_started_ms = ms_now()
    request_headers = headers("POST", ORDER_PATH)

    try:
        response = _session.post(
            HOST + ORDER_PATH,
            headers=request_headers,
            json=body,
            timeout=10
        )
        log_timing("live.exit.post", request_started_ms, f"status={response.status_code} ticker={ticker}")

    except requests.exceptions.RequestException as e:
        repaint(f"🔴 [STOP EXIT ERROR] {e}")

        post_trade_side_effects(
            messages=[
                f"🔴 **STOP EXIT ERROR** | "
                f"`{ticker}` | {side} | `{e}`"
            ]
        )

        return False

    if response.status_code not in [200, 201]:
        repaint(
            f"🔴 [STOP EXIT FAILED] "
            f"Status={response.status_code}"
        )

        post_trade_side_effects(
            messages=[
                f"🔴 **STOP EXIT FAILED** | "
                f"`{ticker}` | {side} | Status `{response.status_code}`"
            ]
        )

        return False

    data = response.json()

    fill = float(
        data.get(
            "fill_count",
            "0"
        )
    )

    if fill <= 0:
        repaint(
            f"⚪ [STOP EXIT NO FILL] "
            f"{side} | "
            f"Limit={exit_limit:.2f}"
        )

        return False

    exit_price = round(
        float(current_price),
        4
    )

    entry_price = float(
        trade.get(
            "avg_fill_price",
            trade.get("entry", 0)
        )
    )

    pnl = round(
        fill * (exit_price - entry_price),
        2
    )

    bankroll_before = float(
        trade.get(
            "bankroll_before",
            0
        )
    )

    bankroll_after = round(
        bankroll_before + pnl,
        2
    )

    close_data = {
        "closed_at": trade_logger.now_iso(),
        "btc_close_price": kalshi_client.get_btc_price(),
        "exit_contract_value": exit_price,
        "winning_side": None,
        "result": "LOSS",
        "exit_reason": "STOP_LOSS",
        "pnl": pnl,
        "bankroll_after": bankroll_after,
    }

    trade_logger.log_trade_close(
        trade,
        close_data
    )

    stats.save_trade(
        market=ticker,
        side=side,
        entry=trade.get("entry"),
        result="LOSS",
        pnl=pnl,
        bankroll=bankroll_after,
    )

    exit_message = (
        f"🛑 **STOP LOSS EXIT** | `{ticker}`\n"
        f"Side: **{side}** | "
        f"Entry: `{entry_price:.2f}` | "
        f"Exit: `{exit_price:.2f}` | "
        f"Contracts: `{int(fill)}`\n"
        f"Recovered: `${exit_price * fill:.2f}` | "
        f"PnL: `${pnl:+.2f}`"
    )

    repaint(
        f"🛑 [STOP EXIT FILLED] "
        f"{side} | "
        f"Exit={exit_price:.2f} | "
        f"PnL=${pnl:+.2f}"
    )

    _balance_cache["value"] = bankroll_after
    _balance_cache["expires_at"] = time.time() + BALANCE_CACHE_TTL_SECONDS

    post_trade_side_effects(
        trade=trade,
        close_data=close_data,
        messages=[exit_message]
    )
    log_timing(
        "live.exit.total",
        exit_total_started_ms,
        f"ticker={ticker} fill={int(fill)}"
    )

    return True
