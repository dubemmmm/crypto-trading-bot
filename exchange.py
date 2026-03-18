"""
Exchange data module.
Fetches real-time prices and OHLCV candle data using ccxt (public endpoints only).
Includes automatic fallback to alternate exchanges if the primary one fails.
"""

import ccxt
import pandas as pd
from datetime import datetime

import config


def create_exchange(exchange_id: str = None) -> ccxt.Exchange:
    """
    Create and return an exchange instance (public data only, no API keys).
    Tries the primary exchange, then falls back to alternatives if it fails.
    """
    ids_to_try = [exchange_id or config.EXCHANGE_ID] + getattr(config, "EXCHANGE_FALLBACKS", [])

    for eid in ids_to_try:
        try:
            exchange_class = getattr(ccxt, eid)
            exchange = exchange_class({"enableRateLimit": True})
            # Quick connectivity test
            exchange.load_markets()
            print(f"  ✅ Connected to {eid}")
            return exchange
        except Exception as e:
            print(f"  [!] {eid} unavailable ({type(e).__name__}), trying next...")

    raise RuntimeError(
        f"Could not connect to any exchange. Tried: {ids_to_try}. "
        "Check your internet connection or try a different exchange in config.py"
    )


def resolve_symbol(exchange: ccxt.Exchange, symbol: str) -> str:
    """
    Resolve a symbol to one available on the exchange.
    Tries the exact symbol first, then common variants (USD, USDT, USDC).
    """
    if symbol in exchange.markets:
        return symbol

    # Try common quote currency variants
    base = symbol.split("/")[0]
    for quote in ["USD", "USDT", "USDC"]:
        candidate = f"{base}/{quote}"
        if candidate in exchange.markets:
            return candidate

    raise ValueError(f"Symbol {symbol} (or variants) not found on {exchange.id}")


def fetch_ohlcv(exchange: ccxt.Exchange, symbol: str) -> pd.DataFrame:
    """
    Fetch OHLCV candle data for a symbol.
    Returns a DataFrame with columns: timestamp, open, high, low, close, volume
    """
    resolved = resolve_symbol(exchange, symbol)
    raw = exchange.fetch_ohlcv(
        resolved,
        timeframe=config.TIMEFRAME,
        limit=config.CANDLE_LIMIT,
    )

    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.set_index("timestamp")

    return df


def fetch_ticker(exchange: ccxt.Exchange, symbol: str) -> dict:
    """Fetch the current ticker (price info) for a symbol."""
    resolved = resolve_symbol(exchange, symbol)
    ticker = exchange.fetch_ticker(resolved)
    return {
        "symbol": symbol,           # Keep the original symbol for display
        "resolved": resolved,       # Actual symbol used on exchange
        "last": ticker["last"],
        "bid": ticker["bid"],
        "ask": ticker["ask"],
        "high": ticker["high"],
        "low": ticker["low"],
        "volume": ticker["baseVolume"],
        "timestamp": datetime.now(),
    }


def fetch_all_tickers(exchange: ccxt.Exchange) -> dict:
    """Fetch current prices for all configured symbols."""
    tickers = {}
    for symbol in config.SYMBOLS:
        try:
            tickers[symbol] = fetch_ticker(exchange, symbol)
        except Exception as e:
            print(f"  [!] Error fetching {symbol}: {e}")
    return tickers
