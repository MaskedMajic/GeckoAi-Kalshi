import sqlite3

DB_PATH = "data/trades.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            market TEXT,
            side TEXT,
            entry REAL,
            result TEXT,
            pnl REAL,
            bankroll REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_trade(market, side, entry, result, pnl, bankroll):
    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        INSERT INTO trades (
            market,
            side,
            entry,
            result,
            pnl,
            bankroll
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (market, side, entry, result, pnl, bankroll)
    )

    conn.commit()
    conn.close()


def get_summary():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM trades")
    total_trades = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM trades WHERE result = 'WIN'")
    wins = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM trades WHERE result = 'LOSS'")
    losses = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(pnl), 0) FROM trades")
    total_pnl = cursor.fetchone()[0]

    cursor.execute("SELECT bankroll FROM trades ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    latest_bankroll = row[0] if row else 0

    conn.close()

    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

    return {
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "total_pnl": total_pnl,
        "latest_bankroll": latest_bankroll,
    }
def get_latest_bankroll(default=5):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT bankroll
        FROM trades
        ORDER BY id DESC
        LIMIT 1
    """)

    row = cursor.fetchone()

    conn.close()

    if row:
        return row[0]

    return default