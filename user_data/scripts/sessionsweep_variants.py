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
    python user_data/scripts/sessionsweep_variants.py --pair BTC/USDT:USDT --only baseline
    # the full robustness check: both pairs, both years, one summary table at the end
    python user_data/scripts/sessionsweep_variants.py --enhance-set \
        --pair SUI/USDT:USDT BTC/USDT:USDT --timerange 20241031-20251031 20251031-20261031

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
    "range_min_1.5": {"buy": {"asia_range_min_pct": 1.5}},
    "range_min_2.5": {"buy": {"asia_range_min_pct": 2.5}},
    "tp0.75_breakeven": {"sell": {"tp_range_fraction": 0.75, "breakeven_at_midrange": True}},
    "flat_at_17utc": {"sell": {"exit_at_session_end": True}},
    # Combinations built on the 1h trend filter, the best single change on 2025-26 data
    "trend_rr1.5": {"buy": {"use_trend_filter": True, "min_rr": 1.5}},
    "trend_flat17": {"buy": {"use_trend_filter": True}, "sell": {"exit_at_session_end": True}},
    "trend_rr1.5_flat17": {
        "buy": {"use_trend_filter": True, "min_rr": 1.5},
        "sell": {"exit_at_session_end": True},
    },
    "trend_ema100": {"buy": {"use_trend_filter": True, "trend_ema_len": 100}},
    "trend_ema20": {"buy": {"use_trend_filter": True, "trend_ema_len": 20}},
}

# The short list worth checking on a second, unseen year.
TREND_SET = ["baseline", "trend_1h", "trend_rr1.5", "trend_flat17", "trend_ema20", "trend_ema100"]

# Structural enhancements (see the strategy docstring). All use 1% risk per trade so
# that drawdowns are comparable; "risk1" alone shows the pure effect of sizing.
RISK = {"risk_per_trade_pct": 1.0}
VARIANTS.update(
    {
        "risk1": {"buy": {**RISK}},
        "risk1_first_sweep": {"buy": {**RISK, "max_trades_per_session": 1}},
        "risk1_mss": {"buy": {**RISK, "require_mss": True}},
        "risk1_displacement": {"buy": {**RISK, "displacement_atr_mult": 1.0}},
        "risk1_retest": {"buy": {**RISK, "entry_retrace_frac": 0.5}},
        "risk1_compression": {"buy": {**RISK, "max_asia_adr_ratio": 0.5}},
        "risk1_timestop6h": {"buy": {**RISK}, "sell": {"max_trade_hours": 6}},
        "risk1_confluence": {
            "buy": {**RISK, "max_trades_per_session": 1, "require_mss": True,
                    "displacement_atr_mult": 0.8},
            "sell": {"max_trade_hours": 8},
        },
    }
)  # fmt: skip
ENHANCE_SET = [
    "risk1", "risk1_first_sweep", "risk1_mss", "risk1_displacement", "risk1_retest",
    "risk1_compression", "risk1_timestop6h", "risk1_confluence",
]  # fmt: skip

# Breakout-confirmation entry model with Fibonacci / resistance targets and the
# flush-reversal exit. All at 1% risk. "brk_all_signals" is the full model:
# sweep -> reclaim -> displacement -> structure break, 61.8% or resistance target,
# flush exit, 8h time stop.
BRK = {**RISK, "entry_mode": "breakout"}
VARIANTS.update(
    {
        "brk": {"buy": {**BRK}},
        "brk_fib50": {"buy": {**BRK}, "sell": {"tp_range_fraction": 0.5}},
        "brk_fib618": {"buy": {**BRK}, "sell": {"tp_range_fraction": 0.618}},
        "brk_resistance": {"buy": {**BRK}, "sell": {"tp_mode": "resistance"}},
        "brk_flush": {"buy": {**BRK}, "sell": {"flush_atr_mult": 1.0}},
        "brk_disp_flush": {
            "buy": {**BRK, "displacement_atr_mult": 0.8}, "sell": {"flush_atr_mult": 1.0},
        },
        "brk_all_signals": {
            "buy": {**BRK, "displacement_atr_mult": 0.8},
            "sell": {"tp_mode": "resistance", "tp_range_fraction": 0.618,
                     "flush_atr_mult": 1.0, "max_trade_hours": 8},
        },
        "reclaim_fib618_flush": {
            "buy": {**RISK}, "sell": {"tp_range_fraction": 0.618, "flush_atr_mult": 1.0},
        },
    }
)  # fmt: skip
ENTRY_SET = [
    "risk1", "brk", "brk_fib50", "brk_fib618", "brk_resistance", "brk_flush",
    "brk_disp_flush", "brk_all_signals", "reclaim_fib618_flush",
]  # fmt: skip

# Session-timing variants, all on the full breakout model. Windows are minutes
# after 00:00 UTC. The Asia window must not cross midnight (ranges are per UTC day).
T_BUY = {**BRK, "displacement_atr_mult": 0.8}
T_SELL = {"tp_mode": "resistance", "tp_range_fraction": 0.618, "flush_atr_mult": 1.0,
          "max_trade_hours": 8}  # fmt: skip


def _t(**over):
    return {"buy": {**T_BUY, **over.get("buy", {})}, "sell": {**T_SELL, **over.get("sell", {})}}


