"""Result extraction and persistence utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def _safe_get(mapping: Any, *keys: str, default: float = 0.0) -> float:
    current = mapping
    for key in keys:
        if current is None:
            return default
        if isinstance(current, dict):
            current = current.get(key)
        else:
            try:
                current = getattr(current, key)
            except (AttributeError, KeyError):
                return default
    return default if current is None else current


def _annualized_volatility(return_series: pd.Series, trading_days: int = 252) -> float:
    clean = pd.Series(return_series).dropna()
    if clean.empty:
        return 0.0
    return float(clean.std(ddof=1) * (trading_days ** 0.5) * 100.0)


def summarize_benchmark(data: pd.DataFrame, strategy_label: str = "Buy & Hold") -> dict[str, float | str]:
    returns = data["daily_return"].dropna()
    total_return = float(data["Close"].iloc[-1] / data["Close"].iloc[0] - 1.0) * 100.0
    annual_return = float(((1.0 + total_return / 100.0) ** (252 / max(len(returns), 1)) - 1.0) * 100.0)
    annual_vol = _annualized_volatility(returns)
    sharpe = (annual_return / annual_vol) if annual_vol else 0.0
    wealth = (1.0 + returns.fillna(0.0)).cumprod()
    running_max = wealth.cummax()
    drawdown = ((wealth / running_max) - 1.0) * 100.0

    return {
        "strategy": strategy_label,
        "entry_run": None,
        "exit_run": None,
        "final_value": float("nan"),
        "total_return_pct": total_return,
        "annual_return_pct": annual_return,
        "annualized_volatility_pct": annual_vol,
        "sharpe_ratio": sharpe,
        "max_drawdown_pct": abs(float(drawdown.min())) if not drawdown.empty else 0.0,
        "closed_trades": 0,
        "win_rate_pct": float("nan"),
        "buy_hold_return_pct": total_return,
    }


def summarize_result(
    name: str,
    result: dict[str, Any],
    buy_hold_total_return: float,
) -> dict[str, Any]:
    """Convert analyzer output into a flat summary row."""

    strategy = result["strategy"]
    sharpe = strategy.analyzers.sharpe.get_analysis()
    drawdown = strategy.analyzers.drawdown.get_analysis()
    returns = strategy.analyzers.returns.get_analysis()
    trades = strategy.analyzers.trades.get_analysis()
    annual_volatility = _annualized_volatility(equity_curve(result))

    total_trades = int(_safe_get(trades, "total", "closed", default=0.0))
    won_trades = int(_safe_get(trades, "won", "total", default=0.0))

    sharpe_ratio = sharpe.get("sharperatio") if isinstance(sharpe, dict) else None
    win_rate = (won_trades / total_trades * 100.0) if total_trades else 0.0

    return {
        "strategy": name,
        "entry_run": result["strategy_params"].get("entry_run"),
        "exit_run": result["strategy_params"].get("exit_run"),
        "final_value": result["final_value"],
        "total_return_pct": returns.get("rtot", 0.0) * 100.0,
        "annual_return_pct": returns.get("rnorm", 0.0) * 100.0,
        "annualized_volatility_pct": annual_volatility,
        "sharpe_ratio": sharpe_ratio if sharpe_ratio is not None else float("nan"),
        "max_drawdown_pct": _safe_get(drawdown, "max", "drawdown", default=0.0),
        "closed_trades": total_trades,
        "win_rate_pct": win_rate,
        "buy_hold_return_pct": buy_hold_total_return * 100.0,
    }


def equity_curve(result: dict[str, Any]) -> pd.Series:
    """Extract strategy daily returns as a time series."""

    series = pd.Series(result["strategy"].analyzers.time_return.get_analysis()).sort_index()
    series.index = pd.to_datetime(series.index)
    series.name = "strategy_return"
    return series


def save_outputs(
    summary: pd.DataFrame,
    result_map: dict[str, dict[str, Any]],
    output_dir: str | Path,
    benchmark_summary: dict[str, float | str] | None = None,
) -> Path:
    """Persist summary, trade logs, and equity curves."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    summary.to_csv(output_path / "strategy_summary.csv", index=False)
    if benchmark_summary is not None:
        pd.DataFrame([benchmark_summary]).to_csv(output_path / "benchmark_summary.csv", index=False)

    for strategy_name, result in result_map.items():
        slug = strategy_name.lower().replace(" ", "_")
        trade_frame = result["strategy"].trade_frame()
        signal_frame = result["strategy"].signal_frame()

        trade_frame.to_csv(output_path / f"{slug}_trades.csv", index=False)
        signal_frame.to_csv(output_path / f"{slug}_signals.csv", index=False)
        curve = equity_curve(result)
        curve.to_frame().to_csv(output_path / f"{slug}_daily_returns.csv")
    _write_performance_summary_csv(
        output_path=output_path,
        summary=summary,
        benchmark_summary=benchmark_summary,
    )

    return output_path


def _write_performance_summary_csv(
    output_path: Path,
    summary: pd.DataFrame,
    benchmark_summary: dict[str, float | str] | None = None,
) -> None:
    frames = []
    if benchmark_summary is not None:
        benchmark_frame = pd.DataFrame([benchmark_summary]).assign(category="benchmark")
        frames.append(benchmark_frame)

    strategy_frame = summary.copy()
    strategy_frame["category"] = "strategy"
    frames.append(strategy_frame)

    combined = pd.concat(frames, ignore_index=True, sort=False)
    combined = combined[
        [
            "category",
            "strategy",
            "entry_run",
            "exit_run",
            "total_return_pct",
            "annual_return_pct",
            "annualized_volatility_pct",
            "sharpe_ratio",
            "max_drawdown_pct",
            "closed_trades",
            "win_rate_pct",
            "buy_hold_return_pct",
        ]
    ]
    combined.to_csv(output_path / "performance_summary.csv", index=False)
