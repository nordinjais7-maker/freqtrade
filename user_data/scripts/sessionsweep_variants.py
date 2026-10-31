#!/usr/bin/env python3
"""
Backtest a batch of SessionSweep parameter variants and print one compact table.

For each variant this script writes a temporary parameter file
(user_data/strategies/SessionSweep.json), runs `freqtrade backtesting`, reads the
exported result and reports trades, win rate, profit factor, total profit, max
drawdown and the London vs New York split. Any SessionSweep.json you already had
is backed up first and restored at the end.

Usage (repo root, freqtrade virtualenv active, data already downloaded):
    python user_data/scripts/sessionsweep_variants.py
    python user_data/scripts/sessionsweep_variants.py --timerange 20250101-20251031
    python user_data/scripts/sessionsweep_variants.py --only baseline ny_only

Each backtest takes about a minute on a recent Mac.
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path


STRATEGY = "SessionSweep"
CONFIG = "user_data/config_sessionsweep.json"
PARAM_FILE = Path("user_data/strategies/SessionSweep.json")
RESULTS_DIR = Path("user_data/backtest_results")

# name -> parameter overrides (anything not listed keeps the strategy default)
VARIANTS: dict[str, dict] = {
    "baseline": {},
    "ny_only": {"buy": {"trade_london": False}},
    "london_only": {"buy": {"trade_ny": False}},
    "trend_1h": {"buy": {"use_trend_filter": True}},
    "ny_only_trend": {"buy": {"trade_london": False, "use_trend_filter": True}},
    "min_rr_1.5": {"buy": {"min_rr": 1.5}},
    "lookback_1": {"buy": {"sweep_lookback": 1}},
    "range_min_0.6": {"buy": {"asia_range_min_pct": 0.6}},
    "tp0.75_breakeven": {"sell": {"tp_range_fraction": 0.75, "breakeven_at_midrange": True}},
    "flat_at_17utc": {"sell": {"exit_at_session_end": True}},
}


def default_timerange() -> str:
    end = datetime.now(UTC).date()
    start = end - timedelta(days=365)
    return f"{start:%Y%m%d}-{end:%Y%m%d}"


def run_backtest(timerange: str, label: str) -> Path:
    before = set(RESULTS_DIR.glob("backtest-result-*.zip"))
    cmd = [
        sys.executable, "-m", "freqtrade", "backtesting",
        "--config", CONFIG, "--userdir", "user_data",
        "--strategy", STRATEGY,
        "--timerange", timerange,
        "--cache", "none",
        "--export", "signals",
        "--notes", f"variant {label}",
    ]  # fmt: skip
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout[-3000:], proc.stderr[-3000:], sep="\n")
        raise SystemExit(f"Backtest for variant '{label}' failed (see output above).")
    new = sorted(set(RESULTS_DIR.glob("backtest-result-*.zip")) - before)
    if not new:
        raise SystemExit(f"No new backtest result found for variant '{label}'.")
    return new[-1]


def _pf(profits) -> float:
    gains = profits[profits > 0].sum()
    losses = -profits[profits < 0].sum()
    return float("inf") if losses == 0 else gains / losses


def summarize(result_zip: Path) -> dict:
    """Headline metrics plus the London / NY split from one backtest result."""
    from freqtrade.data.btanalysis import load_backtest_data, load_backtest_stats

    stats = load_backtest_stats(result_zip)["strategy"][STRATEGY]
    trades = load_backtest_data(result_zip, STRATEGY)
    row = {
        "trades": stats["total_trades"],
        "win%": 100 * stats["winrate"],
        "PF": stats["profit_factor"],
        "profit%": 100 * stats["profit_total"],
        "maxDD%": 100 * stats["max_drawdown_account"],
        "maxLossStreak": stats["max_consecutive_losses"],
    }
    for session in ("london", "ny"):
        t = trades[trades["enter_tag"].fillna("").str.startswith(session + "_")]
        row[f"{session}_n"] = len(t)
        row[f"{session}_win%"] = 100 * (t["profit_abs"] > 0).mean() if len(t) else 0.0
        row[f"{session}_PF"] = _pf(t["profit_abs"]) if len(t) else 0.0
        row[f"{session}_usdt"] = t["profit_abs"].sum()
    return row


def print_table(rows: dict[str, dict]) -> None:
    cols = [
        ("trades", "{:>6.0f}"), ("win%", "{:>5.1f}"), ("PF", "{:>5.2f}"),
        ("profit%", "{:>8.1f}"), ("maxDD%", "{:>6.1f}"), ("maxLossStreak", "{:>4.0f}"),
        ("london_n", "{:>4.0f}"), ("london_win%", "{:>5.1f}"), ("london_PF", "{:>5.2f}"),
        ("ny_n", "{:>4.0f}"), ("ny_win%", "{:>5.1f}"), ("ny_PF", "{:>5.2f}"),
    ]  # fmt: skip
    heads = ["trades", "win%", "PF", "profit%", "maxDD%", "LStrk",
             "Ln_n", "Ln_w%", "Ln_PF", "NY_n", "NY_w%", "NY_PF"]  # fmt: skip
    width = max(len(n) for n in rows) + 2
    widths = [len(fmt.format(0)) for _, fmt in cols]
    print("variant".ljust(width) + " ".join(h.rjust(w) for h, w in zip(heads, widths, strict=True)))
    print("-" * (width + sum(widths) + len(widths)))
    for name, r in rows.items():
        print(name.ljust(width) + " ".join(fmt.format(r[k]) for k, fmt in cols))
    print(
        "\nPF = profit factor. maxDD% = max drawdown of the account. LStrk = longest losing streak."
    )
    print("Ln_ / NY_ = trades tagged london_* / ny_*. Profit and drawdown compound the whole")
    print("balance at the configured leverage, so compare PF and win% first.")


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--timerange", default=default_timerange())
    p.add_argument("--only", nargs="+", choices=list(VARIANTS), help="run only these variants")
    args = p.parse_args()

    if not Path(CONFIG).is_file():
        raise SystemExit("Run this from the freqtrade repository root.")
    sys.path.insert(0, str(Path.cwd()))

    backup = PARAM_FILE.with_suffix(".json.bak")
    had_file = PARAM_FILE.is_file()
    if had_file:
        shutil.copy2(PARAM_FILE, backup)

    names = args.only or list(VARIANTS)
    rows: dict[str, dict] = {}
    try:
        for i, name in enumerate(names, 1):
            print(f"[{i}/{len(names)}] {name} ...", flush=True)
            params = {"strategy_name": STRATEGY, "params": VARIANTS[name]}
            PARAM_FILE.write_text(json.dumps(params, indent=2))
            rows[name] = summarize(run_backtest(args.timerange, name))
    finally:
        PARAM_FILE.unlink(missing_ok=True)
        if had_file:
            shutil.move(backup, PARAM_FILE)

    print(f"\nSessionSweep variants, SUI/USDT:USDT, {args.timerange}\n")
    print_table(rows)


if __name__ == "__main__":
    main()
