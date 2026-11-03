#!/usr/bin/env python3
"""
Daily trend-following test on Binance USDT-M perps (pre-registered,
user_data/NOTES.md section 4j). Standalone daily simulation; reuses the
data.binance.vision loader and cache of carry_backtest.py (perp 1h closes and
funding, cached under user_data/data/carry/).

Signal, computed on the UTC daily close (last 1h close of the day) and executed
at that price, which is the next day's open:
    s = mean( sign(r20), sign(r60), sign(r120), sign(close - SMA50) )   in [-1, 1]
    long/flat  (LF): exposure = max(s, 0)
    long/short (LS): exposure = s
Sizing: target notional = exposure * min(0.30 / vol30, 1.5) * equity, where vol30 is
the 30-day standard deviation of daily log returns times sqrt(365).
Rebalance only when |target - current| >= 0.20 * equity; a move to zero or a change
of sign is always executed. No stops, no other filters.
Costs: taker 0.05% per side + slippage (2 bp BTC, 5 bp SUI) on traded notional.
Funding: every settlement pays units * rate * perp price (long pays positive rates).
Controls: C1 = same sizing with s = 1 (vol-targeted always long);
          C2 = 1x perp buy-and-hold with funding, never rebalanced.

Usage (repo root):
    python user_data/scripts/trend_backtest.py            # the pre-registered run
    python user_data/scripts/trend_backtest.py --selftest # synthetic checks, no download
"""

# ruff: noqa: S101  (asserts are the self-test)
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


sys.path.insert(0, str(Path(__file__).resolve().parent))

ANN = 365
TARGET_VOL = 0.30
MAX_LEV = 1.5
BAND = 0.20
TAKER = 0.0005
SLIP = {"BTCUSDT": 0.0002, "SUIUSDT": 0.0005}
COMPONENTS = ["r20", "r60", "r120", "sma50"]
OOS = ("2022-01-01", "2026-10-31")
SANITY = ("2020-02-01", "2021-12-31")
DOWNLOAD_START = {"BTCUSDT": "2019-09", "SUIUSDT": "2023-05"}


# ------------------------------------------------------------------ data -------
def daily_frame(perp: pd.DataFrame, funding: pd.DataFrame) -> pd.DataFrame:
    """One row per UTC day: close and funding cash per unit held over that day.

    A position set at the close of day d-1 (= 00:00 of day d) is held through the
    settlements stamped in (00:00 d, 00:00 d+1]; each pays rate * the perp close of
    the hour ending at the settlement.
    """
    h = perp.set_index("date")["close"].sort_index()
    close = h.resample("1D").last().dropna()
    f = funding.set_index("date")["rate"].sort_index()
    px = h.reindex(f.index - pd.Timedelta(hours=1)).to_numpy()
    cash = pd.Series(f.to_numpy() * px, index=f.index).dropna()
    # settlement exactly at 00:00 of d+1 belongs to day d
    day = (cash.index - pd.Timedelta(microseconds=1)).floor("D")
    fund = cash.groupby(day).sum()
    df = pd.DataFrame({"close": close})
    df["fund"] = fund.reindex(df.index).fillna(0.0)
    return df


def features(df: pd.DataFrame) -> pd.DataFrame:
    c = df["close"]
    out = pd.DataFrame(index=df.index)
    out["r20"] = np.sign(c / c.shift(20) - 1)
    out["r60"] = np.sign(c / c.shift(60) - 1)
    out["r120"] = np.sign(c / c.shift(120) - 1)
    out["sma50"] = np.sign(c - c.rolling(50).mean())
    out["vol"] = np.log(c).diff().rolling(30).std() * np.sqrt(ANN)
    return out


