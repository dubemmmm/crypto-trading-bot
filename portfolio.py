"""
Paper trading portfolio engine.
Tracks balances, open positions, and trade history — all with fake money.
"""

import csv
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import config


@dataclass
class Position:
    symbol: str
    side: str              # "long"
    entry_price: float
    quantity: float
    entry_time: datetime
    stop_loss: float
    take_profit: float

    @property
    def cost_basis(self) -> float:
        return self.entry_price * self.quantity

    def unrealized_pnl(self, current_price: float) -> float:
        return (current_price - self.entry_price) * self.quantity

    def unrealized_pnl_pct(self, current_price: float) -> float:
        if self.entry_price == 0:
            return 0.0
        return ((current_price - self.entry_price) / self.entry_price) * 100


@dataclass
class TradeRecord:
    timestamp: datetime
    symbol: str
    side: str              # "BUY" or "SELL"
    price: float
    quantity: float
    total: float
    pnl: Optional[float]   # None for buys, realized P&L for sells
    reason: str            # "signal", "stop_loss", "take_profit"


class Portfolio:
    def __init__(self, starting_balance: float = None):
        self.starting_balance = starting_balance or config.STARTING_BALANCE_USD
        self.cash = self.starting_balance
        self.positions: dict[str, Position] = {}   # symbol -> Position
        self.trade_history: list[TradeRecord] = []
        self.total_realized_pnl = 0.0
        self._init_trade_log()

    def _init_trade_log(self):
        """Initialize the CSV trade log file."""
        if not os.path.exists(config.TRADE_LOG_FILE):
            with open(config.TRADE_LOG_FILE, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "symbol", "side", "price",
                    "quantity", "total", "pnl", "reason",
                    "cash_after", "portfolio_value",
                ])

    def _log_trade(self, trade: TradeRecord, portfolio_value: float):
        """Append a trade to the CSV log."""
        with open(config.TRADE_LOG_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                trade.timestamp.isoformat(),
                trade.symbol,
                trade.side,
                f"{trade.price:.6f}",
                f"{trade.quantity:.8f}",
                f"{trade.total:.2f}",
                f"{trade.pnl:.2f}" if trade.pnl is not None else "",
                trade.reason,
                f"{self.cash:.2f}",
                f"{portfolio_value:.2f}",
            ])

    def get_position_value(self, current_prices: dict[str, float]) -> float:
        """Total value of all open positions at current prices."""
        total = 0.0
        for symbol, pos in self.positions.items():
            price = current_prices.get(symbol, pos.entry_price)
            total += pos.quantity * price
        return total

    def get_total_value(self, current_prices: dict[str, float]) -> float:
        """Total portfolio value = cash + positions."""
        return self.cash + self.get_position_value(current_prices)

    def get_total_return_pct(self, current_prices: dict[str, float]) -> float:
        """Total return as a percentage."""
        total = self.get_total_value(current_prices)
        return ((total - self.starting_balance) / self.starting_balance) * 100

    def can_open_position(self, symbol: str) -> bool:
        """Check if we can open a new position."""
        if symbol in self.positions:
            return False  # Already have a position
        if len(self.positions) >= config.MAX_OPEN_POSITIONS:
            return False  # Too many open positions
        return True

    def calculate_position_size(self, price: float) -> float:
        """Calculate how much to buy based on risk rules."""
        max_spend = self.cash * (config.MAX_POSITION_SIZE_PCT / 100)
        if max_spend < 1.0:
            return 0.0
        quantity = max_spend / price
        return quantity

    def open_position(self, symbol: str, price: float, reason: str = "signal") -> Optional[TradeRecord]:
        """Open a new paper position (buy)."""
        if not self.can_open_position(symbol):
            return None

        quantity = self.calculate_position_size(price)
        if quantity <= 0:
            return None

        cost = quantity * price

        # Create position
        position = Position(
            symbol=symbol,
            side="long",
            entry_price=price,
            quantity=quantity,
            entry_time=datetime.now(),
            stop_loss=price * (1 - config.STOP_LOSS_PCT / 100),
            take_profit=price * (1 + config.TAKE_PROFIT_PCT / 100),
        )

        self.cash -= cost
        self.positions[symbol] = position

        # Record trade
        trade = TradeRecord(
            timestamp=datetime.now(),
            symbol=symbol,
            side="BUY",
            price=price,
            quantity=quantity,
            total=cost,
            pnl=None,
            reason=reason,
        )
        self.trade_history.append(trade)
        self._log_trade(trade, self.get_total_value({symbol: price}))

        return trade

    def close_position(self, symbol: str, price: float, reason: str = "signal") -> Optional[TradeRecord]:
        """Close an existing paper position (sell)."""
        if symbol not in self.positions:
            return None

        position = self.positions[symbol]
        revenue = position.quantity * price
        pnl = (price - position.entry_price) * position.quantity

        self.cash += revenue
        self.total_realized_pnl += pnl
        del self.positions[symbol]

        # Record trade
        trade = TradeRecord(
            timestamp=datetime.now(),
            symbol=symbol,
            side="SELL",
            price=price,
            quantity=position.quantity,
            total=revenue,
            pnl=pnl,
            reason=reason,
        )
        self.trade_history.append(trade)
        self._log_trade(trade, self.get_total_value({symbol: price}))

        return trade

    def check_stop_loss_take_profit(self, current_prices: dict[str, float]) -> list[TradeRecord]:
        """Check all positions for stop-loss or take-profit triggers."""
        closed_trades = []

        # Iterate over a copy since we may modify during iteration
        for symbol in list(self.positions.keys()):
            if symbol not in current_prices:
                continue

            price = current_prices[symbol]
            position = self.positions[symbol]

            if price <= position.stop_loss:
                trade = self.close_position(symbol, price, reason="stop_loss")
                if trade:
                    closed_trades.append(trade)

            elif price >= position.take_profit:
                trade = self.close_position(symbol, price, reason="take_profit")
                if trade:
                    closed_trades.append(trade)

        return closed_trades
