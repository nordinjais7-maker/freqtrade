"""
SuiFlushShort - Freqtrade strategy built from the "SUI Flush Playbook" backtest
(OKX data, 1 Nov 2026). Original port supplied by the repository owner; this
version keeps its rules and adds backtest fidelity, a second flow-data source and
research parameters. Where the two differ, the comments say so.

Entry (short), 15m:
  * first 15m close below the prior 6h low (24 bars)               -> "range break"
  * long/short account ratio is "crowded":
        ls_mode = absolute   -> ls >= ls_min (default 2.6, the OKX number)
        ls_mode = percentile -> ls >= its rolling ls_pct quantile over ls_window_hours
  * disarm when OI rose >= 1% in 4h AND L/S rose over 2h            -> crowded-rebuild squeeze risk
  * optional: BTC also closes below its own 6h low on the same bar  (use_btc_filter)

Exit / management:
  * stop  = 0.2% above max(break candle high, broken 6h low)        (structural, ~1% median)
  * T1    = 1R  -> close half, stop to breakeven   (adjust_trade_position)
  * T2    = 2R  -> close the rest                  (custom_roi: checked against the candle's
                                                    low in backtests, so it fills intra-candle)
  * cover on reclaim: a 15m close above the high of the candle that made the lowest low
    since entry, within 4 candles of that low
  * time stop: 2h if T1 not hit, 4h hard limit

Flow data (hourly long/short ratio + open interest):
  * flow_source = okx     -> user_data/data/okx_flow/SUI-USDT-SWAP_1H.feather
                             (user_data/scripts/fetch_okx_flow.py; OKX keeps ~60 days)
  * flow_source = binance -> user_data/data/binance_flow/SUIUSDT_1H.feather
                             (user_data/scripts/fetch_binance_flow.py; years of history
                             from data.binance.vision). Binance's ratio reads lower than
                             OKX's, so use ls_mode = percentile or a lower ls_min with it.
  * live / dry-run refresh the chosen source from its public API every 5 minutes;
    if that fails, entries pause and the bot keeps running.
  * no lookahead: an hourly row is used only after its hour has closed.
  * SUIFLUSH_FLOW_FILE (environment variable) overrides the file path (tests).

Backtest reference from the playbook (OKX, Aug-Nov 2026, before fees):
RB + L/S >= 2.6 -> +0.47R/trade (n=78). Plain range break ~ breakeven after fees.

Backtest with `--timeframe-detail 1m`: T1 (partial exit) and the reclaim / time exits
are evaluated at candle opens, so without detail data they fire late.
Not financial advice. Dry-run first.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

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
    merge_informative_pair,
    stoploss_from_absolute,
)


logger = logging.getLogger(__name__)

OKX_BASE = "https://www.okx.com/api/v5/"
BINANCE_FAPI = "https://fapi.binance.com/futures/data/"


class SuiFlushShort(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "15m"
    can_short = True
    process_only_new_candles = True
    startup_candle_count = 100

    # Hard fallback stop; the real stop comes from custom_stoploss.
    stoploss = -0.05
    use_custom_stoploss = True
    trailing_stop = False
    minimal_roi = {"0": 100}  # static ROI disabled; T2 comes from custom_roi
    use_custom_roi = True

    position_adjustment_enable = True
    max_entry_position_adjustment = 0  # no adding; partial exits are still allowed

    # ---- parameters (defaults = playbook) ---------------------------------------------
    # Flow filter
    require_flow = BooleanParameter(default=True, space="sell", optimize=False)
    flow_source = CategoricalParameter(
        ["okx", "binance"], default="okx", space="sell", optimize=False
    )
    ls_mode = CategoricalParameter(
        ["absolute", "percentile"], default="absolute", space="sell", optimize=False
    )
    ls_min = DecimalParameter(1.0, 4.0, default=2.6, decimals=2, space="sell", optimize=False)
    ls_pct = DecimalParameter(0.5, 0.99, default=0.8, decimals=2, space="sell", optimize=False)
    ls_window_hours = IntParameter(48, 2160, default=720, space="sell", optimize=False)
    disarm_crowded = BooleanParameter(default=True, space="sell", optimize=False)
    use_btc_filter = BooleanParameter(default=False, space="sell", optimize=False)
    # Range / risk geometry
    lookback_bars = IntParameter(8, 96, default=24, space="buy", optimize=False)  # 6h of 15m
    stop_buffer_pct = DecimalParameter(
        0.0, 1.0, default=0.2, decimals=2, space="sell", optimize=False
    )
    use_t1 = BooleanParameter(default=True, space="sell", optimize=False)
    t1_r = DecimalParameter(0.5, 2.0, default=1.0, decimals=2, space="sell", optimize=False)
    t2_r = DecimalParameter(1.0, 5.0, default=2.0, decimals=2, space="sell", optimize=False)
    use_reclaim_exit = BooleanParameter(default=True, space="sell", optimize=False)
    reclaim_window = IntParameter(1, 12, default=4, space="sell", optimize=False)
    time_stop_t1_hours = IntParameter(0, 24, default=2, space="sell", optimize=False)  # 0 = off
    time_stop_max_hours = IntParameter(0, 48, default=4, space="sell", optimize=False)  # 0 = off
    # Sizing
    risk_per_trade_pct = DecimalParameter(
        0.0, 5.0, default=1.0, decimals=2, space="buy", optimize=False
    )
    weekend_factor = DecimalParameter(
        0.0, 1.0, default=0.5, decimals=2, space="buy", optimize=False
    )
    leverage_level = DecimalParameter(
        1.0, 10.0, default=5.0, decimals=1, space="buy", optimize=False
    )

    btc_pair = "BTC/USDT:USDT"
    fee_buffer = 0.001  # ~0.1% round-trip taker fees, added to the stop distance when sizing

    flow_files = {
        "okx": "user_data/data/okx_flow/SUI-USDT-SWAP_1H.feather",
        "binance": "user_data/data/binance_flow/SUIUSDT_1H.feather",
    }
    okx_inst = "SUI-USDT-SWAP"
    binance_symbol = "SUIUSDT"
    flow_refresh = timedelta(minutes=5)

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self._flow: DataFrame | None = None
        self._flow_loaded_at: datetime | None = None

    # ---- informative -------------------------------------------------------------------
    def informative_pairs(self):
        return [(self.btc_pair, self.timeframe)]

    # ---- flow data ---------------------------------------------------------------------
    def _flow_path(self) -> Path:
        override = os.environ.get("SUIFLUSH_FLOW_FILE")
        p = Path(override) if override else Path(self.flow_files[self.flow_source.value])
        if not p.is_absolute():
            p = Path(self.config.get("user_data_dir", "user_data")).parent / p
        return p

    def _load_flow_file(self) -> DataFrame | None:
        path = self._flow_path()
        if not path.exists():
            logger.warning(
                "Flow file %s not found - run the matching fetch script in user_data/scripts", path
            )
            return None
        return pd.read_feather(path)

    def _fetch_flow_live(self) -> DataFrame | None:
        """Last ~100 (OKX) / ~500 (Binance) hourly rows of L/S and OI, public, no key."""
        try:
            import requests

            def get(url: str, ok=lambda j: True, data=lambda j: j):
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                j = r.json()
                return data(j) if ok(j) else []

            if self.flow_source.value == "okx":

                def okx(path: str):
                    return get(
                        OKX_BASE + path,
                        lambda j: j.get("code") == "0",
                        lambda j: j.get("data", []),
                    )

                ls = okx(
                    "rubik/stat/contracts/long-short-account-ratio-contract"
                    f"?instId={self.okx_inst}&period=1H&limit=100"
                )
                oi = okx(
                    f"rubik/stat/contracts/open-interest-history?instId={self.okx_inst}"
                    "&period=1H&limit=100"
                )
                if not ls or not oi:
                    return None
                lsd = pd.DataFrame(ls, columns=["ts", "ls"])
                oid = pd.DataFrame([r[:2] for r in oi], columns=["ts", "oi"])
            else:
                ls = get(
                    f"{BINANCE_FAPI}globalLongShortAccountRatio?symbol={self.binance_symbol}"
                    "&period=1h&limit=500"
                )
                oi = get(
                    f"{BINANCE_FAPI}openInterestHist?symbol={self.binance_symbol}"
                    "&period=1h&limit=500"
                )
                if not ls or not oi:
                    return None
                lsd = pd.DataFrame(ls)[["timestamp", "longShortRatio"]].rename(
                    columns={"timestamp": "ts", "longShortRatio": "ls"}
                )
                oid = pd.DataFrame(oi)[["timestamp", "sumOpenInterest"]].rename(
                    columns={"timestamp": "ts", "sumOpenInterest": "oi"}
                )
            df = lsd.merge(oid, on="ts", how="outer")
            df["date"] = pd.to_datetime(df["ts"].astype("int64"), unit="ms", utc=True)
            df["ls"] = df["ls"].astype(float)
            df["oi"] = df["oi"].astype(float)
            return df[["date", "ls", "oi"]].sort_values("date").reset_index(drop=True)
        except Exception as e:  # network errors must never kill the bot
            logger.warning("%s flow fetch failed: %s", self.flow_source.value, e)
            return None

    def bot_loop_start(self, current_time: datetime, **kwargs) -> None:
        if self._flow is None:
            self._flow = self._load_flow_file()
            self._flow_loaded_at = current_time
        if self.dp.runmode.value not in ("live", "dry_run"):
            return
        if (
            self._flow_loaded_at
            and current_time - self._flow_loaded_at < self.flow_refresh
            and self._flow is not None
        ):
            return
        fresh = self._fetch_flow_live()
        if fresh is not None:
            base = self._flow if self._flow is not None else fresh.iloc[0:0]
            self._flow = (
                pd.concat([base, fresh])
                .drop_duplicates("date", keep="last")
                .sort_values("date")
                .reset_index(drop=True)
            )
        self._flow_loaded_at = current_time

    def _merge_flow(self, df: DataFrame) -> DataFrame:
        flow = self._flow if self._flow is not None else self._load_flow_file()
        cols = ["ls", "ls_ch2", "oi_ch4", "ls_q"]
        if flow is None or flow.empty:
            for c in cols:
                df[c] = np.nan
            return df
        f = flow.sort_values("date").copy()
        f["ls_ch2"] = f["ls"] - f["ls"].shift(2)
        f["oi_ch4"] = f["oi"] / f["oi"].shift(4) - 1
        # Rolling quantile of the ratio's own history (percentile mode). It includes the
        # current row, which is itself only released after its hour has closed.
        w = int(self.ls_window_hours.value)
        f["ls_q"] = (
            f["ls"].rolling(w, min_periods=max(24, w // 4)).quantile(float(self.ls_pct.value))
        )
        # an hourly row is only known once its hour has closed -> available at date + 1h
        f["avail"] = f["date"] + pd.Timedelta(hours=1)
        df = df.sort_values("date").copy()
        df["close_time"] = df["date"] + pd.Timedelta(minutes=15)
        out = pd.merge_asof(
            df,
            f[["avail", *cols]].sort_values("avail"),
            left_on="close_time",
            right_on="avail",
            direction="backward",
            tolerance=pd.Timedelta(hours=3),
        )
        return out.drop(columns=["avail", "close_time"])

    # ---- indicators --------------------------------------------------------------------
    @staticmethod
    def _range_break(df: DataFrame, n: int) -> DataFrame:
        df["rlo"] = df["low"].rolling(n).min().shift(1)  # lowest low of the prior n bars
        df["rb"] = (df["close"] < df["rlo"]) & (df["close"].shift(1) >= df["rlo"].shift(1))
        return df

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        n = int(self.lookback_bars.value)
        df = self._range_break(dataframe, n)
        df["vr"] = df["volume"] / df["volume"].rolling(20).mean().shift(1)
        df["struct_stop"] = np.maximum(df["high"], df["rlo"]) * (
            1 + float(self.stop_buffer_pct.value) / 100
        )

        if self.dp:
            btc = self.dp.get_pair_dataframe(pair=self.btc_pair, timeframe=self.timeframe)
            if btc is not None and not btc.empty:
                btc = self._range_break(btc.copy(), n)
                btc["btc_below"] = btc["close"] < btc["rlo"]
                df = merge_informative_pair(
                    df, btc[["date", "btc_below"]], self.timeframe, self.timeframe, ffill=True
                )
                df = df.rename(columns={f"btc_below_{self.timeframe}": "btc_below"})
        if "btc_below" not in df.columns:
            df["btc_below"] = False

        df = self._merge_flow(df)
        return df

    # ---- entry -------------------------------------------------------------------------
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        df = dataframe
        cond = df["rb"] & (df["volume"] > 0)

        if self.require_flow.value:
            if self.ls_mode.value == "percentile":
                cond &= df["ls"] >= df["ls_q"]
            else:
                cond &= df["ls"] >= float(self.ls_min.value)
        if self.disarm_crowded.value:
            crowded = (df["oi_ch4"] >= 0.01) & (df["ls_ch2"] > 0)
            cond &= ~crowded.fillna(False)
        if self.use_btc_filter.value:
            cond &= df["btc_below"].fillna(False).astype(bool)

        df.loc[cond, ["enter_short", "enter_tag"]] = (1, "rb6h_ls")
        return df

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_short"] = 0
        return dataframe

    # ---- helpers -----------------------------------------------------------------------
    def _signal_candle(self, pair: str, trade: Trade) -> pd.Series | None:
        df, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if df is None or df.empty:
            return None
        # the signal candle closed at (or just before) the open time of the trade
        sig_open = trade.open_date_utc - timedelta(minutes=15)
        rows = df[df["date"] <= sig_open]
        return rows.iloc[-1] if not rows.empty else None

    def _levels(self, pair: str, trade: Trade) -> tuple[float, float] | None:
        stop = trade.get_custom_data("stop")
        if stop is None:
            sig = self._signal_candle(pair, trade)
            if sig is None or pd.isna(sig.get("struct_stop", np.nan)):
                return None
            stop = float(sig["struct_stop"])
            if stop <= trade.open_rate:  # safety: never a stop below entry on a short
                stop = trade.open_rate * 1.006
            trade.set_custom_data("stop", stop)
        r = float(stop) - trade.open_rate
        return float(stop), r

    # ---- sizing ------------------------------------------------------------------------
    def leverage(
        self,
        pair,
        current_time,
        current_rate,
        proposed_leverage,
        max_leverage,
        entry_tag,
        side,
        **kwargs,
    ):
        return min(float(self.leverage_level.value), max_leverage)

    def custom_stake_amount(
        self,
        pair,
        current_time,
        current_rate,
        proposed_stake,
        min_stake,
        max_stake,
        leverage,
        entry_tag,
        side,
        **kwargs,
    ):
        risk_pct = float(self.risk_per_trade_pct.value)
        if risk_pct <= 0:
            return proposed_stake
        df, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if df is None or df.empty:
            return proposed_stake
        stop = float(df.iloc[-1]["struct_stop"])
        stop_pct = max((stop - current_rate) / current_rate, 0.003)
        balance = self.wallets.get_total_stake_amount() if self.wallets else proposed_stake
        risk = balance * risk_pct / 100
        if current_time.weekday() >= 5:
            risk *= float(self.weekend_factor.value)
        notional = risk / (stop_pct + self.fee_buffer)
        stake = notional / max(leverage, 1.0)
        return float(min(max(stake, min_stake or 0), max_stake))

    # ---- stop --------------------------------------------------------------------------
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
        lv = self._levels(pair, trade)
        if lv is None:
            return None
        stop, _ = lv
        if trade.get_custom_data("t1_done"):
            stop = trade.open_rate  # breakeven after T1
        return stoploss_from_absolute(stop, current_rate, is_short=True, leverage=trade.leverage)

    # ---- T2 as ROI: evaluated against the candle extreme in backtests ------------------
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
        lv = self._levels(pair, trade)
        if lv is None or trade.open_rate <= 0:
            return None
        _, r = lv
        return float(self.t2_r.value) * r / trade.open_rate * trade.leverage

    # ---- partial exit at T1 ------------------------------------------------------------
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
    ):
        if not self.use_t1.value or trade.get_custom_data("t1_done") or trade.has_open_orders:
            return None
        lv = self._levels(trade.pair, trade)
        if lv is None:
            return None
        _, r = lv
        if current_rate <= trade.open_rate - float(self.t1_r.value) * r:
            trade.set_custom_data("t1_done", True)
            return -(trade.stake_amount / 2), "t1_1R"
        return None

    # ---- exits -------------------------------------------------------------------------
    def custom_exit(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ):
        lv = self._levels(pair, trade)
        if lv is None:
            return None
        age = current_time - trade.open_date_utc

        t_max = int(self.time_stop_max_hours.value)
        if t_max > 0 and age >= timedelta(hours=t_max):
            return "time_4h"
        t1h = int(self.time_stop_t1_hours.value)
        if t1h > 0 and not trade.get_custom_data("t1_done") and age >= timedelta(hours=t1h):
            return "time_2h"

        if not self.use_reclaim_exit.value:
            return None
        # reclaim: close above the high of the lowest-low candle since entry, within N candles
        df, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if df is None or df.empty:
            return None
        since = df[df["date"] >= trade.open_date_utc]
        if len(since) >= 2:
            low_idx = since["low"].idxmin()
            low_row = df.loc[low_idx]
            last = df.iloc[-1]
            bars_since_low = len(df.loc[low_idx:]) - 1
            if 1 <= bars_since_low <= int(self.reclaim_window.value) and (
                last["close"] > low_row["high"]
            ):
                return "reclaim"
        return None
