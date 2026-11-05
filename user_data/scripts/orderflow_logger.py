#!/usr/bin/env python3
"""
Collect OKX order-flow history (OI, long/short account ratio, top-trader position
ratio, taker buy/sell volume, funding) into local CSVs, so order-flow filters can
be tested against strategy trades later.

Why: free exchange APIs only keep a short window of this data (OKX per-contract
endpoints: ~60 days at 1h, ~5 days at 5m), so it has to be collected forward.
Run it now once (back-fills everything still available), then on a schedule.
Every run merges new rows into the existing files (dedup on timestamp), so missed
runs only cost data older than the API window.

Usage (repo root, freqtrade virtualenv active, needs network access to okx.com):
    python user_data/scripts/orderflow_logger.py
    python user_data/scripts/orderflow_logger.py --insts SUI-USDT-SWAP --periods 1H
    # schedule it (macOS/Linux crontab -e), every hour at minute 7:
    # 7 * * * * cd /path/to/freqtrade && .venv/bin/python user_data/scripts/orderflow_logger.py >> user_data/orderflow/log.txt 2>&1

Output: user_data/orderflow/<INST>_<metric>_<period>.csv (ts in ms UTC + values)
and user_data/orderflow/<INST>_funding.csv.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd
import requests


BASE = "https://www.okx.com"
OUT = Path("user_data/orderflow")
DEFAULT_INSTS = ["SUI-USDT-SWAP", "BTC-USDT-SWAP", "ETH-USDT-SWAP"]
DEFAULT_PERIODS = ["1H", "5m"]
PAUSE = 0.35  # seconds between calls (OKX rubik limit is ~5 req / 2 s)

# metric -> (endpoint, column names after ts)
METRICS: dict[str, tuple[str, list[str]]] = {
    "oi": ("/api/v5/rubik/stat/contracts/open-interest-history", ["oi", "oi_ccy", "oi_usd"]),
    "ls_acct": ("/api/v5/rubik/stat/contracts/long-short-account-ratio-contract", ["ls_acct"]),
    "top_pos": (
        "/api/v5/rubik/stat/contracts/long-short-position-ratio-contract-top-trader",
        ["top_pos"],
    ),
    "taker": ("/api/v5/rubik/stat/taker-volume-contract", ["sell_vol", "buy_vol"]),
}


def _get(session: requests.Session, path: str, params: dict) -> list:
    for attempt in range(8):
        r = session.get(BASE + path, params=params, timeout=20)
        body = r.json() if r.ok else {"code": str(r.status_code), "msg": r.text[:200]}
        if body.get("code") == "0":
            return body.get("data") or []
        if body.get("code") in ("50011", "429") or r.status_code == 429:
            time.sleep(2 + attempt)
            continue
        raise RuntimeError(f"OKX {path} {params}: {body.get('code')} {body.get('msg')}")
    raise RuntimeError(f"OKX {path}: still rate-limited after retries")


def _paged(
    session, path: str, params: dict, stop_ts: int | None, max_pages: int, cursor: str = "end"
) -> list:
    """Walk back in time until no rows, a short page, or stop_ts reached.

    Rubik endpoints page with `end=<ts>`; funding-rate-history uses `after=<ts>`.
    """
    rows: list = []
    end = None
    for _ in range(max_pages):
        p = dict(params, limit=100)
        if end:
            p[cursor] = end
        page = _get(session, path, p)
        time.sleep(PAUSE)
        if not page:
            break
        rows.extend(page)
        oldest = int(page[-1][0] if isinstance(page[-1], list) else page[-1]["fundingTime"])
        if len(page) < 100 or (stop_ts and oldest <= stop_ts):
            break
        end = oldest
    return rows


def _merge(path: Path, new: pd.DataFrame) -> tuple[int, int]:
    """Merge new rows into path (dedup on ts, newest value wins). Returns (added, total)."""
    if path.is_file():
        old = pd.read_csv(path)
        both = pd.concat([old, new], ignore_index=True)
    else:
        old = new.iloc[0:0]
        both = new
    both = both.drop_duplicates("ts", keep="last").sort_values("ts").reset_index(drop=True)
    both.to_csv(path, index=False)
    return len(both) - len(old), len(both)


def _last_ts(path: Path) -> int | None:
    if not path.is_file():
        return None
    try:
        return int(pd.read_csv(path, usecols=["ts"])["ts"].max())
    except (ValueError, KeyError):
        return None


def collect(insts: list[str], periods: list[str], max_pages: int = 30) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    s.headers["User-Agent"] = "freqtrade-orderflow-logger"
    for inst in insts:
        for period in periods:
            for metric, (path, cols) in METRICS.items():
                f = OUT / f"{inst}_{metric}_{period}.csv"
                rows = _paged(s, path, {"instId": inst, "period": period}, _last_ts(f), max_pages)
                if not rows:
                    print(f"{f.name}: no rows")
                    continue
                df = pd.DataFrame([r[: len(cols) + 1] for r in rows], columns=["ts", *cols])
                df = df.apply(pd.to_numeric, errors="coerce")
                added, total = _merge(f, df)
                first = pd.to_datetime(df["ts"].min(), unit="ms", utc=True)
                print(f"{f.name}: +{added} rows (file {total}, API reached back to {first:%Y-%m-%d %H:%M})")
        f = OUT / f"{inst}_funding.csv"
        rows = _paged(s, "/api/v5/public/funding-rate-history", {"instId": inst}, _last_ts(f), 30,
                       cursor="after")
        if rows:
            df = pd.DataFrame(
                {"ts": [int(r["fundingTime"]) for r in rows],
                 "funding": [float(r.get("realizedRate") or r["fundingRate"]) for r in rows]}
            )  # fmt: skip
            added, total = _merge(f, df)
            print(f"{f.name}: +{added} rows (file {total})")


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--insts", nargs="+", default=DEFAULT_INSTS, help="OKX instrument ids")
    p.add_argument("--periods", nargs="+", default=DEFAULT_PERIODS, choices=["5m", "1H"])
    p.add_argument("--max-pages", type=int, default=30, help="pages of 100 rows per series")
    args = p.parse_args()
    if not Path("user_data").is_dir():
        raise SystemExit("Run this from the freqtrade repository root.")
    collect(args.insts, args.periods, args.max_pages)


if __name__ == "__main__":
    main()
