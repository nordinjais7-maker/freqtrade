#!/usr/bin/env python3
"""
Deep timing breakdown of SessionSweep backtest results.

Reads one or more exported backtest result files (default: the newest one in
user_data/backtest_results) and prints trade count, win rate, profit factor and
net profit split by entry hour (UTC), session tag, weekday, exit reason and
holding time. Use it after any backtest to see *when* the strategy makes or
loses its money.

    python user_data/scripts/sessionsweep_timing.py
    python user_data/scripts/sessionsweep_timing.py user_data/backtest_results/<result>.zip
"""

import argparse
import sys
from pathlib import Path

import pandas as pd


def _pf(x: pd.Series) -> float:
    gains, losses = x[x > 0].sum(), -x[x < 0].sum()
    return float("inf") if losses == 0 else gains / losses


def table(trades: pd.DataFrame, key: pd.Series, title: str) -> None:
    g = trades.groupby(key)["profit_abs"]
    out = pd.DataFrame(
        {
            "trades": g.size(),
            "win%": g.apply(lambda x: 100 * (x > 0).mean()),
            "PF": g.apply(_pf),
            "net_usdt": g.sum(),
            "avg_usdt": g.mean(),
        }
    )
    print(f"\n{title}")
    print(out.to_string(float_format=lambda v: f"{v:8.2f}"))


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("results", nargs="*", help="backtest result .zip files (default: newest)")
    args = p.parse_args()
    sys.path.insert(0, str(Path.cwd()))
    from freqtrade.data.btanalysis import get_latest_backtest_filename, load_backtest_data

    files = args.results or [
        str(
            Path("user_data/backtest_results")
            / get_latest_backtest_filename("user_data/backtest_results")
        )
    ]
    frames = []
    for f in files:
        t = load_backtest_data(f)
        t["source"] = Path(f).name
        frames.append(t)
    trades = pd.concat(frames, ignore_index=True)
    trades["enter_tag"] = trades["enter_tag"].fillna("")
    print(
        f"{len(trades)} trades from {len(files)} file(s), pairs: {sorted(trades['pair'].unique())}"
    )
    pa = trades["profit_abs"]
    print(f"overall: win {100 * (pa > 0).mean():.1f}%  PF {_pf(pa):.2f}  net {pa.sum():.1f} USDT")

    table(trades, trades["open_date"].dt.hour, "BY ENTRY HOUR (UTC) - hour of the entry candle")
    table(trades, trades["enter_tag"], "BY SESSION / DIRECTION")
    table(trades, trades["open_date"].dt.day_name(), "BY WEEKDAY")
    table(trades, trades["exit_reason"], "BY EXIT REASON")
    hold = pd.cut(
        trades["trade_duration"], [0, 30, 60, 120, 240, 480, 1440, 1e9],
        labels=["<=30m", "30-60m", "1-2h", "2-4h", "4-8h", "8-24h", ">24h"],
    )  # fmt: skip
    table(trades, hold, "BY HOLDING TIME")
    if trades["pair"].nunique() > 1:
        table(trades, trades["pair"], "BY PAIR")
    print(
        "\nRead PF (profit factor) and trade count together: a cell with fewer than ~30 trades\n"
        "is noise. A real timing effect shows up in the same hours on both pairs and both years."
    )


if __name__ == "__main__":
    main()
