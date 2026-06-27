import os
from dotenv import load_dotenv

load_dotenv()


def env_bool(name, default=True):

    value = os.getenv(
        name,
        str(default)
    )

    return value.lower() == "true"


# ==========================
# Runtime
# ==========================

BOT_VERSION = os.getenv(
    "BOT_VERSION",
    "0.3.7"
)

MODE = os.getenv(
    "MODE",
    "paper"
)

SIZING_MODE = os.getenv(
    "SIZING_MODE",
    "balance_step"
)


# ==========================
# Bankroll
# ==========================

STARTING_BANKROLL = float(
    os.getenv(
        "STARTING_BANKROLL",
        5
    )
)

MIN_BANKROLL = float(
    os.getenv(
        "MIN_BANKROLL",
        1
    )
)


# ==========================
# Position Sizing
# ==========================

FIXED_CONTRACTS = int(
    os.getenv(
        "FIXED_CONTRACTS",
        1
    )
)

MAX_CONTRACTS = int(
    os.getenv(
        "MAX_CONTRACTS",
        50
    )
)

LIVE_MAX_CONTRACTS = int(
    os.getenv(
        "LIVE_MAX_CONTRACTS",
        10
    )
)

BALANCE_STEPS = [
    (5, 1),
    (10, 2),
    (25, 3),
    (30, 5),
    (40, 6),
    (50, 8),
    (75, 9),
    (100, 12),
    (200, 20),
    (350, 30),
    (500, 40),
    (750, 55),
]


# ==========================
# Strategy Rules
# ==========================

ENTRY_MIN = float(
    os.getenv(
        "ENTRY_MIN",
        0.87
    )
)

ENTRY_MAX = float(
    os.getenv(
        "ENTRY_MAX",
        0.95
    )
)

MAX_TIME_LEFT_MINUTES = int(
    os.getenv(
        "MAX_TIME_LEFT_MINUTES",
        6
    )
)


# ==========================
# Stop Loss
# ==========================

ENABLE_STOP_LOSS = env_bool(
    "ENABLE_STOP_LOSS",
    True
)

STOP_LOSS_PRICE = float(
    os.getenv(
        "STOP_LOSS_PRICE",
        0.15
    )
)


# ==========================
# Discord
# ==========================

DISCORD_ENABLED = env_bool(
    "DISCORD_ENABLED",
    True
)

DISCORD_WEBHOOK_URL = os.getenv(
    "DISCORD_WEBHOOK_URL",
    ""
)


# ==========================
# Global Stats
# ==========================

GLOBAL_STATS_ENABLED = env_bool(
    "GLOBAL_STATS_ENABLED",
    True
)

GLOBAL_LIVE_ONLY = env_bool(
    "GLOBAL_LIVE_ONLY",
    True
)

GLOBAL_STATS_URL = os.getenv(
    "GLOBAL_STATS_URL",
    ""
)

SHARE_BALANCE = env_bool(
    "SHARE_BALANCE",
    True
)

SHARE_TRADE_LOGS = env_bool(
    "SHARE_TRADE_LOGS",
    True
)


# ==========================
# Kalshi Auth
# ==========================

KALSHI_KEY_ID = os.getenv(
    "KALSHI_KEY_ID",
    ""
)

KALSHI_PRIVATE_KEY_PATH = os.getenv(
    "KALSHI_PRIVATE_KEY_PATH",
    "kalshi_private.key.pem"
)


# ==========================
# Logging
# ==========================

ENABLE_LOGS = env_bool(
    "ENABLE_LOGS",
    True
)