# ------------------------------------------------------------ simulation -------
def simulate(
    df: pd.DataFrame,
    expo: pd.Series,
    scale: pd.Series,
    start: pd.Timestamp,
    end: pd.Timestamp,
    cost: float,
    rebalance: bool = True,
) -> dict:
    """Equity per 1 unit of capital from `start` to `end` (inclusive days).

    The position for day `start` is set at the close of the previous day.
    expo/scale are indexed by day and known at that day's close.
    """
    idx = df.index
    i0 = idx.get_loc(start) - 1
    i1 = idx.get_loc(end)
    close, fund = df["close"].to_numpy(), df["fund"].to_numpy()
    e_arr, s_arr = expo.to_numpy(), scale.to_numpy()
    eq, units = 1.0, 0.0
    equity, traded, funding_paid, costs, days_in = [], 0.0, 0.0, 0.0, 0
    for i in range(i0, i1 + 1):
        if i > i0:
            fcash = units * fund[i]
            eq += units * (close[i] - close[i - 1]) - fcash
            funding_paid += fcash
            days_in += units != 0
            equity.append(eq)
            if eq <= 0:
                eq, units = 0.0, 0.0
                break
        if i == i1:
            break
        cur = units * close[i]
        if rebalance:
            tgt = e_arr[i] * s_arr[i] * eq
            if np.isnan(tgt):
                raise ValueError(f"signal not warm at {idx[i].date()}")
            flip = tgt == 0 or np.sign(tgt) != np.sign(cur)
            if abs(tgt - cur) >= BAND * eq or (flip and cur != 0) or (cur == 0 and tgt != 0):
                c = abs(tgt - cur) * cost
                eq -= c
                costs += c
                traded += abs(tgt - cur)
                units = tgt / close[i]
        elif units == 0:  # buy-and-hold: one entry at 1x
            c = eq * cost
            eq -= c
            costs += c
            traded += eq + c
            units = (eq + c) / close[i]
    ser = pd.Series(equity, index=idx[i0 + 1 : i0 + 1 + len(equity)])
    years = len(ser) / ANN
    return {
        "equity": ser,
        "turnover": traded / max(ser.mean(), 1e-9) / max(years, 1e-9),
        "funding": funding_paid,
        "costs": costs,
        "time_in": days_in / max(len(ser), 1),
    }


def stationary_bootstrap_sharpe(r: np.ndarray, block: int = 20, draws: int = 10_000) -> float:
    """One-sided 90% lower bound (10th percentile) of the annualised Sharpe."""
    rng = np.random.default_rng(20261103)
    n = len(r)
    pos = rng.integers(0, n, size=draws)
    tot, tot2 = np.zeros(draws), np.zeros(draws)
    for t in range(n):  # vectorised across draws, one day at a time
        if t:
            jump = rng.random(draws) < 1.0 / block
            pos = np.where(jump, rng.integers(0, n, size=draws), (pos + 1) % n)
        x = r[pos]
        tot += x
        tot2 += x * x
    mean = tot / n
    sd = np.sqrt(np.maximum(tot2 / n - mean**2, 0) * n / (n - 1))
    sh = np.where(sd > 0, mean / np.where(sd > 0, sd, 1) * np.sqrt(ANN), 0.0)
    return float(np.percentile(sh, 10))


def metrics(res: dict, boot: bool = False) -> dict:
    eq = pd.concat([pd.Series([1.0]), res["equity"].reset_index(drop=True)])
    r = eq.pct_change().dropna().to_numpy()
    years = len(r) / ANN
    sd = r.std(ddof=1)
    out = {
        "sharpe": r.mean() / sd * np.sqrt(ANN) if sd > 0 else float("nan"),
        "ann%": 100 * ((max(eq.iloc[-1], 1e-9)) ** (1 / years) - 1),
        "maxDD%": 100 * (eq / eq.cummax() - 1).min(),
        "time_in%": 100 * res["time_in"],
        "turnover/yr": res["turnover"],
        "funding%": -100 * res["funding"],
        "costs%": -100 * res["costs"],
    }
    if boot:
        out["boot90lo"] = stationary_bootstrap_sharpe(r)
    yr = res["equity"].groupby(res["equity"].index.year).last()
    prev = yr.shift(1).fillna(1.0)
    for y, v in (yr / prev - 1).items():
        out[str(y)] = 100 * v
    return out


# ------------------------------------------------------------------ runs -------
def scale_series(feat: pd.DataFrame) -> pd.Series:
    return np.minimum(TARGET_VOL / feat["vol"], MAX_LEV)


