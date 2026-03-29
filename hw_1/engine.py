"""Backtesting engine helpers."""

from __future__ import annotations

from typing import Any

import backtrader as bt
import pandas as pd

from hw_1.config import BacktestConfig
from hw_1.data import BIST100Data


def build_cerebro(
    data: pd.DataFrame,
    strategy_class: type[bt.Strategy],
    config: BacktestConfig,
    **strategy_params: Any,
) -> bt.Cerebro:
    """Create a configured Cerebro instance."""

    cerebro = bt.Cerebro()
    cerebro.adddata(BIST100Data(dataname=data))
    cerebro.addstrategy(strategy_class, printlog=config.printlog, **strategy_params)
    cerebro.broker.setcash(config.initial_cash)
    cerebro.broker.setcommission(commission=config.commission)
    cerebro.addsizer(bt.sizers.PercentSizer, percents=config.allocation_pct)

    cerebro.addanalyzer(
        bt.analyzers.SharpeRatio,
        _name="sharpe",
        riskfreerate=0.0,
        timeframe=bt.TimeFrame.Days,
    )
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="time_return")
    return cerebro


def run_strategy(
    data: pd.DataFrame,
    strategy_class: type[bt.Strategy],
    config: BacktestConfig,
    **strategy_params: Any,
) -> dict[str, Any]:
    """Run a single strategy and return the full result bundle."""

    cerebro = build_cerebro(data=data, strategy_class=strategy_class, config=config, **strategy_params)
    results = cerebro.run()
    strategy = results[0]
    return {
        "cerebro": cerebro,
        "strategy": strategy,
        "final_value": cerebro.broker.getvalue(),
        "strategy_params": strategy_params,
    }

