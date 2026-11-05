"""
SessionMomentum - session-range breakout momentum strategy for Freqtrade.

Market:    Binance USDT-M perpetuals (built for SUI/USDT:USDT and BTC/USDT:USDT).
Timeframe: 5m, with 1h and 4h informative data.

Idea (the opposite bet to SessionSweep)
---------------------------------------
1. Record the Asia session high and low each UTC day (default 00:00-07:00).
2. During London (07:00-12:00) or New York (12:30-17:00), go WITH the break:
     * a 5m candle CLOSES above the Asia high with a strong body (displacement,
       measured in ATR) and above-average volume            -> LONG
     * the mirror image below the Asia low                   -> SHORT
3. Optional alignment: 4h (or 1h) EMA trend in the trade direction and 1h RSI
   on the momentum side of 50.
4. Stop under the breakout candle (long) / over it (short), capped at a maximum
   distance. Target = a multiple of the Asia range projected from the broken
   level ("measured move"). Optional ATR trailing stop, time stop and flatten.
5. Risk-based sizing (default 1% of equity per trade), first breakout per
   session only (default), max 1 open trade.

Every window and threshold is a strategy parameter. Lookahead safety follows
SessionSweep: Asia levels are cumulative inside the window and only used after
it closes; informative candles are shifted by Freqtrade so only closed 1h/4h
candles are visible.
"""

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import (
    BooleanParameter,
    CategoricalParameter,
    DecimalParameter,
    IntParameter,
    IStrategy,
    informative,
    stoploss_from_absolute,
)


