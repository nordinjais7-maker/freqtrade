#!/usr/bin/env python3
"""
Offline *plumbing* test for the SessionSweep strategy.

This script does NOT measure the strategy's edge. It generates deterministic
synthetic SUI/USDT:USDT candles (random walk with session-dependent volatility),
stubs the exchange market metadata so no network is needed, and runs the real
Freqtrade backtester end to end. Use it to prove that indicators, entries,
custom stoploss / ROI / exit callbacks and the futures data pipeline all work
before spending time on real data.

Usage (from the repo root):
    python user_data/scripts/sessionsweep_smoke_backtest.py [--days 365] [--seed 7]

Synthetic data is written to user_data/data_synthetic/ (never to user_data/data/).
"""

import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import numpy as np
import pandas as pd


PAIR = "SUI/USDT:USDT"
PAIR_FILE = "SUI_USDT_USDT"
EXMS = "freqtrade.exchange.exchange.Exchange"


def make_synthetic(days: int, seed: int, start: pd.Timestamp) -> pd.DataFrame:
    """Random walk 5m candles. Volatility is lower in Asia and higher in
    London/NY, with a small mean reversion so Asia-range sweeps and reclaims
    actually occur."""
    rng = np.random.default_rng(seed)
    n = days * 288
    dates = pd.date_range(start, periods=n, freq="5min", tz="UTC")
    mod = dates.hour * 60 + dates.minute
    vol = np.where(mod < 420, 0.0012, np.where(mod < 1020, 0.0030, 0.0018))
    rets = rng.normal(0, 1, n) * vol
    log_px = np.cumsum(rets) + np.log(2.5)
    # Gentle mean reversion towards a slowly drifting centre so prices stay sane
    centre = np.log(2.5) + 0.3 * np.sin(np.arange(n) / (288 * 30))
    log_px = log_px - 0.02 * (log_px - centre).cumsum() / np.arange(1, n + 1)
    close = np.exp(log_px)
    open_ = np.concatenate([[close[0]], close[:-1]])
    wick = np.abs(rng.normal(0, 1, n)) * vol * close
    high = np.maximum(open_, close) + wick
    low = np.minimum(open_, close) - np.abs(rng.normal(0, 1, n)) * vol * close
    volume = rng.lognormal(10, 0.5, n)
    return pd.DataFrame(
        {"date": dates, "open": open_, "high": high, "low": low, "close": close, "volume": volume}
    )


def resample(df5: pd.DataFrame, tf: str) -> pd.DataFrame:
    o = (
        df5.set_index("date")
        .resample(tf)
        .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
    )
    return o.dropna().reset_index()


def write_data(datadir: Path, days: int, seed: int) -> None:
    # --datadir is used verbatim by freqtrade (no exchange sub-folder is appended)
    fut = datadir / "futures"
    fut.mkdir(parents=True, exist_ok=True)
    end = pd.Timestamp.now("UTC").floor("D")
    start = end - pd.Timedelta(days=days)
    df5 = make_synthetic(days, seed, start)
    df1h = resample(df5, "1h")
    df5.to_feather(fut / f"{PAIR_FILE}-5m-futures.feather")
    df1h.to_feather(fut / f"{PAIR_FILE}-1h-futures.feather")
    resample(df5, "4h").to_feather(fut / f"{PAIR_FILE}-4h-futures.feather")
    # Mark price ~ last price; funding every 8h at a small positive rate.
    df1h.to_feather(fut / f"{PAIR_FILE}-1h-mark.feather")
    fr = df1h[df1h["date"].dt.hour % 8 == 0].copy()
    for c in ("open", "high", "low", "close"):
        fr[c] = 0.0001
    fr["volume"] = 0.0
    fr.to_feather(fut / f"{PAIR_FILE}-1h-funding_rate.feather")
    print(f"Synthetic data written to {fut}: {len(df5)} x 5m candles")
    print(f"  range {start:%Y-%m-%d} -> {end:%Y-%m-%d}")


def fake_markets() -> dict:
    return {
        PAIR: {
            "id": "SUIUSDT",
            "symbol": PAIR,
            "base": "SUI",
            "quote": "USDT",
            "settle": "USDT",
            "baseId": "SUI",
            "quoteId": "USDT",
            "settleId": "USDT",
            "type": "swap",
            "spot": False,
            "margin": False,
            "swap": True,
            "future": False,
            "option": False,
            "active": True,
            "contract": True,
            "linear": True,
            "inverse": False,
            "taker": 0.0005,
            "maker": 0.0002,
            "contractSize": 1.0,
            "expiry": None,
            "expiryDatetime": None,
            "strike": None,
            "optionType": None,
            "precision": {"amount": 1, "price": 4, "base": 8, "quote": 8},
            "limits": {
                "leverage": {"min": 1, "max": 75},
                "amount": {"min": 0.1, "max": 10000000},
                "price": {"min": 0.0001, "max": 10000},
                "cost": {"min": 5, "max": None},
            },
            "info": {},
        }
    }


def run_backtest(datadir: Path, timerange: str, extra: list[str]) -> None:
    from freqtrade.commands import Arguments

    argv = [
        "backtesting",
        "--config",
        "user_data/config_sessionsweep.json",
        "--userdir",
        "user_data",
        "--datadir",
        str(datadir),
        "--timerange",
        timerange,
        "--fee",
        "0.0005",
        "--breakdown",
        "month",
        "--export",
        "trades",
        "--notes",
        "SYNTHETIC smoke test - not real market data",
        *extra,
    ]
    args = Arguments(argv).get_parsed_arg()
    with (
        patch(f"{EXMS}.validate_config", MagicMock()),
        patch(f"{EXMS}.validate_timeframes", MagicMock()),
        patch(f"{EXMS}.check_time_offset", MagicMock()),
        patch(f"{EXMS}.precisionMode", PropertyMock(return_value=2)),
        patch(f"{EXMS}.precision_mode_price", PropertyMock(return_value=2)),
        patch(f"{EXMS}._load_async_markets", return_value={}),
        patch(f"{EXMS}.reload_markets", MagicMock()),
        patch(f"{EXMS}.markets", PropertyMock(return_value=fake_markets())),
        patch(
            f"{EXMS}.timeframes", PropertyMock(return_value=["1m", "5m", "15m", "1h", "4h", "1d"])
        ),
    ):
        args["func"](args)


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--days", type=int, default=365)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--datadir", default="user_data/data_synthetic")
    p.add_argument("--no-generate", action="store_true", help="reuse existing synthetic data")
    args, extra = p.parse_known_args()

    root = Path(__file__).resolve().parents[2]
    if Path.cwd() != root:
        sys.exit(f"Run from the repository root: cd {root}")
    # Allow running against a source checkout that is not pip-installed.
    sys.path.insert(0, str(root))
    datadir = Path(args.datadir)
    if not args.no_generate:
        write_data(datadir, args.days, args.seed)
    end = pd.Timestamp.now("UTC").floor("D")
    start = end - pd.Timedelta(days=args.days - 6)  # leave startup candles
    print("=" * 70)
    print("SYNTHETIC DATA - results below prove the plumbing works, nothing else")
    print("=" * 70)
    run_backtest(datadir, f"{start:%Y%m%d}-{end:%Y%m%d}", extra)


if __name__ == "__main__":
    main()
