"""Grid-search optimization for the hybrid trend-filtered mean-reversion strategy."""

from __future__ import annotations

import argparse
from itertools import product
from pathlib import Path

import pandas as pd

from hw_1.config import BacktestConfig
from hw_1.data import download_bist100_data
from hw_1.engine import run_strategy
from hw_1.reporting import summarize_benchmark, summarize_result
from hw_1.strategies import HybridTrendMeanReversionStrategy

METRIC_DIRECTIONS = {
    "total_return_pct": "max",
    "annual_return_pct": "max",
    "annualized_volatility_pct": "min",
    "sharpe_ratio": "max",
    "max_drawdown_pct": "min",
}

OPTIMIZATION_METRICS = list(METRIC_DIRECTIONS.keys())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Optimize n and m parameters for the hybrid BIST100 strategy."
    )
    parser.add_argument("--start", default="2010-01-01", help="Backtest start date (YYYY-MM-DD)")
    parser.add_argument("--end", default=None, help="Backtest end date (YYYY-MM-DD)")
    parser.add_argument("--cash", type=float, default=100_000.0, help="Initial cash")
    parser.add_argument("--commission", type=float, default=0.001, help="Commission rate")
    parser.add_argument("--allocation", type=float, default=95.0, help="Portfolio allocation percent")
    parser.add_argument("--n-min", type=int, default=1, help="Minimum n value")
    parser.add_argument("--n-max", type=int, default=10, help="Maximum n value")
    parser.add_argument("--m-min", type=int, default=1, help="Minimum m value")
    parser.add_argument("--m-max", type=int, default=10, help="Maximum m value")
    parser.add_argument("--trend-period", type=int, default=200, help="Single long-term SMA period")
    parser.add_argument(
        "--trend-periods",
        default=None,
        help="Comma-separated list of long-term SMA periods for optimization, e.g. 50,100,150,200",
    )
    parser.add_argument(
        "--objective",
        default="sharpe_ratio",
        choices=sorted(METRIC_DIRECTIONS),
        help="Metric used for the main optimized comparison",
    )
    parser.add_argument("--output-dir", default="hw_1/output", help="Directory for CSV outputs")
    parser.add_argument("--label", default=None, help="Optional custom run label")
    parser.add_argument("--printlog", action="store_true", help="Print order and trade logs")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> BacktestConfig:
    return BacktestConfig(
        start=args.start,
        end=args.end,
        initial_cash=args.cash,
        commission=args.commission,
        allocation_pct=args.allocation,
        printlog=args.printlog,
    )


def build_run_label(args: argparse.Namespace) -> str:
    if args.label:
        return args.label

    end_label = args.end or "latest"
    periods = parse_trend_periods(args)
    if len(periods) == 1:
        trend_label = f"trend{periods[0]}"
    else:
        trend_label = f"trend{'-'.join(str(value) for value in periods)}"
    return (
        f"hybrid_optimization__start_{args.start}"
        f"__end_{end_label}"
        f"__n_{args.n_min}_{args.n_max}"
        f"__m_{args.m_min}_{args.m_max}"
        f"__{trend_label}"
        f"__objective_{args.objective}"
    )


def parse_trend_periods(args: argparse.Namespace) -> list[int]:
    if args.trend_periods:
        values = [int(part.strip()) for part in args.trend_periods.split(",") if part.strip()]
        unique_values = sorted(set(values))
        if not unique_values:
            raise ValueError("No valid trend periods provided.")
        return unique_values
    return [args.trend_period]


def metric_sort_ascending(metric: str) -> bool:
    return METRIC_DIRECTIONS[metric] == "min"


def build_metric_grid(frame: pd.DataFrame, metric: str) -> pd.DataFrame:
    grid = frame.pivot(index="entry_run", columns="exit_run", values=metric)
    return grid.sort_index().sort_index(axis=1)


def best_row_for_metric(frame: pd.DataFrame, metric: str) -> pd.Series:
    ascending = metric_sort_ascending(metric)
    sorted_frame = frame.sort_values(
        by=[metric, "entry_run", "exit_run"],
        ascending=[ascending, True, True],
    )
    return sorted_frame.iloc[0]


