# pragma pylint: disable=missing-docstring, invalid-name, too-many-arguments
"""
DailyTrend: frozen daily trend ensemble with volatility targeting (long/flat).

Freqtrade implementation of the rule pre-registered in user_data/NOTES.md
section 4j and tested with user_data/scripts/trend_backtest.py. Nothing here is
tuned; every number is the pre-registered one.

    s = mean( sign(r20), sign(r60), sign(r120), sign(close - SMA50) ),  exposure = max(s, 0)
    target notional = exposure * min(0.30 / vol30, 1.5) * equity

Computed on the daily close, executed at the next daily open (Freqtrade's normal
signal timing). Rebalances with adjust_trade_position only when the target moves by
at least 0.20 x equity; exposure 0 exits the whole position. No stops.

Run with --fee 0.0007 (taker 0.05% + 2 bp slippage) to match the simulation.
"""

from datetime import datetime

import numpy as np
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy


class DailyTrend(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1d"
    can_short = False
    startup_candle_count = 130  # 120-day return + 1, SMA50, vol30, with margin

    # Exits come only from the signal; disable ROI and set a stop that cannot trigger
    # before liquidation logic would.
    minimal_roi = {"0": 100.0}
    stoploss = -0.99
    trailing_stop = False
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = True

    position_adjustment_enable = True
    max_entry_position_adjustment = -1

    process_only_new_candles = True
    order_types = {
        "entry": "market",
        "exit": "market",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    # Pre-registered constants (NOTES 4j)
    target_vol = 0.30
    max_lev = 1.5
    band = 0.20
    leverage_setting = 2.0  # margin multiple; notional never exceeds 1.5x equity

    # ----------------------------------------------------------------- data ---
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        c = dataframe["close"]
        comps = [
            np.sign(c / c.shift(20) - 1),
            np.sign(c / c.shift(60) - 1),
            np.sign(c / c.shift(120) - 1),
            np.sign(c - c.rolling(50).mean()),
        ]
        s = sum(comps) / 4.0
        vol = np.log(c).diff().rolling(30).std() * np.sqrt(365)
        dataframe["trend_s"] = s
        dataframe["exposure"] = s.clip(lower=0)
        dataframe["scale"] = np.minimum(self.target_vol / vol, self.max_lev)
        dataframe["target_frac"] = dataframe["exposure"] * dataframe["scale"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["target_frac"] > 0, ["enter_long", "enter_tag"]] = (1, "trend")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe["exposure"] <= 0, ["exit_long", "exit_tag"]] = (1, "flat")
        return dataframe

    # -------------------------------------------------------------- helpers ---
    def _target_frac(self, pair: str) -> float | None:
        df, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if df is None or df.empty:
            return None
        v = df["target_frac"].iloc[-1]
        return None if np.isnan(v) else float(v)

    def _equity(self, trade: Trade | None, rate: float) -> float:
        """Starting balance + closed profit + open trade's realised and unrealised P&L."""
        eq = self.wallets.get_starting_balance()
        eq += sum(t.close_profit_abs or 0.0 for t in Trade.get_trades_proxy(is_open=False))
        if trade is not None:
            eq += (trade.realized_profit or 0.0) + trade.calc_profit(rate)
        return eq

    # ------------------------------------------------------------ callbacks ---
    def leverage(
        self,
        pair: str,
        current_time: datetime,
        current_rate: float,
        proposed_leverage: float,
        max_leverage: float,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> float:
        return min(self.leverage_setting, max_leverage)

    def custom_stake_amount(
        self,
        pair: str,
        current_time: datetime,
        current_rate: float,
        proposed_stake: float,
        min_stake: float | None,
        max_stake: float,
        leverage: float,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> float:
        frac = self._target_frac(pair)
        if not frac:
            return 0.0
        stake = frac * self._equity(None, current_rate) / leverage
        return min(stake, max_stake)

    def adjust_trade_position(
        self,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        min_stake: float | None,
        max_stake: float,
        current_entry_rate: float,
        current_exit_rate: float,
        current_entry_profit: float,
        current_exit_profit: float,
        **kwargs,
    ) -> float | tuple[float | None, str | None] | None:
        if trade.has_open_orders:
            return None
        frac = self._target_frac(trade.pair)
        if frac is None or frac <= 0:
            return None  # the exit signal closes the position
        equity = self._equity(trade, current_rate)
        cur = trade.amount * current_rate
        tgt = frac * equity
        delta = tgt - cur
        if abs(delta) < self.band * equity:
            return None
        if delta > 0:
            return min(delta / trade.leverage, max_stake), "rebalance_up"
        # Backtesting/freqtradebot turn a negative stake into
        # amount = |stake| * trade.amount / trade.stake_amount.
        sell_amount = min(-delta / current_rate, trade.amount)
        return -sell_amount * trade.stake_amount / trade.amount, "rebalance_down"