def run_window(
    df: pd.DataFrame, start: str, end: str, slip: float, fee_mult: float
) -> pd.DataFrame:
    feat = features(df)
    warm = feat.dropna().index[0] + pd.Timedelta(days=1)
    s0 = max(pd.Timestamp(start, tz="UTC"), warm)
    e0 = min(pd.Timestamp(end, tz="UTC"), df.index[-1])
    cost = (TAKER + slip) * fee_mult
    sc = scale_series(feat)
    ens = feat[COMPONENTS].mean(axis=1)
    rows = {}
    for tag, f in (("LF", lambda x: x.clip(lower=0)), ("LS", lambda x: x)):
        rows[f"{tag}_ensemble"] = metrics(simulate(df, f(ens), sc, s0, e0, cost), boot=True)
        for c in COMPONENTS:
            rows[f"{tag}_{c}"] = metrics(simulate(df, f(feat[c]), sc, s0, e0, cost))
    ones = pd.Series(1.0, index=df.index)
    rows["C1_voltarget_long"] = metrics(simulate(df, ones, sc, s0, e0, cost), boot=True)
    rows["C2_buyhold_1x"] = metrics(simulate(df, ones, ones, s0, e0, cost, rebalance=False))
    t = pd.DataFrame(rows).T
    t.attrs["window"] = (s0.date(), e0.date())
    return t


def verdict(norm: pd.DataFrame, dbl: pd.DataFrame, tag: str) -> list[tuple[str, bool, str]]:
    r, c1 = norm.loc[f"{tag}_ensemble"], norm.loc["C1_voltarget_long"]
    years = [c for c in norm.columns if c.isdigit()]
    comps = sum(norm.loc[f"{tag}_{c}", "sharpe"] > 0 for c in COMPONENTS)
    worst = min(r[y] for y in years)
    return [
        ("Sharpe >= 0.50", r["sharpe"] >= 0.50, f"{r['sharpe']:.2f}"),
        ("bootstrap 90% lower bound > 0", r["boot90lo"] > 0, f"{r['boot90lo']:.2f}"),
        (
            "Sharpe - C1 >= +0.15",
            r["sharpe"] - c1["sharpe"] >= 0.15,
            f"{r['sharpe'] - c1['sharpe']:+.2f} (C1 {c1['sharpe']:.2f})",
        ),
        (
            "maxDD <= 35% and <= 0.75 x C1",
            r["maxDD%"] >= -35 and r["maxDD%"] >= 0.75 * c1["maxDD%"],
            (
                f"{r['maxDD%']:.1f}% (C1 {c1['maxDD%']:.1f}%, "
                f"limit {max(-35, 0.75 * c1['maxDD%']):.1f}%)"
            ),
        ),
        ("worst calendar year >= -20%", worst >= -20, f"{worst:.1f}%"),
        (
            "double-cost Sharpe >= 0.35",
            dbl.loc[f"{tag}_ensemble", "sharpe"] >= 0.35,
            f"{dbl.loc[f'{tag}_ensemble', 'sharpe']:.2f}",
        ),
        (">= 3 of 4 components positive", comps >= 3, f"{comps}/4"),
    ]


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--symbol", nargs="+", default=["BTCUSDT", "SUIUSDT"])
    p.add_argument("--end", default="2026-10", help="last month to download, YYYY-MM")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    if a.selftest:
        selftest()
        return
    from carry_backtest import load

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)
    for sym in a.symbol:
        df = daily_frame(
            load(sym, "perp", DOWNLOAD_START[sym], a.end),
            load(sym, "funding", DOWNLOAD_START[sym], a.end),
        )
        slip = SLIP[sym]
        windows = [("sanity (no judgement)", SANITY), ("OUT OF SAMPLE", OOS)]
        if not sym.startswith("BTC"):
            windows = [("report only", OOS)]
        for label, (s, e) in windows:
            norm = run_window(df, s, e, slip, 1.0)
            w = norm.attrs["window"]
            print(f"\n{sym}  {label}  {w[0]} -> {w[1]}   normal costs")
            print(norm.round(2).to_string())
            if label != "OUT OF SAMPLE":
                if label == "report only":
                    sh = norm.loc["LF_ensemble", "sharpe"], norm.loc["LS_ensemble", "sharpe"]
                    print(
                        f"  SUI label: LF {'consistent' if sh[0] > 0 else 'inconsistent'}, "
                        f"LS {'consistent' if sh[1] > 0 else 'inconsistent'}"
                    )
                continue
            dbl = run_window(df, s, e, slip, 2.0)
            print(f"\n{sym}  {label}  doubled costs (ensembles and controls)")
            keep = ["LF_ensemble", "LS_ensemble", "C1_voltarget_long", "C2_buyhold_1x"]
            print(dbl.loc[keep, ["sharpe", "ann%", "maxDD%", "costs%"]].round(2).to_string())
            for tag in ("LF", "LS"):
                checks = verdict(norm, dbl, tag)
                ok = all(c[1] for c in checks)
                print(f"\n  {tag} ensemble on {sym}: {'PASS' if ok else 'FAIL'}")
                for name, passed, val in checks:
                    print(f"    [{'x' if passed else ' '}] {name:34s} {val}")
    print(
        "\nsharpe = annualised daily Sharpe; ann% = compound annual return; boot90lo = 10th"
        "\npercentile Sharpe from a stationary block bootstrap (20-day blocks, 10,000 draws);"
        "\nturnover/yr = traded notional / mean equity per year; funding% and costs% are"
        "\ncontributions to return (negative = paid); year columns are calendar-year returns."
    )


