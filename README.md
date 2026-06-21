# 🦎 GeckoAi — Kalshi BTC Trading Bot

Automated Bitcoin event trading for Kalshi with paper + live execution, balance-based sizing, Discord alerts, trade logging, startup updating, and automatic database setup.

---

## ⚡ Features

- 📈 Automated BTC market participation
- 🧪 Paper trading mode
- 💵 Live execution mode
- 🧠 Balance-step position sizing
- 📊 SQLite trade logging + performance tracking
- 🔔 Discord notifications
- 📡 Websocket + REST fallback pricing
- 🔄 Auto-update on startup
- 📁 Automatic database creation
- ⚙️ Configurable risk controls

---

## Preview

### Startup

```text
📡 BOT STARTED
Mode: LIVE
Balance: $47.00
Contracts: 8
Sizing: balance_step

### Monitoring

🟢 [WATCH]
YES=0.90
NO=0.11
TIME=04:52
SIDE=YES
SRC=STREAM

### Trade Result

✅ LIVE WIN

Side: NO
Entry: 0.91
Contracts: 5

Trade: +$0.45
Total: +$17.53
Balance: $22.53
Record: 14W / 3L

### Project Structure

GeckoAi.py          → Startup launcher + updater

main.py             → Main trading loop
strategy.py         → Entry logic
risk.py             → Position sizing

live_broker.py      → Live execution
paper_broker.py     → Paper execution

kalshi_client.py    → Market/API interface
kalshi_stream.py    → Websocket pricing

trade_logger.py     → JSON trade logging
stats.py            → SQLite stats

discord_alerts.py   → Notifications
config.py           → Runtime configuration

### Installation

Clone:
git clone https://github.com/MaskedMajic/GeckoAi-Kalshi.git
cd GeckoAi-Kalshi

Install:
pip install -r requirements.txt

Windows:
copy .env.example .env

Mac/Linux
cp .env.example .env

Configure:
KALSHI_KEY_ID=
KALSHI_PRIVATE_KEY_PATH=
DISCORD_WEBHOOK=
MODE=

### Run GeckoAi
python GeckoAi.py

### Start-up Flow
Check GitHub
↓
Pull updates
↓
Start main.py
↓
Create database automatically
↓
Begin trading

### Modes

Paper:
MODE=paper

Live:
MODE=live_test

### Data Storage
data/
├── trades.db
└── trades.json

### Disclaimer

Experimental software.

Trading involves risk.

Paper results do not guarantee live performance.

Use responsibly.


☕ Support

SOL:
GFAZfcwjddxPJ2HgMbBd8a1Mg7KKCJQgUmKCm8v81Rix

Discord:
https://discord.gg/rZYFMthacs