def save_outputs(
    output_dir: Path,
    results_frame: pd.DataFrame,
    benchmark_summary: dict[str, float | str],
    objective: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    results_frame = results_frame.sort_values(["trend_period", "entry_run", "exit_run"]).reset_index(drop=True)
    results_frame.to_csv(output_dir / "hybrid_optimization_results.csv", index=False)
    pd.DataFrame([benchmark_summary]).to_csv(output_dir / "benchmark_summary.csv", index=False)

    best_rows: list[dict[str, object]] = []
    multi_period = results_frame["trend_period"].nunique() > 1
    for metric in OPTIMIZATION_METRICS:
        for trend_period, period_frame in results_frame.groupby("trend_period", sort=True):
            grid = build_metric_grid(period_frame, metric)
            if multi_period:
                filename = f"hybrid_trend_{trend_period}_{metric}_grid.csv"
            else:
                filename = f"hybrid_{metric}_grid.csv"
            grid.to_csv(output_dir / filename)

        best = best_row_for_metric(results_frame, metric)
        best_rows.append(
            {
                "metric": metric,
                "selection_rule": METRIC_DIRECTIONS[metric],
                "trend_period": int(best["trend_period"]),
                "best_entry_run_n": int(best["entry_run"]),
                "best_exit_run_m": int(best["exit_run"]),
                "metric_value": float(best[metric]),
                "total_return_pct": float(best["total_return_pct"]),
                "annual_return_pct": float(best["annual_return_pct"]),
                "annualized_volatility_pct": float(best["annualized_volatility_pct"]),
                "sharpe_ratio": float(best["sharpe_ratio"]),
                "max_drawdown_pct": float(best["max_drawdown_pct"]),
                "closed_trades": int(best["closed_trades"]),
                "win_rate_pct": float(best["win_rate_pct"]),
            }
        )

    best_frame = pd.DataFrame(best_rows).sort_values("metric").reset_index(drop=True)
    best_frame.to_csv(output_dir / "hybrid_best_params_by_metric.csv", index=False)

    objective_best = best_row_for_metric(results_frame, objective)
    pd.DataFrame(
        [
            {
                "strategy": "Hybrid Trend-Filtered Mean Reversion",
                "objective_metric": objective,
                "objective_rule": METRIC_DIRECTIONS[objective],
                "trend_period": int(objective_best["trend_period"]),
                "best_entry_run_n": int(objective_best["entry_run"]),
                "best_exit_run_m": int(objective_best["exit_run"]),
                "objective_value": float(objective_best[objective]),
                "total_return_pct": float(objective_best["total_return_pct"]),
                "annual_return_pct": float(objective_best["annual_return_pct"]),
                "annualized_volatility_pct": float(objective_best["annualized_volatility_pct"]),
                "sharpe_ratio": float(objective_best["sharpe_ratio"]),
                "max_drawdown_pct": float(objective_best["max_drawdown_pct"]),
                "closed_trades": int(objective_best["closed_trades"]),
                "win_rate_pct": float(objective_best["win_rate_pct"]),
            }
        ]
    ).to_csv(output_dir / "hybrid_optimized_summary.csv", index=False)


def main() -> None:
    args = parse_args()
    config = build_config(args)
    run_label = build_run_label(args)
    output_dir = Path(args.output_dir) / run_label
    trend_periods = parse_trend_periods(args)

    data = download_bist100_data(
        symbol=config.symbol,
        start=config.start,
        end=config.end,
    )
    used_symbol = data.attrs.get("downloaded_symbol", config.symbol)
    benchmark_summary = summarize_benchmark(data)

    rows: list[dict[str, object]] = []
    for trend_period, n_value, m_value in product(
        trend_periods,
        range(args.n_min, args.n_max + 1),
        range(args.m_min, args.m_max + 1),
    ):
        result = run_strategy(
            data=data,
            strategy_class=HybridTrendMeanReversionStrategy,
            config=config,
            entry_run=n_value,
            exit_run=m_value,
            trend_period=trend_period,
        )
        row = summarize_result(
            name="Hybrid Trend-Filtered Mean Reversion",
            result=result,
            buy_hold_total_return=benchmark_summary["buy_hold_return_pct"] / 100.0,
        )
        row["trend_period"] = trend_period
        rows.append(row)

    results_frame = pd.DataFrame(rows)
    save_outputs(
        output_dir=output_dir,
        results_frame=results_frame,
        benchmark_summary=benchmark_summary,
        objective=args.objective,
    )
    optimized = pd.read_csv(output_dir / "hybrid_optimized_summary.csv")

    pd.set_option("display.float_format", lambda value: f"{value:,.2f}")
    print("\nBIST100 Hybrid Strategy Optimization")
    print("=" * 80)
    print(f"Requested symbol: {config.symbol} | Downloaded symbol: {used_symbol}")
    print(f"Run label: {run_label}")
    print(f"Trend periods: {', '.join(str(value) for value in trend_periods)}")
    print(f"Objective metric: {args.objective} ({METRIC_DIRECTIONS[args.objective]})")
    print(f"Grid: n={args.n_min}..{args.n_max}, m={args.m_min}..{args.m_max}")
    print("\nOptimized summary")
    print(optimized.to_string(index=False))
    print(f"\nOutputs saved to: {output_dir}")


if __name__ == "__main__":
    main()
