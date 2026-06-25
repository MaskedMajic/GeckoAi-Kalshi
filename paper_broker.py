import stats
import config
import risk
import discord_alerts
import kalshi_client
import trade_logger
import global_stats


def open_paper_trade(market, side, entry, time_left):
    bankroll = stats.get_latest_bankroll(
        config.STARTING_BANKROLL
    )

    contracts = risk.get_contracts(
        bankroll,
        entry
    )

    if contracts < 1:
        discord_alerts.send_message(
            f"NO PAPER TRADE | Balance ${bankroll:.2f} too low | "
            f"{side} @ {entry:.2f}"
        )
        return None

    position = round(
        contracts * entry,
        2
    )

    trade = {
        "market": market["market"],
        "ticker": market["ticker"],
        "side": side,
        "entry": entry,
        "close": market["close"],
        "time_left": time_left,
        "position": position,
        "bankroll_before": bankroll,
        "contracts": contracts,
        "contract_cost": position,
        "fees": 0,
        "btc_entry_price": kalshi_client.get_btc_price(),
        "opened_at": trade_logger.now_iso(),
        "live": False,
    }

    trade_logger.log_trade_open(trade)

    message = (
        f"🚀 **PAPER OPEN** | `{trade['ticker']}`\n"
        f"Side: **{side}** | "
        f"Entry: `{entry:.2f}` | "
        f"Time: `{time_left}m` | "
        f"Contracts: `{contracts}` | "
        f"Cost: `${position:.2f}`"
    )

    print(message)
    discord_alerts.send_message(message)

    return trade


def close_paper_trade(trade):
    winning_side = kalshi_client.get_market_result(
        trade["ticker"]
    )

    if winning_side is None:
        print("Settlement not ready yet")
        return False

    side = trade["side"]
    entry = trade["entry"]

    bankroll = trade.get(
        "bankroll_before",
        stats.get_latest_bankroll(
            config.STARTING_BANKROLL
        ),
    )

    contracts = trade.get("contracts", 1)
    is_live = trade.get("live", False)
    btc_close_price = kalshi_client.get_btc_price()

    won = side == winning_side

    entry_cost = float(
        trade.get(
            "avg_fill_price",
            entry
        )
    )

    exit_contract_value = 1 if won else 0

    pnl = contracts * (
        exit_contract_value - entry_cost
    )

    result = "WIN" if won else "LOSS"

    new_bankroll = bankroll + pnl

    stats.save_trade(
        market=trade["ticker"],
        side=side,
        entry=entry,
        result=result,
        pnl=round(pnl, 2),
        bankroll=round(new_bankroll, 2),
    )

    close_data = {
        "closed_at": trade_logger.now_iso(),
        "btc_close_price": btc_close_price,
        "exit_contract_value": exit_contract_value,
        "winning_side": winning_side,
        "result": result,
        "pnl": round(pnl, 2),
        "bankroll_after": round(new_bankroll, 2),
    }

    trade_logger.log_trade_close(
        trade,
        close_data
    )

    global_stats.send_trade(
        trade,
        close_data
    )

    summary = stats.get_summary()
    streak = stats.get_streak()

    if streak["current_type"] == "WIN":
        streak_label = f"W{streak['current_count']}"
    elif streak["current_type"] == "LOSS":
        streak_label = f"L{streak['current_count']}"
    else:
        streak_label = "-"

    total_pnl = (
        summary["latest_bankroll"]
        -
        config.STARTING_BANKROLL
    )

    emoji = "✅" if won else "❌"
    mode = "LIVE" if is_live else "PAPER"

    message = (
        f"{emoji} "
        f"**{mode} {result}** | "
        f"`{trade['ticker']}`\n"

        f"Side: **{side}** | "
        f"Winning: **{winning_side}** | "
        f"Entry: `{entry:.2f}` | "
        f"Contracts: `{int(contracts)}`\n"

        f"Trade: `${pnl:+.2f}` | "
        f"Total: `${total_pnl:+.2f}` | "
        f"Balance: `${summary['latest_bankroll']:.2f}` | "
        f"Record: `{summary['wins']}W / {summary['losses']}L`\n"

        f"🔥 Streak: `{streak_label}`"
    )

    print(message)

    discord_alerts.send_message(message)

    return True