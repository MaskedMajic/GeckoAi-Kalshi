import math
import config


def get_max_contracts():

    if config.MODE == "live_test":
        return config.LIVE_MAX_CONTRACTS

    return config.MAX_CONTRACTS


def get_step_contracts(balance):

    for balance_limit, contracts in config.BALANCE_STEPS:

        if balance < balance_limit:
            return contracts

    return get_max_contracts()


def get_affordable_contracts(
    balance,
    entry
):

    if entry <= 0:
        return 0

    return math.floor(
        balance /
        entry
    )


def get_contracts(
    balance,
    entry
):

    mode = (
        config
        .SIZING_MODE
        .lower()
    )

    if mode == "fixed":

        contracts = (
            config
            .FIXED_CONTRACTS
        )

    elif mode == "balance_step":

        contracts = (
            get_step_contracts(
                balance
            )
        )

    elif mode == "max_affordable":

        contracts = (
            get_affordable_contracts(
                balance,
                entry
            )
        )

    else:

        contracts = 1

    affordable = (
        get_affordable_contracts(
            balance,
            entry
        )
    )

    max_contracts = (
        get_max_contracts()
    )

    contracts = min(
        contracts,
        affordable,
        max_contracts
    )

    return max(
        0,
        contracts
    )