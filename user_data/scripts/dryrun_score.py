#!/usr/bin/env python3
"""
Score a DailyTrend dry run against the execution criteria in user_data/NOTES.md 4j.

Reads the bot's own SQLite database (read-only) and Binance's public daily candles
and funding history (no API key), then checks:

  1. No missed days: on every full day since the bot started, it held a position
     exactly when the model's signal (computed on the previous daily close) said so,
     and every order filled within 60 minutes of 00:00 UTC.
  2. Fills within 10 bp of the 00:00 UTC open on average.
  3. Funding charged within 10% of amount x rate x mark price from Binance history
     (checked once the total expected funding is large enough to measure).
  4. Position size within 5% of the model target after each entry or rebalance.

Profit is reported for information only; it is not a criterion.

Usage (repo root; safe to run while the bots are running):
    python user_data/scripts/dryrun_score.py
    python user_data/scripts/dryrun_score.py --db user_data/dailytrend_sui_dryrun.sqlite \\
        --pair SUI/USDT:USDT
"""

import argparse
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd


sys.path.insert(0, str(Path(__file__).resolve().parent))

FAPI = "https://fapi.binance.com/fapi/v1"
DEFAULTS = [
    ("user_data/dailytrend_dryrun.sqlite", "BTC/USDT:USDT"),
    ("user_data/dailytrend_sui_dryrun.sqlite", "SUI/USDT:USDT"),
]
FILL_WINDOW_MIN = 60
FILL_BP_LIMIT = 10.0
FUNDING_TOL = 0.10
SIZE_TOL = 0.05
MIN_FUNDING_TO_SCORE = 1.0  # USDT; below this the 10% check is noise


