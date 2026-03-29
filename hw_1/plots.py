"""Plotting utilities for HW1 outputs."""

from __future__ import annotations

import os
from pathlib import Path

MPL_CACHE_DIR = Path(__file__).resolve().parent / ".mpl_cache"
MPL_CACHE_DIR.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE_DIR))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from hw_1.reporting import equity_curve


def _wealth_index(return_series: pd.Series, start_value: float = 1.0) -> pd.Series:
    clean = return_series.fillna(0.0).sort_index()
    return start_value * (1.0 + clean).cumprod()


def plot_equity_curves(
    data: pd.DataFrame,
    result_map: dict[str, dict],
    output_dir: str | Path,
) -> Path:
    """Save cumulative performance comparison plot."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(14, 7))

    benchmark_curve = _wealth_index(data["daily_return"])
    ax.plot(
        benchmark_curve.index,
        benchmark_curve.values,
        label="Buy & Hold",
        linewidth=2.4,
        color="#1f77b4",
    )

    palette = {
        "Trend Following": "#d62728",
        "Mean Reversion": "#2ca02c",
    }

    for name, result in result_map.items():
        strategy_curve = _wealth_index(equity_curve(result))
        ax.plot(
            strategy_curve.index,
            strategy_curve.values,
            label=name,
            linewidth=2.0,
            color=palette.get(name),
        )

    symbol_label = data.attrs.get("downloaded_symbol", data.attrs.get("requested_symbol", "BIST100"))
    ax.set_title(f"BIST100 Strategy Equity Curves ({symbol_label})")
    ax.set_xlabel("Date")
    ax.set_ylabel("Growth of 1 TRY")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    save_path = output_path / "equity_curves.png"
    fig.savefig(save_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return save_path


def plot_trade_signals(
    data: pd.DataFrame,
    result_map: dict[str, dict],
    output_dir: str | Path,
) -> Path:
    """Save price plot with strategy entry/exit markers."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    strategy_order = list(result_map.keys())
    fig_height = max(5, 4 * len(strategy_order))
    fig, axes = plt.subplots(len(strategy_order), 1, figsize=(14, fig_height), sharex=True)
    if len(strategy_order) == 1:
        axes = [axes]

    for ax, strategy_name in zip(axes, strategy_order):
        ax.plot(data.index, data["Close"], color="#222222", linewidth=1.2, label="BIST100 Close")

        trades = result_map[strategy_name]["strategy"].trade_frame().copy()
        if not trades.empty:
            entries = pd.to_datetime(trades["entry_date"])
            exits = pd.to_datetime(trades["exit_date"])
            entry_prices = data.reindex(entries)["Close"]
            exit_prices = data.reindex(exits)["Close"]

            ax.scatter(
                entries,
                entry_prices,
                marker="^",
                s=70,
                color="#2ca02c",
                label="Buy",
                zorder=5,
            )
            ax.scatter(
                exits,
                exit_prices,
                marker="v",
                s=70,
                color="#d62728",
                label="Sell",
                zorder=5,
            )

        ax.set_title(strategy_name)
        ax.set_ylabel("Index Level")
        ax.grid(True, alpha=0.3)
        ax.legend()

    axes[-1].set_xlabel("Date")
    fig.suptitle("BIST100 Price with Strategy Signals", fontsize=14)
    fig.tight_layout()

    save_path = output_path / "trade_signals.png"
    fig.savefig(save_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return save_path


def save_plots(
    data: pd.DataFrame,
    result_map: dict[str, dict],
    output_dir: str | Path,
) -> list[Path]:
    """Generate all output plots."""

    return [
        plot_equity_curves(data=data, result_map=result_map, output_dir=output_dir),
        plot_trade_signals(data=data, result_map=result_map, output_dir=output_dir),
    ]
