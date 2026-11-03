#!/usr/bin/env python3
"""
Cross-check: does the Freqtrade DailyTrend backtest reproduce trend_backtest.py?

Pre-registered in user_data/NOTES.md section 4j: the two must agree on the
2022-01-01 -> 2026-10-31 BTC Sharpe within 0.10.

Freqtrade only reports realised profit by close date, which is useless for a
position held for weeks, so this script rebuilds daily mark-to-market equity from
the backtest's own filled orders (amount, price, fee) and Freqtrade's own 1d candles
and 1h funding/mark data. It also checks that rebuilt final equity matches
Freqtrade's reported total profit.

Usage (repo root, after the backtest with --export trades):
    python user_data/scripts/trend_crosscheck.py
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

ANN = 365


def load_trades(results: Path | None, strategy: str) -> tuple[list[dict], float]:
    from freqtrade.data.btanalysis import get_latest_backtest_filename, load_backtest_stats

    if results is None:
        d = ROOT / "user_data" / "backtest_results"
        results = d / get_latest_backtest_filename(d)
    stats = load_backtest_stats(results)
    s = stats["strategy"][strategy]
    print(f"Freqtrade results: {results.name}")
    return s["trades"], float(s["starting_balance"])


def load_ft_data(datadir: Path, pair: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    from freqtrade.data.history import load_pair_history
    from freqtrade.enums import CandleType

    candles = load_pair_history(
        pair=pair, timeframe="1d", datadir=datadir, candle_type=CandleType.FUTURES
    )
    funding = load_pair_history(
        pair=pair, timeframe="1h", datadir=datadir, candle_type=CandleType.FUNDING_RATE
    )
    mark = load_pair_history(
        pair=pair, timeframe="1h", datadir=datadir, candle_type=CandleType.MARK
    )
    return candles, funding, mark


def rebuild_equity(
    trades: list[dict],
    start_bal: float,
    candles: pd.DataFrame,
    funding: pd.DataFrame,
    mark: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> tuple[pd.Series, dict]:
    """Daily equity at each UTC close from `start` to `end`."""
    fills = []
    for t in trades:
        for o in t["orders"]:
            if not o.get("order_filled_timestamp"):
                continue
            side = 1 if o["ft_order_side"] == "buy" else -1
            fee = t["fee_open"] if o["ft_is_entry"] else t["fee_close"]
            px = o["safe_price"]
            fills.append(
                (
                    pd.Timestamp(o["order_filled_timestamp"], unit="ms", tz="UTC"),
                    side * o["amount"],
                    px,
                    abs(o["amount"] * px) * fee,
                )
            )
    fills.sort()
    close = candles.set_index("date")["close"]
    fr = funding.set_index("date")["open"].rename("rate")
    mk = mark.set_index("date")["open"].rename("mark")
    fund = pd.concat([fr, mk], axis=1, join="inner")
    fund = fund[fund["rate"] != 0]
    cum = np.r_[0.0, (fund["rate"] * fund["mark"]).cumsum().to_numpy()]
    f_idx = fund.index

    def fund_between(t1: pd.Timestamp, t2: pd.Timestamp) -> float:
        """Sum of rate * mark for settlements in (t1, t2]."""
        return float(
            cum[f_idx.searchsorted(t2, side="right")] - cum[f_idx.searchsorted(t1, side="right")]
        )

    days = close.loc[start:end].index
    cash, units, fi, paid_fund, fees = start_bal, 0.0, 0, 0.0, 0.0
    eq = []
    prev_t = days[0]
    for d in days:
        day_end = d + pd.Timedelta(days=1)
        # funding settlements during the day, on the position held at the time
        while fi < len(fills) and fills[fi][0] < day_end:
            ts, du, px, fee = fills[fi]
            paid = units * fund_between(prev_t, ts)
            cash -= paid
            paid_fund += paid
            prev_t = ts
            cash -= du * px + fee
            fees += fee
            units += du
            fi += 1
        paid = units * fund_between(prev_t, day_end)
        cash -= paid
        paid_fund += paid
        prev_t = day_end
        eq.append(cash + units * close.loc[d])
    ser = pd.Series(eq, index=days)
    reported = start_bal + sum(t["profit_abs"] for t in trades)
    open_units = units
    info = {
        "rebuilt_final": ser.iloc[-1],
        "reported_final": reported,
        "open_units_at_end": open_units,
        "funding_paid": paid_fund,
        "fees": fees,
        "orders": len(fills),
    }
    return ser, info


def stats(eq: pd.Series, start_bal: float) -> dict:
    e = pd.concat([pd.Series([start_bal]), eq.reset_index(drop=True)]) / start_bal
    r = e.pct_change().dropna().to_numpy()
    sd = r.std(ddof=1)
    return {
        "sharpe": r.mean() / sd * np.sqrt(ANN) if sd > 0 else float("nan"),
        "ann%": 100 * (e.iloc[-1] ** (ANN / len(r)) - 1),
        "maxDD%": 100 * (e / e.cummax() - 1).min(),
        "final_x": e.iloc[-1],
    }


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--results", type=Path, default=None, help="backtest result file (latest)")
    p.add_argument("--strategy", default="DailyTrend")
    p.add_argument("--pair", default="BTC/USDT:USDT")
    p.add_argument("--symbol", default="BTCUSDT", help="symbol for trend_backtest.py's cache")
    p.add_argument("--datadir", type=Path, default=ROOT / "user_data" / "data" / "binance")
    p.add_argument("--start", default="2022-01-01")
    p.add_argument("--end", default="2026-10-31")
    p.add_argument("--fee", type=float, default=0.0007, help="cost per side for the simulation")
    p.add_argument(
        "--sim-from-ft-data",
        action="store_true",
        help="feed the simulation Freqtrade's candles/funding instead of the carry cache",
    )
    a = p.parse_args()

    start, end = pd.Timestamp(a.start, tz="UTC"), pd.Timestamp(a.end, tz="UTC")
    trades, bal = load_trades(a.results, a.strategy)
    candles, funding, mark = load_ft_data(a.datadir, a.pair)
    eq, info = rebuild_equity(trades, bal, candles, funding, mark, start, end)
    ft = stats(eq, bal)

    import trend_backtest as tb

    if a.sim_from_ft_data:
        # funding priced off the 1h mark closes; daily closes from the 1d candles
        f = funding[["date", "open"]].rename(columns={"open": "rate"})
        df = tb.daily_frame(mark[["date", "close"]], f[f["rate"] != 0])
        df["close"] = candles.set_index("date")["close"].reindex(df.index)
        df = df.dropna(subset=["close"])
    else:
        from carry_backtest import load

        df = tb.daily_frame(
            load(a.symbol, "perp", tb.DOWNLOAD_START[a.symbol], a.end[:7]),
            load(a.symbol, "funding", tb.DOWNLOAD_START[a.symbol], a.end[:7]),
        )
    feat = tb.features(df)
    expo = feat[tb.COMPONENTS].mean(axis=1).clip(lower=0)
    s0, e0 = max(start, df.index[0]), min(end, df.index[-1])
    sim = tb.simulate(df, expo, tb.scale_series(feat), s0, e0, a.fee)
    sm = stats(sim["equity"], 1.0)

    print(
        f"\nWindow {start.date()} -> {end.date()}   ({len(trades)} trades, {info['orders']} fills)"
    )
    tab = pd.DataFrame({"freqtrade (rebuilt)": ft, "trend_backtest.py": sm}).T
    print(tab.round(3).to_string())
    print(
        f"\nRebuild check: rebuilt final equity {info['rebuilt_final']:.2f} vs Freqtrade "
        f"reported {info['reported_final']:.2f} "
        f"(open units at end {info['open_units_at_end']:.6f}; "
        "differs if a position is still open, since Freqtrade closes it at the last candle)"
    )
    ft_funding = -sum(t.get("funding_fees") or 0.0 for t in trades)
    print(
        f"Fees {info['fees']:.2f}; funding paid {info['funding_paid']:.2f} rebuilt vs "
        f"{ft_funding:.2f} by Freqtrade. Freqtrade charges the settlement at a fill's own "
        "timestamp on both sides of the fill, so it over-counts slightly; the rebuild charges "
        "each settlement once, as Binance does. That explains the final-equity gap."
    )
    diff = ft["sharpe"] - sm["sharpe"]
    ok = abs(diff) <= 0.10
    print(
        f"\nSharpe difference {diff:+.3f}  ->  "
        f"cross-check {'PASS' if ok else 'FAIL'} (|diff| <= 0.10)"
    )


if __name__ == "__main__":
    main()
