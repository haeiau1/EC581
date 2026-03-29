"""Data download and preprocessing helpers."""

from __future__ import annotations

import backtrader as bt
import pandas as pd
import yfinance as yf


class BIST100Data(bt.feeds.PandasData):
    """Backtrader feed with an extra daily return line."""

    lines = ("daily_return",)
    params = (("daily_return", "daily_return"),)


def _normalize_columns(data: pd.DataFrame) -> pd.DataFrame:
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data


def download_bist100_data(symbol: str, start: str, end: str | None = None) -> pd.DataFrame:
    """Download daily BIST100 data from Yahoo Finance."""

    candidates = [symbol]
    if symbol.startswith("^"):
        candidates.append(f"{symbol.removeprefix('^')}.IS")

    tried_symbols: list[str] = []

    for candidate in dict.fromkeys(candidates):
        tried_symbols.append(candidate)
        data = yf.download(
            candidate,
            start=start,
            end=end,
            auto_adjust=False,
            progress=False,
        )
        data = _normalize_columns(data)

        if data.empty:
            continue

        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        missing = [col for col in required_cols if col not in data.columns]
        if missing:
            raise ValueError(f"Missing required columns for {candidate}: {missing}")

        data = data.loc[:, required_cols].copy()
        data = data.dropna(subset=["Open", "High", "Low", "Close"])
        data["Volume"] = data["Volume"].fillna(0.0)
        data["daily_return"] = data["Close"].pct_change().fillna(0.0)
        data.index = pd.to_datetime(data.index)
        data.attrs["requested_symbol"] = symbol
        data.attrs["downloaded_symbol"] = candidate
        return data

    raise ValueError(f"No data returned for requested symbol(s): {', '.join(tried_symbols)}")


def buy_and_hold_return(data: pd.DataFrame) -> float:
    """Compute the total return of a buy-and-hold benchmark."""

    if data.empty:
        return 0.0
    return float(data["Close"].iloc[-1] / data["Close"].iloc[0] - 1.0)
