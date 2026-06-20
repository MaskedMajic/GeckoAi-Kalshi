import time
import uuid
import base64
import requests

import config
import risk
import discord_alerts
import kalshi_client
import trade_logger

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.asymmetric import padding


HOST = "https://external-api.kalshi.com"

ORDER_PATH = "/trade-api/v2/portfolio/events/orders"
BALANCE_PATH = "/trade-api/v2/portfolio/balance"

MAX_FILL_ATTEMPTS = 5


def load_key():
    with open(config.KALSHI_PRIVATE_KEY_PATH, "rb") as f:
        return load_pem_private_key(
            f.read(),
            password=None
        )


def sign_request(method, path):
    timestamp = str(int(time.time() * 1000))
    key = load_key()

    message = f"{timestamp}{method}{path}".encode()

    signature = key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH
        ),
        hashes.SHA256()
    )

    return timestamp, base64.b64encode(signature).decode()


def headers(method, path):
    timestamp, signature = sign_request(method, path)

    return {
        "KALSHI-ACCESS-KEY": config.KALSHI_KEY_ID,
        "KALSHI-ACCESS-TIMESTAMP": timestamp,
        "KALSHI-ACCESS-SIGNATURE": signature,
        "Content-Type": "application/json",
    }


def get_live_balance():
    try:
        response = requests.get(
            HOST + BALANCE_PATH,
            headers=headers("GET", BALANCE_PATH),
            timeout=10
        )

        if response.status_code != 200:
            print(f"[BALANCE ERROR] {response.status_code} | {response.text}")
            return 0

        data = response.json()

        return float(
            data.get(
                "balance_dollars",
                0
            )
        )

    except requests.exceptions.RequestException as e:
        print(f"[BALANCE ERROR] {e}")
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


def place_live_order(market, side, entry, time_left):
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

        body = {
            "ticker": market["ticker"],
            "client_order_id": str(uuid.uuid4()),
            "side": order_side,
            "count": str(contracts),
            "price": f"{price:.4f}",
            "time_in_force": "immediate_or_cancel",
            "self_trade_prevention_type": "taker_at_cross",
        }

        print()
        print(f"[LIVE] {attempt}/{MAX_FILL_ATTEMPTS}")
        print(body)

        try:
            response = requests.post(
                HOST + ORDER_PATH,
                headers=headers("POST", ORDER_PATH),
                json=body,
                timeout=10
            )

        except requests.exceptions.RequestException as e:
            print(f"[ORDER ERROR] {e}")
            discord_alerts.send_message(
                f"❌ **ORDER ERROR {attempt}/{MAX_FILL_ATTEMPTS}** | "
                f"`{market['ticker']}` | {side} @ `{entry:.2f}` | "
                f"`{contracts}`ct | `{e}`"
            )
            time.sleep(1)
            continue

        print(response.status_code)
        print(response.text)

        if response.status_code not in [200, 201]:
            discord_alerts.send_message(
                f"❌ **LIVE FAILED {attempt}/{MAX_FILL_ATTEMPTS}** | "
                f"`{market['ticker']}` | {side} @ `{entry:.2f}` | "
                f"Limit `{price:.2f}` | Status `{response.status_code}`"
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
            avg_fill = float(
                data.get(
                    "average_fill_price",
                    f"{price:.4f}"
                )
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

            avg_fill_display = data.get(
                "average_fill_price",
                f"{price:.4f}"
            )

            fee_display = data.get(
                "average_fee_paid",
                "0"
            )

            discord_alerts.send_message(
                f"✅ **FILL {attempt}/{MAX_FILL_ATTEMPTS}** | "
                f"`{market['ticker']}` | {side} @ `{entry:.2f}` | "
                f"`{fill}`ct | Limit `{price:.2f}` | "
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
                "limit_price": price,
                "fees": fee,
                "btc_entry_price": kalshi_client.get_btc_price(),
                "opened_at": trade_logger.now_iso(),
                "bankroll_before": balance,
                "live": True,
                "order_response": data,
            }

            trade_logger.log_trade_open(
                trade
            )

            return trade

        print("NO FILL")

        discord_alerts.send_message(
            f"⚪ **NO FILL {attempt}/{MAX_FILL_ATTEMPTS}** | "
            f"`{market['ticker']}` | {side} @ `{entry:.2f}` | "
            f"`{contracts}`ct | Limit `{price:.2f}`"
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

    discord_alerts.send_message(
        f"⚪ **FAILED AFTER {MAX_FILL_ATTEMPTS}** | "
        f"`{market['ticker']}` | {side}"
    )

    return None