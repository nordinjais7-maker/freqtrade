#!/usr/bin/env python3
"""
Funding-rate carry backtest for Binance USDT-M perpetuals (pre-registered,
user_data/NOTES.md section 4i). Not a Freqtrade strategy: Freqtrade cannot hold
a spot leg and a perp leg as one hedged position, so this is a standalone,
hour-by-hour simulation.

The trade: buy q units on spot and short q units of the USDT-M perp. Price moves
cancel except for the spot-perp basis; the short collects funding whenever the
rate is positive and pays it when negative.

Rules
  * always_on: enter at the start, hold to the end.
  * switched(X): at each funding settlement, compute the mean of the last 9
    settled rates (3 days at 8h), annualised. Enter when it is above X, exit when
    it is below X/4 (hysteresis keeps switching costs down). The decision uses
    only rates already settled and is executed at the NEXT hour's close.
Costs (per leg, per side): spot taker 0.10%, perp taker 0.05%, plus slippage
(1 bp BTC, 3 bp SUI). Capital per unit = spot notional + perp margin
(notional / leverage). Default leverage 2 on the perp leg.
Liquidation is not simulated: the report counts how often the perp leg's
unrealised loss would have used more than 80% of its margin before the next
daily rebalance, i.e. how often a real operator must move collateral.

Data (public, no key; cached under user_data/data/carry/):
  futures/um/monthly/fundingRate/<SYM>/<SYM>-fundingRate-YYYY-MM.zip
  spot/monthly/klines/<SYM>/1h/<SYM>-1h-YYYY-MM.zip
  futures/um/monthly/klines/<SYM>/1h/<SYM>-1h-YYYY-MM.zip

Usage (repo root):
    python user_data/scripts/carry_backtest.py --symbol BTCUSDT --start 2023-05 --end 2026-10 \\
        --periods 2023-05-12:2023-12-31 2024-01-01:2024-12-31
"""

import argparse
import io
import sys
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import requests


BASE = "https://data.binance.vision/data"
CACHE = Path("user_data/data/carry")
KLINE_COLS = [
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore",
]  # fmt: skip


# ---------------------------------------------------------------- data ---------
def _months(start: str, end: str) -> list[str]:
    return [p.strftime("%Y-%m") for p in pd.period_range(start, end, freq="M")]


def _fetch(url: str) -> bytes | None:
    for i in range(3):
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.content
        except Exception as e:  # retry, then report
            if i == 2:
                print(f"  failed {url.rsplit('/', 1)[-1]}: {e}")
                return None
            time.sleep(1.5 * (i + 1))
    return None


