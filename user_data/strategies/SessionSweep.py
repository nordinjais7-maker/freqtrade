"""
SessionSweep - session-timing liquidity-sweep strategy for Freqtrade.

Market:    SUI/USDT:USDT (Binance USDT-M perpetual), but pair-agnostic.
Timeframe: 5m, with 1h informative data for an optional trend filter.

Idea
----
1. Record the high and low of the Asia session (default 00:00-07:00 UTC) each day.
2. During London (07:00-12:00 UTC) or New York (12:30-17:00 UTC):
     * price trades ABOVE the Asia high (a "sweep" of the resting liquidity)
       and then CLOSES back BELOW it         -> SHORT
     * price trades BELOW the Asia low and then CLOSES back ABOVE it -> LONG
3. Stop loss sits just beyond the sweep wick (the extreme that took out the level).
4. Take profit is the opposite side of the Asia range (configurable fraction),
   with an optional break-even move at mid-range and Freqtrade's native trailing stop.

Enhancements (all OFF by default, so the defaults reproduce the original rules):
  * risk_per_trade_pct      - size each trade so the stop loses a fixed % of equity
  * max_trades_per_session  - trade only the first sweep(s) of each session
  * require_mss             - after the reclaim, price must also break the recent
                              swing low/high (market-structure shift)
  * displacement_atr_mult   - the reclaim candle needs a strong body vs. ATR
  * entry_retrace_frac      - enter with a limit order on a pull-back toward the
                              swept level instead of at market
  * max_asia_adr_ratio      - only trade days where the Asia range is compressed
                              relative to the average daily range
  * max_trade_hours         - close trades that have not resolved in N hours

All session windows and thresholds are strategy parameters, so they can be
overridden from `SessionSweep.json` next to this file, from the `strategy`
section of the config, or via hyperopt.

Lookahead safety
----------------
* Asia high/low are *running* (cumulative) extremes inside the Asia window and are
  only used once the Asia window has closed (`asia_done`), so a London/NY candle
  never sees data from its own future.
* The 1h informative data is merged with Freqtrade's `@informative` decorator,
  which shifts the 1h candle so only closed 1h candles are visible to a 5m candle.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import (
    BooleanParameter,
    DecimalParameter,
    IntParameter,
    IStrategy,
    informative,
    stoploss_from_absolute,
)


def _hhmm(minute_of_day: int) -> str:
    """Pretty-print a minute-of-day integer as HH:MM (used for logging only)."""
    return f"{minute_of_day // 60:02d}:{minute_of_day % 60:02d}"


class SessionSweep(IStrategy):
    INTERFACE_VERSION = 3

    # ------------------------------------------------------------------ #
    # Core strategy settings
    # ------------------------------------------------------------------ #
    timeframe = "5m"
    can_short = True
    process_only_new_candles = True
    # 1h trend EMA (default 50) needs 50h = 600 five-minute candles. Add headroom.
    startup_candle_count = 720

    # ROI: effectively disabled - the take profit is handled by custom_roi()
    # (target = opposite side of the Asia range). A ridiculous value keeps
    # Freqtrade's static ROI table from ever firing.
    minimal_roi = {"0": 100.0}
    use_custom_roi = True

    # Hard stop (maximum risk per trade as a fraction of the *stake*, so with 3x
    # leverage -0.15 == a 5% adverse price move). The real stop is the sweep wick,
    # placed via custom_stoploss(); this only acts as a safety cap.
    stoploss = -0.15
    use_custom_stoploss = True

    # Native trailing stop (OFF by default). Flip `trailing_stop` to True to
    # trail once the trade is `trailing_stop_positive_offset` in profit
    # (values are stake-relative, i.e. already multiplied by leverage).
    trailing_stop = False
    trailing_stop_positive = 0.03
    trailing_stop_positive_offset = 0.06
    trailing_only_offset_is_reached = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }
    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    # ------------------------------------------------------------------ #
    # Parameters - sessions (minutes after 00:00 UTC; 420 == 07:00)
    # ------------------------------------------------------------------ #
    # Window boundaries are [start, end): a 5m candle whose *open* time is
    # inside the window belongs to it.  optimize=False -> pure configuration.
    asia_start_min = IntParameter(0, 1439, default=0, space="buy", optimize=False)  # 00:00
    asia_end_min = IntParameter(0, 1439, default=420, space="buy", optimize=False)  # 07:00
    london_start_min = IntParameter(0, 1439, default=420, space="buy", optimize=False)  # 07:00
    london_end_min = IntParameter(0, 1439, default=720, space="buy", optimize=False)  # 12:00
    ny_start_min = IntParameter(0, 1439, default=750, space="buy", optimize=False)  # 12:30
    ny_end_min = IntParameter(0, 1439, default=1020, space="buy", optimize=False)  # 17:00

    # Trade both sessions by default; switch one off to isolate it.
    trade_london = BooleanParameter(default=True, space="buy", optimize=False)
    trade_ny = BooleanParameter(default=True, space="buy", optimize=False)

    # ------------------------------------------------------------------ #
    # Parameters - sweep detection
    # ------------------------------------------------------------------ #
    # How many recent 5m candles may separate the sweep wick from the
    # reclaiming close (1 == wick and close must be on the same candle).
    sweep_lookback = IntParameter(1, 24, default=6, space="buy", optimize=True)
    # Minimum penetration beyond the Asia level, in % of price (0 = any tick).
    sweep_min_pct = DecimalParameter(0.0, 1.0, default=0.0, decimals=2, space="buy", optimize=True)
    # Ignore days whose Asia range is tiny (% of price) - no liquidity to sweep.
    asia_range_min_pct = DecimalParameter(
        0.0, 3.0, default=0.3, decimals=2, space="buy", optimize=True
    )
    # Skip setups whose stop distance (price %) is larger than this.
    max_stop_distance_pct = DecimalParameter(
        0.2, 5.0, default=2.0, decimals=2, space="buy", optimize=False
    )
    # Minimum reward:risk (TP distance / stop distance). 0 disables the filter.
    min_rr = DecimalParameter(0.0, 3.0, default=0.0, decimals=2, space="buy", optimize=True)

    # ------------------------------------------------------------------ #
    # Parameters - risk / exits
    # ------------------------------------------------------------------ #
    # Stop buffer beyond the sweep wick, in % of price.
    stop_buffer_pct = DecimalParameter(
        0.0, 1.0, default=0.15, decimals=2, space="sell", optimize=True
    )
    # Take profit as a fraction of the Asia range measured from the swept level:
    # 1.0 = opposite side of the range, 0.5 = mid-range.
    tp_range_fraction = DecimalParameter(
        0.25, 1.5, default=1.0, decimals=2, space="sell", optimize=True
    )
    # Move the stop to break-even once price reaches the Asia mid-range.
    breakeven_at_midrange = BooleanParameter(default=False, space="sell", optimize=True)
    # Close any open trade at `flat_time_min` UTC (default 17:00 == NY end).
    exit_at_session_end = BooleanParameter(default=False, space="sell", optimize=True)
    flat_time_min = IntParameter(0, 1439, default=1020, space="sell", optimize=False)

    # ------------------------------------------------------------------ #
    # Parameters - 1h trend filter (optional)
    # ------------------------------------------------------------------ #
    use_trend_filter = BooleanParameter(default=False, space="buy", optimize=True)
    trend_ema_len = IntParameter(10, 200, default=50, space="buy", optimize=False)

    # ------------------------------------------------------------------ #
    # Parameters - enhancements (every default = OFF / original behaviour)
    # ------------------------------------------------------------------ #
    # Position sizing: % of total equity lost if the stop is hit. 0 = use the
    # config stake_amount (original behaviour: whole balance per trade).
    risk_per_trade_pct = DecimalParameter(
        0.0, 5.0, default=0.0, decimals=2, space="buy", optimize=False
    )
    # Max entries per session per UTC day (London and NY counted separately).
    # 0 = unlimited (original behaviour).
    max_trades_per_session = IntParameter(0, 5, default=0, space="buy", optimize=False)
    # Market-structure shift: the signal candle must close beyond the lowest low
    # (short) / highest high (long) of the previous `mss_lookback` candles.
    require_mss = BooleanParameter(default=False, space="buy", optimize=False)
    mss_lookback = IntParameter(2, 24, default=6, space="buy", optimize=False)
    # Displacement: signal candle body in the trade direction must be at least
    # this many 5m ATR(14). 0 = off.
    displacement_atr_mult = DecimalParameter(
        0.0, 3.0, default=0.0, decimals=2, space="buy", optimize=False
    )
    # Retest entry: place a limit order this fraction of the way from the signal
    # close back toward the swept Asia level (0 = enter at market, 1 = at the
    # level). Unfilled orders are cancelled after `entry_wait_candles`.
    entry_retrace_frac = DecimalParameter(
        0.0, 1.0, default=0.0, decimals=2, space="buy", optimize=False
    )
    entry_wait_candles = IntParameter(1, 24, default=6, space="buy", optimize=False)
    # Compression: Asia range must be <= this fraction of the 14-day average
    # daily range (computed from previous days only). 0 = off.
    max_asia_adr_ratio = DecimalParameter(
        0.0, 2.0, default=0.0, decimals=2, space="buy", optimize=False
    )
    # Time stop: close a trade still open after this many hours. 0 = off.
    max_trade_hours = IntParameter(0, 48, default=0, space="sell", optimize=False)

    # ------------------------------------------------------------------ #
    # Parameters - leverage
    # ------------------------------------------------------------------ #
    leverage_level = DecimalParameter(
        1.0, 10.0, default=3.0, decimals=1, space="buy", optimize=False
    )

    # Columns we want to see in the FreqUI / plot
    plot_config = {
        "main_plot": {
            "asia_high": {"color": "orange"},
            "asia_low": {"color": "orange"},
            "ema_1h": {"color": "grey"},
        },
        "subplots": {"session": {"session_id": {"color": "blue"}}},
    }

    # ================================================================== #
    # Informative 1h data (trend filter)
    # ================================================================== #
    @informative("1h")
    def populate_indicators_1h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Pure-pandas EMA so the strategy has no TA-Lib dependency.
        dataframe["ema"] = (
            dataframe["close"].ewm(span=int(self.trend_ema_len.value), adjust=False).mean()
        )
        return dataframe

    # ================================================================== #
    # Indicators
    # ================================================================== #
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        date = dataframe["date"]
        # Minute of day in UTC (freqtrade candles are UTC tz-aware).
        mod = date.dt.hour * 60 + date.dt.minute
        day = date.dt.floor("D")
        dataframe["minute_of_day"] = mod

        a0, a1 = int(self.asia_start_min.value), int(self.asia_end_min.value)
        l0, l1 = int(self.london_start_min.value), int(self.london_end_min.value)
        n0, n1 = int(self.ny_start_min.value), int(self.ny_end_min.value)

        in_asia = (mod >= a0) & (mod < a1)
        in_london = (mod >= l0) & (mod < l1)
        in_ny = (mod >= n0) & (mod < n1)
        dataframe["in_london"] = in_london
        dataframe["in_ny"] = in_ny
        # 0 = none, 1 = Asia, 2 = London, 3 = NY  (plot helper only)
        dataframe["session_id"] = np.select([in_asia, in_london, in_ny], [1, 2, 3], default=0)

        # --- Asia range: running extremes inside the window, carried forward
        #     for the rest of the UTC day. Cummax/cummin are per calendar day so
        #     nothing leaks across midnight. --------------------------------
        asia_high = dataframe["high"].where(in_asia)
        asia_low = dataframe["low"].where(in_asia)
        asia_high = asia_high.groupby(day).cummax()
        asia_low = asia_low.groupby(day).cummin()
        dataframe["asia_high"] = asia_high.groupby(day).ffill()
        dataframe["asia_low"] = asia_low.groupby(day).ffill()
        dataframe["asia_mid"] = (dataframe["asia_high"] + dataframe["asia_low"]) / 2
        dataframe["asia_range_pct"] = (
            (dataframe["asia_high"] - dataframe["asia_low"]) / dataframe["asia_low"] * 100
        )
        # The Asia range is final (safe to use) only after the window closed.
        dataframe["asia_done"] = (
            (mod >= a1) & dataframe["asia_high"].notna() & dataframe["asia_low"].notna()
        )

        # --- Sweep extremes: highest high / lowest low over the last N candles,
        #     counting only post-Asia candles (so an Asia candle can never be the
        #     "sweep" of its own range). ---------------------------------------
        lb = int(self.sweep_lookback.value)
        post_asia_high = dataframe["high"].where(dataframe["asia_done"])
        post_asia_low = dataframe["low"].where(dataframe["asia_done"])
        dataframe["sweep_high"] = post_asia_high.rolling(lb, min_periods=1).max()
        dataframe["sweep_low"] = post_asia_low.rolling(lb, min_periods=1).min()

        # --- Enhancement inputs (all computed from past data only) ----------
        # 5m ATR(14), Wilder smoothing, for the displacement filter.
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

        # Recent swing extremes for the market-structure-shift filter,
        # excluding the current candle.
        ml = int(self.mss_lookback.value)
        dataframe["swing_low_prev"] = dataframe["low"].shift(1).rolling(ml).min()
        dataframe["swing_high_prev"] = dataframe["high"].shift(1).rolling(ml).max()

        # 14-day average daily range in % of price, using completed days only.
        daily = dataframe.groupby(day).agg(d_high=("high", "max"), d_low=("low", "min"))
        daily_range_pct = (daily["d_high"] - daily["d_low"]) / daily["d_low"] * 100
        adr = daily_range_pct.shift(1).rolling(14, min_periods=5).mean()
        dataframe["adr_pct"] = day.map(adr).to_numpy()

        return dataframe

    # ================================================================== #
    # Entry signals
    # ================================================================== #
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pen = 1 + float(self.sweep_min_pct.value) / 100
        buf = float(self.stop_buffer_pct.value) / 100
        tp_frac = float(self.tp_range_fraction.value)
        max_stop = float(self.max_stop_distance_pct.value)
        min_rr = float(self.min_rr.value)

        tradable = dataframe["asia_done"] & (
            dataframe["asia_range_pct"] >= float(self.asia_range_min_pct.value)
        )
        session_ok = pd.Series(False, index=dataframe.index)
        if self.trade_london.value:
            session_ok |= dataframe["in_london"]
        if self.trade_ny.value:
            session_ok |= dataframe["in_ny"]

        # Raw state: "a sweep happened within the lookback AND we are now closed
        # back inside the range".  The entry fires on the first candle where the
        # state becomes true (edge), which avoids firing on every following bar.
        raw_short = (
            tradable
            & session_ok
            & (dataframe["sweep_high"] > dataframe["asia_high"] * pen)
            & (dataframe["close"] < dataframe["asia_high"])
        )
        raw_long = (
            tradable
            & session_ok
            & (dataframe["sweep_low"] < dataframe["asia_low"] / pen)
            & (dataframe["close"] > dataframe["asia_low"])
        )
        # --- Enhancement filters that define a valid reclaim candle --------
        # They are applied BEFORE edge detection, so the signal fires on the
        # first candle that is both inside the reclaim state and confirmed.
        if self.require_mss.value:
            raw_short &= dataframe["close"] < dataframe["swing_low_prev"]
            raw_long &= dataframe["close"] > dataframe["swing_high_prev"]
        disp = float(self.displacement_atr_mult.value)
        if disp > 0:
            body = dataframe["close"] - dataframe["open"]
            raw_short &= -body >= disp * dataframe["atr"]
            raw_long &= body >= disp * dataframe["atr"]
        adr_ratio = float(self.max_asia_adr_ratio.value)
        if adr_ratio > 0:
            compressed = dataframe["asia_range_pct"] <= adr_ratio * dataframe["adr_pct"]
            raw_short &= compressed
            raw_long &= compressed

        short_edge = raw_short & ~raw_short.shift(1, fill_value=False)
        long_edge = raw_long & ~raw_long.shift(1, fill_value=False)

        # --- Risk geometry (price terms) ----------------------------------
        asia_range = dataframe["asia_high"] - dataframe["asia_low"]
        short_stop = dataframe["sweep_high"] * (1 + buf)
        long_stop = dataframe["sweep_low"] * (1 - buf)
        short_tp = dataframe["asia_high"] - asia_range * tp_frac
        long_tp = dataframe["asia_low"] + asia_range * tp_frac

        # Planned entry: signal close, or a retest limit part-way back to the level.
        frac = float(self.entry_retrace_frac.value)
        short_entry = dataframe["close"] + frac * (dataframe["asia_high"] - dataframe["close"])
        long_entry = dataframe["close"] - frac * (dataframe["close"] - dataframe["asia_low"])

        short_stop_dist = (short_stop - short_entry) / short_entry * 100
        long_stop_dist = (long_entry - long_stop) / long_entry * 100
        short_rr = (short_entry - short_tp) / (short_stop - short_entry)
        long_rr = (long_tp - long_entry) / (long_entry - long_stop)

        short_ok = short_edge & (short_stop_dist <= max_stop) & (short_stop_dist > 0)
        long_ok = long_edge & (long_stop_dist <= max_stop) & (long_stop_dist > 0)
        if min_rr > 0:
            short_ok &= short_rr >= min_rr
            long_ok &= long_rr >= min_rr

        # --- Optional 1h trend filter --------------------------------------
        if self.use_trend_filter.value and "ema_1h" in dataframe.columns:
            short_ok &= dataframe["close_1h"] < dataframe["ema_1h"]
            long_ok &= dataframe["close_1h"] > dataframe["ema_1h"]

        # Persist the trade geometry on the signal candle so the callbacks can
        # read it back (see _signal_candle()).
        dataframe["stop_px"] = np.nan
        dataframe["tp_px"] = np.nan
        dataframe["entry_px"] = np.nan
        dataframe.loc[short_ok, "stop_px"] = short_stop[short_ok]
        dataframe.loc[short_ok, "tp_px"] = short_tp[short_ok]
        dataframe.loc[short_ok, "entry_px"] = short_entry[short_ok]
        dataframe.loc[long_ok, "stop_px"] = long_stop[long_ok]
        dataframe.loc[long_ok, "tp_px"] = long_tp[long_ok]
        dataframe.loc[long_ok, "entry_px"] = long_entry[long_ok]

        # --- Signals, tagged by session so the backtest report splits them ---
        dataframe.loc[short_ok & dataframe["in_london"], ["enter_short", "enter_tag"]] = (
            1,
            "london_short",
        )
        dataframe.loc[short_ok & dataframe["in_ny"], ["enter_short", "enter_tag"]] = (
            1,
            "ny_short",
        )
        dataframe.loc[long_ok & dataframe["in_london"], ["enter_long", "enter_tag"]] = (
            1,
            "london_long",
        )
        dataframe.loc[long_ok & dataframe["in_ny"], ["enter_long", "enter_tag"]] = (
            1,
            "ny_long",
        )
        return dataframe

    # ================================================================== #
    # Exit signals (none - exits come from stop / TP / time)
    # ================================================================== #
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    # ================================================================== #
    # Helpers
    # ================================================================== #
    def _signal_candle(self, pair: str, trade: Trade) -> pd.Series | None:
        """Return the candle that generated the entry signal for `trade`.

        The entry order is placed at the open of the candle *after* the signal
        candle, so the signal candle is the last analysed row strictly before
        the trade open time (true both in backtesting and in dry/live).
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty:
            return None
        rows = dataframe.loc[dataframe["date"] < trade.open_date_utc]
        if rows.empty:
            return None
        return rows.iloc[-1]

    def _trade_levels(self, pair: str, trade: Trade) -> tuple[float | None, float | None]:
        """Stop and TP prices for this trade, cached on the trade object."""
        stop_px = trade.get_custom_data("stop_px")
        tp_px = trade.get_custom_data("tp_px")
        if stop_px is None or tp_px is None:
            candle = self._signal_candle(pair, trade)
            if candle is None:
                return None, None
            stop_px = candle.get("stop_px")
            tp_px = candle.get("tp_px")
            if stop_px is None or tp_px is None or np.isnan(stop_px) or np.isnan(tp_px):
                return None, None
            trade.set_custom_data("stop_px", float(stop_px))
            trade.set_custom_data("tp_px", float(tp_px))
            trade.set_custom_data("asia_mid", float(candle.get("asia_mid", np.nan)))
        return float(stop_px), float(tp_px)

    # ================================================================== #
    # Callbacks
    # ================================================================== #
    def _last_candle(self, pair: str) -> pd.Series | None:
        """Most recent analysed candle (the signal candle when an entry is placed)."""
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty:
            return None
        return dataframe.iloc[-1]

    def custom_entry_price(
        self,
        pair: str,
        trade: Trade | None,
        current_time: datetime,
        proposed_rate: float,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> float:
        """Retest entry: limit order part-way back toward the swept level."""
        if float(self.entry_retrace_frac.value) <= 0:
            return proposed_rate
        candle = self._last_candle(pair)
        if candle is None or np.isnan(candle.get("entry_px", np.nan)):
            return proposed_rate
        entry_px = float(candle["entry_px"])
        # Never chase: only improve on the proposed price.
        return max(entry_px, proposed_rate) if side == "short" else min(entry_px, proposed_rate)

    def check_entry_timeout(
        self, pair: str, trade: Trade, order, current_time: datetime, **kwargs
    ) -> bool:
        """Cancel a retest limit order that has not filled within N candles."""
        waited = (current_time - order.order_date_utc).total_seconds()
        return waited >= int(self.entry_wait_candles.value) * 300

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
        """Risk-based sizing: the stop loses `risk_per_trade_pct` of equity."""
        risk_pct = float(self.risk_per_trade_pct.value)
        if risk_pct <= 0:
            return proposed_stake
        candle = self._last_candle(pair)
        if candle is None or np.isnan(candle.get("stop_px", np.nan)):
            return proposed_stake
        entry = candle.get("entry_px", np.nan)
        entry = float(entry) if not np.isnan(entry) else current_rate
        stop_dist = abs(entry - float(candle["stop_px"])) / entry
        if stop_dist <= 0:
            return proposed_stake
        equity = self.wallets.get_total_stake_amount() if self.wallets else proposed_stake
        # stake is margin; position notional = stake * leverage
        stake = equity * risk_pct / 100 / (stop_dist * leverage)
        if min_stake is not None and stake < min_stake:
            return 0  # setup too small to size correctly - skip it
        return min(stake, max_stake)

    def confirm_trade_entry(
        self,
        pair: str,
        order_type: str,
        amount: float,
        rate: float,
        time_in_force: str,
        current_time: datetime,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> bool:
        """Limit the number of entries per session per UTC day."""
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
        """Fixed leverage (default 3x), capped by what the exchange allows."""
        return min(float(self.leverage_level.value), max_leverage)

    def custom_stoploss(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        after_fill: bool,
        **kwargs,
    ) -> float | None:
        """Stop just beyond the sweep wick; optional break-even at mid-range.

        Returned value is stake-relative (risk), hence the `leverage` argument to
        `stoploss_from_absolute`. Freqtrade only ever *tightens* the stop, so
        returning the same wick level every candle is safe.
        """
        stop_px, _tp = self._trade_levels(pair, trade)
        if stop_px is None:
            return None  # keep whatever stop is currently set (hard cap on first call)

        if self.breakeven_at_midrange.value:
            mid = trade.get_custom_data("asia_mid")
            if mid is not None and not np.isnan(mid):
                reached = current_rate <= mid if trade.is_short else current_rate >= mid
                if reached:
                    stop_px = (
                        min(stop_px, trade.open_rate)
                        if trade.is_short
                        else max(stop_px, trade.open_rate)
                    )

        sl = stoploss_from_absolute(
            stop_px, current_rate, is_short=trade.is_short, leverage=trade.leverage
        )
        # stoploss_from_absolute returns 0 when the stop is already beyond the
        # current price (e.g. slippage); return a hair-trigger stop instead so
        # the position is closed rather than left without protection.
        return -sl if sl > 0 else -0.0001

    def custom_roi(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        trade_duration: int,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> float | None:
        """Take profit at the opposite side of the Asia range (stake-relative)."""
        _stop, tp_px = self._trade_levels(pair, trade)
        if tp_px is None or trade.open_rate == 0:
            return None
        if trade.is_short:
            dist = (trade.open_rate - tp_px) / trade.open_rate
        else:
            dist = (tp_px - trade.open_rate) / trade.open_rate
        if dist <= 0:
            return None  # TP already behind us - let stop / time handle it
        return dist * trade.leverage

    def custom_exit(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> str | None:
        """Optional time stop and time-based flatten at the end of the trading day."""
        max_hours = int(self.max_trade_hours.value)
        if max_hours > 0 and current_time - trade.open_date_utc >= timedelta(hours=max_hours):
            return "time_stop"
        if not self.exit_at_session_end.value:
            return None
        mod = current_time.hour * 60 + current_time.minute
        if mod >= int(self.flat_time_min.value):
            return "session_end"
        return None
