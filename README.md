# Crypto Paper Trading Bot

A fully functional crypto trading bot that uses **real market prices** but **fake money** — so you can learn and experiment with zero financial risk.

## How It Works

Every 60 seconds, the bot:

1. Pulls live prices for **BTC, ETH, and SOL** from Kraken
2. Checks if any open positions need to be auto-sold (stop-loss / take-profit)
3. Runs a trading strategy on the price history to generate a **BUY**, **SELL**, or **HOLD** signal
4. Executes trades on paper and updates your portfolio
5. Displays a live dashboard in the terminal

No API keys required — the bot only reads publicly available price data.

## Quick Start

```bash
cd crypto-trading-bot

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the bot
python bot.py
```

## Usage

```bash
# Live paper trading (runs continuously, Ctrl+C to stop)
python bot.py

# Backtest strategy on historical data
python bot.py --backtest

# Use a different strategy
python bot.py --strategy rsi
python bot.py --strategy bollinger_bands

# Start with more fake money
python bot.py --balance 50000

# Faster polling interval (every 30 seconds)
python bot.py --interval 30

# Combine options
python bot.py --strategy rsi --balance 25000 --interval 15
```

## Trading Strategies

### SMA Crossover (default)

Uses two Simple Moving Averages (short-term and long-term). When the fast average crosses above the slow average, the trend is shifting upward — **BUY**. When it crosses below — **SELL**. Best for trending markets but can be slow to trigger in sideways conditions.

### RSI (Relative Strength Index)

Measures whether a coin is overbought or oversold on a 0–100 scale. Below 30 means oversold — **BUY**. Above 70 means overbought — **SELL**. Triggers more frequently than SMA crossover.

### Bollinger Bands

Draws upper and lower bands around the price using standard deviation. When price hits the lower band, it's unusually cheap — **BUY**. When it hits the upper band, it's unusually expensive — **SELL**.

## Risk Management

| Setting | Default | Description |
|---|---|---|
| Position size | 10% | Max percentage of portfolio per trade |
| Stop-loss | 5% | Auto-sell if price drops this much below entry |
| Take-profit | 15% | Auto-sell if price rises this much above entry |
| Max positions | 5 | Maximum concurrent open positions |

All risk parameters are configurable in `config.py`.

## Project Structure

```
crypto-trading-bot/
├── bot.py             Main entry point — live trading loop and backtest mode
├── config.py          All settings (strategy, risk limits, symbols, balance)
├── exchange.py        Fetches real prices from Kraken with exchange fallback
├── strategies.py      Three strategy algorithms (SMA, RSI, Bollinger Bands)
├── portfolio.py       Paper trading engine (positions, P&L, trade logging)
├── dashboard.py       Live terminal dashboard with colored output
├── requirements.txt   Python dependencies
└── trade_history.csv  Auto-generated log of every trade
```

## Configuration

Edit `config.py` to customize:

```python
STARTING_BALANCE_USD = 10_000.00       # Starting fake money
SYMBOLS = ["BTC/USD", "ETH/USD", "SOL/USD"]  # Coins to trade
STRATEGY = "sma_crossover"             # Strategy to use
POLL_INTERVAL_SECONDS = 60             # Check interval
TIMEFRAME = "1h"                       # Candle timeframe

# Strategy parameters
SMA_SHORT_PERIOD = 10
SMA_LONG_PERIOD = 30
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
BB_PERIOD = 20
BB_STD_DEV = 2.0

# Risk management
MAX_POSITION_SIZE_PCT = 10.0
STOP_LOSS_PCT = 5.0
TAKE_PROFIT_PCT = 15.0
MAX_OPEN_POSITIONS = 5
```

## Dependencies

- **ccxt** — Exchange connectivity for real-time price data
- **pandas** — OHLCV candle data handling and indicator calculations
- **tabulate** — Terminal dashboard table formatting

## Supported Exchanges

The bot uses Kraken by default (works worldwide, no API key needed). If Kraken is unavailable, it automatically falls back to Coinbase Pro, then Bybit. Change this in `config.py`:

```python
EXCHANGE_ID = "kraken"
EXCHANGE_FALLBACKS = ["coinbasepro", "bybit"]
```

## Trade Logging

Every trade is logged to `trade_history.csv` with the following fields:

```
timestamp, symbol, side, price, quantity, total, pnl, reason, cash_after, portfolio_value
```

## Disclaimer

This bot trades with **fake money only**. It is intended for learning and experimentation. Past performance in backtests does not guarantee future results. If you choose to adapt this for real trading, you do so at your own risk.
