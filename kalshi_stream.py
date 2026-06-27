import asyncio
import base64
import json
import threading
import time
import os

import websockets

import config

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key


WS_URL = "wss://external-api-ws.kalshi.com/trade-api/ws/v2"
WS_PATH = "/trade-api/ws/v2"

BLUE = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"

_latest = {}
_running = False
_warned_missing_auth = False


def auth_ready():
    return bool(
        getattr(config, "KALSHI_KEY_ID", "")
    ) and os.path.exists(
        getattr(config, "KALSHI_PRIVATE_KEY_PATH", "")
    )


def load_key():
    with open(config.KALSHI_PRIVATE_KEY_PATH, "rb") as f:
        return load_pem_private_key(f.read(), password=None)


def sign_ws_request():
    timestamp = str(int(time.time() * 1000))
    message = f"{timestamp}GET{WS_PATH}".encode()

    signature = load_key().sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH,
        ),
        hashes.SHA256(),
    )

    return timestamp, base64.b64encode(signature).decode()


def get_latest():
    return _latest.copy()


def _handle_ticker(msg):
    yes_bid = float(msg.get("yes_bid_dollars", 0))
    yes_ask = float(msg.get("yes_ask_dollars", 0))

    _latest.update(
        {
            "ticker": msg.get("market_ticker"),
            "yes": yes_ask,
            "no": round(1 - yes_bid, 2),
            "yes_bid": yes_bid,
            "yes_ask": yes_ask,
            "no_bid": round(1 - yes_ask, 2),
            "no_ask": round(1 - yes_bid, 2),
            "updated_at": msg.get("time"),
        }
    )


async def _stream(market_ticker):
    global _running

    timestamp, signature = sign_ws_request()

    headers = {
        "KALSHI-ACCESS-KEY": config.KALSHI_KEY_ID,
        "KALSHI-ACCESS-TIMESTAMP": timestamp,
        "KALSHI-ACCESS-SIGNATURE": signature,
    }

    async with websockets.connect(
        WS_URL,
        additional_headers=headers,
        ping_interval=20,
        ping_timeout=20,
    ) as ws:
        subscribe = {
            "id": 1,
            "cmd": "subscribe",
            "params": {
                "channels": ["ticker"],
                "market_tickers": [market_ticker],
            },
        }

        await ws.send(json.dumps(subscribe))

        print()
        print(f"{BLUE}🔵 [STREAM]{RESET} Subscribed to {market_ticker}")

        _running = True

        while _running:
            raw = await ws.recv()
            data = json.loads(raw)

            if data.get("type") == "ticker":
                _handle_ticker(data["msg"])


def _run_loop(market_ticker):
    try:
        asyncio.run(_stream(market_ticker))
    except Exception as e:
        print()
        print(f"{RED}🔴 [STREAM ERROR]{RESET} {e}")


def start(market_ticker):
    global _warned_missing_auth

    if not auth_ready():
        if not _warned_missing_auth:
            print()
            print(
                f"{RED}🔴 [STREAM DISABLED]{RESET} "
                "Missing Kalshi auth; using REST-only paper mode."
            )
            _warned_missing_auth = True
        return None

    thread = threading.Thread(
        target=_run_loop,
        args=(market_ticker,),
        daemon=True,
    )

    thread.start()
    return thread


def stop():
    global _running
    global _latest

    _running = False
    _latest = {}