# --------------------------------------------------------------- selftest ------
def selftest() -> None:
    days = pd.date_range("2020-01-01", periods=400, freq="D", tz="UTC")

    def frame(close, fund=0.0):
        return pd.DataFrame({"close": np.asarray(close, float), "fund": fund}, index=days)

    ones = pd.Series(1.0, index=days)
    s, e = days[200], days[399]

    # 1. constant price, constant funding: P&L is exactly -units * funding
    df = frame(np.full(400, 100.0), fund=100.0 * 0.0001 * 3)
    r = simulate(df, ones, ones, s, e, cost=0.0)
    exp = 1.0 - 200 * 0.0003
    assert abs(r["equity"].iloc[-1] - exp) < 1e-9, (r["equity"].iloc[-1], exp)

    # 2. no costs, exposure 1, no band trades: 1x hold == buy-and-hold
    px = 100 * np.exp(np.cumsum(np.r_[0, np.full(399, 0.001)]))
    df = frame(px)
    a = simulate(df, ones, ones, s, e, cost=0.0)["equity"].iloc[-1]
    b = simulate(df, ones, ones, s, e, cost=0.0, rebalance=False)["equity"].iloc[-1]
    assert abs(a - px[399] / px[199]) < 1e-3, a  # band keeps it nearly un-rebalanced
    assert abs(b - px[399] / px[199]) < 1e-12, b

    # 3. costs: one entry at 1x costs exactly `cost` of capital
    df = frame(np.full(400, 100.0))
    r = simulate(df, ones, ones, s, e, cost=0.001)
    assert abs(r["equity"].iloc[-1] - 0.999) < 1e-12

    # 4. no look-ahead: changing prices after day k leaves equity up to k unchanged
    rng = np.random.default_rng(1)
    px = 100 * np.exp(np.cumsum(rng.normal(0, 0.03, 400)))
    df1 = frame(px)
    px2 = px.copy()
    px2[300:] *= 1.5
    df2 = frame(px2)
    out = []
    for d in (df1, df2):
        f = features(d)
        ens = f[COMPONENTS].mean(axis=1)
        out.append(simulate(d, ens, scale_series(f), s, e, 0.0007)["equity"])
    assert np.allclose(out[0].iloc[:99], out[1].iloc[:99]), "look-ahead"
    assert not np.allclose(out[0].iloc[99:], out[1].iloc[99:])

    # 5. sizing: 30% target, capped at 1.5x
    f = features(df1)
    assert (scale_series(f).dropna() <= MAX_LEV + 1e-12).all()

    # 6. funding bucketing: settlement at 00:00 of d+1 belongs to day d
    hrs = pd.date_range("2020-01-01", periods=72, freq="h", tz="UTC")
    perp = pd.DataFrame({"date": hrs, "close": 10.0})
    fund = pd.DataFrame(
        {"date": pd.to_datetime(["2020-01-01 08:00", "2020-01-02 00:00"], utc=True), "rate": 0.01}
    )
    d = daily_frame(perp, fund)
    assert abs(d["fund"].iloc[0] - 0.2) < 1e-12 and d["fund"].iloc[1] == 0, d

    # 7. bootstrap on iid noise with zero mean is centred near zero, below the point estimate
    r = rng.normal(0.001, 0.02, 1500)
    lo = stationary_bootstrap_sharpe(r, draws=2000)
    point = r.mean() / r.std(ddof=1) * np.sqrt(ANN)
    assert lo < point
    print("selftest: all 7 checks passed")


if __name__ == "__main__":
    main()
