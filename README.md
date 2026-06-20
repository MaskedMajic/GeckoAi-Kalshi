# 🦎 GeckoAi — Kalshi BTC Trading Bot

Automated Bitcoin event trading for Kalshi with paper + live execution, dynamic sizing, Discord alerts, and trade logging.

---

## ⚡ Features

📈 Automated BTC market participation
🧪 Paper mode for testing strategies
💵 Live execution mode
🧠 Balance-step position sizing
📊 Trade logging + performance tracking
🔔 Discord notifications
⚙️ Configurable risk controls

---

## Preview

```text
📡 BOT STARTED
Mode: PAPER
Balance: $5.00
Contracts: 3
Sizing: balance_step
```

```text
✅ LIVE WIN
Side: NO
Entry: 0.91
Contracts: 5

Trade: +$0.45
Balance: $22.53
Record: 14W / 3L
```

---

# Project Structure

```plaintext
main.py              → Main execution loop
strategy.py          → Entry logic
risk.py              → Position sizing + limits
live_broker.py       → Live order execution
paper_broker.py      → Simulated trading
kalshi_client.py     → Market/API interface
discord_alerts.py    → Notifications
trade_logger.py      → Trade persistence
stats.py             → Metrics
config.py            → Runtime config
```

---

# Installation

Clone:

```bash
git clone https://github.com/MaskedMajic/GeckoAi-Kalshi.git
cd GeckoAi-Kalshi
```

Install:

```bash
pip install -r requirements.txt
```

Create environment:

```bash
copy .env.example .env
```

---

# Run

Paper:

```bash
python main.py
```

Live:

```bash
MODE=live
python main.py
```

---

# Position Sizing

Example balance-step sizing:

| Balance | Contracts |
| ------- | --------- |
| <$5     | 1         |
| <$10    | 2         |
| <$25    | 3         |
| <$50    | 5         |
| <$100   | 8         |
| $100+   | 10        |

---

# Disclaimer

This software is experimental.

Trading involves risk.

Paper results do not guarantee live performance.

Use responsibly.

---

Built by **MaskedMajic**
