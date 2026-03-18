"""
CLI dashboard — renders a live-updating terminal view of the bot's state.
"""

import os
from datetime import datetime
from tabulate import tabulate

from portfolio import Portfolio
import config


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def render(portfolio: Portfolio, current_prices: dict[str, float], signals: dict[str, str], cycle: int):
    """Render the full dashboard to the terminal."""
    clear_screen()

    total_value = portfolio.get_total_value(current_prices)
    total_return = portfolio.get_total_return_pct(current_prices)
    return_color = "\033[92m" if total_return >= 0 else "\033[91m"
    reset = "\033[0m"

    print("=" * 70)
    print(f"  🤖  CRYPTO PAPER TRADING BOT")
    print(f"  Strategy: {config.STRATEGY}  |  Cycle: #{cycle}  |  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # ── Portfolio Summary ─────────────────────────────────────────
    print(f"\n  💰 PORTFOLIO")
    print(f"  ┌─────────────────────────────────────────┐")
    print(f"  │  Starting Balance:  ${portfolio.starting_balance:>12,.2f}      │")
    print(f"  │  Cash Available:    ${portfolio.cash:>12,.2f}      │")
    print(f"  │  Position Value:    ${portfolio.get_position_value(current_prices):>12,.2f}      │")
    print(f"  │  Total Value:       ${total_value:>12,.2f}      │")
    print(f"  │  Total Return:   {return_color}{total_return:>+10.2f}%{reset}          │")
    print(f"  │  Realized P&L:     ${portfolio.total_realized_pnl:>12,.2f}      │")
    print(f"  └─────────────────────────────────────────┘")

    # ── Market Prices ─────────────────────────────────────────────
    print(f"\n  📊 MARKET PRICES & SIGNALS")
    price_rows = []
    for symbol in config.SYMBOLS:
        price = current_prices.get(symbol, 0)
        signal = signals.get(symbol, "—")

        if signal == "BUY":
            signal_str = "\033[92m● BUY\033[0m"
        elif signal == "SELL":
            signal_str = "\033[91m● SELL\033[0m"
        else:
            signal_str = "\033[90m● HOLD\033[0m"

        price_rows.append([symbol, f"${price:>12,.2f}", signal_str])

    print(tabulate(price_rows, headers=["Symbol", "Price", "Signal"], tablefmt="simple_outline", stralign="right"))

    # ── Open Positions ────────────────────────────────────────────
    print(f"\n  📂 OPEN POSITIONS ({len(portfolio.positions)}/{config.MAX_OPEN_POSITIONS})")
    if portfolio.positions:
        pos_rows = []
        for symbol, pos in portfolio.positions.items():
            price = current_prices.get(symbol, pos.entry_price)
            pnl = pos.unrealized_pnl(price)
            pnl_pct = pos.unrealized_pnl_pct(price)
            pnl_color = "\033[92m" if pnl >= 0 else "\033[91m"
            pos_rows.append([
                symbol,
                f"${pos.entry_price:>12,.2f}",
                f"${price:>12,.2f}",
                f"{pos.quantity:.6f}",
                f"{pnl_color}${pnl:>+10,.2f} ({pnl_pct:+.2f}%){reset}",
                f"${pos.stop_loss:,.2f}",
                f"${pos.take_profit:,.2f}",
            ])
        print(tabulate(
            pos_rows,
            headers=["Symbol", "Entry", "Current", "Qty", "P&L", "Stop Loss", "Take Profit"],
            tablefmt="simple_outline",
            stralign="right",
        ))
    else:
        print("  (no open positions)")

    # ── Recent Trades ─────────────────────────────────────────────
    print(f"\n  📜 RECENT TRADES (last 10)")
    if portfolio.trade_history:
        recent = portfolio.trade_history[-10:]
        trade_rows = []
        for t in reversed(recent):
            side_color = "\033[92m" if t.side == "BUY" else "\033[91m"
            pnl_str = f"${t.pnl:>+10,.2f}" if t.pnl is not None else "—"
            trade_rows.append([
                t.timestamp.strftime("%H:%M:%S"),
                t.symbol,
                f"{side_color}{t.side}{reset}",
                f"${t.price:>12,.2f}",
                f"${t.total:>10,.2f}",
                pnl_str,
                t.reason,
            ])
        print(tabulate(
            trade_rows,
            headers=["Time", "Symbol", "Side", "Price", "Total", "P&L", "Reason"],
            tablefmt="simple_outline",
            stralign="right",
        ))
    else:
        print("  (no trades yet)")

    print(f"\n  ⏳ Next check in {config.POLL_INTERVAL_SECONDS}s  |  Press Ctrl+C to stop")
    print("=" * 70)
