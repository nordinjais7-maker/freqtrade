"""
Download OKX hourly account long/short ratio and open interest for SUI-USDT-SWAP
(public API, no key) and save them for SuiFlushShort backtests.

OKX keeps about 60 days of this hourly history, so rerun this regularly (e.g. weekly via cron)
to keep extending the local file: new rows are merged into the existing file.

Usage (from your freqtrade project root):
    python user_data/scripts/fetch_okx_flow.py
    python user_data/scripts/fetch_okx_flow.py --inst SUI-USDT-SWAP --out user_data/data/okx_flow
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd
import requests


BASE = "https://www.okx.com/api/v5/"


def get(path: str, retries: int = 5) -> list:
    for i in range(retries):
        try:
            r = requests.get(BASE + path, timeout=15)
            j = r.json()
            if j.get("code") == "0":
                return j.get("data", [])
        except Exception as e:
            print(f"  attempt {i + 1}: {e}")
        time.sleep(1.5 * (i + 1))  # OKX rate limit: back off
    return []


def paginate(base: str, max_pages: int = 20) -> list:
    rows, end = [], None
    for _ in range(max_pages):
        data = get(base + (f"&end={end}" if end else ""))
        if not data:
            break
        rows.extend(data)
        oldest = data[-1][0]
        if oldest == end:
            break
        end = oldest
        time.sleep(0.4)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inst", default="SUI-USDT-SWAP")
    ap.add_argument("--out", default="user_data/data/okx_flow")
    a = ap.parse_args()

    ls = paginate(
        f"rubik/stat/contracts/long-short-account-ratio-contract?instId={a.inst}&period=1H&limit=100"
    )
    oi = paginate(f"rubik/stat/contracts/open-interest-history?instId={a.inst}&period=1H&limit=100")
    if not ls or not oi:
        raise SystemExit("No data returned from OKX - check your connection/VPN.")

    lsd = pd.DataFrame(ls, columns=["ts", "ls"])
    oid = pd.DataFrame([r[:2] for r in oi], columns=["ts", "oi"])
    df = lsd.merge(oid, on="ts", how="outer")
    df["date"] = pd.to_datetime(df["ts"].astype("int64"), unit="ms", utc=True)
    df["ls"] = df["ls"].astype(float)
    df["oi"] = df["oi"].astype(float)
    df = df[["date", "ls", "oi"]]

    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{a.inst}_1H.feather"
    if path.exists():
        old = pd.read_feather(path)
        df = pd.concat([old, df])
    df = df.drop_duplicates("date", keep="last").sort_values("date").reset_index(drop=True)
    df.to_feather(path)
    print(f"Saved {len(df)} hourly rows {df['date'].min()} -> {df['date'].max()} to {path}")


if __name__ == "__main__":
    main()
