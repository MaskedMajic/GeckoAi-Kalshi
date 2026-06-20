import config
import stats
import requests

from live_broker import (
    headers,
    HOST
)


BALANCE_PATH = (
    "/trade-api/v2/"
    "portfolio/balance"
)


def get_live_balance():

    try:

        response = requests.get(

            HOST
            +
            BALANCE_PATH,

            headers=headers(
                "GET",
                BALANCE_PATH
            ),

            timeout=10
        )

        if (
            response.status_code
            !=
            200
        ):

            return 0

        data = (
            response.json()
        )

        return float(
            data.get(
                "balance_dollars",
                0
            )
        )

    except:

        return 0


def should_trade(
    entry,
    time_left_minutes
):

    if (
        config.MODE
        ==
        "live_test"
    ):

        bankroll = (
            get_live_balance()
        )

    else:

        summary = (
            stats.get_summary()
        )

        bankroll = (
            summary[
                "latest_bankroll"
            ]
        )

    if bankroll < 1:
        return (
            False,
            "Bankroll below $1"
        )

    if time_left_minutes > 6:
        return (
            False,
            f"{time_left_minutes}m remaining"
        )

    if entry < 0.87:
        return (
            False,
            "Entry below .87"
        )

    if entry > 0.95:
        return (
            False,
            "Entry above .95"
        )

    return (
        True,
        f"Balance ${bankroll:.2f}"
    )