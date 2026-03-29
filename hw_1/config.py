"""Configuration objects for the BIST100 backtests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BacktestConfig:
    symbol: str = "^XU100"
    start: str = "2010-01-01"
    end: str | None = None
    initial_cash: float = 100_000.0
    commission: float = 0.001
    allocation_pct: float = 95.0
    printlog: bool = False


DEFAULT_CONFIG = BacktestConfig()

