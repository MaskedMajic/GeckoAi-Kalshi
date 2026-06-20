import requests

import config
import stats

from live_broker import HOST, headers


BALANCE_PATH = "/trade-api/v2/portfolio/balance"


def get_live_balance():
    try:
        response = requests.get(
            HOST + BALANCE_PATH,
            headers=headers("GET", BALANCE_PATH),
            timeout=10,
        )

        if response.status_code != 200:
            print(f"[BALANCE ERROR] {response.status_code} | {response.text}")
            return 0

        data = response.json()
        return float(data.get("balance_dollars", 0))

    except requests.exceptions.RequestException as e:
        print(f"[BALANCE ERROR] {e}")
        return 0


def get_bankroll():
    if config.MODE == "live_test":
        return get_live_balance()

    summary = stats.get_summary()
    return summary["latest_bankroll"]


def should_trade(entry, time_left_minutes):
    bankroll = get_bankroll()

    if bankroll < config.MIN_BANKROLL:
        return False, f"Bankroll below ${config.MIN_BANKROLL}"

    if time_left_minutes > config.MAX_TIME_LEFT_MINUTES:
        return False, f"{time_left_minutes}m remaining"

    if entry < config.ENTRY_MIN:
        return False, f"Entry below {config.ENTRY_MIN:.2f}"

    if entry > config.ENTRY_MAX:
        return False, f"Entry above {config.ENTRY_MAX:.2f}"

    return True, f"Balance ${bankroll:.2f}"