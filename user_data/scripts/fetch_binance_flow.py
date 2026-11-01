#!/usr/bin/env python3
"""
Build an hourly long/short-ratio + open-interest history for SuiFlushShort from
Binance's public archive (https://data.binance.vision, USDT-M futures "metrics").

Binance publishes one CSV per day with 5-minute samples back to 2021:
    create_time, symbol, sum_open_interest, sum_open_interest_value,
    count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio,
    count_long_short_ratio, sum_taker_long_short_vol_ratio

This script downloads a date range, keeps the last sample of every hour and
writes user_data/data/binance_flow/<SYMBOL>_1H.feather with columns
    date (hour start, UTC), ls (= count_long_short_ratio, all accounts),
    ls_top (= count_toptrader_long_short_ratio), oi (= sum_open_interest)
which is the schema SuiFlushShort reads with flow_source = binance.

Usage (repo root):
    python user_data/scripts/fetch_binance_flow.py --symbol SUIUSDT \\
        --start 2024-10-20 --end 2026-10-31
Days that are missing on the archive (404) are skipped and listed at the end.
Existing rows in the output file are kept; new days are merged in.
"""

import argparse
import io
import sys
import time
import zipfile
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests


URL = "https://data.binance.vision/data/futures/um/daily/metrics/{sym}/{sym}-metrics-{d}.zip"


def fetch_day(sym: str, d: date, retries: int = 3) -> pd.DataFrame | None:
    url = URL.format(sym=sym, d=d.isoformat())
    for i in range(retries):
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                return parse_metrics_csv(z.read(z.namelist()[0]))
        except Exception as e:  # retry on anything, report at the end
            if i == retries - 1:
                print(f"  {d}: failed ({e})")
                return None
            time.sleep(1.5 * (i + 1))
    return None


def parse_metrics_csv(raw: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(raw))
    df.columns = [c.strip().lower() for c in df.columns]
    needed = {"create_time", "count_long_short_ratio", "sum_open_interest"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"metrics file lacks columns {sorted(missing)}; has {list(df.columns)}")
    out = pd.DataFrame(
        {
            "sample_time": pd.to_datetime(df["create_time"], utc=True),
            "ls": pd.to_numeric(df["count_long_short_ratio"], errors="coerce"),
            "ls_top": pd.to_numeric(df.get("count_toptrader_long_short_ratio"), errors="coerce"),
            "oi": pd.to_numeric(df["sum_open_interest"], errors="coerce"),
        }
    )
    return out.dropna(subset=["ls", "oi"])


def to_hourly(samples: pd.DataFrame) -> pd.DataFrame:
    """Last 5-minute sample of each hour, labelled with the hour START.

    A sample stamped 10:05..11:00 belongs to the 10:00 hour, so the strategy's
    rule "row at hour H is usable from H + 1h" means: usable from 11:00, when the
    last sample of that hour has been published.
    """
    s = samples.sort_values("sample_time").copy()
    s["date"] = (s["sample_time"] - pd.Timedelta(seconds=1)).dt.floor("h")
    hourly = s.groupby("date", as_index=False).last()
    return hourly[["date", "ls", "ls_top", "oi"]]


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--symbol", default="SUIUSDT")
    p.add_argument("--start", required=True, help="YYYY-MM-DD")
    p.add_argument("--end", required=True, help="YYYY-MM-DD (inclusive)")
    p.add_argument("--out", default="user_data/data/binance_flow")
    a = p.parse_args()

    start, end = date.fromisoformat(a.start), date.fromisoformat(a.end)
    days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    frames, missing = [], []
    for i, d in enumerate(days, 1):
        df = fetch_day(a.symbol, d)
        if df is None:
            missing.append(d.isoformat())
        else:
            frames.append(df)
        if i % 30 == 0 or i == len(days):
            print(f"  {i}/{len(days)} days, {len(missing)} missing", flush=True)
        time.sleep(0.15)
    if not frames:
        sys.exit("No data downloaded - check the symbol and your connection.")

    hourly = to_hourly(pd.concat(frames, ignore_index=True))
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{a.symbol}_1H.feather"
    if path.exists():
        hourly = pd.concat([pd.read_feather(path), hourly])
    hourly = hourly.drop_duplicates("date", keep="last").sort_values("date").reset_index(drop=True)
    hourly.to_feather(path)
    print(f"Saved {len(hourly)} hourly rows to {path}")
    print(f"  range {hourly['date'].min()} -> {hourly['date'].max()}")
    q = hourly["ls"].quantile
    print(f"  ls quantiles: 50% {q(0.5):.2f}, 80% {q(0.8):.2f}, 90% {q(0.9):.2f}")
    if missing:
        print(f"{len(missing)} days missing on the archive, e.g. {missing[:5]}")


if __name__ == "__main__":
    main()
