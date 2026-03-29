"""Backtrader strategies for consecutive-return signals."""

from __future__ import annotations

import backtrader as bt
import pandas as pd


class BaseConsecutiveReturnStrategy(bt.Strategy):
    """Base class that tracks consecutive positive/negative return runs."""

    params = dict(
        entry_run=3,
        exit_run=2,
        printlog=False,
    )

    def __init__(self) -> None:
        self.order = None
        self.positive_run = 0
        self.negative_run = 0
        self.entry_size = 0
        self.trade_log: list[dict[str, object]] = []
        self.signal_log: list[dict[str, object]] = []
        self.signal_counter = 0
        self.current_trade_entry_signal_id: int | None = None
        self.current_trade_exit_signal_id: int | None = None

    def log(self, message: str) -> None:
        if self.p.printlog:
            print(f"{self.data.datetime.date(0)}: {message}")

    def notify_order(self, order: bt.Order) -> None:
        if order.status in [order.Submitted, order.Accepted]:
            return

        signal_id = getattr(order.info, "signal_id", None)

        if order.status == order.Completed:
            action = "BUY" if order.isbuy() else "SELL"
            self.log(
                f"{action} @ {order.executed.price:.2f} "
                f"Size={order.executed.size:.0f}"
            )
            if order.isbuy():
                self.entry_size = abs(int(order.executed.size))
                self.current_trade_entry_signal_id = signal_id
            else:
                self.current_trade_exit_signal_id = signal_id
            self._update_signal_record(
                signal_id,
                order_status="completed",
                execution_date=self.data.datetime.date(0),
                execution_price=order.executed.price,
                execution_size=order.executed.size,
                execution_action=action,
            )
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order canceled/margin/rejected")
            self._update_signal_record(
                signal_id,
                order_status=str(order.getstatusname()).lower(),
            )

        self.order = None

    def notify_trade(self, trade: bt.Trade) -> None:
        if not trade.isclosed:
            return

        entry_value = trade.price * max(self.entry_size, 1)
        trade_record = {
            "entry_date": bt.num2date(trade.dtopen).date(),
            "exit_date": bt.num2date(trade.dtclose).date(),
            "bars_held": trade.barlen,
            "pnl": trade.pnl,
            "pnl_net": trade.pnlcomm,
            "return_pct": (trade.pnlcomm / entry_value * 100.0) if entry_value else 0.0,
            "entry_signal_id": self.current_trade_entry_signal_id,
            "exit_signal_id": self.current_trade_exit_signal_id,
        }
        self.trade_log.append(trade_record)
        feedback = "positive" if trade.pnlcomm > 0 else "negative" if trade.pnlcomm < 0 else "flat"
        self._update_signal_record(
            self.current_trade_entry_signal_id,
            resulting_trade_entry_date=trade_record["entry_date"],
            resulting_trade_exit_date=trade_record["exit_date"],
            resulting_trade_pnl=trade_record["pnl"],
            resulting_trade_pnl_net=trade_record["pnl_net"],
            resulting_trade_return_pct=trade_record["return_pct"],
            resulting_trade_feedback=feedback,
        )
        self._update_signal_record(
            self.current_trade_exit_signal_id,
            resulting_trade_entry_date=trade_record["entry_date"],
            resulting_trade_exit_date=trade_record["exit_date"],
            resulting_trade_pnl=trade_record["pnl"],
            resulting_trade_pnl_net=trade_record["pnl_net"],
            resulting_trade_return_pct=trade_record["return_pct"],
            resulting_trade_feedback=feedback,
        )
        self.log(f"TRADE CLOSED: PnL={trade.pnl:.2f}, Net={trade.pnlcomm:.2f}")
        self.current_trade_entry_signal_id = None
        self.current_trade_exit_signal_id = None

    def next(self) -> None:
        if self.order:
            return

        daily_return = float(self.data.daily_return[0])

        if daily_return > 0:
            self.positive_run += 1
            self.negative_run = 0
        elif daily_return < 0:
            self.negative_run += 1
            self.positive_run = 0
        else:
            self.positive_run = 0
            self.negative_run = 0

        if not self.position and self.should_enter():
            reason = self.entry_reason()
            signal_id = self.record_signal("entry", "buy", reason)
            self.log(f"ENTRY SIGNAL | {reason}")
            self.order = self.buy()
            self.order.addinfo(signal_id=signal_id)
        elif self.position and self.should_exit():
            reason = self.exit_reason()
            signal_id = self.record_signal("exit", "sell", reason)
            self.log(f"EXIT SIGNAL | {reason}")
            self.order = self.close()
            self.order.addinfo(signal_id=signal_id)

    def trade_frame(self) -> pd.DataFrame:
        if not self.trade_log:
            return pd.DataFrame(
                columns=[
                    "entry_date",
                    "exit_date",
                    "bars_held",
                    "pnl",
                    "pnl_net",
                    "return_pct",
                    "entry_signal_id",
                    "exit_signal_id",
                ]
            )
        return pd.DataFrame(self.trade_log)

    def signal_frame(self) -> pd.DataFrame:
        if not self.signal_log:
            return pd.DataFrame(
                columns=[
                    "signal_id",
                    "signal_date",
                    "signal_type",
                    "action",
                    "reason",
                    "daily_return",
                    "positive_run",
                    "negative_run",
                    "order_status",
                    "execution_date",
                    "execution_price",
                    "execution_size",
                    "execution_action",
                    "resulting_trade_entry_date",
                    "resulting_trade_exit_date",
                    "resulting_trade_pnl",
                    "resulting_trade_pnl_net",
                    "resulting_trade_return_pct",
                    "resulting_trade_feedback",
                ]
            )
        return pd.DataFrame(self.signal_log)

    def record_signal(self, signal_type: str, action: str, reason: str) -> int:
        self.signal_counter += 1
        self.signal_log.append(
            {
                "signal_id": self.signal_counter,
                "signal_date": self.data.datetime.date(0),
                "signal_type": signal_type,
                "action": action,
                "reason": reason,
                "daily_return": float(self.data.daily_return[0]),
                "positive_run": self.positive_run,
                "negative_run": self.negative_run,
                "order_status": "created",
                "execution_date": None,
                "execution_price": None,
                "execution_size": None,
                "execution_action": None,
                "resulting_trade_entry_date": None,
                "resulting_trade_exit_date": None,
                "resulting_trade_pnl": None,
                "resulting_trade_pnl_net": None,
                "resulting_trade_return_pct": None,
                "resulting_trade_feedback": None,
            }
        )
        return self.signal_counter

    def _update_signal_record(self, signal_id: int | None, **updates: object) -> None:
        if signal_id is None:
            return
        for record in self.signal_log:
            if record["signal_id"] == signal_id:
                record.update(updates)
                break

    def entry_reason(self) -> str:
        return (
            f"{self.p.entry_run} consecutive signal days reached | "
            f"pos_run={self.positive_run}, neg_run={self.negative_run}"
        )

    def exit_reason(self) -> str:
        return (
            f"{self.p.exit_run} consecutive opposite-signal days reached | "
            f"pos_run={self.positive_run}, neg_run={self.negative_run}"
        )

    def should_enter(self) -> bool:
        raise NotImplementedError

    def should_exit(self) -> bool:
        raise NotImplementedError


