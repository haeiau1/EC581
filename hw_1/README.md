# HW1 Scripts

This file lists the scripts used in `hw_1`, the commands to run them, the main outputs they generate, and the folders where those outputs are saved.

## 1. Manual Backtest: Trend Following + Mean Reversion

Command:

```bash
python -m hw_1.run_backtests \
  --start 1997-07-01 \
  --end 2026-03-27 \
  --trend-entry 3 \
  --trend-exit 2 \
  --mean-entry 4 \
  --mean-exit 1
```

Output folder:

```text
hw_1/output/start_1997-07-01__end_2026-03-27__trend_n3_m2__mean_n4_m1/
```

Main outputs:

- `strategy_summary.csv`
- `benchmark_summary.csv`
- `performance_summary.csv`
- `trend_following_trades.csv`
- `trend_following_signals.csv`
- `trend_following_daily_returns.csv`
- `mean_reversion_trades.csv`
- `mean_reversion_signals.csv`
- `mean_reversion_daily_returns.csv`
- `equity_curves.png`
- `trade_signals.png`

## 2. Short Sample Manual Backtest: Trend Following + Mean Reversion

Command:

```bash
python -m hw_1.run_backtests \
  --start 2024-01-01 \
  --end 2026-03-27 \
  --trend-entry 3 \
  --trend-exit 2 \
  --mean-entry 4 \
  --mean-exit 1
```

Output folder:

```text
hw_1/output/start_2024-01-01__end_2026-03-27__trend_n3_m2__mean_n4_m1/
```

Main outputs:

- `strategy_summary.csv`
- `benchmark_summary.csv`
- `performance_summary.csv`
- `trend_following_trades.csv`
- `trend_following_signals.csv`
- `trend_following_daily_returns.csv`
- `mean_reversion_trades.csv`
- `mean_reversion_signals.csv`
- `mean_reversion_daily_returns.csv`
- `equity_curves.png`
- `trade_signals.png`

## 3. Optimization: Trend Following + Mean Reversion

Command:

```bash
python -m hw_1.optimize_strategies \
  --start 1997-07-01 \
  --end 2026-03-27 \
  --n-min 1 \
  --n-max 10 \
  --m-min 1 \
  --m-max 10 \
  --objective sharpe_ratio
```

Output folder:

```text
hw_1/output/optimization__start_1997-07-01__end_2026-03-27__n_1_10__m_1_10__objective_sharpe_ratio/
```

Main outputs:

- `optimization_results.csv`
- `trend_following_optimization_results.csv`
- `mean_reversion_optimization_results.csv`
- `trend_following_total_return_pct_grid.csv`
- `trend_following_annual_return_pct_grid.csv`
- `trend_following_annualized_volatility_pct_grid.csv`
- `trend_following_sharpe_ratio_grid.csv`
- `trend_following_max_drawdown_pct_grid.csv`
- `mean_reversion_total_return_pct_grid.csv`
- `mean_reversion_annual_return_pct_grid.csv`
- `mean_reversion_annualized_volatility_pct_grid.csv`
- `mean_reversion_sharpe_ratio_grid.csv`
- `mean_reversion_max_drawdown_pct_grid.csv`
- `best_params_by_metric.csv`
- `optimized_strategy_comparison.csv`
- `benchmark_summary.csv`

## 4. Manual Hybrid Backtest

Command:

```bash
python -m hw_1.run_hybrid_backtest \
  --start 1997-07-01 \
  --end 2026-03-27 \
  --entry-run 1 \
  --exit-run 4 \
  --trend-period 100
```

Output folder:

```text
hw_1/output/hybrid__start_1997-07-01__end_2026-03-27__n1__m4__trend100/
```

Main outputs:

- `strategy_summary.csv`
- `benchmark_summary.csv`
- `performance_summary.csv`
- `hybrid_trend-filtered_mean_reversion_trades.csv`
- `hybrid_trend-filtered_mean_reversion_signals.csv`
- `hybrid_trend-filtered_mean_reversion_daily_returns.csv`
- `equity_curves.png`
- `trade_signals.png`

## 5. Hybrid Optimization: Fixed Trend Period

Command:

```bash
python -m hw_1.optimize_hybrid_strategy \
  --start 1997-07-01 \
  --end 2026-03-27 \
  --n-min 1 \
  --n-max 10 \
  --m-min 1 \
  --m-max 10 \
  --trend-period 200 \
  --objective sharpe_ratio
```

Output folder:

```text
hw_1/output/hybrid_optimization__start_1997-07-01__end_2026-03-27__n_1_10__m_1_10__trend200__objective_sharpe_ratio/
```

Main outputs:

- `hybrid_optimization_results.csv`
- `hybrid_best_params_by_metric.csv`
- `hybrid_optimized_summary.csv`
- `hybrid_total_return_pct_grid.csv`
- `hybrid_annual_return_pct_grid.csv`
- `hybrid_annualized_volatility_pct_grid.csv`
- `hybrid_sharpe_ratio_grid.csv`
- `hybrid_max_drawdown_pct_grid.csv`
- `benchmark_summary.csv`

## 6. Hybrid Optimization: Variable Trend Period

Command:

```bash
python -m hw_1.optimize_hybrid_strategy \
  --start 1997-07-01 \
  --end 2026-03-27 \
  --n-min 1 \
  --n-max 10 \
  --m-min 1 \
  --m-max 10 \
  --trend-periods 50,100,150,200 \
  --objective sharpe_ratio
```

Output folder:

```text
hw_1/output/hybrid_optimization__start_1997-07-01__end_2026-03-27__n_1_10__m_1_10__trend50-100-150-200__objective_sharpe_ratio/
```

Main outputs:

- `hybrid_optimization_results.csv`
- `hybrid_best_params_by_metric.csv`
- `hybrid_optimized_summary.csv`
- `hybrid_trend_50_total_return_pct_grid.csv`
- `hybrid_trend_50_annual_return_pct_grid.csv`
- `hybrid_trend_50_annualized_volatility_pct_grid.csv`
- `hybrid_trend_50_sharpe_ratio_grid.csv`
- `hybrid_trend_50_max_drawdown_pct_grid.csv`
- `hybrid_trend_100_total_return_pct_grid.csv`
- `hybrid_trend_100_annual_return_pct_grid.csv`
- `hybrid_trend_100_annualized_volatility_pct_grid.csv`
- `hybrid_trend_100_sharpe_ratio_grid.csv`
- `hybrid_trend_100_max_drawdown_pct_grid.csv`
- `hybrid_trend_150_total_return_pct_grid.csv`
- `hybrid_trend_150_annual_return_pct_grid.csv`
- `hybrid_trend_150_annualized_volatility_pct_grid.csv`
- `hybrid_trend_150_sharpe_ratio_grid.csv`
- `hybrid_trend_150_max_drawdown_pct_grid.csv`
- `hybrid_trend_200_total_return_pct_grid.csv`
- `hybrid_trend_200_annual_return_pct_grid.csv`
- `hybrid_trend_200_annualized_volatility_pct_grid.csv`
- `hybrid_trend_200_sharpe_ratio_grid.csv`
- `hybrid_trend_200_max_drawdown_pct_grid.csv`
- `benchmark_summary.csv`

## Notes

- All scripts save their results under `hw_1/output/`.
- Each run creates a separate folder based on the selected dates and parameters.
- If `^XU100` does not return data, the scripts automatically try `XU100.IS`.