# ------------------------------------------------------------------ data -------
def _get(path: str, params: dict) -> list:
    import requests

    for i in range(3):
        try:
            r = requests.get(f"{FAPI}/{path}", params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if i == 2:
                sys.exit(f"Binance request failed ({path}): {e}")
            time.sleep(2 * (i + 1))
    return []


def fetch_daily(symbol: str, days: int = 400) -> pd.DataFrame:
    start = int((pd.Timestamp.now("UTC").floor("D") - pd.Timedelta(days=days)).timestamp() * 1000)
    rows = _get("klines", {"symbol": symbol, "interval": "1d", "startTime": start, "limit": 1000})
    df = pd.DataFrame(
        [(int(r[0]), float(r[1]), float(r[4]), int(r[6])) for r in rows],
        columns=["t", "open", "close", "close_t"],
    )
    df["date"] = pd.to_datetime(df["t"], unit="ms", utc=True)
    now_ms = pd.Timestamp.now("UTC").timestamp() * 1000
    df["complete"] = df["close_t"] < now_ms
    return df.set_index("date")[["open", "close", "complete"]]


def fetch_funding(symbol: str, since: pd.Timestamp) -> pd.DataFrame:
    out, start = [], int(since.timestamp() * 1000)
    while True:
        rows = _get("fundingRate", {"symbol": symbol, "startTime": start, "limit": 1000})
        if not rows:
            break
        out += rows
        if len(rows) < 1000:
            break
        start = int(rows[-1]["fundingTime"]) + 1
    if not out:
        return pd.DataFrame(columns=["rate", "mark"])
    df = pd.DataFrame(
        {
            "date": pd.to_datetime([int(r["fundingTime"]) for r in out], unit="ms", utc=True),
            "rate": [float(r["fundingRate"]) for r in out],
            "mark": [float(r.get("markPrice") or "nan") for r in out],
        }
    )
    df["date"] = df["date"].dt.floor("s")
    return df.set_index("date")


def load_db(path: Path, pair: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        trades = pd.read_sql_query(
            "SELECT id, pair, is_open, open_date, close_date, leverage, funding_fees, "
            "close_profit_abs, realized_profit FROM trades WHERE pair = ?",
            con,
            params=(pair,),
        )
        orders = pd.read_sql_query(
            "SELECT o.ft_trade_id, o.ft_order_side, o.status, o.filled, o.average, "
            "o.order_filled_date, o.ft_order_tag FROM orders o "
            "JOIN trades t ON t.id = o.ft_trade_id WHERE t.pair = ?",
            con,
            params=(pair,),
        )
    finally:
        con.close()
    orders = orders[(orders["filled"].fillna(0) > 0) & orders["order_filled_date"].notna()].copy()
    orders["ts"] = pd.to_datetime(orders["order_filled_date"], utc=True)
    orders["du"] = np.where(orders["ft_order_side"] == "buy", 1, -1) * orders["filled"]
    return trades, orders.sort_values("ts").reset_index(drop=True)


def bot_start(path: Path) -> pd.Timestamp:
    """First time the bot ran: earliest wallet snapshot, else the file's creation time."""
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        t = con.execute("SELECT MIN(timestamp) FROM wallet_history").fetchone()[0]
    except sqlite3.Error:
        t = None
    finally:
        con.close()
    if t:
        return (
            pd.Timestamp(t, tz="UTC")
            if not isinstance(t, (int, float))
            else pd.Timestamp(t, unit="ms", tz="UTC")
        )
    st = path.stat()
    return pd.Timestamp(getattr(st, "st_birthtime", st.st_mtime), unit="s", tz="UTC")


# ---------------------------------------------------------------- scoring ------
def model_target(daily: pd.DataFrame) -> pd.Series:
    """target_frac known at each day's close (same code path as trend_backtest.py)."""
    import trend_backtest as tb

    closes = daily.loc[daily["complete"], ["close"]]
    feat = tb.features(closes)
    expo = feat[tb.COMPONENTS].mean(axis=1).clip(lower=0)
    return (expo * tb.scale_series(feat)).rename("target")


def units_at(orders: pd.DataFrame, t: pd.Timestamp) -> float:
    return float(orders.loc[orders["ts"] <= t, "du"].sum())


def score(  # noqa: C901 - four independent checks, kept together for readability
    trades: pd.DataFrame,
    orders: pd.DataFrame,
    daily: pd.DataFrame,
    funding: pd.DataFrame,
    start: pd.Timestamp,
    wallet: float,
    fee: float,
) -> list[tuple[str, bool | None, str]]:
    target = model_target(daily)
    first_day = start.floor("D") + pd.Timedelta(days=1)
    days = [d for d in daily.index if d >= first_day and bool(daily.loc[d, "complete"])]
    res: list[tuple[str, bool | None, str]] = []

    # 1. missed days and late fills
    miss = []
    for d in days:
        prev = d - pd.Timedelta(days=1)
        if prev not in target.index or np.isnan(target.loc[prev]):
            continue
        want = target.loc[prev] > 0
        have = units_at(orders, d + pd.Timedelta(minutes=FILL_WINDOW_MIN)) > 1e-12
        if want != have:
            miss.append(
                f"{d.date()} (model {'in' if want else 'out'}, bot {'in' if have else 'out'})"
            )
    late = orders[
        (orders["ts"] - orders["ts"].dt.floor("D")) > pd.Timedelta(minutes=FILL_WINDOW_MIN)
    ]
    ok1 = not miss and late.empty
    detail = f"{len(days)} full days checked"
    if miss:
        detail += f"; mismatched: {', '.join(miss[:5])}{' ...' if len(miss) > 5 else ''}"
    if not late.empty:
        detail += f"; {len(late)} fill(s) later than {FILL_WINDOW_MIN} min after 00:00 UTC"
    res.append(("1. no missed days, fills by 01:00 UTC", ok1 if days else None, detail))

    # 2. fill slippage vs daily open
    if orders.empty:
        res.append(("2. fills within 10 bp of the open", None, "no fills yet"))
    else:
        opens = daily["open"].reindex(orders["ts"].dt.floor("D")).to_numpy()
        bp = np.abs(orders["average"].to_numpy() / opens - 1) * 1e4
        avg = float(np.nanmean(bp))
        res.append(
            (
                "2. fills within 10 bp of the open",
                avg <= FILL_BP_LIMIT,
                f"mean {avg:.1f} bp, worst {np.nanmax(bp):.1f} bp over {len(orders)} fills",
            )
        )

    # 3. funding vs Binance history
    expected = 0.0
    for t, row in funding.iterrows():
        if t <= start:
            continue
        u = units_at(orders, t - pd.Timedelta(seconds=1))
        if u and not np.isnan(row["mark"]):
            expected += u * row["rate"] * row["mark"]
    charged = -float(trades["funding_fees"].fillna(0).sum())
    if abs(expected) < MIN_FUNDING_TO_SCORE:
        res.append(
            (
                "3. funding within 10% of Binance",
                None,
                f"too little to measure yet (expected {expected:.2f}, charged {charged:.2f} USDT)",
            )
        )
    else:
        err = abs(charged - expected) / abs(expected)
        res.append(
            (
                "3. funding within 10% of Binance",
                err <= FUNDING_TOL,
                f"charged {charged:.2f} vs expected {expected:.2f} USDT ({100 * err:.1f}% off)",
            )
        )

    # 4. size after each entry / rebalance-up / rebalance-down
    checks = []
    cash, units = wallet, 0.0
    for _, o in orders.iterrows():
        px = float(o["average"])
        cash -= o["du"] * px + abs(o["du"]) * px * fee
        units += o["du"]
        if o["ft_order_tag"] == "flat" or units <= 1e-12:
            continue  # exits are checked by criterion 1
        prev = o["ts"].floor("D") - pd.Timedelta(days=1)
        if prev not in target.index or target.loc[prev] <= 0:
            continue
        equity = cash + units * px
        frac = units * px / equity
        checks.append(abs(frac / target.loc[prev] - 1))
    if not checks:
        res.append(("4. size within 5% of target", None, "no entries or rebalances yet"))
    else:
        worst = max(checks)
        res.append(
            (
                "4. size within 5% of target",
                worst <= SIZE_TOL,
                f"worst {100 * worst:.1f}% off over {len(checks)} entries/rebalances",
            )
        )
    return res


def report(db: Path, pair: str, wallet: float, fee: float, since: str | None = None) -> None:
    symbol = pair.split("/")[0] + "USDT"
    print(f"\n=== {pair}  ({db}) ===")
    if not db.exists():
        print("  database not found - has this bot been started?")
        return
    trades, orders = load_db(db, pair)
    start = pd.Timestamp(since, tz="UTC") if since else bot_start(db)
    daily = fetch_daily(symbol)
    funding = fetch_funding(symbol, start - pd.Timedelta(days=1))
    target = model_target(daily)
    last = target.dropna()
    open_units = float(orders["du"].sum()) if not orders.empty else 0.0
    print(
        f"  running since {start:%Y-%m-%d %H:%M} UTC; {len(trades)} trade(s), {len(orders)} fill(s)"
    )
    print(
        f"  model target at last close ({last.index[-1].date()}): {last.iloc[-1]:.2f}x equity; "
        f"bot position now: {open_units:g} {symbol[:-4]}"
    )
    for name, ok, detail in score(trades, orders, daily, funding, start, wallet, fee):
        mark = "PASS" if ok else ("----" if ok is None else "FAIL")
        print(f"  [{mark}] {name:40s} {detail}")
    closed = float(trades["close_profit_abs"].fillna(0).sum())
    print(f"  (info) closed profit {closed:.2f} USDT - not a criterion")


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--db", type=Path)
    p.add_argument("--pair")
    p.add_argument("--wallet", type=float, default=10_000.0)
    p.add_argument("--fee", type=float, default=0.0005, help="dry-run fee per side")
    p.add_argument("--since", help="override the detected start, e.g. '2026-11-03 20:00'")
    a = p.parse_args()
    pd.set_option("display.width", 160)
    targets = [(a.db, a.pair)] if a.db else [(Path(d), pr) for d, pr in DEFAULTS]
    for db, pair in targets:
        report(Path(db), pair or "BTC/USDT:USDT", a.wallet, a.fee, a.since)
    print(
        "\n---- = not enough activity yet to judge. The dry run is judged after six months;"
        "\nprofit is not a criterion (see NOTES 4j)."
    )


if __name__ == "__main__":
    main()
