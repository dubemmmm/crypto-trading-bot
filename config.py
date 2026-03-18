"""
Configuration for the paper trading bot.
Edit these values to customize your bot's behavior.
"""

# ── Starting Capital ──────────────────────────────────────────────
STARTING_BALANCE_USD = 10_000.00

# ── Trading Pairs ─────────────────────────────────────────────────
SYMBOLS = [
    "BTC/USD",
    "ETH/USD",
    "SOL/USD",
]

# ── Exchange ──────────────────────────────────────────────────────
# Public data only — no API keys needed for paper trading
# Kraken works worldwide with no API key required for public data
# Fallback order if primary fails: kraken -> coinbasepro -> bybit
EXCHANGE_ID = "kraken"
EXCHANGE_FALLBACKS = ["coinbasepro", "bybit"]

# ── Strategy ──────────────────────────────────────────────────────
# Options: "sma_crossover", "rsi", "bollinger_bands"
STRATEGY = "sma_crossover"

# SMA Crossover settings
SMA_SHORT_PERIOD = 10
SMA_LONG_PERIOD = 30

# RSI settings
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

# Bollinger Bands settings
BB_PERIOD = 20
BB_STD_DEV = 2.0

# ── Risk Management ──────────────────────────────────────────────
MAX_POSITION_SIZE_PCT = 10.0    # Max % of portfolio per trade
STOP_LOSS_PCT = 5.0             # Sell if price drops this % below entry
TAKE_PROFIT_PCT = 15.0          # Sell if price rises this % above entry
MAX_OPEN_POSITIONS = 5          # Max concurrent positions

# ── Bot Settings ──────────────────────────────────────────────────
POLL_INTERVAL_SECONDS = 60      # How often to check for signals
TIMEFRAME = "1h"                # Candle timeframe
CANDLE_LIMIT = 100              # Candles to fetch for indicators

# ── Logging ───────────────────────────────────────────────────────
TRADE_LOG_FILE = "trade_history.csv"
