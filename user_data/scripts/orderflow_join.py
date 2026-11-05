#!/usr/bin/env python3
"""
Attach OKX order-flow features to backtest trades and score trades by them.

Reads the CSVs written by orderflow_logger.py and one or more Freqtrade backtest
result zips. For every trade it looks only at 1h order-flow bars that had fully
closed before the entry (bar start <= entry - 1h, no look-ahead) and computes:

  oi_chg_3h      open-interest change over the last 3 closed hours (fraction)
  ls_chg_3h      change in the all-account long/short ratio over the same 3 hours
  taker_delta_3h (buy - sell) / (buy + sell) taker volume over the last 3 hours
  top_pos        top-trader long/short position ratio at the last closed hour
  funding        last settled funding rate before the entry

and the SUI-desk filter, written down before looking at any result:
  long  "flush ending":         ls_chg_3h < 0 and oi_chg_3h < 0
  short "retail chasing highs": ls_chg_3h > 0 and taker_delta_3h < 0

Then it prints the robustness numbers (robustness.py) for: all covered trades,
desk_ok vs not, and simple splits of each feature. Trades outside the order-flow
window (older than the data you have collected) are counted and skipped.

Usage (repo root):
    python user_data/scripts/orderflow_join.py --last 3          # newest 3 result zips
    python user_data/scripts/orderflow_join.py user_data/backtest_results/backtest-result-XXXX.zip
    python user_data/scripts/orderflow_join.py --last 3 --csv trades_with_flow.csv

Treat any result here as exploratory until the forward log has months of data:
~60 days of 1h history is all OKX keeps, so early samples are small.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


sys.path.insert(0, str(Path(__file__).parent))
import robustness  # noqa: E402


FLOW = Path("user_data/orderflow")
RESULTS = Path("user_data/backtest_results")
HOUR_MS = 3_600_000


def okx_inst(pair: str) -> str:
    """'SUI/USDT:USDT' -> 'SUI-USDT-SWAP'."""
    base, rest = pair.split("/")
    quote = rest.split(":")[0]
    return f"{base}-{quote}-SWAP"


def load_flow(inst: str, flow_dir: Path = FLOW) -> pd.DataFrame | None:
    """One 1h frame per instrument: ts, oi, ls_acct, top_pos, sell_vol, buy_vol."""
    parts = []
    for metric, cols in (("oi", ["oi"]), ("ls_acct", ["ls_acct"]), ("top_pos", ["top_pos"]),
                         ("taker", ["sell_vol", "buy_vol"])):  # fmt: skip
        f = flow_dir / f"{inst}_{metric}_1H.csv"
        if not f.is_file():
            return None
        parts.append(pd.read_csv(f, usecols=["ts", *cols]).set_index("ts"))
    flow = pd.concat(parts, axis=1, join="inner").sort_index()
    flow = flow[~flow.index.duplicated(keep="last")]
    return flow.reset_index()


def load_funding(inst: str, flow_dir: Path = FLOW) -> pd.DataFrame | None:
    f = flow_dir / f"{inst}_funding.csv"
    return pd.read_csv(f).sort_values("ts") if f.is_file() else None


def features(trades: pd.DataFrame, flow: pd.DataFrame, funding: pd.DataFrame | None) -> pd.DataFrame:
    """Add order-flow features to each trade (NaN when outside the data window)."""
    out = trades.copy()
    # resolution-independent ms (pandas 3 datetimes can be s / ms / us / ns)
    epoch = pd.Timestamp(0, tz="UTC")
    entry_ms = (pd.to_datetime(out["open_date"], utc=True) - epoch) // pd.Timedelta(milliseconds=1)
    ts = flow["ts"].to_numpy()
    # last bar whose start is <= entry - 1h, i.e. the bar had closed by the entry
    idx = np.searchsorted(ts, (entry_ms - HOUR_MS).to_numpy(), side="right") - 1
    cols = {k: np.full(len(out), np.nan) for k in
            ("oi_chg_3h", "ls_chg_3h", "taker_delta_3h", "top_pos", "funding")}  # fmt: skip
    oi, ls, top = flow["oi"].to_numpy(), flow["ls_acct"].to_numpy(), flow["top_pos"].to_numpy()
    buy, sell = flow["buy_vol"].to_numpy(), flow["sell_vol"].to_numpy()
    entry_arr = entry_ms.to_numpy()
    for k, i in enumerate(idx):
        # need 4 consecutive hourly bars ending at i (gaps would mix unrelated hours),
        # and bar i must be the hour just before the entry (no stale data after a gap
        # in collection or past the end of the collected window)
        if i < 3 or ts[i] - ts[i - 3] != 3 * HOUR_MS or entry_arr[k] - ts[i] >= 2 * HOUR_MS:
            continue
        cols["oi_chg_3h"][k] = oi[i] / oi[i - 3] - 1
        cols["ls_chg_3h"][k] = ls[i] - ls[i - 3]
        b, s = buy[i - 2 : i + 1].sum(), sell[i - 2 : i + 1].sum()
        cols["taker_delta_3h"][k] = (b - s) / (b + s) if (b + s) else np.nan
        cols["top_pos"][k] = top[i]
    if funding is not None and len(funding):
        fts = funding["ts"].to_numpy()
        j = np.searchsorted(fts, entry_ms.to_numpy(), side="right") - 1
        ok = j >= 0
        cols["funding"][ok] = funding["funding"].to_numpy()[j[ok]]
    for k, v in cols.items():
        out[k] = v
    short = out["is_short"].astype(bool) if "is_short" in out else pd.Series(False, index=out.index)
    long_ok = (out["ls_chg_3h"] < 0) & (out["oi_chg_3h"] < 0)
    short_ok = (out["ls_chg_3h"] > 0) & (out["taker_delta_3h"] < 0)
    # 1.0 = pass, 0.0 = fail, NaN = no order-flow data for this trade
    out["desk_ok"] = np.where(short, short_ok, long_ok).astype(float)
    out.loc[out["ls_chg_3h"].isna(), "desk_ok"] = np.nan
    return out


def load_trades(zips: list[Path]) -> pd.DataFrame:
    from freqtrade.data.btanalysis import load_backtest_data, load_backtest_stats

    frames = []
    for z in zips:
        for strat in load_backtest_stats(z)["strategy"]:
            t = load_backtest_data(z, strat)
            if not t.empty:
                t["result_file"] = z.name
                frames.append(t)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def score(rows: dict[str, pd.DataFrame]) -> None:
    head = f"{'bucket':34} {'n':>5} {'PF':>6} {'exp$/tr':>9} {'p_perm':>7} {'PF95%lo':>8} {'PF95%hi':>8}"
    print(head + "\n" + "-" * len(head))
    for name, t in rows.items():
        p = t["profit_abs"].to_numpy(dtype=float)
        if len(p) == 0:
            print(f"{name:34} {0:>5}")
            continue
        r = robustness.analyze(t)
        pf = robustness.profit_factor(p)
        flag = "  (thin: < 30)" if len(p) < 30 else ""
        print(f"{name:34} {len(p):>5} {pf:>6.2f} {r['exp']:>9.3f} {r['p_perm']:>7.3f} "
              f"{r['pf_lo']:>8.2f} {r['pf_hi']:>8.2f}{flag}")  # fmt: skip


def report(t: pd.DataFrame) -> None:
    cov = t[t["ls_chg_3h"].notna()]
    print(f"\nTrades: {len(t)} total, {len(cov)} inside the order-flow window, "
          f"{len(t) - len(cov)} skipped (outside the collected order-flow data).")  # fmt: skip
    if cov.empty:
        return
    print(f"Window covered: {cov['open_date'].min()} -> {cov['open_date'].max()}\n")
    short = cov["is_short"].astype(bool)
    desk = cov["desk_ok"].astype(bool)
    rows = {
        "all covered trades": cov,
        "desk filter PASS (pre-registered)": cov[desk],
        "desk filter FAIL": cov[~desk],
        "  longs, desk PASS": cov[~short & desk],
        "  longs, desk FAIL": cov[~short & ~desk],
        "  shorts, desk PASS": cov[short & desk],
        "  shorts, desk FAIL": cov[short & ~desk],
        "OI falling into entry": cov[cov["oi_chg_3h"] < 0],
        "OI rising into entry": cov[cov["oi_chg_3h"] >= 0],
        "taker delta with trade side": cov[np.where(short, cov["taker_delta_3h"] < 0,
                                                    cov["taker_delta_3h"] > 0)],
        "taker delta against trade side": cov[np.where(short, cov["taker_delta_3h"] >= 0,
                                                       cov["taker_delta_3h"] <= 0)],
        "top traders net short (<1)": cov[cov["top_pos"] < 1],
        "top traders net long (>=1)": cov[cov["top_pos"] >= 1],
    }  # fmt: skip
    score(rows)
    n_tests = len(rows) - 1
    print(f"\n{n_tests} splits tested: 'not luck' needs p_perm < {0.05 / n_tests:.4f}. Only the"
          "\npre-registered desk filter counts as a test; the other splits are exploratory.")  # fmt: skip


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("zips", nargs="*", type=Path, help="backtest result zip files")
    p.add_argument("--last", type=int, default=0, help="use the newest N result zips")
    p.add_argument("--csv", type=Path, help="also write the enriched trade list here")
    args = p.parse_args()
    zips = list(args.zips)
    if args.last:
        zips += sorted(RESULTS.glob("backtest-result-*.zip"))[-args.last :]
    if not zips:
        raise SystemExit("Give result zips or --last N (run a backtest first).")
    trades = load_trades(zips)
    if trades.empty:
        raise SystemExit("No trades in those results.")
    enriched = []
    for pair, t in trades.groupby("pair"):
        inst = okx_inst(pair)
        flow = load_flow(inst)
        if flow is None:
            print(f"{pair}: no order-flow CSVs for {inst} (run orderflow_logger.py first)")
            continue
        enriched.append(features(t, flow, load_funding(inst)))
    if not enriched:
        raise SystemExit("Nothing to score.")
    out = pd.concat(enriched, ignore_index=True)
    report(out)
    if args.csv:
        out.to_csv(args.csv, index=False)
        print(f"\nWrote {args.csv}")


if __name__ == "__main__":
    main()
