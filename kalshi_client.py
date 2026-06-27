import time
import requests
from datetime import datetime, timezone

BASE = "https://external-api.kalshi.com/trade-api/v2"

SERIES_TICKER = "KXBTC15M"

_session = requests.Session()
_market_cache = {"value": None, "expires_at": 0.0}
_price_cache = {}
MARKET_CACHE_TTL_SECONDS = 2.0
PRICE_CACHE_TTL_SECONDS = 0.35


def get_btc_price():

    try:

        response = _session.get(
            "https://api.coinbase.com/v2/prices/BTC-USD/spot",
            timeout=10
        )

        data = response.json()

        return float(
            data["data"]["amount"]
        )

    except Exception as e:

        print(
            "BTC PRICE ERROR:",
            e
        )

        return None


def get_yes_no_prices(ticker):

    now_ts = time.time()
    cached = _price_cache.get(ticker)

    if cached and cached["expires_at"] > now_ts:
        return cached["value"]

    response = _session.get(
        f"{BASE}/markets/{ticker}/orderbook",
        timeout=10
    )

    data = response.json()

    orderbook = data.get(
        "orderbook_fp",
        {}
    )

    no_bids = orderbook.get(
        "no_dollars",
        []
    )

    if not no_bids:
        return None

    best_no = float(
        no_bids[-1][0]
    )

    yes = round(
        1 - best_no,
        2
    )

    no = round(
        best_no,
        2
    )

    value = (yes, no)
    _price_cache[ticker] = {
        "value": value,
        "expires_at": now_ts + PRICE_CACHE_TTL_SECONDS,
    }

    return value


def get_market_prices(ticker):

    prices = (
        get_yes_no_prices(
            ticker
        )
    )

    if not prices:
        return None

    return {
        "yes":
            prices[0],

        "no":
            prices[1]
    }


def get_market(force_refresh=False):

    now_ts = time.time()
    cached = _market_cache.get("value")

    if (
        not force_refresh
        and cached
        and _market_cache.get("expires_at", 0.0) > now_ts
    ):
        return cached

    try:

        response = _session.get(
            f"{BASE}/markets",
            params={
                "series_ticker":
                    SERIES_TICKER,

                "status":
                    "open",

                "limit":
                    20
            },
            timeout=10
        )

        data = (
            response.json()
        )

        markets = (
            data.get(
                "markets",
                []
            )
        )

        now = (
            datetime.now(
                timezone.utc
            )
        )

        valid = []

        for market in markets:

            ticker = (
                market.get(
                    "ticker"
                )
            )

            close = (
                market.get(
                    "close_time"
                )
            )

            if (
                not ticker
                or
                not close
            ):
                continue

            dt = (
                datetime.fromisoformat(
                    close.replace(
                        "Z",
                        "+00:00"
                    )
                )
            )

            left = (
                dt
                -
                now
            ).total_seconds()

            if left <= 0:
                continue

            prices = (
                get_yes_no_prices(
                    ticker
                )
            )

            if not prices:
                continue

            valid.append({

                "market":
                    market.get(
                        "title"
                    ),

                "ticker":
                    ticker,

                "yes_entry":
                    prices[0],

                "no_entry":
                    prices[1],

                "close":
                    close
            })

        if not valid:
            _market_cache["value"] = None
            _market_cache["expires_at"] = now_ts + 0.5
            return None

        _market_cache["value"] = valid[0]
        _market_cache["expires_at"] = now_ts + MARKET_CACHE_TTL_SECONDS

        return valid[0]

    except Exception as e:

        print(
            "KALSHI ERROR:",
            e
        )

        return None


def get_market_result(ticker):

    try:

        response = _session.get(
            f"{BASE}/markets/{ticker}",
            timeout=10
        )

        data = (
            response.json()
        )

        market = (
            data.get(
                "market",
                data
            )
        )

        settlement = (

            market.get(
                "settlement_value_dollars"
            )

            or

            market.get(
                "expiration_value"
            )

        )

        if (
            settlement is None
            or
            settlement == ""
        ):
            return None

        settlement = (
            float(
                settlement
            )
        )

        return (
            "YES"
            if settlement >= .5
            else "NO"
        )

    except:

        return None
