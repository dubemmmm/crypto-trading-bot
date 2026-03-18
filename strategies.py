"""
Trading strategies.
Each strategy takes OHLCV data and returns a signal: "BUY", "SELL", or "HOLD".
"""

import pandas as pd
import config


def sma_crossover(df: pd.DataFrame) -> str:
    """
    Simple Moving Average Crossover Strategy.
    - BUY when short SMA crosses above long SMA
    - SELL when short SMA crosses below long SMA
    - HOLD otherwise
    """
    df = df.copy()
    df["sma_short"] = df["close"].rolling(window=config.SMA_SHORT_PERIOD).mean()
    df["sma_long"] = df["close"].rolling(window=config.SMA_LONG_PERIOD).mean()

    # Drop NaN rows
    df = df.dropna()

    if len(df) < 2:
        return "HOLD"

    # Check for crossover on the last two candles
    prev = df.iloc[-2]
    curr = df.iloc[-1]

    prev_short_above = prev["sma_short"] > prev["sma_long"]
    curr_short_above = curr["sma_short"] > curr["sma_long"]

    if not prev_short_above and curr_short_above:
        return "BUY"
    elif prev_short_above and not curr_short_above:
        return "SELL"

    return "HOLD"


def rsi(df: pd.DataFrame) -> str:
    """
    Relative Strength Index Strategy.
    - BUY when RSI < oversold threshold (default 30)
    - SELL when RSI > overbought threshold (default 70)
    - HOLD otherwise
    """
    df = df.copy()
    delta = df["close"].diff()

    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=config.RSI_PERIOD).mean()
    avg_loss = loss.rolling(window=config.RSI_PERIOD).mean()

    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))

    df = df.dropna()

    if len(df) < 1:
        return "HOLD"

    current_rsi = df.iloc[-1]["rsi"]

    if current_rsi < config.RSI_OVERSOLD:
        return "BUY"
    elif current_rsi > config.RSI_OVERBOUGHT:
        return "SELL"

    return "HOLD"


def bollinger_bands(df: pd.DataFrame) -> str:
    """
    Bollinger Bands Strategy.
    - BUY when price touches/crosses below the lower band
    - SELL when price touches/crosses above the upper band
    - HOLD otherwise
    """
    df = df.copy()
    df["sma"] = df["close"].rolling(window=config.BB_PERIOD).mean()
    df["std"] = df["close"].rolling(window=config.BB_PERIOD).std()
    df["upper"] = df["sma"] + (config.BB_STD_DEV * df["std"])
    df["lower"] = df["sma"] - (config.BB_STD_DEV * df["std"])

    df = df.dropna()

    if len(df) < 1:
        return "HOLD"

    last = df.iloc[-1]

    if last["close"] <= last["lower"]:
        return "BUY"
    elif last["close"] >= last["upper"]:
        return "SELL"

    return "HOLD"


# ── Strategy dispatcher ──────────────────────────────────────────

STRATEGIES = {
    "sma_crossover": sma_crossover,
    "rsi": rsi,
    "bollinger_bands": bollinger_bands,
}


def get_signal(strategy_name: str, df: pd.DataFrame) -> str:
    """Run the configured strategy and return a signal."""
    if strategy_name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy_name}. Choose from: {list(STRATEGIES.keys())}")
    return STRATEGIES[strategy_name](df)