class TrendFollowingStrategy(BaseConsecutiveReturnStrategy):
    """
    Buy after n consecutive positive-return days.
    Sell after m consecutive negative-return days.
    """

    def should_enter(self) -> bool:
        return self.positive_run >= self.p.entry_run

    def should_exit(self) -> bool:
        return self.negative_run >= self.p.exit_run

    def entry_reason(self) -> str:
        return (
            f"Buy because there were {self.positive_run} consecutive positive return days "
            f"(threshold n={self.p.entry_run})."
        )

    def exit_reason(self) -> str:
        return (
            f"Sell because there were {self.negative_run} consecutive negative return days "
            f"(threshold m={self.p.exit_run})."
        )


class MeanReversionStrategy(BaseConsecutiveReturnStrategy):
    """
    Buy after n consecutive negative-return days.
    Sell after m consecutive positive-return days.
    """

    def should_enter(self) -> bool:
        return self.negative_run >= self.p.entry_run

    def should_exit(self) -> bool:
        return self.positive_run >= self.p.exit_run

    def entry_reason(self) -> str:
        return (
            f"Buy because there were {self.negative_run} consecutive negative return days "
            f"(threshold n={self.p.entry_run})."
        )

    def exit_reason(self) -> str:
        return (
            f"Sell because there were {self.positive_run} consecutive positive return days "
            f"(threshold m={self.p.exit_run})."
        )


class HybridTrendMeanReversionStrategy(BaseConsecutiveReturnStrategy):
    """
    Hybrid strategy:
    - Long-term regime filter: close > SMA(trend_period)
    - Entry: n consecutive negative-return days while the long-term trend is up
    - Exit: m consecutive days below the long-term SMA
    """

    params = dict(
        entry_run=3,
        exit_run=2,
        trend_period=200,
        printlog=False,
    )

    def __init__(self) -> None:
        super().__init__()
        self.long_sma = bt.indicators.SimpleMovingAverage(
            self.data.close,
            period=self.p.trend_period,
        )
        self.downtrend_run = 0

    def next(self) -> None:
        if self.order:
            return

        daily_return = float(self.data.daily_return[0])

        if daily_return > 0:
            self.positive_run += 1
            self.negative_run = 0
        elif daily_return < 0:
            self.negative_run += 1
            self.positive_run = 0
        else:
            self.positive_run = 0
            self.negative_run = 0

        if self.data.close[0] > self.long_sma[0]:
            self.downtrend_run = 0
        elif self.data.close[0] < self.long_sma[0]:
            self.downtrend_run += 1

        if not self.position and self.should_enter():
            reason = self.entry_reason()
            signal_id = self.record_signal("entry", "buy", reason)
            self.log(f"ENTRY SIGNAL | {reason}")
            self.order = self.buy()
            self.order.addinfo(signal_id=signal_id)
        elif self.position and self.should_exit():
            reason = self.exit_reason()
            signal_id = self.record_signal("exit", "sell", reason)
            self.log(f"EXIT SIGNAL | {reason}")
            self.order = self.close()
            self.order.addinfo(signal_id=signal_id)

    def should_enter(self) -> bool:
        return self.data.close[0] > self.long_sma[0] and self.negative_run >= self.p.entry_run

    def should_exit(self) -> bool:
        return self.downtrend_run >= self.p.exit_run

    def entry_reason(self) -> str:
        return (
            f"Buy because the long-term trend is up (Close={self.data.close[0]:.2f} > "
            f"SMA({self.p.trend_period})={self.long_sma[0]:.2f}) and there were "
            f"{self.negative_run} consecutive negative return days (threshold n={self.p.entry_run})."
        )

    def exit_reason(self) -> str:
        return (
            f"Sell because price stayed below SMA({self.p.trend_period}) for "
            f"{self.downtrend_run} consecutive days (threshold m={self.p.exit_run})."
        )
