import math
import config


# ========= BALANCE STEP SETTINGS =========
STEP_1_BALANCE = 5
STEP_1_CONTRACTS = 1

STEP_2_BALANCE = 10
STEP_2_CONTRACTS = 2

STEP_3_BALANCE = 25
STEP_3_CONTRACTS = 3

STEP_4_BALANCE = 30
STEP_4_CONTRACTS = 5

STEP_5_BALANCE = 40
STEP_5_CONTRACTS = 6

STEP_6_BALANCE = 50
STEP_6_CONTRACTS = 8

STEP_7_BALANCE = 75
STEP_7_CONTRACTS = 9

STEP_8_BALANCE = 100
STEP_8_CONTRACTS = 12

STEP_9_BALANCE = 250
STEP_9_CONTRACTS = 20

STEP_10_BALANCE = 500
STEP_10_CONTRACTS = 30

MAX_CONTRACTS = 50
# =========================================


def get_step_contracts(balance):

    if balance < STEP_1_BALANCE:
        return STEP_1_CONTRACTS

    elif balance < STEP_2_BALANCE:
        return STEP_2_CONTRACTS

    elif balance < STEP_3_BALANCE:
        return STEP_3_CONTRACTS

    elif balance < STEP_4_BALANCE:
        return STEP_4_CONTRACTS

    elif balance < STEP_5_BALANCE:
        return STEP_5_CONTRACTS

    elif balance < STEP_6_BALANCE:
        return STEP_6_CONTRACTS

    elif balance < STEP_7_BALANCE:
        return STEP_7_CONTRACTS

    elif balance < STEP_8_BALANCE:
        return STEP_8_CONTRACTS

    elif balance < STEP_9_BALANCE:
        return STEP_9_CONTRACTS

    elif balance < STEP_10_BALANCE:
        return STEP_10_CONTRACTS

    return MAX_CONTRACTS


def get_contracts(balance, entry):

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

        contracts = math.floor(
            balance
            /
            entry
        )

    else:

        contracts = 1

    affordable = math.floor(
        balance
        /
        entry
    )

    contracts = min(
        contracts,
        affordable
    )

    return max(
        0,
        contracts
    )