def _read_zip_csv(raw: bytes, names: list[str] | None) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        text = z.read(z.namelist()[0])
    has_header = not text.split(b"\n", 1)[0][:1].isdigit()
    df = pd.read_csv(io.BytesIO(text), header=0 if has_header else None)
    if not has_header and names:
        df.columns = names[: len(df.columns)]
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def parse_klines(raw: bytes) -> pd.DataFrame:
    df = _read_zip_csv(raw, KLINE_COLS)
    t = pd.to_numeric(df["open_time"])
    # Spot archives switched to microsecond timestamps in 2025; normalise to ms.
    t = np.where(t > 1e14, t // 1000, t)
    return pd.DataFrame(
        {"date": pd.to_datetime(t, unit="ms", utc=True), "close": pd.to_numeric(df["close"])}
    )


def parse_funding(raw: bytes) -> pd.DataFrame:
    df = _read_zip_csv(raw, ["calc_time", "funding_interval_hours", "last_funding_rate"])
    t = pd.to_numeric(df["calc_time"])
    return pd.DataFrame(
        {
            "date": pd.to_datetime(t, unit="ms", utc=True).dt.floor("h"),
            "rate": pd.to_numeric(df["last_funding_rate"]),
        }
    )


def load(symbol: str, kind: str, start: str, end: str) -> pd.DataFrame:
    """kind: funding | spot | perp. Cached per symbol and kind."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{symbol}_{kind}.feather"
    have = pd.read_feather(path) if path.exists() else None
    frames = [have] if have is not None else []
    done = set(have["date"].dt.strftime("%Y-%m")) if have is not None else set()
    for m in _months(start, end):
        if m in done:
            continue
        if kind == "funding":
            url = f"{BASE}/futures/um/monthly/fundingRate/{symbol}/{symbol}-fundingRate-{m}.zip"
            parse = parse_funding
        elif kind == "spot":
            url = f"{BASE}/spot/monthly/klines/{symbol}/1h/{symbol}-1h-{m}.zip"
            parse = parse_klines
        else:
            url = f"{BASE}/futures/um/monthly/klines/{symbol}/1h/{symbol}-1h-{m}.zip"
            parse = parse_klines
        raw = _fetch(url)
        if raw is None:
            print(f"  {symbol} {kind} {m}: not on the archive")
            continue
        frames.append(parse(raw))
        print(f"  {symbol} {kind} {m}", flush=True)
        time.sleep(0.1)
    if not frames:
        sys.exit(f"No {kind} data for {symbol}")
    df = pd.concat(frames).drop_duplicates("date").sort_values("date").reset_index(drop=True)
    df.to_feather(path)
    return df


# ---------------------------------------------------------- simulation ---------
@dataclass
class Costs:
    spot_fee: float = 0.0010
    perp_fee: float = 0.0005
    slippage: float = 0.0001  # per leg per side
    leverage: float = 2.0

    def side_cost(self) -> float:
        """Cost of entering OR exiting both legs, as a fraction of notional."""
        return self.spot_fee + self.perp_fee + 2 * self.slippage


def build_frame(spot: pd.DataFrame, perp: pd.DataFrame, funding: pd.DataFrame) -> pd.DataFrame:
    df = spot.rename(columns={"close": "spot"}).merge(
        perp.rename(columns={"close": "perp"}), on="date", how="inner"
    )
    df = df.merge(funding, on="date", how="left")
    return df.sort_values("date").reset_index(drop=True)


def signal_series(df: pd.DataFrame, lookback: int = 9) -> pd.Series:
    """Annualised mean of the last `lookback` SETTLED funding rates, known at each hour."""
    f = df.loc[df["rate"].notna(), ["date", "rate"]].copy()
    hours = f["date"].diff().dt.total_seconds().div(3600).median()
    per_year = 365 * 24 / (hours if hours and hours > 0 else 8)
    f["ann"] = f["rate"].rolling(lookback, min_periods=lookback).mean() * per_year
    # A rate settled at time t is known from t on (the settlement hour's close).
    return df[["date"]].merge(f[["date", "ann"]], on="date", how="left")["ann"].ffill()


def _decide(rule: str, threshold: float, ann: float, in_pos: bool, want: bool, last: bool) -> bool:
    """Position wanted for the NEXT hour (hysteresis: enter above X, exit below X/4)."""
    if last:
        return False
    if rule == "always_on":
        return True
    if np.isnan(ann):
        return want
    if not in_pos and ann > threshold:
        return True
    if in_pos and ann < threshold / 4:
        return False
    return want


def simulate(df: pd.DataFrame, rule: str, threshold: float, costs: Costs) -> dict:
    """Return the hourly equity curve and trade stats for one rule.

    Equity is measured per 1 USDT of starting capital. Position size is re-set at
    each entry to the current equity (no compounding inside a holding period).
    """
    ann = signal_series(df).to_numpy()
    spot = df["spot"].to_numpy()
    perp = df["perp"].to_numpy()
    rate = df["rate"].to_numpy()
    n = len(df)
    eq = np.empty(n)
    equity, q, in_pos, entry_perp = 1.0, 0.0, False, 0.0
    trades = 0
    funding_sum = cost_sum = basis_sum = 0.0
    margin_events = 0
    hours_in = 0
    want = False
    lev = costs.leverage
    for i in range(n):
        # P&L over the hour that just ended, if holding
        if in_pos and i > 0:
            basis = q * ((spot[i] - spot[i - 1]) - (perp[i] - perp[i - 1]))
            equity += basis
            basis_sum += basis
            if not np.isnan(rate[i]):
                f = q * perp[i] * rate[i]  # short receives a positive rate
                equity += f
                funding_sum += f
            hours_in += 1
            # margin use on the perp leg since entry (rebalanced daily in practice)
            if (perp[i] - entry_perp) * q > 0.8 * (q * entry_perp / lev):
                margin_events += 1
                entry_perp = perp[i]  # assume collateral was moved; reset reference
            if i % 24 == 0:
                entry_perp = perp[i]
        # act on the decision made at the previous hour (no lookahead)
        if want and not in_pos:
            notional = equity / (1 + 1 / lev)
            q = notional / spot[i]
            c = notional * costs.side_cost()
            equity -= c
            cost_sum += c
            in_pos, entry_perp, trades = True, perp[i], trades + 1
        elif not want and in_pos:
            c = q * spot[i] * costs.side_cost()
            equity -= c
            cost_sum += c
            in_pos, q = False, 0.0
        eq[i] = equity
        want = _decide(rule, threshold, ann[i], in_pos, want, last=i >= n - 2)
    return {
        "equity": pd.Series(eq, index=df["date"]),
        "trades": trades,
        "funding": funding_sum,
        "costs": cost_sum,
        "basis": basis_sum,
        "time_in": hours_in / max(n - 1, 1),
        "margin_events": margin_events,
    }


def metrics(res: dict) -> dict:
    eq = res["equity"]
    daily = eq.resample("1D").last().dropna()
    rets = daily.pct_change().dropna()
    years = max((eq.index[-1] - eq.index[0]).total_seconds() / (365 * 86400), 1e-9)
    total = eq.iloc[-1] / eq.iloc[0] - 1
    sharpe = rets.mean() / rets.std() * np.sqrt(365) if rets.std() > 0 else float("nan")
    dd = (eq / eq.cummax() - 1).min()
    return {
        "net%": 100 * total,
        "ann%": 100 * ((1 + total) ** (1 / years) - 1),
        "sharpe": sharpe,
        "maxDD%": 100 * dd,
        "time_in%": 100 * res["time_in"],
        "trades": res["trades"],
        "funding%": 100 * res["funding"],
        "costs%": 100 * res["costs"],
        "basis%": 100 * res["basis"],
        "margin_ev": res["margin_events"],
    }


RULES = [("always_on", 0.0), ("switched", 0.05), ("switched", 0.10), ("switched", 0.20)]


def run_period(df_all: pd.DataFrame, start: str, end: str, costs: Costs) -> pd.DataFrame:
    # include 7 days before the start so the 9-settlement signal is warm
    lo = pd.Timestamp(start, tz="UTC")
    hi = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)
    warm = df_all[(df_all["date"] >= lo - pd.Timedelta(days=7)) & (df_all["date"] < hi)]
    rows = {}
    for rule, x in RULES:
        res = simulate(warm.reset_index(drop=True), rule, x, costs)
        res["equity"] = res["equity"][res["equity"].index >= lo]
        res["equity"] = res["equity"] / res["equity"].iloc[0]
        name = "always_on" if rule == "always_on" else f"switched_{int(x * 100)}"
        rows[name] = metrics(res)
    return pd.DataFrame(rows).T


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--symbol", nargs="+", default=["BTCUSDT", "SUIUSDT"])
    p.add_argument("--start", default="2023-05", help="first month to download, YYYY-MM")
    p.add_argument("--end", default="2026-10", help="last month to download, YYYY-MM")
    p.add_argument(
        "--periods", nargs="+", required=True, help="evaluation windows, START:END (YYYY-MM-DD)"
    )
    p.add_argument("--leverage", type=float, default=2.0)
    p.add_argument("--fee-mult", type=float, default=1.0, help="multiply all fees (stress)")
    a = p.parse_args()

    pd.set_option("display.width", 160)
    for sym in a.symbol:
        slip = 0.0001 if sym.startswith("BTC") else 0.0003
        costs = Costs(
            spot_fee=0.0010 * a.fee_mult,
            perp_fee=0.0005 * a.fee_mult,
            slippage=slip * a.fee_mult,
            leverage=a.leverage,
        )
        df = build_frame(
            load(sym, "spot", a.start, a.end),
            load(sym, "perp", a.start, a.end),
            load(sym, "funding", a.start, a.end),
        )
        for per in a.periods:
            s, e = per.split(":")
            print(f"\n{sym}  {s} -> {e}   (per 1 USDT of capital; perp leverage {a.leverage})")
            print(run_period(df, s, e, costs).round(2).to_string())
    print(
        "\nnet% = total return on capital, ann% = annualised, maxDD% = worst peak-to-trough,"
        "\nfunding% / costs% / basis% = contributions to net, time_in% = share of hours"
        "\nhedged, margin_ev = times the perp leg would have needed more collateral."
    )


if __name__ == "__main__":
    main()