VARIANTS.update(
    {
        "t_base": _t(),
        "t_asia01_08": _t(buy={"asia_start_min": 60, "asia_end_min": 480, "london_start_min": 480}),
        "t_asia00_08": _t(buy={"asia_end_min": 480, "london_start_min": 480}),
        "t_london_07_09": _t(buy={"london_end_min": 540}),
        "t_london_08_11": _t(buy={"london_start_min": 480, "london_end_min": 660}),
        "t_ny_1230_1430": _t(buy={"ny_end_min": 870}),
        "t_ny_1330_1600": _t(buy={"ny_start_min": 810, "ny_end_min": 960}),
        "t_ny_1430_1700": _t(buy={"ny_start_min": 870}),
        "t_london_only": _t(buy={"trade_ny": False}),
        "t_ny_only": _t(buy={"trade_london": False}),
        "t_flat_1700": _t(sell={"exit_at_session_end": True}),
        "t_flat_2100": _t(sell={"exit_at_session_end": True, "flat_time_min": 1260}),
    }
)  # fmt: skip
TIMING_SET = [
    "t_base", "t_asia01_08", "t_asia00_08", "t_london_07_09", "t_london_08_11",
    "t_ny_1230_1430", "t_ny_1330_1600", "t_ny_1430_1700", "t_london_only", "t_ny_only",
    "t_flat_1700", "t_flat_2100",
]  # fmt: skip


def default_timerange() -> str:
    end = datetime.now(UTC).date()
    start = end - timedelta(days=365)
    return f"{start:%Y%m%d}-{end:%Y%m%d}"


def run_backtest(timerange: str, label: str, pair: str) -> Path:
    before = set(RESULTS_DIR.glob("backtest-result-*.zip"))
    cmd = [
        sys.executable, "-m", "freqtrade", "backtesting",
        "--config", CONFIG, "--userdir", "user_data",
        "--strategy", STRATEGY,
        "--timerange", timerange,
        "--pairs", pair,
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
    p.add_argument(
        "--timerange", nargs="+", default=[default_timerange()],
        help="one or more YYYYMMDD-YYYYMMDD ranges; each gets its own table",
    )  # fmt: skip
    p.add_argument("--only", nargs="+", choices=list(VARIANTS), help="run only these variants")
    p.add_argument("--trend-set", action="store_true", help="run only the trend-filter short list")
    p.add_argument(
        "--pair", nargs="+", default=["SUI/USDT:USDT"],
        help="one or more futures pairs (data must be downloaded); each gets its own table",
    )  # fmt: skip
    p.add_argument(
        "--enhance-set", action="store_true", help="run the structural-enhancement variants"
    )
    p.add_argument("--entry-set", action="store_true", help="run the breakout-entry variants")
    p.add_argument("--timing-set", action="store_true", help="run the session-window variants")
    args = p.parse_args()

    if not Path(CONFIG).is_file():
        raise SystemExit("Run this from the freqtrade repository root.")
    sys.path.insert(0, str(Path.cwd()))

    backup = PARAM_FILE.with_suffix(".json.bak")
    had_file = PARAM_FILE.is_file()
    if had_file:
        shutil.copy2(PARAM_FILE, backup)

    sets = {
        "trend_set": TREND_SET, "enhance_set": ENHANCE_SET,
        "entry_set": ENTRY_SET, "timing_set": TIMING_SET,
    }  # fmt: skip
    chosen = [v for k, v in sets.items() if getattr(args, k)]
    names = args.only or (chosen[0] if chosen else list(VARIANTS))
    combos = [(pair, tr) for pair in args.pair for tr in args.timerange]
    total = len(names) * len(combos)
    results: dict[tuple[str, str], dict[str, dict]] = {}
    i = 0
    try:
        for pair, timerange in combos:
            rows: dict[str, dict] = {}
            for name in names:
                i += 1
                print(f"[{i}/{total}] {pair} {timerange} {name} ...", flush=True)
                params = {"strategy_name": STRATEGY, "params": VARIANTS[name]}
                PARAM_FILE.write_text(json.dumps(params, indent=2))
                rows[name] = summarize(run_backtest(timerange, name, pair))
            results[(pair, timerange)] = rows
    finally:
        PARAM_FILE.unlink(missing_ok=True)
        if had_file:
            shutil.move(backup, PARAM_FILE)

    for (pair, timerange), rows in results.items():
        print(f"\nSessionSweep variants, {pair}, {timerange}\n")
        print_table(rows)

    if len(results) > 1:
        print(
            "\nPROFIT FACTOR ACROSS ALL PAIRS / YEARS (a robust rule stays > 1 in every column)\n"
        )
        heads = [f"{p.split('/')[0]} {tr[:4]}-{tr[11:13]}" for p, tr in results]
        width = max(len(n) for n in names) + 2
        print("variant".ljust(width) + " ".join(h.rjust(12) for h in heads) + "      min")
        for name in names:
            pfs = [results[k][name]["PF"] for k in results]
            print(name.ljust(width) + " ".join(f"{pf:12.2f}" for pf in pfs) + f" {min(pfs):8.2f}")


if __name__ == "__main__":
    main()
