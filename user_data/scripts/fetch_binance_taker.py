#!/usr/bin/env python3
"""
Build a 5-minute taker-buy-volume file for FlushReversal from Binance's public
USDT-M futures kline archive (https://data.binance.vision).

Binance klines carry `taker_buy_volume` (base-asset volume bought by aggressive
market orders). Freqtrade's own candles drop that column, so this script stores
it separately as user_data/data/binance_taker/<SYMBOL>_5m.feather with columns
    date (candle open, UTC), volume, taker_buy_volume

Monthly archives are used for complete months and daily archives for the
current month. Existing rows are kept and new ones merged in.

Usage (repo root):
    python user_data/scripts/fetch_binance_taker.py --symbol SUIUSDT \
        --start 2023-05-01 --end 2026-10-31
"""

import argparse
import io
import sys
import time
import zipfile
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pandas as pd
import requests


BASE = "https://data.binance.vision/data/futures/um"
COLS = [
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore",
]  # fmt: skip


def _get_zip(url: str, retries: int = 3) -> bytes | None:
    for i in range(retries):
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.content
        except Exception as e:  # retry on anything, report at the end
            if i == retries - 1:
                print(f"  {url.rsplit('/', 1)[-1]}: failed ({e})")
                return None
            time.sleep(1.5 * (i + 1))
    return None


def parse_klines_zip(raw: bytes) -> pd.DataFrame:
    """Parse one Binance klines zip. Newer files have a header row, older ones do not."""
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        text = z.read(z.namelist()[0])
    first = text.split(b"\n", 1)[0]
    has_header = not first[:1].isdigit()
    df = pd.read_csv(io.BytesIO(text), header=0 if has_header else None)
    if not has_header:
        df.columns = COLS[: len(df.columns)]
    df.columns = [str(c).strip().lower() for c in df.columns]
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(pd.to_numeric(df["open_time"]), unit="ms", utc=True),
            "volume": pd.to_numeric(df["volume"], errors="coerce"),
            "taker_buy_volume": pd.to_numeric(df["taker_buy_volume"], errors="coerce"),
        }
    )
    return out.dropna()


def month_starts(start: date, end: date) -> list[date]:
    out, d = [], date(start.year, start.month, 1)
    while d <= end:
        out.append(d)
        d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    return out


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--symbol", default="SUIUSDT")
    p.add_argument("--start", required=True, help="YYYY-MM-DD")
    p.add_argument("--end", required=True, help="YYYY-MM-DD (inclusive)")
    p.add_argument("--interval", default="5m")
    p.add_argument("--out", default="user_data/data/binance_taker")
    a = p.parse_args()

    start, end = date.fromisoformat(a.start), date.fromisoformat(a.end)
    today = datetime.now(UTC).date()
    frames, missing = [], []
    for m in month_starts(start, end):
        is_current = (m.year, m.month) == (today.year, today.month)
        raw = None
        if not is_current:
            name = f"{a.symbol}-{a.interval}-{m:%Y-%m}.zip"
            url = f"{BASE}/monthly/klines/{a.symbol}/{a.interval}/{name}"
            raw = _get_zip(url)
        if raw is not None:
            frames.append(parse_klines_zip(raw))
            print(f"  {m:%Y-%m}: monthly", flush=True)
            continue
        # fall back to daily files (current month, or a monthly file not published yet)
        last = min(end, date(m.year + (m.month == 12), m.month % 12 + 1, 1) - timedelta(days=1))
        d, got = m, 0
        while d <= last:
            url = f"{BASE}/daily/klines/{a.symbol}/{a.interval}/{a.symbol}-{a.interval}-{d}.zip"
            raw = _get_zip(url)
            if raw is None:
                missing.append(d.isoformat())
            else:
                frames.append(parse_klines_zip(raw))
                got += 1
            d += timedelta(days=1)
            time.sleep(0.1)
        print(f"  {m:%Y-%m}: {got} daily files", flush=True)
    if not frames:
        sys.exit("No data downloaded - check the symbol and your connection.")

    df = pd.concat(frames, ignore_index=True)
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{a.symbol}_{a.interval}.feather"
    if path.exists():
        df = pd.concat([pd.read_feather(path), df])
    df = df.drop_duplicates("date", keep="last").sort_values("date").reset_index(drop=True)
    df = df[(df["date"] >= pd.Timestamp(start, tz="UTC"))].reset_index(drop=True)
    df.to_feather(path)
    share = (df["taker_buy_volume"] / df["volume"].where(df["volume"] > 0)).describe()
    print(f"Saved {len(df)} rows to {path}")
    print(f"  range {df['date'].min()} -> {df['date'].max()}")
    print(f"  taker-buy share: mean {share['mean']:.3f}, std {share['std']:.3f}")
    if missing:
        print(f"{len(missing)} daily files missing, e.g. {missing[:5]}")


if __name__ == "__main__":
    main()
