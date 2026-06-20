import os
from dotenv import load_dotenv

load_dotenv()

MODE = os.getenv("MODE", "paper")

STARTING_BANKROLL = float(os.getenv("STARTING_BANKROLL", "5"))
MAX_TRADE_PCT = float(os.getenv("MAX_TRADE_PCT", "20"))

DISCORD_ENABLED = os.getenv("DISCORD_ENABLED", "false").lower() == "true"
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

KALSHI_KEY_ID = os.getenv("KALSHI_KEY_ID", "")
KALSHI_PRIVATE_KEY_PATH = os.getenv("KALSHI_PRIVATE_KEY_PATH", "")

SIZING_MODE = os.getenv("SIZING_MODE", "fixed").lower()
FIXED_CONTRACTS = int(os.getenv("FIXED_CONTRACTS", "1"))
MAX_CONTRACTS = int(os.getenv("MAX_CONTRACTS", "10"))

LIVE_MAX_CONTRACTS = int(os.getenv("LIVE_MAX_CONTRACTS", "1"))

TRADE_JSON_PATH = os.getenv("TRADE_JSON_PATH", "data/trades.json")
