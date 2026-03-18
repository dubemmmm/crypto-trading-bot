#!/usr/bin/env python3
"""
🤖 Crypto Paper Trading Bot
=============================
A fully-functional trading bot that uses REAL market data but FAKE money.
No API keys required — fetches public price data from Binance via ccxt.

Usage:
    python bot.py              # Run the live trading loop
    python bot.py --backtest   # Run a quick backtest on historical data
    python bot.py --status     # Show current portfolio status and exit

Configure everything in config.py
"""

import sys
import time
import argparse
from datetime import datetime

import config
from exchange import create_exchange, fetch_ohlcv, fetch_all_tickers
from strategies import get_signal
from portfolio import Portfolio
from dashboard import render


def run_bot():
    """Main trading loop."""
    print("\n  🚀 Starting Paper Trading Bot...")
    print(f"  Strategy: {config.STRATEGY}")
    print(f"  Symbols: {', '.join(config.SYMBOLS)}")
    print(f"  Starting balance: ${config.STARTING_BALANCE_USD:,.2f}")
    print(f"  Fetching market data...\n")

    exchange = create_exchange()
    portfolio = Portfolio()
    cycle = 0

    while True:
        try:
            cycle += 1

            # 1. Fetch current prices
            tickers = fetch_all_tickers(exchange)
            current_prices = {sym: t["last"] for sym, t in tickers.items() if t["last"]}

            if not current_prices:
                print("  [!] No price data available. Retrying...")
                time.sleep(10)
                continue

            # 2. Check stop-loss / take-profit on open positions
            sl_tp_trades = portfolio.check_stop_loss_take_profit(current_prices)
            for trade in sl_tp_trades:
                emoji = "🛑" if trade.reason == "stop_loss" else "🎯"
                pnl_str = f"${trade.pnl:+,.2f}" if trade.pnl else ""
                print(f"  {emoji} {trade.reason.upper()}: Sold {trade.symbol} @ ${trade.price:,.2f}  {pnl_str}")

            # 3. Run strategy on each symbol
            signals = {}
            for symbol in config.SYMBOLS:
                try:
                    df = fetch_ohlcv(exchange, symbol)
                    signal = get_signal(config.STRATEGY, df)
                    signals[symbol] = signal
                except Exception as e:
                    signals[symbol] = "HOLD"

            # 4. Execute signals
            for symbol, signal in signals.items():
                price = current_prices.get(symbol)
                if not price:
                    continue

                if signal == "BUY":
                    trade = portfolio.open_position(symbol, price, reason="signal")
                    if trade:
                        print(f"  🟢 BUY: {symbol} — {trade.quantity:.6f} @ ${price:,.2f} (${trade.total:,.2f})")

                elif signal == "SELL":
                    trade = portfolio.close_position(symbol, price, reason="signal")
                    if trade:
                        pnl_str = f"${trade.pnl:+,.2f}" if trade.pnl else ""
                        print(f"  🔴 SELL: {symbol} — {trade.quantity:.6f} @ ${price:,.2f}  {pnl_str}")

            # 5. Render dashboard
            render(portfolio, current_prices, signals, cycle)

            # 6. Wait
            time.sleep(config.POLL_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            print("\n\n  ⛔ Bot stopped by user.")
            print_summary(portfolio, current_prices)
            sys.exit(0)

        except Exception as e:
            print(f"\n  [!] Error in cycle {cycle}: {e}")
            time.sleep(10)


def run_backtest():
    """Run a quick backtest using historical candle data."""
    print("\n  📊 Running Backtest...")
    print(f"  Strategy: {config.STRATEGY}")
    print(f"  Timeframe: {config.TIMEFRAME}")
    print(f"  Candles: {config.CANDLE_LIMIT}")
    print()

    exchange = create_exchange()
    portfolio = Portfolio()

    for symbol in config.SYMBOLS:
        print(f"  Fetching {symbol} history...")
        try:
            df = fetch_ohlcv(exchange, symbol)
        except Exception as e:
            print(f"  [!] Failed to fetch {symbol}: {e}")
            continue

        min_candles = max(config.SMA_LONG_PERIOD, config.RSI_PERIOD, config.BB_PERIOD) + 2

        # Walk through candles one at a time
        for i in range(min_candles, len(df)):
            window = df.iloc[:i + 1]
            signal = get_signal(config.STRATEGY, window)
            price = float(window.iloc[-1]["close"])
            current_prices = {symbol: price}

            # Check stops
            portfolio.check_stop_loss_take_profit(current_prices)

            if signal == "BUY":
                portfolio.open_position(symbol, price, reason="signal")
            elif signal == "SELL":
                portfolio.close_position(symbol, price, reason="signal")

        # Close any remaining position at the last price
        if symbol in portfolio.positions:
            last_price = float(df.iloc[-1]["close"])
            portfolio.close_position(symbol, last_price, reason="backtest_end")

    # Summary
    last_prices = {}
    for symbol in config.SYMBOLS:
        try:
            df = fetch_ohlcv(exchange, symbol)
            last_prices[symbol] = float(df.iloc[-1]["close"])
        except Exception:
            pass

    print_summary(portfolio, last_prices)

    total_trades = len(portfolio.trade_history)
    winning = sum(1 for t in portfolio.trade_history if t.pnl and t.pnl > 0)
    losing = sum(1 for t in portfolio.trade_history if t.pnl and t.pnl < 0)

    print(f"\n  📈 BACKTEST RESULTS")
    print(f"  ─────────────────────────────────────")
    print(f"  Total trades:    {total_trades}")
    print(f"  Winning trades:  {winning}")
    print(f"  Losing trades:   {losing}")
    if winning + losing > 0:
        print(f"  Win rate:        {winning / (winning + losing) * 100:.1f}%")
    print(f"  Realized P&L:    ${portfolio.total_realized_pnl:+,.2f}")
    print(f"  Final value:     ${portfolio.get_total_value(last_prices):,.2f}")
    print(f"  Total return:    {portfolio.get_total_return_pct(last_prices):+.2f}%")
    print()


def print_summary(portfolio: Portfolio, current_prices: dict):
    """Print a final portfolio summary."""
    total = portfolio.get_total_value(current_prices)
    ret = portfolio.get_total_return_pct(current_prices)

    print(f"\n  ═══════════════════════════════════════")
    print(f"  📋 FINAL SUMMARY")
    print(f"  ═══════════════════════════════════════")
    print(f"  Starting balance:  ${portfolio.starting_balance:>12,.2f}")
    print(f"  Current cash:      ${portfolio.cash:>12,.2f}")
    print(f"  Position value:    ${portfolio.get_position_value(current_prices):>12,.2f}")
    print(f"  Total value:       ${total:>12,.2f}")
    print(f"  Realized P&L:      ${portfolio.total_realized_pnl:>+12,.2f}")
    print(f"  Total return:      {ret:>+11.2f}%")
    print(f"  Total trades:      {len(portfolio.trade_history):>12}")
    print(f"  Open positions:    {len(portfolio.positions):>12}")
    print(f"  Trade log:         {config.TRADE_LOG_FILE}")
    print(f"  ═══════════════════════════════════════\n")


def main():
    parser = argparse.ArgumentParser(
        description="🤖 Crypto Paper Trading Bot — trade with fake money using real market data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bot.py                      Run live paper trading
  python bot.py --backtest           Backtest strategy on historical data
  python bot.py --strategy rsi       Use RSI strategy
  python bot.py --balance 50000      Start with $50,000 fake dollars

Configure defaults in config.py
        """,
    )
    parser.add_argument("--backtest", action="store_true", help="Run a backtest instead of live trading")
    parser.add_argument("--strategy", type=str, choices=["sma_crossover", "rsi", "bollinger_bands"],
                        help="Override the trading strategy")
    parser.add_argument("--balance", type=float, help="Override starting balance (USD)")
    parser.add_argument("--interval", type=int, help="Override poll interval (seconds)")

    args = parser.parse_args()

    # Apply overrides
    if args.strategy:
        config.STRATEGY = args.strategy
    if args.balance:
        config.STARTING_BALANCE_USD = args.balance
    if args.interval:
        config.POLL_INTERVAL_SECONDS = args.interval

    print(r"""
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║   🤖  CRYPTO PAPER TRADING BOT                       ║
    ║                                                       ║
    ║   Real market data  •  Fake money  •  Zero risk      ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    if args.backtest:
        run_backtest()
    else:
        run_bot()


if __name__ == "__main__":
    main()
