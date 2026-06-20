import os
from dotenv import load_dotenv

load_dotenv()


# ==========================
# Runtime
# ==========================

MODE = os.getenv(
    "MODE",
    "paper"
)

SIZING_MODE = os.getenv(
    "SIZING_MODE",
    "balance_step"
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

MIN_BANKROLL = float(
    os.getenv(
        "MIN_BANKROLL",
        1
    )
)


# ==========================
# Discord
# ==========================

DISCORD_ENABLED = (
    os.getenv(
        "DISCORD_ENABLED",
        "true"
    ).lower()
    ==
    "true"
)

DISCORD_WEBHOOK_URL = os.getenv(
    "DISCORD_WEBHOOK_URL",
    ""
)


# ==========================
# Logging
# ==========================

ENABLE_LOGS = (
    os.getenv(
        "ENABLE_LOGS",
        "true"
    ).lower()
    ==
    "true"
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