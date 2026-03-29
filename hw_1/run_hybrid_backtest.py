"""CLI entry point for the hybrid trend-filtered mean-reversion strategy."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from hw_1.config import BacktestConfig
from hw_1.data import download_bist100_data
from hw_1.engine import run_strategy
from hw_1.plots import save_plots
from hw_1.reporting import save_outputs, summarize_benchmark, summarize_result
from hw_1.strategies import HybridTrendMeanReversionStrategy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the hybrid trend-filtered mean-reversion strategy on BIST100."
    )
    parser.add_argument("--start", default="2010-01-01", help="Backtest start date (YYYY-MM-DD)")
    parser.add_argument("--end", default=None, help="Backtest end date (YYYY-MM-DD)")
    parser.add_argument("--cash", type=float, default=100_000.0, help="Initial cash")
    parser.add_argument("--commission", type=float, default=0.001, help="Commission rate")
    parser.add_argument("--allocation", type=float, default=95.0, help="Portfolio allocation percent")
    parser.add_argument("--entry-run", type=int, default=3, help="Buy after n consecutive negative returns")
    parser.add_argument("--exit-run", type=int, default=2, help="Sell after m consecutive days below long SMA")
    parser.add_argument("--trend-period", type=int, default=200, help="Long-term SMA period")
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
    return (
        f"hybrid__start_{args.start}"
        f"__end_{end_label}"
        f"__n{args.entry_run}"
        f"__m{args.exit_run}"
        f"__trend{args.trend_period}"
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
    benchmark_summary = summarize_benchmark(data)
    used_symbol = data.attrs.get("downloaded_symbol", config.symbol)

    result = run_strategy(
        data=data,
        strategy_class=HybridTrendMeanReversionStrategy,
        config=config,
        entry_run=args.entry_run,
        exit_run=args.exit_run,
        trend_period=args.trend_period,
    )
    summary_row = summarize_result(
        name="Hybrid Trend-Filtered Mean Reversion",
        result=result,
        buy_hold_total_return=benchmark_summary["buy_hold_return_pct"] / 100.0,
    )
    summary = pd.DataFrame([summary_row])

    save_path = save_outputs(
        summary=summary,
        result_map={"Hybrid Trend-Filtered Mean Reversion": result},
        output_dir=run_output_dir,
        benchmark_summary=benchmark_summary,
    )
    plot_paths = save_plots(
        data=data,
        result_map={"Hybrid Trend-Filtered Mean Reversion": result},
        output_dir=run_output_dir,
    )

    pd.set_option("display.float_format", lambda value: f"{value:,.2f}")
    print("\nBIST100 Hybrid Strategy")
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

