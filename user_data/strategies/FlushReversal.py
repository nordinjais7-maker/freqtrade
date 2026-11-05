"""
FlushReversal - fade short, taker-driven flushes with resting limit orders.

Evidence (see reports/BTC SUI futures orderflow edges.md): after a short move
driven by aggressive (taker) flow, price tends to partially reverse over ~15
minutes to a few hours. One 2026 preprint finds this in 90% of 183 Binance
pairs and reads it as a premium for providing liquidity, so entries here are
limit (maker) orders. The effect is statistically small; this strategy exists
to test it under a pre-registered protocol, not because it is known to profit.

Rules, 5m candles:
  * event: the 15-minute return (3 candles) is at least k x its trailing 7-day
    standard deviation, AND the taker share of those 15 minutes' volume in the
    direction of the move is at or above its trailing 7-day p-th percentile
    (flow_mode = "high"). flow_mode = "low" is the mechanism control: same-size
    moves whose taker share is BELOW the trailing median.
  * trade: fade the move with a limit order at the event close moved e x ATR(14)
    further in the move's direction, valid for 15 minutes.
  * exits (fixed, not tuned): take profit at 50% retracement of the 15-minute
    move, stop 1.0 x the move's 3-candle range beyond its extreme, 60-minute
    time stop.
  * no entries within 10 minutes of a funding settlement.
  * 1% of equity at risk per trade, 3x isolated, max 1 open trade.

Taker-buy volume is not part of Freqtrade's candles; it comes from
user_data/data/binance_taker/<BASE>USDT_5m.feather, built by
user_data/scripts/fetch_binance_taker.py. Without that file there are no entries.
FLUSHREV_TAKER_DIR (environment variable) overrides the directory (tests).

Backtest caveats: Freqtrade fills a limit order as soon as a candle touches its
price, which overstates maker fills; `fill_through_ticks` moves the limit one or
more ticks further so a fill needs price to trade through. Freqtrade charges one
fee rate on both legs (the taker rate unless --fee is given), which is
conservative for the maker entry, and models no slippage on the exit.
Not financial advice.
"""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import (
    CategoricalParameter,
    DecimalParameter,
    IntParameter,
    IStrategy,
    stoploss_from_absolute,
)


logger = logging.getLogger(__name__)

BARS_PER_DAY = 288  # 5m


