# GeckoAI Kalshi

GeckoAI Kalshi is an automated **Kalshi BTC 15-minute market bot** focused on the `KXBTC15M` series.

It watches short-expiry BTC prediction markets, looks for qualifying entries inside a configured price band, sizes positions from bankroll rules, and logs every trade for review.

This is **not** a general crypto bot, and it is **not** trying to predict all of Bitcoin. It is a narrow execution-focused bot for short-duration Kalshi event contracts.

## What it does

- Watches live `KXBTC15M` markets
- Chooses **YES** or **NO** based on current qualifying market price
- Enforces configurable entry range and time-left rules
- Supports **paper mode** and **live test mode**
- Uses balance-based position sizing
- Logs trades locally for review
- Optionally sends Discord notifications
- Optionally sends closed trades to a global analytics receiver
- Displays a live terminal dashboard

## Current behavior at a glance

The bot is built around:
- short-expiry Kalshi BTC markets
- high-selectivity entries inside a configured price band
- simple bankroll-based sizing
- detailed trade logging for analysis and iteration

Core strategy rules currently come from config values such as:
- `ENTRY_MIN`
- `ENTRY_MAX`
- `MAX_TIME_LEFT_MINUTES`
- `SIZING_MODE`
- `ENABLE_STOP_LOSS`
- `STOP_LOSS_PRICE`

## Modes

### `paper`
Safe testing mode.

Uses live market data, but does **not** place live orders.

### `live_test`
Live order mode.

Uses Kalshi auth, places real orders, and should only be used when your config is correct and you understand the risk.

## Features

- Live Kalshi websocket price support
- REST fallback for market pricing
- Balance-step, fixed, and max-affordable sizing modes
- Local SQLite trade stats
- Detailed JSON trade logs
- Optional Discord alerts
- Optional global trade analytics feed
- Smoother in-place dashboard rendering
- Timing logs written to `data/timing.log`
- Live entry / exit timing instrumentation

## v0.3.7 runtime improvements

`v0.3.7` is mainly a **runtime / execution quality update**, not a strategy rewrite.

Highlights:
- cached Kalshi signing key in memory
- reused HTTP sessions
- reduced redundant market discovery work
- reduced repeated price lookup overhead
- improved dashboard rendering so it is smoother and less flashy
- moved timing spam out of the terminal and into `data/timing.log`
- added timing instrumentation for:
  - market fetch
  - price fetch
  - dashboard refresh / repaint
  - live balance fetch
  - request signing / header creation
  - live order body / POST / total time
  - live stop-exit body / POST / total time
- moved Coinbase BTC entry-price lookup out of the immediate trade-open hot path

**Important:** these changes are intended to improve execution behavior and observability. They do **not** intentionally change the core trading rules.

## Requirements

- Python 3.11+
- Kalshi account
- Kalshi API key ID
- Kalshi private PEM key

Python packages:
- `requests`
- `cryptography`
- `python-dotenv`
- `streamlit`
- `websockets`

Install them with:

```bash
pip install -r requirements.txt
```

## Installation

### Clone the repo

```bash
git clone https://github.com/MaskedMajic/GeckoAi-Kalshi.git
cd GeckoAi-Kalshi
```

### Create a virtual environment

#### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the repo root.

### Safe paper example

```env
BOT_VERSION=0.3.7
MODE=paper
SIZING_MODE=balance_step

STARTING_BANKROLL=5
MIN_BANKROLL=1

FIXED_CONTRACTS=1
MAX_CONTRACTS=50
LIVE_MAX_CONTRACTS=10

ENTRY_MIN=0.87
ENTRY_MAX=0.95
MAX_TIME_LEFT_MINUTES=6

ENABLE_STOP_LOSS=false
STOP_LOSS_PRICE=0.15

DISCORD_ENABLED=false
DISCORD_WEBHOOK_URL=

GLOBAL_STATS_ENABLED=false
GLOBAL_LIVE_ONLY=true
GLOBAL_STATS_URL=
SHARE_BALANCE=false
SHARE_TRADE_LOGS=false

KALSHI_KEY_ID=
KALSHI_PRIVATE_KEY_PATH=kalshi_private.key.pem

ENABLE_LOGS=true
```

### Live test mode

Set:

```env
MODE=live_test
```

and provide:

```env
KALSHI_KEY_ID=your_key_id
KALSHI_PRIVATE_KEY_PATH=path_to_your_key.pem
```

## Running the bot

### Recommended

Run directly:

#### Windows

```powershell
py main.py
```

#### macOS / Linux

```bash
python3 main.py
```

### Optional first-run helper

```bash
python start.py
```

### Startup scripts

The repo may include convenience launchers like `Run.bat` or `Mac & Linux Start.sh`, but direct `main.py` execution is the clearest way to run and debug the bot.

## Files worth knowing

- `main.py` — main loop and dashboard
- `live_broker.py` — live entry / exit order handling
- `paper_broker.py` — paper-mode order simulation
- `kalshi_client.py` — market and orderbook REST helpers
- `kalshi_stream.py` — websocket market updates
- `strategy.py` — trade eligibility rules
- `risk.py` — sizing logic
- `stats.py` — local SQLite stats
- `trade_logger.py` — detailed trade JSON logging
- `global_stats.py` — optional global closed-trade reporting
- `data/timing.log` — runtime timing/debug log

## Notes on logging and analytics

The bot writes two useful local data outputs:

- SQLite summary stats via `data/trades.db`
- detailed JSON trade records via `data/trades.json`

If enabled, it can also send closed-trade payloads to a central receiver for multi-bot/global analytics.

## Safety notes

- Start in **paper mode** first
- Do not switch to live mode until your auth and config are correct
- Treat stop-loss and sizing changes carefully
- Review logs before assuming the bot is faster or smarter just because it feels smoother

## Disclaimer

This software is provided for educational and experimental purposes only.

Trading prediction markets involves real financial risk. Use at your own risk.