class SessionMomentum(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "5m"
    can_short = True
    process_only_new_candles = True
    startup_candle_count = 1200  # 100h: warm-up for the 4h EMA / RSI

    minimal_roi = {"0": 100.0}
    use_custom_roi = True
    stoploss = -0.15  # hard cap on risk per trade (stake-relative)
    use_custom_stoploss = True
    trailing_stop = False
    use_exit_signal = True

    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }
    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    # --- sessions (minutes after 00:00 UTC, [start, end)) -------------------
    asia_start_min = IntParameter(0, 1439, default=0, space="buy", optimize=False)
    asia_end_min = IntParameter(0, 1439, default=420, space="buy", optimize=False)
    london_start_min = IntParameter(0, 1439, default=420, space="buy", optimize=False)
    london_end_min = IntParameter(0, 1439, default=720, space="buy", optimize=False)
    ny_start_min = IntParameter(0, 1439, default=750, space="buy", optimize=False)
    ny_end_min = IntParameter(0, 1439, default=1020, space="buy", optimize=False)
    trade_london = BooleanParameter(default=True, space="buy", optimize=False)
    trade_ny = BooleanParameter(default=True, space="buy", optimize=False)

    # --- breakout definition ----------------------------------------------
    # Close must be beyond the level by at least this % of price (0 = any close).
    break_min_pct = DecimalParameter(0.0, 1.0, default=0.0, decimals=2, space="buy", optimize=False)
    # Breakout candle body >= N x ATR(14) in the trade direction. 0 = off.
    displacement_atr_mult = DecimalParameter(
        0.0, 3.0, default=1.0, decimals=2, space="buy", optimize=False
    )
    # Breakout candle volume >= N x 20-candle average volume. 0 = off.
    volume_mult = DecimalParameter(0.0, 5.0, default=1.5, decimals=2, space="buy", optimize=False)
    # Skip days whose Asia range is tiny or huge (% of price). 0 max = off.
    asia_range_min_pct = DecimalParameter(
        0.0, 3.0, default=0.3, decimals=2, space="buy", optimize=False
    )
    asia_range_max_pct = DecimalParameter(
        0.0, 10.0, default=0.0, decimals=2, space="buy", optimize=False
    )
    # Max breakouts per session per UTC day (0 = unlimited).
    max_trades_per_session = IntParameter(0, 5, default=1, space="buy", optimize=False)

    # --- alignment filters --------------------------------------------------
    use_trend_filter = BooleanParameter(default=False, space="buy", optimize=False)
    trend_timeframe = CategoricalParameter(["1h", "4h"], default="4h", space="buy", optimize=False)
    trend_ema_len = IntParameter(10, 200, default=50, space="buy", optimize=False)
    use_rsi_filter = BooleanParameter(default=False, space="buy", optimize=False)
    rsi_timeframe = CategoricalParameter(
        ["5m", "1h", "4h"], default="1h", space="buy", optimize=False
    )
    rsi_len = IntParameter(5, 30, default=14, space="buy", optimize=False)
    # Momentum side of 50: longs need RSI >= rsi_long_min, shorts RSI <= rsi_short_max.
    rsi_long_min = IntParameter(40, 80, default=55, space="buy", optimize=False)
    rsi_short_max = IntParameter(20, 60, default=45, space="buy", optimize=False)

    # --- risk / exits -------------------------------------------------------
    # Stop reference: "candle" = beyond the breakout candle's extreme,
    # "level" = back inside the range at the broken level, "mid" = Asia mid-range.
    stop_mode = CategoricalParameter(
        ["candle", "level", "mid"], default="candle", space="sell", optimize=False
    )
    stop_buffer_pct = DecimalParameter(
        0.0, 1.0, default=0.1, decimals=2, space="sell", optimize=False
    )
    max_stop_distance_pct = DecimalParameter(
        0.2, 5.0, default=1.5, decimals=2, space="sell", optimize=False
    )
    # Target = this multiple of the Asia range beyond the broken level.
    tp_range_mult = DecimalParameter(
        0.25, 3.0, default=1.0, decimals=2, space="sell", optimize=False
    )
    # ATR trailing stop (chandelier): trail N x ATR behind the best price once the
    # trade is `trail_start_r` R in profit. 0 = off.
    trail_atr_mult = DecimalParameter(
        0.0, 6.0, default=0.0, decimals=2, space="sell", optimize=False
    )
    trail_start_r = DecimalParameter(
        0.0, 3.0, default=1.0, decimals=2, space="sell", optimize=False
    )
    max_trade_hours = IntParameter(0, 48, default=0, space="sell", optimize=False)
    exit_at_session_end = BooleanParameter(default=False, space="sell", optimize=False)
    flat_time_min = IntParameter(0, 1439, default=1020, space="sell", optimize=False)

    # --- sizing / leverage --------------------------------------------------
    risk_per_trade_pct = DecimalParameter(
        0.0, 5.0, default=1.0, decimals=2, space="buy", optimize=False
    )
    leverage_level = DecimalParameter(
        1.0, 10.0, default=3.0, decimals=1, space="buy", optimize=False
    )

    plot_config = {
        "main_plot": {"asia_high": {"color": "orange"}, "asia_low": {"color": "orange"}},
        "subplots": {"rsi": {"rsi_1h": {"color": "purple"}}, "vol_ratio": {"vol_ratio": {}}},
    }

    # ================================================================== #
    # Indicators
    # ================================================================== #
    @staticmethod
    def _rsi(close: pd.Series, length: int) -> pd.Series:
        delta = close.diff()
        gain = delta.clip(lower=0).ewm(alpha=1 / length, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(alpha=1 / length, adjust=False).mean()
        rs = gain / loss.replace(0, np.nan)
        return (100 - 100 / (1 + rs)).fillna(100.0)

    def _htf(self, dataframe: DataFrame) -> DataFrame:
        dataframe["ema"] = (
            dataframe["close"].ewm(span=int(self.trend_ema_len.value), adjust=False).mean()
        )
        dataframe["rsi"] = self._rsi(dataframe["close"], int(self.rsi_len.value))
        return dataframe

    @informative("1h")
    def populate_indicators_1h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return self._htf(dataframe)

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return self._htf(dataframe)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        date = dataframe["date"]
        mod = date.dt.hour * 60 + date.dt.minute
        day = date.dt.floor("D")
        a0, a1 = int(self.asia_start_min.value), int(self.asia_end_min.value)
        in_asia = (mod >= a0) & (mod < a1)
        dataframe["in_london"] = (mod >= int(self.london_start_min.value)) & (
            mod < int(self.london_end_min.value)
        )
        dataframe["in_ny"] = (mod >= int(self.ny_start_min.value)) & (
            mod < int(self.ny_end_min.value)
        )

        asia_high = dataframe["high"].where(in_asia).groupby(day).cummax()
        asia_low = dataframe["low"].where(in_asia).groupby(day).cummin()
        dataframe["asia_high"] = asia_high.groupby(day).ffill()
        dataframe["asia_low"] = asia_low.groupby(day).ffill()
        dataframe["asia_mid"] = (dataframe["asia_high"] + dataframe["asia_low"]) / 2
        dataframe["asia_range_pct"] = (
            (dataframe["asia_high"] - dataframe["asia_low"]) / dataframe["asia_low"] * 100
        )
        dataframe["asia_done"] = (
            (mod >= a1) & dataframe["asia_high"].notna() & dataframe["asia_low"].notna()
        )

        prev_close = dataframe["close"].shift(1)
        tr = pd.concat(
            [
                dataframe["high"] - dataframe["low"],
                (dataframe["high"] - prev_close).abs(),
                (dataframe["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        dataframe["atr"] = tr.ewm(alpha=1 / 14, adjust=False).mean()
        dataframe["rsi"] = self._rsi(dataframe["close"], int(self.rsi_len.value))
        vol_avg = dataframe["volume"].shift(1).rolling(20, min_periods=5).mean()
        dataframe["vol_ratio"] = dataframe["volume"] / vol_avg.replace(0, np.nan)
        return dataframe

    # ================================================================== #
    # Entries
    # ================================================================== #
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        brk = 1 + float(self.break_min_pct.value) / 100
        buf = float(self.stop_buffer_pct.value) / 100
        tradable = dataframe["asia_done"] & (
            dataframe["asia_range_pct"] >= float(self.asia_range_min_pct.value)
        )
        rmax = float(self.asia_range_max_pct.value)
        if rmax > 0:
            tradable &= dataframe["asia_range_pct"] <= rmax
        session_ok = pd.Series(False, index=dataframe.index)
        if self.trade_london.value:
            session_ok |= dataframe["in_london"]
        if self.trade_ny.value:
            session_ok |= dataframe["in_ny"]

        # State: closed beyond the level. The entry is the FIRST close beyond it
        # (edge), so a day that has already broken out does not re-signal on
        # every following candle; it can signal again after a close back inside.
        # The state ignores the session so that a close beyond the level inside
        # the London/NY gap is not re-counted as a fresh break at the NY open.
        above = dataframe["asia_done"] & (dataframe["close"] > dataframe["asia_high"] * brk)
        below = dataframe["asia_done"] & (dataframe["close"] < dataframe["asia_low"] / brk)
        long_edge = above & ~above.shift(1, fill_value=False) & tradable & session_ok
        short_edge = below & ~below.shift(1, fill_value=False) & tradable & session_ok

        body = dataframe["close"] - dataframe["open"]
        disp = float(self.displacement_atr_mult.value)
        if disp > 0:
            long_edge &= body >= disp * dataframe["atr"]
            short_edge &= -body >= disp * dataframe["atr"]
        vm = float(self.volume_mult.value)
        if vm > 0:
            long_edge &= dataframe["vol_ratio"] >= vm
            short_edge &= dataframe["vol_ratio"] >= vm
        tf = self.trend_timeframe.value
        if self.use_trend_filter.value and f"ema_{tf}" in dataframe.columns:
            long_edge &= dataframe[f"close_{tf}"] > dataframe[f"ema_{tf}"]
            short_edge &= dataframe[f"close_{tf}"] < dataframe[f"ema_{tf}"]
        if self.use_rsi_filter.value:
            rtf = self.rsi_timeframe.value
            rsi_col = "rsi" if rtf == "5m" else f"rsi_{rtf}"
            long_edge &= dataframe[rsi_col] >= int(self.rsi_long_min.value)
            short_edge &= dataframe[rsi_col] <= int(self.rsi_short_max.value)

        # --- geometry -------------------------------------------------------
        asia_range = dataframe["asia_high"] - dataframe["asia_low"]
        mode = self.stop_mode.value
        if mode == "candle":
            long_ref, short_ref = dataframe["low"], dataframe["high"]
        elif mode == "level":
            long_ref, short_ref = dataframe["asia_high"], dataframe["asia_low"]
        else:
            long_ref, short_ref = dataframe["asia_mid"], dataframe["asia_mid"]
        long_stop = long_ref * (1 - buf)
        short_stop = short_ref * (1 + buf)
        mult = float(self.tp_range_mult.value)
        long_tp = dataframe["asia_high"] + asia_range * mult
        short_tp = dataframe["asia_low"] - asia_range * mult

        max_stop = float(self.max_stop_distance_pct.value)
        long_dist = (dataframe["close"] - long_stop) / dataframe["close"] * 100
        short_dist = (short_stop - dataframe["close"]) / dataframe["close"] * 100
        long_ok = (
            long_edge & (long_dist > 0) & (long_dist <= max_stop) & (long_tp > dataframe["close"])
        )
        short_ok = (
            short_edge
            & (short_dist > 0)
            & (short_dist <= max_stop)
            & (short_tp < dataframe["close"])
        )

        dataframe["stop_px"] = np.nan
        dataframe["tp_px"] = np.nan
        dataframe.loc[long_ok, "stop_px"] = long_stop[long_ok]
        dataframe.loc[long_ok, "tp_px"] = long_tp[long_ok]
        dataframe.loc[short_ok, "stop_px"] = short_stop[short_ok]
        dataframe.loc[short_ok, "tp_px"] = short_tp[short_ok]

        for side, ok in (("long", long_ok), ("short", short_ok)):
            for sess in ("london", "ny"):
                sel = ok & dataframe[f"in_{sess}"]
                dataframe.loc[sel, [f"enter_{side}", "enter_tag"]] = (1, f"{sess}_{side}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    # ================================================================== #
    # Helpers
    # ================================================================== #
    def _last_candle(self, pair: str) -> pd.Series | None:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty:
            return None
        return dataframe.iloc[-1]

    def _signal_candle(self, pair: str, trade: Trade) -> pd.Series | None:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty:
            return None
        rows = dataframe.loc[dataframe["date"] < trade.open_date_utc]
        return None if rows.empty else rows.iloc[-1]

    def _trade_levels(self, pair: str, trade: Trade) -> tuple[float | None, float | None]:
        stop_px = trade.get_custom_data("stop_px")
        tp_px = trade.get_custom_data("tp_px")
        if stop_px is None or tp_px is None:
            candle = self._signal_candle(pair, trade)
            if candle is None:
                return None, None
            stop_px, tp_px = candle.get("stop_px"), candle.get("tp_px")
            if stop_px is None or tp_px is None or np.isnan(stop_px) or np.isnan(tp_px):
                return None, None
            trade.set_custom_data("stop_px", float(stop_px))
            trade.set_custom_data("tp_px", float(tp_px))
        return float(stop_px), float(tp_px)

    # ================================================================== #
    # Callbacks
    # ================================================================== #
    def leverage(self, pair, current_time, current_rate, proposed_leverage, max_leverage,
                 entry_tag, side, **kwargs) -> float:  # fmt: skip
        return min(float(self.leverage_level.value), max_leverage)

    def custom_stake_amount(self, pair, current_time, current_rate, proposed_stake, min_stake,
                            max_stake, leverage, entry_tag, side, **kwargs) -> float:  # fmt: skip
        risk_pct = float(self.risk_per_trade_pct.value)
        if risk_pct <= 0:
            return proposed_stake
        candle = self._last_candle(pair)
        if candle is None or np.isnan(candle.get("stop_px", np.nan)):
            return proposed_stake
        stop_dist = abs(current_rate - float(candle["stop_px"])) / current_rate
        if stop_dist <= 0:
            return proposed_stake
        equity = self.wallets.get_total_stake_amount() if self.wallets else proposed_stake
        stake = equity * risk_pct / 100 / (stop_dist * leverage)
        if min_stake is not None and stake < min_stake:
            return 0
        return min(stake, max_stake)

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:  # fmt: skip
        limit = int(self.max_trades_per_session.value)
        if limit <= 0 or not entry_tag:
            return True
        session = entry_tag.split("_")[0]
        day_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        taken = [
            t
            for t in Trade.get_trades_proxy(pair=pair)
            if t.open_date_utc >= day_start and (t.enter_tag or "").startswith(session + "_")
        ]
        return len(taken) < limit

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit,
                        after_fill, **kwargs) -> float | None:  # fmt: skip
        stop_px, _tp = self._trade_levels(pair, trade)
        if stop_px is None:
            return None
        trail = float(self.trail_atr_mult.value)
        if trail > 0:
            # Chandelier trail once the trade is `trail_start_r` R in profit
            # (R = initial stop distance). Freqtrade only ever tightens the stop.
            risk = abs(trade.open_rate - stop_px)
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if dataframe is not None and not dataframe.empty and risk > 0:
                atr = float(dataframe["atr"].iloc[-1])
                if trade.is_short:
                    best = float(trade.min_rate or current_rate)
                    if trade.open_rate - best >= float(self.trail_start_r.value) * risk:
                        stop_px = min(stop_px, best + trail * atr)
                else:
                    best = float(trade.max_rate or current_rate)
                    if best - trade.open_rate >= float(self.trail_start_r.value) * risk:
                        stop_px = max(stop_px, best - trail * atr)
        sl = stoploss_from_absolute(
            stop_px, current_rate, is_short=trade.is_short, leverage=trade.leverage
        )
        return -sl if sl > 0 else -0.0001

    def custom_roi(self, pair, trade, current_time, trade_duration, entry_tag, side,
                   **kwargs) -> float | None:  # fmt: skip
        _stop, tp_px = self._trade_levels(pair, trade)
        if tp_px is None or trade.open_rate == 0:
            return None
        dist = (
            (trade.open_rate - tp_px) if trade.is_short else (tp_px - trade.open_rate)
        ) / trade.open_rate
        return dist * trade.leverage if dist > 0 else None

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit,
                    **kwargs) -> str | None:  # fmt: skip
        max_hours = int(self.max_trade_hours.value)
        if max_hours > 0 and current_time - trade.open_date_utc >= timedelta(hours=max_hours):
            return "time_stop"
        if self.exit_at_session_end.value:
            mod = current_time.hour * 60 + current_time.minute
            if mod >= int(self.flat_time_min.value):
                return "session_end"
        return None