class FlushReversal(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "5m"
    can_short = True
    process_only_new_candles = True
    # 7 days of 5m candles for the volatility and flow windows, plus headroom.
    # Freqtrade caps Binance 5m startup at 5 x 499 = 2494 candles (~8.7 days), so
    # the 30-day flow window in the research report is not possible live; 7 days
    # is used for both windows (recorded in the pre-registration, NOTES.md §4h).
    startup_candle_count = 7 * BARS_PER_DAY + 50

    minimal_roi = {"0": 100.0}
    use_custom_roi = True
    stoploss = -0.15  # hard cap (stake-relative); the real stop is structural
    use_custom_stoploss = True
    trailing_stop = False
    use_exit_signal = True  # required: custom_exit (the time stop) only runs when this is on

    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }
    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    # ---- pre-registered grid ---------------------------------------------------
    k_sigma = DecimalParameter(1.0, 5.0, default=2.5, decimals=2, space="buy", optimize=False)
    flow_pct = IntParameter(50, 99, default=90, space="buy", optimize=False)
    entry_atr = DecimalParameter(0.0, 1.0, default=0.0, decimals=2, space="buy", optimize=False)
    flow_mode = CategoricalParameter(
        ["high", "low", "any"], default="high", space="buy", optimize=False
    )
    # ---- fixed rules (documented, not tuned) -----------------------------------
    move_bars = IntParameter(2, 12, default=3, space="buy", optimize=False)
    sigma_days = IntParameter(1, 8, default=7, space="buy", optimize=False)
    flow_days = IntParameter(2, 8, default=7, space="buy", optimize=False)
    entry_valid_min = IntParameter(5, 60, default=15, space="buy", optimize=False)
    funding_buffer_min = IntParameter(0, 30, default=10, space="buy", optimize=False)
    funding_hours = (0, 8, 16)
    fill_through_ticks = IntParameter(0, 5, default=0, space="buy", optimize=False)
    tp_retrace = DecimalParameter(0.1, 1.0, default=0.5, decimals=2, space="sell", optimize=False)
    stop_range_mult = DecimalParameter(
        0.25, 3.0, default=1.0, decimals=2, space="sell", optimize=False
    )
    time_stop_min = IntParameter(0, 480, default=60, space="sell", optimize=False)
    risk_per_trade_pct = DecimalParameter(
        0.0, 5.0, default=1.0, decimals=2, space="buy", optimize=False
    )
    leverage_level = DecimalParameter(
        1.0, 10.0, default=3.0, decimals=1, space="buy", optimize=False
    )

    taker_dir = "user_data/data/binance_taker"

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self._taker: dict[str, DataFrame | None] = {}

    # ---- taker volume ----------------------------------------------------------
    def _taker_path(self, pair: str) -> Path:
        base = pair.split("/")[0]
        d = Path(os.environ.get("FLUSHREV_TAKER_DIR", self.taker_dir))
        if not d.is_absolute():
            d = Path(self.config.get("user_data_dir", "user_data")).parent / d
        return d / f"{base}USDT_5m.feather"

    def _load_taker(self, pair: str) -> DataFrame | None:
        if pair not in self._taker:
            path = self._taker_path(pair)
            if not path.exists():
                logger.warning(
                    "Taker file %s not found - run user_data/scripts/fetch_binance_taker.py", path
                )
                self._taker[pair] = None
            else:
                t = pd.read_feather(path)[["date", "taker_buy_volume", "volume"]]
                self._taker[pair] = t.rename(columns={"volume": "kl_volume"})
        return self._taker[pair]

    # ---- indicators ------------------------------------------------------------
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        df = dataframe
        taker = self._load_taker(metadata["pair"])
        if taker is not None:
            df = df.merge(taker, on="date", how="left")
        else:
            df["taker_buy_volume"] = np.nan
            df["kl_volume"] = np.nan

        n = int(self.move_bars.value)
        df["ret_n"] = df["close"] / df["close"].shift(n) - 1
        # trailing std of the n-bar return, previous candles only
        df["ret_sd"] = (
            df["ret_n"]
            .rolling(int(self.sigma_days.value) * BARS_PER_DAY, min_periods=BARS_PER_DAY)
            .std()
            .shift(1)
        )
        vol_n = df["kl_volume"].rolling(n).sum()
        buy_n = df["taker_buy_volume"].rolling(n).sum()
        df["buy_share"] = buy_n / vol_n.where(vol_n > 0)
        df["sell_share"] = 1 - df["buy_share"]

        w = int(self.flow_days.value) * BARS_PER_DAY
        minp = min(w, 3 * BARS_PER_DAY)
        q = float(self.flow_pct.value) / 100
        roll = df["buy_share"].rolling(w, min_periods=minp)
        # trailing quantiles, previous candles only. The sell-share p-quantile is
        # 1 - the buy-share (1-p)-quantile, because sell_share = 1 - buy_share.
        df["buy_q"] = roll.quantile(q).shift(1)
        df["sell_q"] = 1 - roll.quantile(1 - q).shift(1)
        df["buy_med"] = roll.quantile(0.5).shift(1)

        prev_close = df["close"].shift(1)
        tr = pd.concat(
            [
                df["high"] - df["low"],
                (df["high"] - prev_close).abs(),
                (df["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        df["atr"] = tr.ewm(alpha=1 / 14, adjust=False).mean()
        df["move_hi"] = df["high"].rolling(n).max()
        df["move_lo"] = df["low"].rolling(n).min()
        df["move_start"] = df["close"].shift(n)
        return df

    # ---- entries ---------------------------------------------------------------
    def _near_funding(self, dates: pd.Series) -> pd.Series:
        buf = int(self.funding_buffer_min.value)
        if buf <= 0:
            return pd.Series(False, index=dates.index)
        # the signal candle closes 5 minutes after its open; the order is placed then
        t = dates + pd.Timedelta(minutes=5)
        mod = t.dt.hour * 60 + t.dt.minute
        near = pd.Series(False, index=dates.index)
        for h in self.funding_hours:
            dist = (mod - h * 60).abs()
            dist = np.minimum(dist, 1440 - dist)
            near |= dist <= buf
        return near

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        df = dataframe
        k = float(self.k_sigma.value)
        down = df["ret_n"] <= -k * df["ret_sd"]
        up = df["ret_n"] >= k * df["ret_sd"]
        mode = self.flow_mode.value
        if mode == "high":
            long_flow = df["sell_share"] >= df["sell_q"]
            short_flow = df["buy_share"] >= df["buy_q"]
        elif mode == "low":
            # control: the move happened WITHOUT dominant taker flow in its direction
            long_flow = df["sell_share"] < (1 - df["buy_med"])
            short_flow = df["buy_share"] < df["buy_med"]
        else:
            long_flow = df["buy_share"].notna()
            short_flow = df["buy_share"].notna()
        ok = df["ret_sd"].notna() & ~self._near_funding(df["date"]) & (df["volume"] > 0)

        e = float(self.entry_atr.value)
        retr = float(self.tp_retrace.value)
        smult = float(self.stop_range_mult.value)
        rng = df["move_hi"] - df["move_lo"]
        # long (fade a down-move)
        df["long_entry"] = df["close"] - e * df["atr"]
        df["long_tp"] = df["close"] + retr * (df["move_start"] - df["close"])
        df["long_stop"] = df["move_lo"] - smult * rng
        # short (fade an up-move)
        df["short_entry"] = df["close"] + e * df["atr"]
        df["short_tp"] = df["close"] - retr * (df["close"] - df["move_start"])
        df["short_stop"] = df["move_hi"] + smult * rng

        go_long = ok & down & long_flow & (df["long_stop"] < df["long_entry"])
        go_short = ok & up & short_flow & (df["short_stop"] > df["short_entry"])
        go_long &= df["long_tp"] > df["long_entry"]
        go_short &= df["short_tp"] < df["short_entry"]
        tag = {"high": "flush", "low": "ctrl", "any": "any"}[mode]
        df.loc[go_long, ["enter_long", "enter_tag"]] = (1, f"{tag}_long")
        df.loc[go_short, ["enter_short", "enter_tag"]] = (1, f"{tag}_short")
        return df

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    # ---- helpers ---------------------------------------------------------------
    def _last_candle(self, pair: str) -> pd.Series | None:
        df, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        return None if df is None or df.empty else df.iloc[-1]

    def _signal_candle(self, pair: str, trade: Trade) -> pd.Series | None:
        df, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if df is None or df.empty:
            return None
        rows = df.loc[df["date"] < trade.open_date_utc]
        return None if rows.empty else rows.iloc[-1]

    def _levels(self, pair: str, trade: Trade) -> tuple[float, float] | None:
        stop, tp = trade.get_custom_data("stop"), trade.get_custom_data("tp")
        if stop is None or tp is None:
            c = self._signal_candle(pair, trade)
            if c is None:
                return None
            side = "short" if trade.is_short else "long"
            stop, tp = c.get(f"{side}_stop"), c.get(f"{side}_tp")
            if stop is None or tp is None or np.isnan(stop) or np.isnan(tp):
                return None
            trade.set_custom_data("stop", float(stop))
            trade.set_custom_data("tp", float(tp))
        return float(stop), float(tp)

    def _tick(self, pair: str) -> float:
        try:
            market = self.dp.market(pair) or {}
            prec = market.get("precision", {}).get("price")
            if prec is None:
                return 0.0
            return float(prec) if prec < 1 else 10.0 ** (-int(prec))
        except Exception:
            return 0.0

    # ---- callbacks -------------------------------------------------------------
    def custom_entry_price(self, pair: str, trade: Trade | None, current_time: datetime,
                           proposed_rate: float, entry_tag: str | None, side: str,
                           **kwargs) -> float:  # fmt: skip
        c = self._last_candle(pair)
        if c is None:
            return proposed_rate
        price = float(c[f"{side}_entry"])
        if np.isnan(price):
            return proposed_rate
        through = int(self.fill_through_ticks.value) * self._tick(pair)
        # Never chase: a long bids at or below the market, a short offers at or above it.
        if side == "long":
            return min(price, proposed_rate) - through
        return max(price, proposed_rate) + through

    def check_entry_timeout(self, pair: str, trade: Trade, order, current_time: datetime,
                            **kwargs) -> bool:  # fmt: skip
        waited = (current_time - order.order_date_utc).total_seconds()
        return waited >= int(self.entry_valid_min.value) * 60

    def custom_stake_amount(self, pair, current_time, current_rate, proposed_stake, min_stake,
                            max_stake, leverage, entry_tag, side, **kwargs) -> float:  # fmt: skip
        risk_pct = float(self.risk_per_trade_pct.value)
        c = self._last_candle(pair)
        if risk_pct <= 0 or c is None:
            return proposed_stake
        entry, stop = float(c[f"{side}_entry"]), float(c[f"{side}_stop"])
        if np.isnan(entry) or np.isnan(stop) or entry <= 0:
            return proposed_stake
        stop_dist = abs(entry - stop) / entry
        if stop_dist <= 0:
            return proposed_stake
        equity = self.wallets.get_total_stake_amount() if self.wallets else proposed_stake
        stake = equity * risk_pct / 100 / (stop_dist * leverage)
        if min_stake is not None and stake < min_stake:
            return 0
        return min(stake, max_stake)

    def leverage(self, pair, current_time, current_rate, proposed_leverage, max_leverage,
                 entry_tag, side, **kwargs) -> float:  # fmt: skip
        return min(float(self.leverage_level.value), max_leverage)

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit,
                        after_fill, **kwargs) -> float | None:  # fmt: skip
        lv = self._levels(pair, trade)
        if lv is None:
            return None
        stop, _ = lv
        sl = stoploss_from_absolute(
            stop, current_rate, is_short=trade.is_short, leverage=trade.leverage
        )
        return -sl if sl > 0 else -0.0001

    def custom_roi(self, pair, trade, current_time, trade_duration, entry_tag, side,
                   **kwargs) -> float | None:  # fmt: skip
        lv = self._levels(pair, trade)
        if lv is None or trade.open_rate <= 0:
            return None
        _, tp = lv
        dist = (
            (trade.open_rate - tp) if trade.is_short else (tp - trade.open_rate)
        ) / trade.open_rate
        return dist * trade.leverage if dist > 0 else None

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit,
                    **kwargs) -> str | None:  # fmt: skip
        mins = int(self.time_stop_min.value)
        if mins > 0 and current_time - trade.open_date_utc >= timedelta(minutes=mins):
            return "time_stop"
        return None
