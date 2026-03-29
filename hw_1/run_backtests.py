"""CLI entry point for the EC581 BIST100 homework."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from hw_1.config import BacktestConfig
from hw_1.data import buy_and_hold_return, download_bist100_data
from hw_1.engine import run_strategy
from hw_1.plots import save_plots
from hw_1.reporting import save_outputs, summarize_benchmark, summarize_result
from hw_1.strategies import MeanReversionStrategy, TrendFollowingStrategy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run consecutive-return strategies on BIST100 (^XU100)."
    )
    parser.add_argument("--start", default="2010-01-01", help="Backtest start date (YYYY-MM-DD)")
    parser.add_argument("--end", default=None, help="Backtest end date (YYYY-MM-DD)")
    parser.add_argument("--cash", type=float, default=100_000.0, help="Initial cash")
    parser.add_argument("--commission", type=float, default=0.001, help="Commission rate")
    parser.add_argument("--allocation", type=float, default=95.0, help="Portfolio allocation percent")
    parser.add_argument("--trend-entry", type=int, default=3, help="Trend following buy threshold")
    parser.add_argument("--trend-exit", type=int, default=2, help="Trend following sell threshold")
    parser.add_argument("--mean-entry", type=int, default=3, help="Mean reversion buy threshold")
    parser.add_argument("--mean-exit", type=int, default=2, help="Mean reversion sell threshold")
    parser.add_argument("--output-dir", default="hw_1/output", help="Directory for CSV outputs")
    parser.add_argument("--label", default=None, help="Optional custom run label for output naming")
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
    return (
        f"start_{args.start}"
        f"__end_{end_label}"
        f"__trend_n{args.trend_entry}_m{args.trend_exit}"
        f"__mean_n{args.mean_entry}_m{args.mean_exit}"
    )


def main() -> None:
    args = parse_args()
    config = build_config(args)
    run_label = build_run_label(args)
    run_output_dir = Path(args.output_dir) / run_label

    data = download_bist100_data(
        symbol=config.symbol,
        start=config.start,
        end=config.end,
    )
    benchmark_return = buy_and_hold_return(data)
    benchmark_summary = summarize_benchmark(data)
    used_symbol = data.attrs.get("downloaded_symbol", config.symbol)

    strategies = {
        "Trend Following": (
            TrendFollowingStrategy,
            {"entry_run": args.trend_entry, "exit_run": args.trend_exit},
        ),
        "Mean Reversion": (
            MeanReversionStrategy,
            {"entry_run": args.mean_entry, "exit_run": args.mean_exit},
        ),
    }

    results: dict[str, dict] = {}
    summary_rows: list[dict] = []

    for name, (strategy_class, strategy_params) in strategies.items():
        result = run_strategy(
            data=data,
            strategy_class=strategy_class,
            config=config,
            **strategy_params,
        )
        results[name] = result
        summary_rows.append(summarize_result(name, result, benchmark_return))

    summary = pd.DataFrame(summary_rows)
    save_path = save_outputs(
        summary,
        results,
        run_output_dir,
        benchmark_summary=benchmark_summary,
    )
    plot_paths = save_plots(
        data=data,
        result_map=results,
        output_dir=run_output_dir,
    )

    pd.set_option("display.float_format", lambda value: f"{value:,.2f}")
    print("\nBIST100 Strategy Comparison")
    print("=" * 80)
    print(f"Requested symbol: {config.symbol} | Downloaded symbol: {used_symbol}")
    print(f"Run label: {run_label}")
    print(summary.to_string(index=False))
    print(f"\nOutputs saved to: {save_path}")
    print("Generated plots:")
    for plot_path in plot_paths:
        print(f" - {plot_path}")


if __name__ == "__main__":
    main()
