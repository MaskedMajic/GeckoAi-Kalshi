import sqlite3
import os


DB_PATH = "data/trades.db"


def ensure_db_dir():
    directory = os.path.dirname(DB_PATH)

    if directory:
        os.makedirs(directory, exist_ok=True)


def init_db():
    ensure_db_dir()

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
    ensure_db_dir()

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
    ensure_db_dir()

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

    cursor.execute("""
        SELECT bankroll
        FROM trades
        ORDER BY id DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()

    latest_bankroll = row[0] if row else 0

    win_rate = wins / total_trades * 100 if total_trades > 0 else 0

    return {
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "total_pnl": total_pnl,
        "latest_bankroll": latest_bankroll,
    }


def get_latest_bankroll(default=5):
    ensure_db_dir()

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


def get_streak():
    ensure_db_dir()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT result
        FROM trades
        WHERE result IN ('WIN', 'LOSS')
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {
            "current_type": "-",
            "current_count": 0,
        }

    current_type = rows[0][0]
    count = 0

    for row in rows:
        if row[0] == current_type:
            count += 1
        else:
            break

    return {
        "current_type": current_type,
        "current_count": count,
    }